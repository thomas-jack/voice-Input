"""转录控制器

负责音频转文本的处理逻辑。
"""

import time
import numpy as np

from ..interfaces import (
    ITranscriptionController,
    ISpeechService,
    IConfigService,
    IEventService,
    IStateManager
)
from ..interfaces.state import AppState
from ..services.event_bus import Events
from ...utils import app_logger, ErrorMessageTranslator


class TranscriptionController(ITranscriptionController):
    """转录控制器实现

    职责：
    - 处理音频转录
    - 管理流式转录
    - 通过 EventBus 发送转录事件
    """

    def __init__(
        self,
        speech_service: ISpeechService,
        config_service: IConfigService,
        event_service: IEventService,
        state_manager: IStateManager
    ):
        self._speech_service = speech_service
        self._config = config_service
        self._events = event_service
        self._state = state_manager

        # 性能追踪数据（从 RecordingController 接收）
        self._audio_duration: float = 0.0
        self._recording_stop_time: float = 0.0

        # 监听转录请求事件
        self._events.on("transcription_request", self._on_transcription_request)

        app_logger.log_audio_event("TranscriptionController initialized", {})

    def _on_transcription_request(self, data: dict) -> None:
        """处理转录请求事件

        Args:
            data: 包含 audio_duration 和 recording_stop_time
        """
        self._audio_duration = data.get("audio_duration", 0.0)
        self._recording_stop_time = data.get("recording_stop_time", time.time())

        # 启动流式转录处理
        self.process_streaming_transcription()

    def process_transcription(self, audio_data: np.ndarray) -> None:
        """处理普通转录（非流式）

        Args:
            audio_data: 音频数据
        """
        try:
            self._state.set_app_state(AppState.PROCESSING)
            self._events.emit(Events.TRANSCRIPTION_STARTED)

            # 获取语言配置
            language = self._config.get_setting("whisper.language")
            if language == "auto":
                language = None

            # 执行转录
            transcribe_start = time.time()
            result = self._speech_service.transcribe(audio_data, language=language)
            transcribe_duration = time.time() - transcribe_start

            text = result.get("text", "")

            app_logger.log_audio_event("Transcription completed", {
                "text_length": len(text),
                "duration": f"{transcribe_duration:.2f}s"
            })

            # 发送转录完成事件
            self._events.emit(Events.TRANSCRIPTION_COMPLETED, {"text": text})

        except Exception as e:
            app_logger.log_error(e, "process_transcription")
            # 转换为用户友好消息
            error_info = ErrorMessageTranslator.translate(e, "transcription")
            self._events.emit(Events.TRANSCRIPTION_ERROR, error_info["user_message"])

            # 错误时也要重置状态，否则无法进行下一次录音
            self._state.set_app_state(AppState.IDLE)

    def process_streaming_transcription(self) -> None:
        """处理流式转录（等待所有块完成并拼接）"""
        try:
            self._state.set_app_state(AppState.PROCESSING)
            self._events.emit(Events.TRANSCRIPTION_STARTED)

            # 等待流式转录完成（主要是最后一块）
            transcribe_start = time.time()

            if hasattr(self._speech_service, 'finalize_streaming_transcription'):
                text = self._speech_service.finalize_streaming_transcription(timeout=30.0)
            else:
                text = ""

            transcribe_duration = time.time() - transcribe_start

            app_logger.log_audio_event("Streaming transcription finalized", {
                "text_length": len(text),
                "finalize_duration": f"{transcribe_duration:.3f}s",
                "text_preview": text[:50] + "..." if len(text) > 50 else text
            })

            # 发送转录完成事件（携带文本和音频时长信息）
            self._events.emit(Events.TRANSCRIPTION_COMPLETED, {
                "text": text,
                "audio_duration": self._audio_duration,
                "transcribe_duration": transcribe_duration,
                "recording_stop_time": self._recording_stop_time
            })

        except Exception as e:
            app_logger.log_error(e, "process_streaming_transcription")
            # 转换为用户友好消息
            error_info = ErrorMessageTranslator.translate(e, "transcription")
            self._events.emit(Events.TRANSCRIPTION_ERROR, error_info["user_message"])

            # 错误时也要重置状态，否则无法进行下一次录音
            self._state.set_app_state(AppState.IDLE)

    def start_streaming_mode(self) -> None:
        """启动流式转录模式"""
        if hasattr(self._speech_service, 'start_streaming_mode'):
            self._speech_service.start_streaming_mode()
            app_logger.log_audio_event("Streaming mode started", {})
