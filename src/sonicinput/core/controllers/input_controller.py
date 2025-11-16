"""输入控制器

负责文本输入到活动窗口。
"""

import time

from ..interfaces import (
    IInputController,
    IInputService,
    IConfigService,
    IEventService,
    IStateManager,
)
from ..interfaces.state import AppState
from ..services.event_bus import Events
from ...utils import app_logger, logger
from .base_controller import BaseController
from .text_diff_helper import calculate_text_diff


class InputController(BaseController, IInputController):
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
        state_manager: IStateManager,
    ):
        # Initialize base controller
        super().__init__(config_service, event_service, state_manager)

        # Controller-specific services
        self._input_service = input_service

        # Realtime 模式状态追踪（用于实时文本差量更新）
        self._last_realtime_text: str = ""  # 上一次输入的实时文本

        # Register event listeners and log initialization
        self._register_event_listeners()
        self._log_initialization()

    def _register_event_listeners(self) -> None:
        """Register event listeners for input events"""
        # AI 处理完成的文本（chunked 模式）
        self._events.on("ai_processed_text", self._on_text_ready_for_input)

        # 实时文本更新（realtime 模式）
        self._events.on("realtime_text_updated", self._on_realtime_text_updated)

        # 录音开始/停止事件（用于重置状态）
        self._events.on(Events.RECORDING_STARTED, self._on_recording_started)
        self._events.on(Events.RECORDING_STOPPED, self._on_recording_stopped)

        # 转录错误事件（用于恢复剪贴板）
        self._events.on(Events.TRANSCRIPTION_ERROR, self._on_transcription_error_restore_clipboard)

    def _on_text_ready_for_input(self, data: dict) -> None:
        """处理准备好输入的文本事件

        Args:
            data: 包含 text、性能统计数据和 streaming_mode
        """
        # 从事件数据中获取实际的 streaming_mode，而不是依赖本地标志
        streaming_mode = data.get("streaming_mode", "chunked")

        # 关键修复：realtime模式下，文本已经在录音过程中实时输入了
        # 不应该在录音结束后再输入一遍
        if streaming_mode == "realtime":
            app_logger.log_audio_event(
                "Skipping final text input in realtime mode (already input during recording)",
                {
                    "text_length": len(data.get("text", "")),
                    "streaming_mode": streaming_mode
                }
            )

            # 关键修复：realtime 模式下也要恢复剪贴板
            if hasattr(self._input_service, 'stop_recording_mode'):
                self._input_service.stop_recording_mode()

            # 关键修复：即使跳过文本输入，也要触发完成事件和设置状态
            # 让 RecordingOverlay 能够正常隐藏
            self._events.emit(Events.TEXT_INPUT_COMPLETED, "")
            self._state.set_app_state(AppState.IDLE)

            # 记录整体性能日志
            self._log_performance(data)
            return

        text = data.get("text", "")
        if text.strip():
            self.input_text(text)

            # 记录整体性能日志
            self._log_performance(data)
        else:
            # 空文本处理：仍需触发完成事件，让悬浮窗正常关闭
            app_logger.log_audio_event(
                "Empty text received, skipping input but triggering completion",
                {"data_keys": list(data.keys()), "streaming_mode": streaming_mode}
            )

            # 空文本时也要恢复剪贴板
            if hasattr(self._input_service, 'stop_recording_mode'):
                self._input_service.stop_recording_mode()

            # 触发完成事件
            self._events.emit(Events.TEXT_INPUT_COMPLETED, "")
            # 设置状态为 IDLE
            self._state.set_app_state(AppState.IDLE)
            # 记录性能日志
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

                # 文本输入成功后，恢复原始剪贴板内容
                # 修复：将剪贴板恢复从 TRANSCRIPTION_COMPLETED 移到这里，确保在文本输入完成后才恢复
                if hasattr(self._input_service, 'stop_recording_mode'):
                    self._input_service.stop_recording_mode()

                # 重置应用状态为 IDLE（完成整个语音输入流程）
                self._state.set_app_state(AppState.IDLE)

                app_logger.log_audio_event(
                    "Text input completed",
                    {
                        "duration": f"{input_duration:.3f}s",
                        "text_length": len(text),
                        "text": text[:50] + "..." if len(text) > 50 else text,
                    },
                )
                return True
            else:
                self._events.emit(Events.TEXT_INPUT_ERROR, "Failed to input text")

                # 文本输入失败时也要恢复剪贴板
                if hasattr(self._input_service, 'stop_recording_mode'):
                    self._input_service.stop_recording_mode()

                # 即使失败也要重置状态，否则无法进行下一次录音
                self._state.set_app_state(AppState.IDLE)

                return False

        except Exception as e:
            app_logger.log_error(e, "input_text")
            self._events.emit(Events.TEXT_INPUT_ERROR, str(e))

            # 异常时也要恢复剪贴板
            if hasattr(self._input_service, 'stop_recording_mode'):
                self._input_service.stop_recording_mode()

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

        app_logger.log_audio_event("Input method changed", {"method": method})

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
                },
            )

            app_logger.log_audio_event(
                "Voice input completed",
                {
                    "audio_duration": f"{audio_duration:.1f}s",
                    "wait_time": f"{wait_time:.2f}s",
                },
            )

        except Exception as e:
            app_logger.log_error(e, "_log_performance")

    def _on_recording_started(self, data=None) -> None:
        """处理录音开始事件

        启动录音模式（保存原始剪贴板）
        重置 realtime 模式状态，准备接收新的实时文本更新
        """
        # 重置 realtime 文本追踪（用于实时文本差量更新）
        self._last_realtime_text = ""

        # 启动录音模式：SmartTextInput会保存原始剪贴板，并在录音期间禁用中途restore
        try:
            if hasattr(self._input_service, 'start_recording_mode'):
                self._input_service.start_recording_mode()
        except Exception as e:
            app_logger.log_error(e, "start_recording_mode")

        app_logger.log_audio_event(
            "InputController: Recording started, clipboard backup initiated", {}
        )

    def _on_recording_stopped(self, data=None) -> None:
        """处理录音停止事件

        记录录音停止日志，剪贴板恢复会在文本输入完成后自动处理
        """
        app_logger.log_audio_event(
            "InputController: Recording stopped",
            {"last_realtime_text_length": len(self._last_realtime_text)}
        )

    def _on_realtime_text_updated(self, data: dict) -> None:
        """处理实时文本更新事件（realtime 模式）

        使用差量算法计算文本差异，智能更新输入的文本：
        1. 计算新文本与上次文本的差异
        2. 使用退格键删除变化的部分
        3. 输入新的差异部分

        Args:
            data: 包含 'text' 和 'timestamp' 的字典
        """
        try:
            new_text = data.get("text", "")

            # 空文本或无变化则跳过
            if not new_text or new_text == self._last_realtime_text:
                return

            app_logger.log_audio_event(
                "Realtime text update received",
                {
                    "old_text": self._last_realtime_text[:30] + "..." if len(self._last_realtime_text) > 30 else self._last_realtime_text,
                    "new_text": new_text[:30] + "..." if len(new_text) > 30 else new_text,
                }
            )

            # 关键修复：如果新文本为空或显著变短，可能是sherpa reset导致的异常
            # 不应该删除已输入的文本
            if not new_text or len(new_text) < len(self._last_realtime_text) * 0.5:
                app_logger.log_audio_event(
                    "New text is empty or significantly shorter, likely due to stream reset",
                    {
                        "old_length": len(self._last_realtime_text),
                        "new_length": len(new_text),
                        "skipping_diff": True
                    }
                )
                # 不执行差量更新，保持当前已输入的文本
                return

            # 计算文本差异（差量算法）
            backspace_count, text_to_append = calculate_text_diff(
                self._last_realtime_text, new_text
            )

            app_logger.log_audio_event(
                "Calculated text diff",
                {
                    "backspace_count": backspace_count,
                    "append_text": text_to_append[:30] + "..." if len(text_to_append) > 30 else text_to_append,
                }
            )

            # 如果需要退格，先删除旧的部分
            if backspace_count > 0:
                # 使用退格键删除
                backspace_text = "\b" * backspace_count
                self._input_service.input_text(backspace_text)
                app_logger.log_audio_event(
                    "Sent backspace keys",
                    {"count": backspace_count}
                )

            # 输入新的文本
            if text_to_append:
                self._input_service.input_text(text_to_append)
                app_logger.log_audio_event(
                    "Sent new text",
                    {"text": text_to_append[:50] + "..." if len(text_to_append) > 50 else text_to_append}
                )

            # 更新追踪的文本
            self._last_realtime_text = new_text

        except Exception as e:
            app_logger.log_error(e, "_on_realtime_text_updated")

    def _on_transcription_error_restore_clipboard(self, error_msg: str) -> None:
        """处理转录错误事件 - 恢复剪贴板

        转录失败时也要恢复剪贴板，避免用户原始剪贴板内容丢失

        Args:
            error_msg: 错误信息
        """
        try:
            # 即使转录失败，也要恢复剪贴板
            if hasattr(self._input_service, 'stop_recording_mode'):
                self._input_service.stop_recording_mode()
                app_logger.log_audio_event(
                    "Clipboard restore triggered after transcription error",
                    {"error": error_msg[:100] if error_msg else "Unknown error"}
                )
        except Exception as e:
            app_logger.log_error(e, "_on_transcription_error_restore_clipboard")
