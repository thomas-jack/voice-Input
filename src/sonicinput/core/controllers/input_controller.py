"""输入控制器

负责文本输入到活动窗口。
"""

import time

from ..interfaces import (
    IInputController,
    IInputService,
    IConfigService,
    IEventService,
    IStateManager
)
from ..interfaces.state import AppState
from ..services.event_bus import Events
from ...utils import app_logger, logger


class InputController(IInputController):
    """输入控制器实现

    职责：
    - 处理文本输入
    - 管理输入方法配置
    - 记录性能指标
    - 通过 EventBus 发送输入事件
    """

    def __init__(
        self,
        input_service: IInputService,
        config_service: IConfigService,
        event_service: IEventService,
        state_manager: IStateManager
    ):
        self._input_service = input_service
        self._config = config_service
        self._events = event_service
        self._state = state_manager

        # 监听AI处理完成事件（或转录完成事件）
        self._events.on("ai_processed_text", self._on_text_ready_for_input)

        app_logger.log_audio_event("InputController initialized", {})

    def _on_text_ready_for_input(self, data: dict) -> None:
        """处理准备好输入的文本事件

        Args:
            data: 包含 text 和性能统计数据
        """
        text = data.get("text", "")
        if text.strip():
            self.input_text(text)

            # 记录整体性能日志
            self._log_performance(data)

    def input_text(self, text: str) -> bool:
        """输入文本

        Args:
            text: 要输入的文本

        Returns:
            是否输入成功
        """
        try:
            self._events.emit(Events.TEXT_INPUT_STARTED, text)

            input_start = time.time()
            success = self._input_service.input_text(text)
            input_duration = time.time() - input_start

            if success:
                self._events.emit(Events.TEXT_INPUT_COMPLETED, text)

                # 重置应用状态为 IDLE（完成整个语音输入流程）
                self._state.set_app_state(AppState.IDLE)

                app_logger.log_audio_event("Text input completed", {
                    "duration": f"{input_duration:.3f}s",
                    "text_length": len(text),
                    "text": text[:50] + "..." if len(text) > 50 else text
                })
                return True
            else:
                self._events.emit(Events.TEXT_INPUT_ERROR, "Failed to input text")

                # 即使失败也要重置状态，否则无法进行下一次录音
                self._state.set_app_state(AppState.IDLE)

                return False

        except Exception as e:
            app_logger.log_error(e, "input_text")
            self._events.emit(Events.TEXT_INPUT_ERROR, str(e))

            # 异常时也要重置状态
            self._state.set_app_state(AppState.IDLE)

            return False

    def set_preferred_method(self, method: str) -> None:
        """设置首选输入方法

        Args:
            method: 输入方法 (clipboard 或 sendinput)
        """
        self._input_service.set_preferred_method(method)
        self._config.set_setting("input.preferred_method", method)

        app_logger.log_audio_event("Input method changed", {
            "method": method
        })

    def _log_performance(self, data: dict) -> None:
        """记录整体性能日志

        Args:
            data: 包含各阶段性能数据
        """
        try:
            audio_duration = data.get("audio_duration", 0.0)
            recording_stop_time = data.get("recording_stop_time", time.time())
            transcribe_duration = data.get("transcribe_duration", 0.0)
            ai_tps = data.get("ai_tps", 0.0)

            # 计算用户等待时间（从录音结束到现在）
            wait_time = time.time() - recording_stop_time

            # 使用统一的性能日志API
            logger.performance(
                "streaming_voice_input",
                wait_time,
                audio_duration=audio_duration,
                details={
                    "wait_time": f"{wait_time:.2f}s",
                    "final_chunk_transcribe": f"{transcribe_duration:.2f}s",
                    "ai_tps": f"{ai_tps:.2f}" if ai_tps > 0 else "N/A",
                }
            )

            app_logger.log_audio_event("Voice input completed", {
                "audio_duration": f"{audio_duration:.1f}s",
                "wait_time": f"{wait_time:.2f}s"
            })

        except Exception as e:
            app_logger.log_error(e, "_log_performance")
