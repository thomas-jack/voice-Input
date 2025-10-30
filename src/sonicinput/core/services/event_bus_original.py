"""统一事件总线

基于现有事件系统的增强版本，提供类型安全的事件发布和订阅功能。
支持事件优先级、监听器管理、错误处理和统计功能。
"""

import threading
import time
import uuid
from enum import Enum
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from collections import defaultdict

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
class EventListener:
    """事件监听器信息"""
    id: str
    callback: Callable
    priority: EventPriority
    created_at: float = field(default_factory=time.time)
    call_count: int = 0
    last_called: float = 0.0
    is_once: bool = False


@dataclass
class EventStats:
    """事件统计信息"""
    name: str
    emit_count: int = 0
    listener_count: int = 0
    last_emitted: float = 0.0
    total_processing_time: float = 0.0


class EventBus(IEventService):
    """统一事件总线

    提供线程安全、类型安全的事件发布和订阅功能。
    支持事件优先级、监听器管理、统计和错误处理。
    """

    def __init__(self):
        """初始化事件总线"""
        self._listeners: Dict[str, List[EventListener]] = defaultdict(list)
        self._stats: Dict[str, EventStats] = defaultdict(lambda: EventStats(""))
        self._lock = threading.RLock()
        self._enabled = True

        # 性能优化：缓存机制
        self._sorted_listeners_cache: Dict[str, List[EventListener]] = {}
        self._listener_version: Dict[str, int] = {}

        logger = _get_logger()
        if logger:
            logger.log_audio_event("EventBus initialized", {})

    def _invalidate_cache_for_event(self, event_name: str) -> None:
        """清除指定事件的缓存"""
        keys_to_remove = [key for key in self._sorted_listeners_cache.keys() if key.startswith(f"{event_name}_")]
        for key in keys_to_remove:
            del self._sorted_listeners_cache[key]
        if event_name in self._listener_version:
            del self._listener_version[event_name]

    def emit(self, event_name: str, data: Any = None, priority: EventPriority = EventPriority.NORMAL) -> None:
        """发出事件

        Args:
            event_name: 事件名称
            data: 事件数据
            priority: 事件优先级
        """
        # === DEBUG: 事件发出开始 ===
        import traceback
        start_time = time.time()
        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name

        # 获取logger（避免在锁内导入）
        logger = _get_logger()

        if logger and logger.is_debug_enabled():
            logger.debug("=== EVENT EMIT DEBUG START ===")
            logger.debug(f"Thread: {thread_name} (ID: {thread_id})")
            logger.debug(f"Event name: {event_name}")
            logger.debug(f"Event priority: {priority.name}")
            logger.debug(f"Event enabled: {self._enabled}")
            logger.debug(f"Data type: {type(data).__name__ if data is not None else 'None'}")
            logger.debug(f"Data is None: {data is None}")

            if data is not None:
                try:
                    data_size = len(str(data))
                    logger.debug(f"Data size (string representation): {data_size} chars")
                    if hasattr(data, '__dict__'):
                        logger.debug(f"Data keys: {list(data.__dict__.keys())}")
                except Exception:
                    logger.debug("Could not determine data size/keys")

        if not self._enabled:
            if logger and logger.is_debug_enabled():
                logger.debug("Event bus is disabled, skipping emit")
                logger.debug("=== EVENT EMIT DEBUG END (DISABLED) ===")
            return

        try:
            # === DEBUG: 事件处理准备 ===
            logger = _get_logger()
            if logger and logger.is_debug_enabled():
                logger.debug("Preparing event processing...")

            # 性能优化：使用缓存的已排序监听器
            with self._lock:
                if event_name in self._listeners:
                    # 检查是否需要重新排序
                    current_listeners = self._listeners[event_name]
                    cache_key = f"{event_name}_{len(current_listeners)}"

                    logger = _get_logger()
                    if logger and logger.is_debug_enabled():
                        logger.debug(f"Current listeners count: {len(current_listeners)}")
                        logger.debug(f"Cache key: {cache_key}")
                        logger.debug(f"Cache exists: {cache_key in self._sorted_listeners_cache}")
                        logger.debug(f"Listener version matches: {self._listener_version.get(event_name, 0) == len(current_listeners)}")

                    if (cache_key not in self._sorted_listeners_cache or
                        self._listener_version.get(event_name, 0) != len(current_listeners)):
                        # 需要重新排序和缓存
                        logger = _get_logger()
                        if logger and logger.is_debug_enabled():
                            logger.debug("Re-sorting listeners and updating cache")

                        listeners = sorted(current_listeners, key=lambda x: x.priority.value, reverse=True)
                        self._sorted_listeners_cache[cache_key] = listeners
                        self._listener_version[event_name] = len(current_listeners)
                    else:
                        # 使用缓存的排序结果
                        listeners = self._sorted_listeners_cache[cache_key]
                        logger = _get_logger()
                        if logger and logger.is_debug_enabled():
                            logger.debug("Using cached sorted listeners")
                else:
                    listeners = []
                    logger = _get_logger()
                    if logger and logger.is_debug_enabled():
                        logger.debug("No listeners found for this event")

                logger = _get_logger()
                if logger and logger.is_debug_enabled():
                    logger.debug(f"Final listeners count after sorting: {len(listeners)}")
                    for i, listener in enumerate(listeners[:3]):  # Log first 3 listeners
                        logger.debug(f"Listener {i+1}: ID={listener.id}, Priority={listener.priority.name}, Calls={listener.call_count}")

                # 更新统计信息
                stats = self._stats[event_name]
                stats.name = event_name
                stats.emit_count += 1
                stats.last_emitted = start_time
                stats.listener_count = len(listeners)

        except Exception as cache_error:
            logger = _get_logger()
            if logger and logger.is_debug_enabled():
                logger.debug(f"Error during event preparation: {cache_error}")
                logger.debug(f"Cache error stack trace: {traceback.format_exc()}")
            # 如果缓存出错，使用空监听器列表继续执行
            listeners = []

        # === DEBUG: 执行监听器 ===
        logger = _get_logger()
        if logger and logger.is_debug_enabled():
            logger.debug("Executing listeners...")

        # 在锁外执行监听器，避免死锁
        # 性能优化：收集失败的监听器，循环结束后统一记录错误
        executed_count = 0
        failed_listeners = []
        listener_execution_times = []

        for i, listener in enumerate(listeners):
            listener_start_time = time.time()
            callback_succeeded = False

            logger = _get_logger()
            if logger and logger.is_debug_enabled():
                logger.debug(f"Executing listener {i+1}/{len(listeners)}: ID={listener.id}, Priority={listener.priority.name}")

            try:
                # 执行回调
                if data is not None:
                    listener.callback(data)
                else:
                    listener.callback()
                callback_succeeded = True

                logger = _get_logger()
                if logger and logger.is_debug_enabled():
                    logger.debug(f"Listener {listener.id} executed successfully")

            except Exception as callback_error:
                logger = _get_logger()
                if logger and logger.is_debug_enabled():
                    logger.debug(f"Listener {listener.id} failed: {callback_error}")
                    logger.debug(f"Callback error type: {type(callback_error).__name__}")
                    logger.debug(f"Callback error stack trace: {traceback.format_exc()}")

                failed_listeners.append((listener, callback_error))

            listener_end_time = time.time()
            execution_time = listener_end_time - listener_start_time
            listener_execution_times.append((listener.id, execution_time))

            # 更新监听器统计（仅在成功时）
            if callback_succeeded:
                with self._lock:
                    listener.call_count += 1
                    listener.last_called = time.time()
                executed_count += 1

            # 如果是一次性监听器，无论成功与否都删除（once 的语义）
            if listener.is_once:
                with self._lock:
                    try:
                        self._listeners[event_name].remove(listener)
                        logger = _get_logger()
                        if logger and logger.is_debug_enabled():
                            logger.debug(f"Removed one-time listener {listener.id}")
                    except ValueError:
                        pass  # 监听器可能已被删除

        # === DEBUG: 结果处理 ===
        processing_time = time.time() - start_time
        logger = _get_logger()
        if logger and logger.is_debug_enabled():
            logger.debug(f"Listeners execution summary:")
            logger.debug(f"  - Total listeners: {len(listeners)}")
            logger.debug(f"  - Successfully executed: {executed_count}")
            logger.debug(f"  - Failed: {len(failed_listeners)}")
            logger.debug(f"  - Execution time: {processing_time:.3f}s")

            # Log execution times for first few listeners
            for listener_id, exec_time in listener_execution_times[:3]:
                logger.debug(f"  - Listener {listener_id}: {exec_time:.3f}s")

        # 循环结束后，统一记录失败的监听器
        if failed_listeners:
            logger = _get_logger()
            if logger:
                for listener, error in failed_listeners:
                    logger.log_error(error, f"event_listener_{event_name}_{listener.id}")
                    if logger.is_debug_enabled():
                        logger.debug(f"Error for listener {listener.id}: {error}")

        # 更新处理时间统计
        with self._lock:
            self._stats[event_name].total_processing_time += processing_time

        # 只在DEBUG模式下记录事件日志（减少日志开销）
        # 排除高频事件（audio_level_update, recording_chunk_batch 等）
        high_frequency_events = {"audio_level_update", "recording_chunk_batch"}
        logger = _get_logger()
        if logger and logger.is_debug_enabled() and event_name not in high_frequency_events:
            logger.log_audio_event("Event emitted", {
                "event_name": event_name,
                "listeners_executed": executed_count,
                "has_data": data is not None,
                "priority": priority.name,
                "processing_time_ms": processing_time * 1000
            })

        logger = _get_logger()
        if logger and logger.is_debug_enabled():
            logger.debug("=== EVENT EMIT DEBUG END ===")

    def on(self, event_name: str, callback: Callable, priority: EventPriority = EventPriority.NORMAL) -> str:
        """监听事件

        Args:
            event_name: 事件名称
            callback: 回调函数
            priority: 监听器优先级

        Returns:
            监听器ID，用于后续取消监听
        """
        listener_id = str(uuid.uuid4())
        listener = EventListener(
            id=listener_id,
            callback=callback,
            priority=priority,
            is_once=False
        )

        with self._lock:
            self._listeners[event_name].append(listener)
            # 清除缓存，强制重新排序
            self._invalidate_cache_for_event(event_name)

        # 只在DEBUG模式下记录监听器添加日志（减少日志开销）
        logger = _get_logger()
        if logger and logger.is_debug_enabled():
            logger.log_audio_event("Event listener added", {
                "event_name": event_name,
                "listener_id": listener_id,
                "priority": priority.name,
                "total_listeners": len(self._listeners[event_name])
            })

        return listener_id

    def subscribe(self, event_name: str, callback: Callable, priority: EventPriority = EventPriority.NORMAL) -> str:
        """订阅事件 (alias for on method)

        Args:
            event_name: 事件名称
            callback: 回调函数
            priority: 监听器优先级

        Returns:
            监听器ID，用于后续取消订阅
        """
        return self.on(event_name, callback, priority)

    def off(self, event_name: str, listener_id: str) -> bool:
        """取消监听事件

        Args:
            event_name: 事件名称
            listener_id: 监听器ID

        Returns:
            是否成功取消监听
        """
        with self._lock:
            if event_name not in self._listeners:
                return False

            for listener in self._listeners[event_name]:
                if listener.id == listener_id:
                    self._listeners[event_name].remove(listener)
                    # 清除缓存，强制重新排序
                    self._invalidate_cache_for_event(event_name)

                    # 只在DEBUG模式下记录监听器移除日志（减少日志开销）
                    logger = _get_logger()
                    if logger and logger.is_debug_enabled():
                        logger.log_audio_event("Event listener removed", {
                            "event_name": event_name,
                            "listener_id": listener_id,
                            "remaining_listeners": len(self._listeners[event_name])
                        })

                    # 如果没有监听器了，删除事件键
                    if not self._listeners[event_name]:
                        del self._listeners[event_name]

                    return True

        return False

    def unsubscribe_all(self, event_name: str) -> int:
        """取消订阅指定事件的所有监听器 (alias for clear_listeners)

        Args:
            event_name: 事件名称

        Returns:
            取消订阅的监听器数量
        """
        return self.clear_listeners(event_name)

    def once(self, event_name: str, callback: Callable, priority: EventPriority = EventPriority.NORMAL) -> str:
        """添加一次性事件监听器

        Args:
            event_name: 事件名称
            callback: 回调函数
            priority: 监听器优先级

        Returns:
            监听器ID
        """
        listener_id = str(uuid.uuid4())
        listener = EventListener(
            id=listener_id,
            callback=callback,
            priority=priority,
            is_once=True
        )

        with self._lock:
            self._listeners[event_name].append(listener)

        # 只在DEBUG模式下记录一次性监听器添加日志（减少日志开销）
        logger = _get_logger()
        if logger and logger.is_debug_enabled():
            logger.log_audio_event("One-time event listener added", {
                "event_name": event_name,
                "listener_id": listener_id,
                "priority": priority.name
            })

        return listener_id

    def clear_listeners(self, event_name: str) -> int:
        """清除指定事件的所有监听器

        Args:
            event_name: 事件名称

        Returns:
            清除的监听器数量
        """
        with self._lock:
            if event_name not in self._listeners:
                return 0

            count = len(self._listeners[event_name])
            del self._listeners[event_name]

            # 只在DEBUG模式下记录监听器清除日志（减少日志开销）
            logger = _get_logger()
            if logger and logger.is_debug_enabled():
                logger.log_audio_event("All event listeners cleared", {
                    "event_name": event_name,
                    "cleared_count": count
                })

            return count

    def clear_all_listeners(self) -> int:
        """清除所有事件监听器

        Returns:
            清除的监听器总数
        """
        with self._lock:
            total_count = sum(len(listeners) for listeners in self._listeners.values())
            self._listeners.clear()

            # 只在DEBUG模式下记录所有监听器清除日志（减少日志开销）
            logger = _get_logger()
            if logger and logger.is_debug_enabled():
                logger.log_audio_event("All event listeners cleared", {
                    "total_cleared": total_count
                })

            return total_count

    def get_event_names(self) -> List[str]:
        """获取所有已注册的事件名称

        Returns:
            事件名称列表
        """
        with self._lock:
            return list(self._listeners.keys())

    def get_listener_count(self, event_name: str) -> int:
        """获取事件监听器数量

        Args:
            event_name: 事件名称

        Returns:
            监听器数量
        """
        with self._lock:
            return len(self._listeners.get(event_name, []))

    def get_event_stats(self) -> Dict[str, Any]:
        """获取事件统计信息

        Returns:
            事件统计信息
        """
        with self._lock:
            return {
                "total_events": len(self._stats),
                "total_listeners": self.total_listeners,
                "enabled": self._enabled,
                "events": {
                    name: {
                        "emit_count": stats.emit_count,
                        "listener_count": stats.listener_count,
                        "last_emitted": stats.last_emitted,
                        "avg_processing_time_ms": (
                            (stats.total_processing_time / stats.emit_count * 1000)
                            if stats.emit_count > 0 else 0
                        )
                    }
                    for name, stats in self._stats.items()
                }
            }

    def enable(self) -> None:
        """启用事件总线"""
        self._enabled = True
        # 只在DEBUG模式下记录EventBus状态变更日志（减少日志开销）
        logger = _get_logger()
        if logger and logger.is_debug_enabled():
            logger.log_audio_event("EventBus enabled", {})

    def disable(self) -> None:
        """禁用事件总线"""
        self._enabled = False
        # 只在DEBUG模式下记录EventBus状态变更日志（减少日志开销）
        logger = _get_logger()
        if logger and logger.is_debug_enabled():
            logger.log_audio_event("EventBus disabled", {})

    @property
    def total_listeners(self) -> int:
        """总监听器数量"""
        with self._lock:
            return sum(len(listeners) for listeners in self._listeners.values())

    @property
    def is_enabled(self) -> bool:
        """事件系统是否启用"""
        return self._enabled


# 预定义的事件名称常量（从原有的 Events 类迁移）
class Events(str, Enum):
    """预定义事件名称常量

    使用 str 继承的 Enum 提供类型安全，同时保持向后兼容性。
    Events.RECORDING_STARTED 可以直接作为字符串使用。
    """

    # 录音相关事件
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    RECORDING_ERROR = "recording_error"
    AUDIO_LEVEL_UPDATE = "audio_level_update"

    # 转录相关事件
    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    TRANSCRIPTION_ERROR = "transcription_error"

    # AI优化相关事件
    AI_PROCESSING_STARTED = "ai_processing_started"
    AI_PROCESSING_COMPLETED = "ai_processing_completed"
    AI_PROCESSING_ERROR = "ai_processing_error"

    # 文本输入相关事件
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

    # Whisper模型相关事件
    MODEL_LOADING_STARTED = "model_loading_started"
    MODEL_LOADING_COMPLETED = "model_loading_completed"
    MODEL_LOADING_ERROR = "model_loading_error"
    MODEL_UNLOADED = "model_unloaded"

    # GPU相关事件
    GPU_STATUS_CHANGED = "gpu_status_changed"
    GPU_MEMORY_WARNING = "gpu_memory_warning"

    # 网络相关事件
    NETWORK_ERROR = "network_error"
    API_RATE_LIMITED = "api_rate_limited"

    # 状态变更事件
    STATE_CHANGED = "state_changed"
    APP_STATE_CHANGED = "app_state_changed"
    RECORDING_STATE_CHANGED = "recording_state_changed"

    # 生命周期事件
    COMPONENT_INITIALIZED = "component_initialized"
    COMPONENT_STARTED = "component_started"
    COMPONENT_STOPPED = "component_stopped"
    COMPONENT_ERROR = "component_error"