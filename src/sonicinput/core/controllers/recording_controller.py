"""录音控制器

负责录音的启动、停止和音频数据处理。
"""

import time
import uuid
from typing import Optional
import numpy as np

from ..interfaces import (
    IRecordingController,
    IAudioService,
    IConfigService,
    IEventService,
    IStateManager,
    ISpeechService,
    IHistoryStorageService,
)
from ..interfaces.state import RecordingState, AppState
from ..services.event_bus import Events
from ...utils import app_logger, ErrorMessageTranslator
from .logging_helper import ControllerLogging


class RecordingController(IRecordingController):
    """录音控制器实现

    职责：
    - 管理录音的启动和停止
    - 处理音频数据回调
    - 通过 StateManager 管理录音状态
    - 通过 EventBus 发送录音事件
    """

    def __init__(
        self,
        audio_service: IAudioService,
        config_service: IConfigService,
        event_service: IEventService,
        state_manager: IStateManager,
        speech_service: ISpeechService,
        history_service: IHistoryStorageService,
    ):
        self._audio_service = audio_service
        self._config = config_service
        self._events = event_service
        self._state = state_manager
        self._speech_service = speech_service
        self._history_service = history_service

        # 录音时长追踪（用于性能统计）
        self._recording_start_time: Optional[float] = None
        self._recording_stop_time: Optional[float] = None
        self._last_audio_duration: float = 0.0

        ControllerLogging.log_initialization("RecordingController")

    def start_recording(self, device_id: Optional[int] = None) -> None:
        """开始录音"""
        # 检查状态并强制重置卡住的状态
        current_app_state = self._state.get_app_state()
        if current_app_state == AppState.PROCESSING:
            app_logger.log_audio_event(
                "Detected stuck PROCESSING state, forcing reset",
                {
                    "current_app_state": current_app_state.name,
                    "recording_state": self._state.get_recording_state().name,
                },
            )
            # 强制重置状态
            ControllerLogging.log_state_change(
                "app",
                AppState.PROCESSING,
                AppState.IDLE,
                {"reason": "detected_stuck_state"},
                is_forced=True
            )
            self._state.set_app_state(AppState.IDLE)
            ControllerLogging.log_state_change(
                "recording",
                self._state.get_recording_state(),
                RecordingState.IDLE,
                is_forced=True
            )
            self._state.set_recording_state(RecordingState.IDLE)

        # 再次检查状态
        if self.is_recording() or self._state.is_processing():
            app_logger.log_audio_event(
                "Cannot start recording - already recording or processing",
                {
                    "is_recording": self.is_recording(),
                    "is_processing": self._state.is_processing(),
                    "app_state": self._state.get_app_state().name,
                    "recording_state": self._state.get_recording_state().name,
                },
            )
            return

        try:
            # 从配置获取设备ID
            if device_id is None:
                device_id = self._config.get_setting("audio.device_id")

            # 每次录音开始时从配置重新读取 streaming_mode（实现配置下次录音生效）
            configured_mode = self._config.get_setting(
                "transcription.local.streaming_mode", "chunked"
            )

            # 尝试更新 streaming coordinator 的模式
            if hasattr(self._speech_service, "streaming_coordinator"):
                coordinator = self._speech_service.streaming_coordinator
                current_mode = coordinator.get_streaming_mode()

                # 如果配置的模式与当前模式不同，需要切换
                if configured_mode != current_mode:
                    app_logger.log_audio_event(
                        "Streaming mode config changed, preparing to switch",
                        {"current_mode": current_mode, "configured_mode": configured_mode}
                    )

                    # 关键修复：先强制停止之前的流（如果存在）
                    if coordinator.is_streaming():
                        app_logger.log_audio_event(
                            "Stopping previous streaming session before mode switch", {}
                        )
                        coordinator.stop_streaming()

                    # 现在可以安全切换模式（流已停止）
                    switch_success = coordinator.set_streaming_mode(configured_mode)
                    final_mode = coordinator.get_streaming_mode()

                    app_logger.log_audio_event(
                        "Streaming mode switch result",
                        {
                            "requested_mode": configured_mode,
                            "switch_success": switch_success,
                            "final_mode": final_mode,
                        }
                    )

                streaming_mode = coordinator.get_streaming_mode()
            else:
                streaming_mode = configured_mode

            app_logger.log_audio_event(
                "Recording starting with streaming mode",
                {"mode": streaming_mode}
            )

            # 根据模式创建不同的会话
            streaming_session = None
            if streaming_mode == "realtime":
                # Realtime 模式：创建 sherpa streaming session
                if hasattr(self._speech_service, "model_manager"):
                    whisper_engine = self._speech_service.model_manager.get_whisper_engine()
                    if whisper_engine and hasattr(whisper_engine, "create_streaming_session"):
                        try:
                            streaming_session = whisper_engine.create_streaming_session()
                            app_logger.log_audio_event("Sherpa streaming session created", {})
                        except Exception as e:
                            app_logger.log_error(e, "create_streaming_session")

            # 启用流式转录模式（使用新的TranscriptionService API）
            if hasattr(self._speech_service, "start_streaming"):
                # 重构后的转录服务，传递 streaming_session
                if hasattr(self._speech_service, "streaming_coordinator"):
                    self._speech_service.streaming_coordinator.start_streaming(streaming_session)
                else:
                    self._speech_service.start_streaming()
                app_logger.log_audio_event("Streaming transcription started", {"session": streaming_session is not None})
            else:
                app_logger.log_audio_event(
                    "Streaming not supported by speech service", {}
                )

            # 根据模式设置不同的回调
            if streaming_mode == "chunked":
                # Chunked 模式：使用 30 秒块回调
                if hasattr(self._audio_service, "chunk_callback") and hasattr(
                    self._speech_service, "add_streaming_chunk"
                ):

                    def streaming_chunk_callback(audio_data):
                        """流式转录块回调"""
                        try:
                            self._speech_service.add_streaming_chunk(audio_data)
                            app_logger.log_audio_event(
                                "Streaming chunk added", {"audio_length": len(audio_data)}
                            )
                        except Exception as e:
                            app_logger.log_error(e, "streaming_chunk_callback")

                    self._audio_service.chunk_callback = streaming_chunk_callback
                    app_logger.log_audio_event("Chunked mode: chunk callback set", {})
                else:
                    self._audio_service.chunk_callback = None
                    app_logger.log_audio_event("Chunked mode: chunk callback not available", {})

                # 设置音频数据回调（用于实时波形显示）
                if hasattr(self._audio_service, "set_callback"):
                    self._audio_service.set_callback(self._on_audio_data)

            elif streaming_mode == "realtime":
                # Realtime 模式：使用持续音频流回调
                if hasattr(self._speech_service, "streaming_coordinator"):

                    def realtime_audio_callback(audio_data):
                        """实时音频流回调"""
                        try:
                            # 发送到 streaming coordinator 的 realtime 处理
                            partial_text = self._speech_service.streaming_coordinator.add_realtime_audio(audio_data)

                            # 同时更新音频电平（用于波形显示）
                            if len(audio_data) > 0:
                                level = float(np.sqrt(np.mean(audio_data**2)))
                                self._events.emit(Events.AUDIO_LEVEL_UPDATE, level)

                        except Exception as e:
                            app_logger.log_error(e, "realtime_audio_callback")

                    # 清除 chunk_callback（realtime 不使用分块）
                    if hasattr(self._audio_service, "chunk_callback"):
                        self._audio_service.chunk_callback = None

                    # 设置持续音频回调
                    if hasattr(self._audio_service, "set_callback"):
                        self._audio_service.set_callback(realtime_audio_callback)
                        app_logger.log_audio_event("Realtime mode: audio callback set", {})
                else:
                    app_logger.log_audio_event("Realtime mode: streaming coordinator not available", {})
                    # Fallback: 使用基本音频回调
                    if hasattr(self._audio_service, "set_callback"):
                        self._audio_service.set_callback(self._on_audio_data)

            # 启动录音
            self._audio_service.start_recording(device_id)

            # 记录录音开始时间
            self._recording_start_time = time.time()

            # 更新状态
            ControllerLogging.log_state_change(
                "recording",
                RecordingState.IDLE,
                RecordingState.RECORDING,
                {"device_id": device_id}
            )
            self._state.set_recording_state(RecordingState.RECORDING)

            # 发送事件
            self._events.emit(Events.RECORDING_STARTED)

            app_logger.log_audio_event(
                "Recording started", {"device_id": device_id, "streaming_enabled": True}
            )

        except Exception as e:
            app_logger.log_error(e, "start_recording")
            # 转换为用户友好消息
            error_info = ErrorMessageTranslator.translate(e, "recording")
            self._events.emit(Events.RECORDING_ERROR, error_info["user_message"])

    def stop_recording(self) -> None:
        """停止录音"""
        if not self.is_recording():
            app_logger.log_audio_event("No recording in progress", {})
            return

        try:
            app_logger.log_audio_event("Stopping recording", {})

            # 停止录音服务
            audio_data = self._audio_service.stop_recording()

            # 记录停止时间和音频时长
            self._recording_stop_time = time.time()
            self._last_audio_duration = (
                self._recording_stop_time - self._recording_start_time
            )

            # 更新状态
            ControllerLogging.log_state_change(
                "recording",
                RecordingState.RECORDING,
                RecordingState.IDLE,
                {"duration": f"{self._last_audio_duration:.1f}s"}
            )
            self._state.set_recording_state(RecordingState.IDLE)

            # 发送录音停止事件
            self._events.emit(Events.RECORDING_STOPPED, len(audio_data))

            # 如果有最后一个音频块，提交给转录服务（使用新的API）
            if (
                len(audio_data) > 0
                and self._speech_service
                and hasattr(self._speech_service, "add_streaming_chunk")
            ):
                try:
                    self._speech_service.add_streaming_chunk(audio_data)
                    app_logger.log_audio_event(
                        "Final streaming chunk added", {"audio_length": len(audio_data)}
                    )
                except Exception as e:
                    app_logger.log_error(e, "add_final_streaming_chunk")
            else:
                app_logger.log_audio_event(
                    "Cannot add final chunk - streaming not available", {}
                )

            # 保存音频文件到历史记录
            record_id = str(uuid.uuid4())
            audio_file_path = None

            try:
                # 生成音频文件路径
                audio_file_path = self._history_service.generate_audio_file_path()

                # 保存音频文件
                if hasattr(self._audio_service, "save_to_file"):
                    save_success = self._audio_service.save_to_file(audio_file_path)
                    if save_success:
                        app_logger.log_audio_event(
                            "Audio file saved to history",
                            {
                                "record_id": record_id,
                                "file_path": audio_file_path,
                                "duration": f"{self._last_audio_duration:.1f}s",
                            }
                        )
                    else:
                        app_logger.log_audio_event(
                            "Failed to save audio file",
                            {"record_id": record_id}
                        )
                        audio_file_path = None
                else:
                    app_logger.log_audio_event(
                        "AudioService does not support save_to_file",
                        {}
                    )
                    audio_file_path = None
            except Exception as e:
                app_logger.log_error(e, "save_audio_file_to_history")
                audio_file_path = None

            # 发送转录请求事件（由 TranscriptionController 监听）
            self._events.emit(
                "transcription_request",
                {
                    "audio_duration": self._last_audio_duration,
                    "recording_stop_time": self._recording_stop_time,
                    "record_id": record_id,
                    "audio_file_path": audio_file_path,
                },
            )

            app_logger.log_audio_event(
                "Recording stopped",
                {
                    "audio_duration": f"{self._last_audio_duration:.1f}s",
                    "final_chunk_length": len(audio_data),
                },
            )

        except Exception as e:
            ControllerLogging.log_state_change(
                "recording",
                RecordingState.RECORDING,
                RecordingState.IDLE,
                {"reason": "error_recovery"},
                is_forced=True
            )
            self._state.set_recording_state(RecordingState.IDLE)
            app_logger.log_error(e, "stop_recording")
            self._events.emit(Events.RECORDING_ERROR, str(e))

    def toggle_recording(self) -> None:
        """切换录音状态"""
        if self.is_recording():
            self.stop_recording()
        else:
            self.start_recording()

    def is_recording(self) -> bool:
        """是否正在录音"""
        return self._state.get_recording_state() == RecordingState.RECORDING

    def get_last_audio_duration(self) -> float:
        """获取最后一次录音的时长（用于性能统计）"""
        return self._last_audio_duration

    def get_recording_stop_time(self) -> Optional[float]:
        """获取最后一次录音停止时间（用于性能统计）"""
        return self._recording_stop_time

    def _on_audio_data(self, audio_data: np.ndarray) -> None:
        """实时音频数据回调

        Args:
            audio_data: 音频数据块
        """
        try:
            if self.is_recording():
                # 计算音频电平
                level = float(np.sqrt(np.mean(audio_data**2)))
                # 发送音频电平更新事件（UI可以监听此事件更新波形）
                self._events.emit(Events.AUDIO_LEVEL_UPDATE, level)

        except Exception as e:
            app_logger.log_error(e, "_on_audio_data")
