"""核心逻辑模块初始化

重构后的核心模块，包含统一的服务组件和应用组件。
"""

# 核心服务组件
from .services import EventBus, Events, ConfigService, StateManager, LifecycleManager

# 接口定义（显式导入，避免import *）
from .interfaces.ai import IAIService
from .interfaces.audio import IAudioService
from .interfaces.config import IConfigService
from .interfaces.event import IEventService
from .interfaces.hotkey import IHotkeyService
from .interfaces.input import IInputService
from .interfaces.lifecycle import ILifecycleManaged, ILifecycleManager
from .interfaces.speech import ISpeechService
from .interfaces.state import IStateManager
from .interfaces.storage import IStorageService, ICacheService
from .interfaces.ui import IUIComponent, IOverlayComponent, ITrayComponent

# 原有组件（保持向后兼容）
from .hotkey_manager import HotkeyManager

__all__ = [
    # 核心服务组件
    'EventBus',
    'Events',
    'ConfigService',
    'StateManager',
    'LifecycleManager',

    # 接口
    'IAIService',
    'IAudioService',
    'IConfigService',
    'IEventService',
    'IHotkeyService',
    'IInputService',
    'ILifecycleManaged',
    'ILifecycleManager',
    'ISpeechService',
    'IStateManager',
    'IStorageService',
    'ICacheService',
    'IUIComponent',
    'IOverlayComponent',
    'ITrayComponent',

    # 应用组件
    'HotkeyManager'
]