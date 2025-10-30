"""动态事件系统 - 支持运行时事件注册和插件扩展

主要改进：
1. 动态事件类型注册 - 支持运行时注册新事件类型
2. 事件验证器 - 支持事件数据验证
3. 事件插件系统 - 支持插件扩展事件功能
4. 事件命名空间 - 避免事件名称冲突
5. 事件元数据 - 支持事件描述、版本等元信息
"""

import threading
import time
import uuid
from enum import Enum
from typing import Callable, Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass, field
from collections import defaultdict
from abc import ABC, abstractmethod

from ..interfaces.event import IEventService, EventPriority


# 延迟导入logger以避免循环依赖
def _get_logger():
    """懒加载logger"""
    try:
        from ...utils import app_logger
        return app_logger
    except ImportError:
        return None


@dataclass
class EventMetadata:
    """事件元数据"""
    name: str
    description: str = ""
    version: str = "1.0.0"
    namespace: str = "default"
    deprecated: bool = False
    deprecation_message: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    created_by: str = "system"


@dataclass
class EventSchema:
    """事件数据模式"""
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    field_types: Dict[str, type] = field(default_factory=dict)
    validators: Dict[str, Callable] = field(default_factory=dict)

    def validate(self, data: Any) -> tuple[bool, List[str]]:
        """验证事件数据"""
        errors = []

        if not isinstance(data, dict):
            errors.append(f"Event data must be a dictionary, got {type(data)}")
            return False, errors

        # 检查必需字段
        for field in self.required_fields:
            if field not in data:
                errors.append(f"Required field '{field}' is missing")

        # 检查字段类型
        for field, expected_type in self.field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                errors.append(f"Field '{field}' must be of type {expected_type.__name__}")

        # 运行自定义验证器
        for field, validator in self.validators.items():
            if field in data:
                try:
                    if not validator(data[field]):
                        errors.append(f"Field '{field}' failed custom validation")
                except Exception as e:
                    errors.append(f"Field '{field}' validation error: {e}")

        return len(errors) == 0, errors


@dataclass
class EventListener:
    """事件监听器信息"""
    id: str
    callback: Callable
    priority: EventPriority
    created_at: float = field(default_factory=time.time)
    call_count: int = 0
    last_called: float = 0.0
    is_once: bool = False
    namespace: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventStats:
    """事件统计信息"""
    name: str
    namespace: str = "default"
    emit_count: int = 0
    listener_count: int = 0
    last_emitted: float = 0.0
    total_processing_time: float = 0.0
    error_count: int = 0


class EventPlugin(ABC):
    """事件插件基类"""

    @abstractmethod
    def get_name(self) -> str:
        """获取插件名称"""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """获取插件版本"""
        pass

    def initialize(self, event_system: 'DynamicEventSystem') -> None:
        """插件初始化"""
        pass

    def cleanup(self) -> None:
        """插件清理"""
        pass

    def on_event_registered(self, event_name: str, metadata: EventMetadata) -> None:
        """事件注册时回调"""
        pass

    def on_event_emitted(self, event_name: str, data: Any) -> None:
        """事件发出时回调"""
        pass

    def on_listener_added(self, event_name: str, listener: EventListener) -> None:
        """监听器添加时回调"""
        pass


class EventValidator:
    """事件验证器"""

    def __init__(self):
        self._schemas: Dict[str, EventSchema] = {}

    def register_schema(self, event_name: str, schema: EventSchema) -> None:
        """注册事件模式"""
        self._schemas[event_name] = schema

    def validate_event(self, event_name: str, data: Any) -> tuple[bool, List[str]]:
        """验证事件数据"""
        schema = self._schemas.get(event_name)
        if not schema:
            return True, []  # 没有模式则跳过验证

        return schema.validate(data)


class DynamicEventSystem(IEventService):
    """动态事件系统

    支持运行时注册事件类型、插件扩展和事件验证。
    完全兼容原有的EventBus接口。
    """

    def __init__(self):
        """初始化动态事件系统"""
        # 基础数据结构
        self._listeners: Dict[str, List[EventListener]] = defaultdict(list)
        self._stats: Dict[str, EventStats] = defaultdict(lambda: EventStats(""))
        self._lock = threading.RLock()
        self._enabled = True

        # 动态事件系统特性
        self._event_metadata: Dict[str, EventMetadata] = {}
        self._event_namespaces: Dict[str, Set[str]] = defaultdict(set)
        self._registered_events: Set[str] = set()

        # 插件系统
        self._plugins: Dict[str, EventPlugin] = {}
        self._plugin_lock = threading.RLock()

        # 验证器
        self._validator = EventValidator()

        # 性能优化：缓存机制
        self._sorted_listeners_cache: Dict[str, List[EventListener]] = {}
        self._listener_version: Dict[str, int] = {}

        # 获取logger
        self.logger = _get_logger()

        # 初始化预定义事件
        self._register_builtin_events()

        if self.logger:
            self.logger.log_audio_event("DynamicEventSystem initialized", {
                "builtin_events": len(self._registered_events)
            })

    def _register_builtin_events(self) -> None:
        """注册内置事件类型"""
        builtin_events = {
            # 录音相关事件
            "recording_started": EventMetadata(
                name="recording_started",
                description="录音开始事件",
                namespace="audio",
                tags=["audio", "recording"]
            ),
            "recording_stopped": EventMetadata(
                name="recording_stopped",
                description="录音停止事件",
                namespace="audio",
                tags=["audio", "recording"]
            ),
            "recording_error": EventMetadata(
                name="recording_error",
                description="录音错误事件",
                namespace="audio",
                tags=["audio", "recording", "error"]
            ),
            "audio_level_update": EventMetadata(
                name="audio_level_update",
                description="音频电平更新事件",
                namespace="audio",
                tags=["audio", "level"]
            ),

            # 转录相关事件
            "transcription_started": EventMetadata(
                name="transcription_started",
                description="转录开始事件",
                namespace="speech",
                tags=["speech", "transcription"]
            ),
            "transcription_completed": EventMetadata(
                name="transcription_completed",
                description="转录完成事件",
                namespace="speech",
                tags=["speech", "transcription"]
            ),
            "transcription_error": EventMetadata(
                name="transcription_error",
                description="转录错误事件",
                namespace="speech",
                tags=["speech", "transcription", "error"]
            ),

            # 模型相关事件
            "model_loading_started": EventMetadata(
                name="model_loading_started",
                description="模型加载开始事件",
                namespace="model",
                tags=["model", "loading"]
            ),
            "model_loaded": EventMetadata(
                name="model_loaded",
                description="模型加载完成事件",
                namespace="model",
                tags=["model", "loading"]
            ),
            "model_loading_failed": EventMetadata(
                name="model_loading_failed",
                description="模型加载失败事件",
                namespace="model",
                tags=["model", "loading", "error"]
            ),
            "model_unloaded": EventMetadata(
                name="model_unloaded",
                description="模型卸载事件",
                namespace="model",
                tags=["model", "loading"]
            ),

            # AI相关事件
            "ai_processing_started": EventMetadata(
                name="ai_processing_started",
                description="AI处理开始事件",
                namespace="ai",
                tags=["ai", "processing"]
            ),
            "ai_processing_completed": EventMetadata(
                name="ai_processing_completed",
                description="AI处理完成事件",
                namespace="ai",
                tags=["ai", "processing"]
            ),
            "ai_processing_error": EventMetadata(
                name="ai_processing_error",
                description="AI处理错误事件",
                namespace="ai",
                tags=["ai", "processing", "error"]
            ),

            # 输入相关事件
            "text_input_started": EventMetadata(
                name="text_input_started",
                description="文本输入开始事件",
                namespace="input",
                tags=["input", "text"]
            ),
            "text_input_completed": EventMetadata(
                name="text_input_completed",
                description="文本输入完成事件",
                namespace="input",
                tags=["input", "text"]
            ),
            "text_input_error": EventMetadata(
                name="text_input_error",
                description="文本输入错误事件",
                namespace="input",
                tags=["input", "text", "error"]
            ),

            # 配置相关事件
            "config_changed": EventMetadata(
                name="config_changed",
                description="配置变更事件",
                namespace="config",
                tags=["config"]
            ),
            "config_loaded": EventMetadata(
                name="config_loaded",
                description="配置加载事件",
                namespace="config",
                tags=["config"]
            ),
            "config_saved": EventMetadata(
                name="config_saved",
                description="配置保存事件",
                namespace="config",
                tags=["config"]
            ),

            # UI相关事件
            "window_shown": EventMetadata(
                name="window_shown",
                description="窗口显示事件",
                namespace="ui",
                tags=["ui", "window"]
            ),
            "window_hidden": EventMetadata(
                name="window_hidden",
                description="窗口隐藏事件",
                namespace="ui",
                tags=["ui", "window"]
            ),
            "tray_clicked": EventMetadata(
                name="tray_clicked",
                description="系统托盘点击事件",
                namespace="ui",
                tags=["ui", "tray"]
            ),

            # 应用程序生命周期事件
            "app_started": EventMetadata(
                name="app_started",
                description="应用程序启动事件",
                namespace="app",
                tags=["app", "lifecycle"]
            ),
            "app_stopping": EventMetadata(
                name="app_stopping",
                description="应用程序停止事件",
                namespace="app",
                tags=["app", "lifecycle"]
            ),

            # 流式转录事件
            "streaming_started": EventMetadata(
                name="streaming_started",
                description="流式转录开始事件",
                namespace="streaming",
                tags=["streaming"]
            ),
            "streaming_stopped": EventMetadata(
                name="streaming_stopped",
                description="流式转录停止事件",
                namespace="streaming",
                tags=["streaming"]
            ),
            "streaming_chunk_completed": EventMetadata(
                name="streaming_chunk_completed",
                description="流式转录块完成事件",
                namespace="streaming",
                tags=["streaming"]
            ),

            # 错误恢复事件
            "error_occurred": EventMetadata(
                name="error_occurred",
                description="错误发生事件",
                namespace="error",
                tags=["error"]
            ),
            "error_auto_resolved": EventMetadata(
                name="error_auto_resolved",
                description="错误自动恢复事件",
                namespace="error",
                tags=["error", "recovery"]
            ),
        }

        for event_name, metadata in builtin_events.items():
            self.register_event_type(event_name, metadata)

    def register_event_type(
        self,
        event_name: str,
        metadata: Optional[EventMetadata] = None,
        schema: Optional[EventSchema] = None
    ) -> None:
        """注册事件类型

        Args:
            event_name: 事件名称
            metadata: 事件元数据
            schema: 事件数据模式
        """
        with self._lock:
            if event_name in self._registered_events:
                if self.logger:
                    self.logger.warning(f"Event '{event_name}' already registered, updating metadata")

            # 创建默认元数据
            if metadata is None:
                metadata = EventMetadata(name=event_name)

            # 注册事件
            self._event_metadata[event_name] = metadata
            self._event_namespaces[metadata.namespace].add(event_name)
            self._registered_events.add(event_name)

            # 注册验证模式
            if schema:
                self._validator.register_schema(event_name, schema)

            # 初始化统计
            if event_name not in self._stats:
                self._stats[event_name] = EventStats(event_name, metadata.namespace)

            # 清除缓存
            self._invalidate_cache_for_event(event_name)

            if self.logger:
                self.logger.log_audio_event("Event type registered", {
                    "event_name": event_name,
                    "namespace": metadata.namespace,
                    "description": metadata.description
                })

            # 通知插件
            self._notify_plugins_event_registered(event_name, metadata)

    def unregister_event_type(self, event_name: str) -> None:
        """注销事件类型

        Args:
            event_name: 事件名称
        """
        with self._lock:
            if event_name not in self._registered_events:
                if self.logger:
                    self.logger.warning(f"Event '{event_name}' not registered")
                return

            # 检查是否有监听器
            if event_name in self._listeners and self._listeners[event_name]:
                if self.logger:
                    self.logger.warning(f"Cannot unregister event '{event_name}' - has active listeners")
                return

            # 移除事件
            metadata = self._event_metadata.get(event_name)
            if metadata:
                self._event_namespaces[metadata.namespace].discard(event_name)
                del self._event_metadata[event_name]

            self._registered_events.discard(event_name)

            # 移除统计
            if event_name in self._stats:
                del self._stats[event_name]

            # 移除验证模式
            if event_name in self._validator._schemas:
                del self._validator._schemas[event_name]

            # 清除缓存
            self._invalidate_cache_for_event(event_name)

            if self.logger:
                self.logger.log_audio_event("Event type unregistered", {
                    "event_name": event_name
                })

    def add_plugin(self, plugin: EventPlugin) -> None:
        """添加事件插件

        Args:
            plugin: 事件插件
        """
        with self._plugin_lock:
            plugin_name = plugin.get_name()

            if plugin_name in self._plugins:
                if self.logger:
                    self.logger.warning(f"Plugin '{plugin_name}' already registered")
                return

            try:
                plugin.initialize(self)
                self._plugins[plugin_name] = plugin

                if self.logger:
                    self.logger.log_audio_event("Event plugin added", {
                        "plugin_name": plugin_name,
                        "plugin_version": plugin.get_version()
                    })

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Failed to initialize plugin '{plugin_name}': {e}")
                raise

    def remove_plugin(self, plugin_name: str) -> None:
        """移除事件插件

        Args:
            plugin_name: 插件名称
        """
        with self._plugin_lock:
            plugin = self._plugins.get(plugin_name)
            if not plugin:
                if self.logger:
                    self.logger.warning(f"Plugin '{plugin_name}' not found")
                return

            try:
                plugin.cleanup()
                del self._plugins[plugin_name]

                if self.logger:
                    self.logger.log_audio_event("Event plugin removed", {
                        "plugin_name": plugin_name
                    })

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error cleaning up plugin '{plugin_name}': {e}")

    def emit(self, event_name: str, data: Any = None, priority: EventPriority = EventPriority.NORMAL) -> None:
        """发出事件（兼容原有接口）

        Args:
            event_name: 事件名称
            data: 事件数据
            priority: 事件优先级
        """
        if not self._enabled:
            return

        start_time = time.time()

        # 检查事件是否已注册
        if event_name not in self._registered_events:
            # 自动注册未定义的事件
            self.register_event_type(event_name)

            if self.logger:
                self.logger.debug(f"Auto-registered event '{event_name}'")

        # 验证事件数据
        is_valid, errors = self._validator.validate_event(event_name, data)
        if not is_valid:
            if self.logger:
                self.logger.error(f"Event data validation failed for '{event_name}': {errors}")
            # 不阻止事件发出，但记录错误

        # 更新统计
        stats = self._stats[event_name]
        stats.emit_count += 1
        stats.last_emitted = time.time()

        try:
            # 获取监听器
            listeners = self._get_sorted_listeners(event_name)

            if not listeners:
                return

            # 执行监听器
            for listener in listeners:
                try:
                    listener_start = time.time()

                    # 执行回调
                    listener.callback(data)

                    # 更新监听器统计
                    listener.call_count += 1
                    listener.last_called = time.time()

                    # 如果是一次性监听器，移除它
                    if listener.is_once:
                        self._remove_listener(event_name, listener.id)

                    # 更新处理时间统计
                    processing_time = time.time() - listener_start
                    stats.total_processing_time += processing_time

                except Exception as e:
                    stats.error_count += 1

                    if self.logger:
                        self.logger.error(f"Error in event listener for '{event_name}': {e}")

                    # 继续处理其他监听器

            # 通知插件
            self._notify_plugins_event_emitted(event_name, data)

        except Exception as e:
            stats.error_count += 1

            if self.logger:
                self.logger.error(f"Error emitting event '{event_name}': {e}")

        # 记录处理时间
        total_time = time.time() - start_time
        if self.logger and total_time > 0.1:  # 只记录慢事件
            self.logger.debug(f"Event '{event_name}' processed in {total_time:.3f}s")

    def subscribe(
        self,
        event_name: str,
        callback: Callable[[Any], None],
        priority: EventPriority = EventPriority.NORMAL,
        is_once: bool = False,
        namespace: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """订阅事件（增强版）

        Args:
            event_name: 事件名称
            callback: 回调函数
            priority: 优先级
            is_once: 是否为一次性监听器
            namespace: 命名空间
            metadata: 监听器元数据

        Returns:
            监听器ID
        """
        with self._lock:
            listener_id = str(uuid.uuid4())

            listener = EventListener(
                id=listener_id,
                callback=callback,
                priority=priority,
                is_once=is_once,
                namespace=namespace,
                metadata=metadata or {}
            )

            self._listeners[event_name].append(listener)

            # 更新统计 - 确保stats对象存在并更新listener_count
            if event_name not in self._stats:
                self._stats[event_name] = EventStats(event_name)
            self._stats[event_name].listener_count = len(self._listeners[event_name])

            # 清除缓存
            self._invalidate_cache_for_event(event_name)

            # 通知插件
            self._notify_plugins_listener_added(event_name, listener)

            if self.logger:
                self.logger.log_audio_event("Event listener added", {
                    "event_name": event_name,
                    "listener_id": listener_id,
                    "priority": priority.name,
                    "is_once": is_once,
                    "namespace": namespace
                })

            return listener_id

    def unsubscribe(self, event_name: str, listener_id: str) -> bool:
        """取消订阅事件

        Args:
            event_name: 事件名称
            listener_id: 监听器ID

        Returns:
            True如果成功取消
        """
        with self._lock:
            return self._remove_listener(event_name, listener_id)

    def _remove_listener(self, event_name: str, listener_id: str) -> bool:
        """移除监听器（内部方法）"""
        if event_name not in self._listeners:
            return False

        original_count = len(self._listeners[event_name])
        self._listeners[event_name] = [
            listener for listener in self._listeners[event_name]
            if listener.id != listener_id
        ]

        removed = len(self._listeners[event_name]) < original_count

        if removed:
            # 更新统计
            if event_name in self._stats:
                self._stats[event_name].listener_count = len(self._listeners[event_name])

            # 清除缓存
            self._invalidate_cache_for_event(event_name)

            if self.logger:
                self.logger.debug(f"Event listener removed: {listener_id} from {event_name}")

        return removed

    def unsubscribe_all(self, event_name: str) -> int:
        """取消所有订阅

        Args:
            event_name: 事件名称

        Returns:
            移除的监听器数量
        """
        with self._lock:
            if event_name not in self._listeners:
                return 0

            count = len(self._listeners[event_name])
            self._listeners[event_name].clear()

            # 更新统计
            if event_name in self._stats:
                self._stats[event_name].listener_count = 0

            # 清除缓存
            self._invalidate_cache_for_event(event_name)

            if self.logger:
                self.logger.log_audio_event("All event listeners removed", {
                    "event_name": event_name,
                    "count": count
                })

            return count

    def _get_sorted_listeners(self, event_name: str) -> List[EventListener]:
        """获取排序后的监听器列表（带缓存）"""
        # 检查缓存
        cache_key = f"{event_name}_{len(self._listeners.get(event_name, []))}"

        if (cache_key in self._sorted_listeners_cache and
            event_name in self._listener_version and
            self._listener_version[event_name] == len(self._listeners.get(event_name, []))):
            return self._sorted_listeners_cache[cache_key].copy()

        # 排序监听器
        listeners = self._listeners.get(event_name, []).copy()
        listeners.sort(key=lambda x: x.priority.value, reverse=True)

        # 缓存结果
        self._sorted_listeners_cache[cache_key] = listeners.copy()
        self._listener_version[event_name] = len(self._listeners[event_name])

        return listeners

    def _invalidate_cache_for_event(self, event_name: str) -> None:
        """清除指定事件的缓存"""
        keys_to_remove = [
            key for key in self._sorted_listeners_cache.keys()
            if key.startswith(f"{event_name}_")
        ]
        for key in keys_to_remove:
            del self._sorted_listeners_cache[key]

        if event_name in self._listener_version:
            del self._listener_version[event_name]

    def get_registered_events(self, namespace: Optional[str] = None) -> List[str]:
        """获取已注册的事件列表

        Args:
            namespace: 命名空间过滤

        Returns:
            事件名称列表
        """
        with self._lock:
            if namespace:
                return list(self._event_namespaces.get(namespace, set()))
            return list(self._registered_events)

    def get_event_metadata(self, event_name: str) -> Optional[EventMetadata]:
        """获取事件元数据

        Args:
            event_name: 事件名称

        Returns:
            事件元数据
        """
        return self._event_metadata.get(event_name)

    def get_event_stats(self, event_name: Optional[str] = None) -> Union[EventStats, Dict[str, EventStats]]:
        """获取事件统计

        Args:
            event_name: 事件名称，None表示获取所有事件统计

        Returns:
            事件统计信息
        """
        with self._lock:
            if event_name:
                return self._stats.get(event_name, EventStats(event_name))
            return dict(self._stats)

    def get_namespaces(self) -> List[str]:
        """获取所有命名空间

        Returns:
            命名空间列表
        """
        with self._lock:
            return list(self._event_namespaces.keys())

    def get_plugins(self) -> List[str]:
        """获取已注册的插件列表

        Returns:
            插件名称列表
        """
        with self._plugin_lock:
            return list(self._plugins.keys())

    def enable(self) -> None:
        """启用事件系统"""
        self._enabled = True

        if self.logger:
            self.logger.log_audio_event("DynamicEventSystem enabled", {})

    def disable(self) -> None:
        """禁用事件系统"""
        self._enabled = False

        if self.logger:
            self.logger.log_audio_event("DynamicEventSystem disabled", {})

    def is_enabled(self) -> bool:
        """检查事件系统是否启用"""
        return self._enabled

    # IEventService接口的额外方法
    def on(self, event_name: str, callback: Callable, priority: EventPriority = EventPriority.NORMAL) -> str:
        """监听事件（IEventService接口）"""
        return self.subscribe(event_name, callback, priority)

    def off(self, event_name: str, listener_id: str) -> bool:
        """取消监听事件（IEventService接口）"""
        return self.unsubscribe(event_name, listener_id)

    def once(self, event_name: str, callback: Callable, priority: EventPriority = EventPriority.NORMAL) -> str:
        """一次性监听事件（IEventService接口）"""
        return self.subscribe(event_name, callback, priority, is_once=True)

    def get_listener_count(self, event_name: str) -> int:
        """获取监听器数量（IEventService接口）"""
        with self._lock:
            return len(self._listeners.get(event_name, []))

    def get_event_names(self) -> List[str]:
        """获取所有事件名称（IEventService接口）"""
        with self._lock:
            return list(self._listeners.keys())

    def total_listeners(self) -> int:
        """获取监听器总数（IEventService接口）"""
        with self._lock:
            return sum(len(listeners) for listeners in self._listeners.values())

    def clear_listeners(self, event_name: str = None) -> int:
        """清除监听器（IEventService接口）"""
        if event_name:
            return self.unsubscribe_all(event_name)
        else:
            self.clear_all_listeners()
            return 0

    def clear_all_listeners(self) -> None:
        """清除所有监听器"""
        with self._lock:
            for event_name in list(self._listeners.keys()):
                self.unsubscribe_all(event_name)

        if self.logger:
            self.logger.log_audio_event("All event listeners cleared", {})

    def cleanup(self) -> None:
        """清理资源"""
        # 移除所有插件
        with self._plugin_lock:
            for plugin_name in list(self._plugins.keys()):
                self.remove_plugin(plugin_name)

        # 清除所有监听器
        self.clear_all_listeners()

        # 清理数据
        with self._lock:
            self._event_metadata.clear()
            self._event_namespaces.clear()
            self._registered_events.clear()
            self._stats.clear()
            self._sorted_listeners_cache.clear()
            self._listener_version.clear()

        if self.logger:
            self.logger.log_audio_event("DynamicEventSystem cleaned up", {})

    def _notify_plugins_event_registered(self, event_name: str, metadata: EventMetadata) -> None:
        """通知插件事件已注册"""
        for plugin in self._plugins.values():
            try:
                plugin.on_event_registered(event_name, metadata)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Plugin error in on_event_registered: {e}")

    def _notify_plugins_event_emitted(self, event_name: str, data: Any) -> None:
        """通知插件事件已发出"""
        for plugin in self._plugins.values():
            try:
                plugin.on_event_emitted(event_name, data)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Plugin error in on_event_emitted: {e}")

    def _notify_plugins_listener_added(self, event_name: str, listener: EventListener) -> None:
        """通知插件监听器已添加"""
        for plugin in self._plugins.values():
            try:
                plugin.on_listener_added(event_name, listener)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Plugin error in on_listener_added: {e}")


# 兼容性：提供原有的事件名称枚举
class Events:
    """预定义事件名称常量（兼容性）"""

    # 录音相关事件
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    RECORDING_ERROR = "recording_error"
    AUDIO_LEVEL_UPDATE = "audio_level_update"

    # 转录相关事件
    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    TRANSCRIPTION_ERROR = "transcription_error"

    # 模型相关事件
    MODEL_LOADING_STARTED = "model_loading_started"
    MODEL_LOADED = "model_loaded"
    MODEL_LOADING_FAILED = "model_loading_failed"
    MODEL_UNLOADED = "model_unloaded"

    # AI相关事件
    AI_PROCESSING_STARTED = "ai_processing_started"
    AI_PROCESSING_COMPLETED = "ai_processing_completed"
    AI_PROCESSING_ERROR = "ai_processing_error"

    # 输入相关事件
    TEXT_INPUT_STARTED = "text_input_started"
    TEXT_INPUT_COMPLETED = "text_input_completed"
    TEXT_INPUT_ERROR = "text_input_error"

    # 快捷键相关事件
    HOTKEY_TRIGGERED = "hotkey_triggered"
    HOTKEY_REGISTERED = "hotkey_registered"
    HOTKEY_UNREGISTERED = "hotkey_unregistered"

    # 配置相关事件
    CONFIG_CHANGED = "config_changed"
    CONFIG_LOADED = "config_loaded"
    CONFIG_SAVED = "config_saved"

    # UI相关事件
    WINDOW_SHOWN = "window_shown"
    WINDOW_HIDDEN = "window_hidden"
    TRAY_CLICKED = "tray_clicked"

    # 应用程序生命周期事件
    APP_STARTED = "app_started"
    APP_STOPPING = "app_stopping"
    APP_ERROR = "app_error"

    # 流式转录事件
    STREAMING_STARTED = "streaming_started"
    STREAMING_STOPPED = "streaming_stopped"
    STREAMING_CHUNK_COMPLETED = "streaming_chunk_completed"

    # 错误恢复事件
    ERROR_OCCURRED = "error_occurred"
    ERROR_AUTO_RESOLVED = "error_auto_resolved"