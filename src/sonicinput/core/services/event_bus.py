"""统一事件总线 - 重构后的新实现

重构目标：
- 支持动态事件类型注册
- 支持事件插件系统
- 支持事件验证和命名空间
- 保持高性能和线程安全

新的特性：
1. 动态事件注册 - 运行时注册新事件类型
2. 事件插件系统 - 扩展事件处理能力
3. 事件验证 - 数据完整性检查
4. 命名空间 - 避免事件名称冲突
5. 事件元数据 - 丰富的描述信息

使用方法：
```python
# 创建事件系统
event_bus = DynamicEventSystem()

# 注册事件类型
event_bus.register_event_type(
    "my_custom_event",
    description="我的自定义事件",
    namespace="my_module"
)

# 订阅事件
listener_id = event_bus.subscribe("my_custom_event", callback)

# 发出事件
event_bus.emit("my_custom_event", {"data": "value"})

# 添加插件
event_bus.add_plugin(MyEventPlugin())
```

注意：新的API更强大且灵活，不再受限于预定义的事件枚举。
"""

# 直接导入动态事件系统
from .dynamic_event_system import (
    DynamicEventSystem,
    EventMetadata,
)

# 主要API - 直接使用动态事件系统
EventBus = DynamicEventSystem


# 导出便利的事件名称常量
class Events:
    """Event name constants."""

    # Recording
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    RECORDING_ERROR = "recording_error"
    AUDIO_LEVEL_UPDATE = "audio_level_update"
    RECORDING_STATE_CHANGED = "recording_state_changed"

    # Transcription
    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    TRANSCRIPTION_ERROR = "transcription_error"
    TRANSCRIPTION_REQUEST = "transcription_request"

    # Model loading
    MODEL_LOADING_STARTED = "model_loading_started"
    MODEL_LOADING_COMPLETED = "model_loading_completed"
    MODEL_LOADED = "model_loaded"
    MODEL_LOADING_FAILED = "model_loading_failed"
    MODEL_LOADING_ERROR = "model_loading_error"
    MODEL_UNLOADED = "model_unloaded"

    # Streaming
    STREAMING_STARTED = "streaming_started"
    STREAMING_STOPPED = "streaming_stopped"
    STREAMING_CHUNK_COMPLETED = "streaming_chunk_completed"

    # AI processing
    AI_PROCESSING_STARTED = "ai_processing_started"
    AI_PROCESSING_COMPLETED = "ai_processing_completed"
    AI_PROCESSING_ERROR = "ai_processing_error"

    # Text input
    TEXT_INPUT_STARTED = "text_input_started"
    TEXT_INPUT_COMPLETED = "text_input_completed"
    TEXT_INPUT_ERROR = "text_input_error"

    # Hotkeys
    HOTKEY_TRIGGERED = "hotkey_triggered"
    HOTKEY_REGISTERED = "hotkey_registered"
    HOTKEY_UNREGISTERED = "hotkey_unregistered"
    HOTKEY_CONFLICT = "hotkey_conflict"
    HOTKEY_REGISTRATION_ERROR = "hotkey_registration_error"

    # Config
    CONFIG_CHANGED = "config_changed"
    CONFIG_LOADED = "config_loaded"
    CONFIG_SAVED = "config_saved"
    CONFIG_RESET = "config_reset"
    CONFIG_IMPORTED = "config_imported"

    # UI
    WINDOW_SHOWN = "window_shown"
    WINDOW_HIDDEN = "window_hidden"
    TRAY_CLICKED = "tray_clicked"
    OVERLAY_POSITION_CHANGED = "overlay_position_changed"
    UI_LANGUAGE_CHANGED = "ui_language_changed"

    # App lifecycle/state
    APP_STARTED = "app_started"
    APP_STOPPING = "app_stopping"
    APP_ERROR = "app_error"
    APP_STATE_CHANGED = "app_state_changed"
    STATE_CHANGED = "state_changed"

    # Component lifecycle
    COMPONENT_REGISTERED = "component_registered"
    COMPONENT_UNREGISTERED = "component_unregistered"
    COMPONENT_INITIALIZED = "component_initialized"
    COMPONENT_STARTED = "component_started"
    COMPONENT_STOPPED = "component_stopped"
    COMPONENT_ERROR = "component_error"
    COMPONENT_STATE_CHANGED = "component_state_changed"

    # Network/API
    NETWORK_ERROR = "network_error"
    API_RATE_LIMITED = "api_rate_limited"

    # GPU
    GPU_STATUS_CHANGED = "gpu_status_changed"
    GPU_MEMORY_WARNING = "gpu_memory_warning"

    # Errors
    ERROR_OCCURRED = "error_occurred"
    ERROR_AUTO_RESOLVED = "error_auto_resolved"


__all__ = [
    "EventBus",
    "DynamicEventSystem",
    # 核心类型
    "EventMetadata",
    # 便利常量
    "Events",
]
