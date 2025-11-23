"""流式模式管理器

负责管理 chunked 和 realtime 流式转录模式的切换和会话生命周期。
"""

from typing import Literal

from ...utils import app_logger
from ..base.lifecycle_component import LifecycleComponent
from ..interfaces import IConfigService, ISpeechService
from ..services.config import ConfigKeys

StreamingMode = Literal["chunked", "realtime", "disabled"]


class StreamingModeManager(LifecycleComponent):
    """流式模式管理器

    职责：
    - 管理 chunked/realtime 模式切换
    - 启动/停止流式会话（StreamingCoordinator）
    - 创建 sherpa streaming session（realtime 模式）
    - 路由不同模式的配置
    """

    def __init__(
        self,
        config_service: IConfigService,
        speech_service: ISpeechService,
    ):
        """初始化流式模式管理器

        Args:
            config_service: 配置服务
            speech_service: 语音服务（包含 streaming_coordinator）
        """
        super().__init__("StreamingModeManager")

        self._config = config_service
        self._speech_service = speech_service

        # StreamingCoordinator 引用（用于上下文管理器协议）
        self._coordinator = None
        self._current_session = None  # realtime 模式的 sherpa session

    def _do_start(self) -> bool:
        """启动流式模式管理器

        Returns:
            True 如果启动成功
        """
        app_logger.log_audio_event(
            "StreamingModeManager started", {"component": self._component_name}
        )
        return True

    def _do_stop(self) -> bool:
        """停止流式模式管理器并清理资源

        Returns:
            True 如果停止成功
        """
        # 停止任何活动的流式会话
        if self._coordinator is not None:
            self.stop_streaming_session()

        app_logger.log_audio_event(
            "StreamingModeManager stopped", {"component": self._component_name}
        )
        return True

    def get_current_mode(self) -> StreamingMode:
        """获取当前流式模式

        Returns:
            "chunked", "realtime", 或 "disabled"
        """
        provider = self._config.get_setting(ConfigKeys.TRANSCRIPTION_PROVIDER, "local")

        # 读取配置的流式模式（对所有提供商）
        configured_mode = self._config.get_setting(
            ConfigKeys.TRANSCRIPTION_LOCAL_STREAMING_MODE, "chunked"
        )

        # 云提供商：仅支持 chunked 模式（不支持 realtime）
        if provider != "local":
            if configured_mode == "realtime":
                app_logger.log_audio_event(
                    "Cloud provider does not support realtime mode, using chunked",
                    {"provider": provider}
                )
                return "chunked"
            # 允许 chunked 或 disabled
            return configured_mode

        # 本地提供商：支持所有模式
        return configured_mode

    def start_streaming_session(self) -> bool:
        """启动流式转录会话

        根据当前模式启动相应的流式会话：
        - chunked: 启动 chunked 模式
        - realtime: 创建 sherpa session 并启动 realtime 模式
        - disabled: 不启动流式

        Returns:
            True 如果启动成功
        """
        mode = self.get_current_mode()

        if mode == "disabled":
            app_logger.log_audio_event(
                "Streaming disabled", {"mode": mode}
            )
            return False

        # 检查提供商类型
        provider = self._config.get_setting(ConfigKeys.TRANSCRIPTION_PROVIDER, "local")

        # 云提供商：使用 CloudChunkAccumulator 进行分块流式转录
        # 不同于本地提供商的 StreamingCoordinator，云提供商直接调用 start_streaming()
        if provider != "local":
            if mode == "chunked":
                try:
                    # CloudTranscriptionBase 实现了 start_streaming() 方法
                    # 创建 CloudChunkAccumulator 实例用于缓冲和异步转录音频分块
                    if hasattr(self._speech_service, "start_streaming"):
                        self._speech_service.start_streaming()  # type: ignore
                        app_logger.log_audio_event(
                            "Cloud provider streaming started",
                            {"provider": provider, "mode": mode}
                        )
                        return True
                    else:
                        app_logger.log_audio_event(
                            "Cloud provider does not support streaming",
                            {"provider": provider}
                        )
                        return False
                except Exception as e:
                    app_logger.log_error(e, "cloud_start_streaming")
                    return False
            else:
                # 云提供商不支持 realtime 模式（仅本地 sherpa-onnx 支持）
                app_logger.log_audio_event(
                    "Cloud provider does not support realtime mode",
                    {"provider": provider, "mode": mode}
                )
                return False

        # 本地提供商：使用 coordinator（原有逻辑）
        if not hasattr(self._speech_service, "streaming_coordinator"):
            app_logger.log_audio_event(
                "Local speech service does not support streaming", {"mode": mode}
            )
            return False

        coordinator = self._speech_service.streaming_coordinator
        current_mode = coordinator.get_streaming_mode()

        # 如果配置模式与当前模式不同，需要切换
        if mode != current_mode:
            app_logger.log_audio_event(
                "Streaming mode config changed, preparing to switch",
                {
                    "current_mode": current_mode,
                    "configured_mode": mode,
                },
            )

            # 先强制停止之前的流（如果存在）
            if coordinator.is_streaming():
                app_logger.log_audio_event(
                    "Stopping previous streaming session before mode switch", {}
                )
                coordinator.stop_streaming()

            # 现在可以安全切换模式（流已停止）
            switch_success = coordinator.set_streaming_mode(mode)
            final_mode = coordinator.get_streaming_mode()

            app_logger.log_audio_event(
                "Streaming mode switch result",
                {
                    "requested_mode": mode,
                    "switch_success": switch_success,
                    "final_mode": final_mode,
                },
            )

        # 根据模式启动不同的会话
        if mode == "realtime":
            return self._start_realtime_mode(coordinator)
        else:  # chunked
            return self._start_chunked_mode(coordinator)

    def stop_streaming_session(self) -> None:
        """停止流式转录会话并清理资源"""
        # 检查提供商类型
        provider = self._config.get_setting(ConfigKeys.TRANSCRIPTION_PROVIDER, "local")

        # 云提供商：不需要停止（由 TranscriptionController 在获取结果时调用 stop_streaming）
        if provider != "local":
            app_logger.log_audio_event(
                "Cloud provider streaming session lifecycle managed by TranscriptionController",
                {"provider": provider}
            )
            return

        # 本地提供商：使用 coordinator
        if self._coordinator is None:
            return

        try:
            # 显式调用 __exit__() 停止流式转录
            self._coordinator.__exit__(None, None, None)
            app_logger.log_audio_event(
                "Streaming transcription stopped via context manager", {}
            )
        except Exception as e:
            app_logger.log_error(e, "stop_streaming_session")
        finally:
            # 清除引用
            self._coordinator = None
            self._current_session = None

    def _start_chunked_mode(self, coordinator) -> bool:
        """启动 chunked 模式

        Args:
            coordinator: StreamingCoordinator 实例

        Returns:
            True 如果启动成功
        """
        try:
            # 保存 coordinator 引用
            self._coordinator = coordinator

            # 显式调用 __enter__() 启动流式转录
            self._coordinator.__enter__()  # type: ignore

            app_logger.log_audio_event(
                "Chunked mode streaming started via context manager", {"session": None}
            )
            return True

        except Exception as e:
            app_logger.log_error(e, "_start_chunked_mode")
            self._coordinator = None
            return False

    def _start_realtime_mode(self, coordinator) -> bool:
        """启动 realtime 模式并创建 sherpa streaming session

        Args:
            coordinator: StreamingCoordinator 实例

        Returns:
            True 如果启动成功
        """
        try:
            # 创建 sherpa streaming session
            streaming_session = None

            if hasattr(self._speech_service, "model_manager"):
                whisper_engine = self._speech_service.model_manager.get_whisper_engine()

                if whisper_engine and hasattr(
                    whisper_engine, "create_streaming_session"
                ):
                    try:
                        streaming_session = whisper_engine.create_streaming_session()
                        app_logger.log_audio_event(
                            "Sherpa streaming session created", {}
                        )
                    except Exception as e:
                        app_logger.log_error(e, "create_streaming_session")
                        return False

            if streaming_session is None:
                app_logger.log_audio_event(
                    "Failed to create realtime streaming session", {}
                )
                return False

            # 保存 session 和 coordinator 引用
            self._current_session = streaming_session
            self._coordinator = coordinator

            # 显式调用 __enter__() 启动流式转录（传递 session）
            # 注意：必须在设置 session 之前调用 start_streaming
            self._coordinator.start_streaming(streaming_session=streaming_session)  # type: ignore

            app_logger.log_audio_event(
                "Realtime mode streaming started via context manager", {"session": True}
            )
            return True

        except Exception as e:
            app_logger.log_error(e, "_start_realtime_mode")
            self._coordinator = None
            self._current_session = None
            return False
