"""UI事件桥接器实现

负责：
- UI组件事件监听管理
- UI状态更新桥接
- 向后兼容性支持
- UI与应用逻辑解耦
"""

from typing import Dict, Callable, Any, Optional
from ..interfaces import IUIEventBridge, IEventService
from ...utils import app_logger


class UIEventBridge(IUIEventBridge):
    """UI事件桥接器实现

    职责：
    - 管理UI组件与应用逻辑之间的事件通信
    - 提供向后兼容的UI接口
    - 解耦UI层和业务逻辑层
    - 支持自定义事件处理器注册
    """

    def __init__(self, event_service: IEventService):
        """初始化UI事件桥接器

        Args:
            event_service: 事件服务
        """
        self.events = event_service
        self._overlay = None
        self._event_handlers: Dict[str, Callable] = {}
        self._is_listening = False

        app_logger.log_audio_event("UIEventBridge initialized", {})

    def setup_overlay_events(self, overlay) -> None:
        """设置悬浮窗事件监听"""
        if overlay is None:
            return

        self._overlay = overlay

        # 如果还没有开始监听，则开始监听
        if not self._is_listening:
            self._setup_event_listeners()
            self._is_listening = True

        app_logger.log_audio_event("Overlay events setup completed", {})

    def remove_overlay_events(self) -> None:
        """移除悬浮窗事件监听"""
        self._overlay = None
        # 注意：不移除事件监听器，因为其他地方可能还在使用
        app_logger.log_audio_event("Overlay events removed", {})

    def register_custom_event_handler(self, event_name: str, handler: Callable) -> None:
        """注册自定义事件处理器"""
        self._event_handlers[event_name] = handler
        app_logger.log_audio_event(
            "Custom event handler registered",
            {"event_name": event_name}
        )

    def handle_recording_started(self, data: Any = None) -> None:
        """处理录音开始事件"""
        if self._overlay:
            self._overlay.show_recording()

        # 执行自定义处理器
        self._execute_custom_handler("recording_started", data)

    def handle_recording_stopped(self, data: dict) -> None:
        """处理录音停止事件"""
        if self._overlay:
            self._overlay.show_processing()

        # 执行自定义处理器
        self._execute_custom_handler("recording_stopped", data)

    def handle_ai_processing_started(self, data: Any = None) -> None:
        """处理AI处理开始事件"""
        if self._overlay:
            self._overlay.set_status_text("AI Processing...")

        # 执行自定义处理器
        self._execute_custom_handler("ai_processing_started", data)

    def handle_ai_processing_completed(self, data: Any = None) -> None:
        """处理AI处理完成事件"""
        if self._overlay:
            from ...ui.overlay import StatusIndicator
            self._overlay.status_indicator.set_state(
                StatusIndicator.STATE_COMPLETED
            )

        # 执行自定义处理器
        self._execute_custom_handler("ai_processing_completed", data)

    def handle_text_input_completed(self, text: str) -> None:
        """处理文本输入完成事件"""
        if self._overlay:
            self._overlay.show_completed(delay_ms=500)

        # 执行自定义处理器
        self._execute_custom_handler("text_input_completed", text)

    def handle_error(self, error_msg: str) -> None:
        """处理错误事件"""
        if self._overlay:
            # 显示完成状态，然后快速隐藏（1秒后）
            self._overlay.show_completed(delay_ms=1000)

        # 执行自定义处理器
        self._execute_custom_handler("error", error_msg)

    def handle_audio_level_update(self, level: float) -> None:
        """处理音频级别更新事件"""
        if self._overlay:
            self._overlay.update_audio_level(level)

        # 执行自定义处理器
        self._execute_custom_handler("audio_level_update", level)

    def _setup_event_listeners(self) -> None:
        """设置事件监听器"""
        from .event_bus import Events

        # 成功事件
        self.events.on(Events.RECORDING_STARTED, self.handle_recording_started)
        self.events.on(Events.RECORDING_STOPPED, self.handle_recording_stopped)
        self.events.on(Events.AI_PROCESSING_STARTED, self.handle_ai_processing_started)
        self.events.on(Events.AI_PROCESSING_COMPLETED, self.handle_ai_processing_completed)
        self.events.on(Events.TEXT_INPUT_COMPLETED, self.handle_text_input_completed)
        self.events.on(Events.AUDIO_LEVEL_UPDATE, self.handle_audio_level_update)

        # 错误事件
        self.events.on(Events.TRANSCRIPTION_ERROR, self.handle_error)
        self.events.on(Events.AI_PROCESSING_ERROR, self.handle_error)
        self.events.on(Events.TEXT_INPUT_ERROR, self.handle_error)

        app_logger.log_audio_event("Event listeners setup completed", {})

    def _execute_custom_handler(self, event_name: str, data: Any) -> None:
        """执行自定义事件处理器"""
        if event_name in self._event_handlers:
            try:
                self._event_handlers[event_name](data)
            except Exception as e:
                app_logger.log_error(e, f"custom_event_handler_{event_name}")

    @property
    def has_overlay(self) -> bool:
        """检查是否有关联的悬浮窗"""
        return self._overlay is not None