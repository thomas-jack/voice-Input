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
    EventSchema,
    EventPlugin,
    EventValidator,
)

# 主要API - 直接使用动态事件系统
EventBus = DynamicEventSystem


# 导出便利的事件名称常量
class Events:
    """常用事件名称常量（向后兼容）"""

    # 录音相关
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    RECORDING_ERROR = "recording_error"
    AUDIO_LEVEL_UPDATE = "audio_level_update"

    # 转录相关
    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    TRANSCRIPTION_ERROR = "transcription_error"
    TRANSCRIPTION_REQUEST = "transcription_request"

    # 模型相关
    MODEL_LOADING_STARTED = "model_loading_started"
    MODEL_LOADING_COMPLETED = "model_loading_completed"
    MODEL_LOADED = "model_loaded"
    MODEL_LOADING_FAILED = "model_loading_failed"
    MODEL_UNLOADED = "model_unloaded"

    # 流式转录相关
    STREAMING_STARTED = "streaming_started"
    STREAMING_STOPPED = "streaming_stopped"
    STREAMING_CHUNK_COMPLETED = "streaming_chunk_completed"

    # AI处理相关
    AI_PROCESSING_STARTED = "ai_processing_started"
    AI_PROCESSING_COMPLETED = "ai_processing_completed"
    AI_PROCESSING_ERROR = "ai_processing_error"

    # 输入相关
    TEXT_INPUT_STARTED = "text_input_started"
    TEXT_INPUT_COMPLETED = "text_input_completed"
    TEXT_INPUT_ERROR = "text_input_error"

    # 应用程序相关
    APP_STARTED = "app_started"
    APP_STOPPING = "app_stopping"
    APP_ERROR = "app_error"
    CONFIG_CHANGED = "config_changed"

    # 错误恢复相关
    ERROR_OCCURRED = "error_occurred"
    ERROR_AUTO_RESOLVED = "error_auto_resolved"


__all__ = [
    "EventBus",
    "DynamicEventSystem",
    # 核心类型
    "EventMetadata",
    "EventSchema",
    "EventPlugin",
    "EventValidator",
    # 便利常量
    "Events",
]
