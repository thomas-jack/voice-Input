"""流式模式管理器

负责管理 chunked 和 realtime 流式转录模式的切换和会话生命周期。
"""

from typing import Literal

from ..base.lifecycle_component import LifecycleComponent
from ..interfaces import IConfigService, ISpeechService
from ..services.config import ConfigKeys
from ...utils import app_logger

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

        # 云提供商强制禁用流式
        if provider != "local":
            return "disabled"

        # 本地提供商读取配置
        configured_mode = self._config.get_setting(
            ConfigKeys.TRANSCRIPTION_LOCAL_STREAMING_MODE, "chunked"
        )

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
                "Streaming disabled for cloud provider", {"mode": mode}
            )
            return False

        # 检查 speech_service 是否支持流式
        if not hasattr(self._speech_service, "streaming_coordinator"):
            app_logger.log_audio_event(
                "Speech service does not support streaming", {"mode": mode}
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
            self._coordinator.__enter__()

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
            self._coordinator.start_streaming(streaming_session=streaming_session)

            app_logger.log_audio_event(
                "Realtime mode streaming started via context manager", {"session": True}
            )
            return True

        except Exception as e:
            app_logger.log_error(e, "_start_realtime_mode")
            self._coordinator = None
            self._current_session = None
            return False
