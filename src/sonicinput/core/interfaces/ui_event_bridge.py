"""UI事件桥接器接口

负责：
- UI组件事件监听
- UI状态更新桥接
- 向后兼容性支持
- UI与应用逻辑解耦
"""

from typing import Protocol, Any, Callable


class IUIEventBridge(Protocol):
    """UI事件桥接器接口"""

    def setup_overlay_events(self, overlay) -> None:
        """设置悬浮窗事件监听"""
        ...

    def remove_overlay_events(self) -> None:
        """移除悬浮窗事件监听"""
        ...

    def register_custom_event_handler(self, event_name: str, handler: Callable) -> None:
        """注册自定义事件处理器"""
        ...

    def handle_recording_started(self, data: Any = None) -> None:
        """处理录音开始事件"""
        ...

    def handle_recording_stopped(self, data: dict) -> None:
        """处理录音停止事件"""
        ...

    def handle_ai_processing_started(self, data: Any = None) -> None:
        """处理AI处理开始事件"""
        ...

    def handle_ai_processing_completed(self, data: Any = None) -> None:
        """处理AI处理完成事件"""
        ...

    def handle_text_input_completed(self, text: str) -> None:
        """处理文本输入完成事件"""
        ...

    def handle_error(self, error_msg: str) -> None:
        """处理错误事件"""
        ...

    def handle_audio_level_update(self, level: float) -> None:
        """处理音频级别更新事件"""
        ...
