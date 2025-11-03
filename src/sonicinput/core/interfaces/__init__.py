"""核心接口定义模块

统一的接口定义，用于实现高内聚、低耦合的架构设计。
所有服务和组件都应该依赖接口而不是具体实现。
"""

from .config import IConfigService
from .audio import IAudioService
from .speech import ISpeechService
from .ai import IAIService
from .input import IInputService
from .hotkey import IHotkeyService
from .event import IEventService
from .ui import IUIComponent, IOverlayComponent, ITrayComponent
from .storage import IStorageService, ICacheService
from .lifecycle import ILifecycleManaged, ILifecycleManager
from .state import IStateManager
from .controller import (
    IRecordingController,
    ITranscriptionController,
    IAIProcessingController,
    IInputController,
)

__all__ = [
    # 核心服务接口
    "IConfigService",
    "IAudioService",
    "ISpeechService",
    "IAIService",
    "IInputService",
    "IHotkeyService",
    "IEventService",
    # UI组件接口
    "IUIComponent",
    "IOverlayComponent",
    "ITrayComponent",
    # 数据存储接口
    "IStorageService",
    "ICacheService",
    # 生命周期管理接口
    "ILifecycleManaged",
    "ILifecycleManager",
    # 状态管理接口
    "IStateManager",
    # 控制器接口
    "IRecordingController",
    "ITranscriptionController",
    "IAIProcessingController",
    "IInputController",
]
