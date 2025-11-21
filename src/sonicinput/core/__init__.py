"""核心逻辑模块初始化

重构后的核心模块，包含统一的服务组件和应用组件。
"""

# 核心服务组件
from .services import EventBus, Events, ConfigService, StateManager

# 接口定义（仅保留多实现接口）
from .interfaces import IAIService, ISpeechService, IInputService

# 原有组件（保持向后兼容）
from .hotkey_manager import HotkeyManager

__all__ = [
    # 核心服务组件
    "EventBus",
    "Events",
    "ConfigService",
    "StateManager",
    # 接口 (仅保留多实现接口)
    "IAIService",
    "ISpeechService",
    "IInputService",
    # 应用组件
    "HotkeyManager",
]
