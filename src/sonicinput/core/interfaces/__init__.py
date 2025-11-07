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
from .history import IHistoryStorageService, HistoryRecord
from .lifecycle import ILifecycleManaged, ILifecycleManager
from .state import IStateManager
from .config_reload_service import IConfigReloadService
from .application_orchestrator import IApplicationOrchestrator
from .ui_event_bridge import IUIEventBridge
from .service_registry_config import IServiceRegistryConfig
from .controller import (
    IRecordingController,
    ITranscriptionController,
    IAIProcessingController,
    IInputController,
)
from .ui_main_service import (
    IUIMainService,
    IUISettingsService,
    IUIModelService,
    IUIAudioService,
    IUIGPUService,
)
from .plugin_system import (
    IPlugin,
    IPluginContext,
    IPluginManager,
    IPluginRegistry,
    IPluginLoader,
    PluginType,
    PluginStatus,
    BasePlugin,
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
    # 历史记录接口
    "IHistoryStorageService",
    "HistoryRecord",
    # 生命周期管理接口
    "ILifecycleManaged",
    "ILifecycleManager",
    # 状态管理接口
    "IStateManager",
    # 配置重载接口
    "IConfigReloadService",
    # 应用编排接口
    "IApplicationOrchestrator",
    # UI事件桥接接口
    "IUIEventBridge",
    # 服务注册配置接口
    "IServiceRegistryConfig",
    # 控制器接口
    "IRecordingController",
    "ITranscriptionController",
    "IAIProcessingController",
    "IInputController",
    # UI服务接口
    "IUIMainService",
    "IUISettingsService",
    "IUIModelService",
    "IUIAudioService",
    "IUIGPUService",
    # 插件系统接口
    "IPlugin",
    "IPluginContext",
    "IPluginManager",
    "IPluginRegistry",
    "IPluginLoader",
    "PluginType",
    "PluginStatus",
    "BasePlugin",
]
