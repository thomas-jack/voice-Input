"""性能监控装饰器

提供方法级别的性能监控、日志记录和缓存功能。
"""

import time
import functools
import threading
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

from ..interfaces.event import IEventService, EventPriority


@dataclass
class PerformanceMetrics:
    """性能指标数据"""
    method_name: str
    call_count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    last_call_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, event_service: Optional[IEventService] = None):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.event_service = event_service
        self._lock = threading.RLock()

    def record_execution(self, method_name: str, execution_time: float,
                        success: bool = True, cache_hit: bool = False):
        """记录执行指标"""
        with self._lock:
            if method_name not in self.metrics:
                self.metrics[method_name] = PerformanceMetrics(method_name=method_name)

            metrics = self.metrics[method_name]
            metrics.call_count += 1
            metrics.total_time += execution_time
            metrics.last_call_time = time.time()

            if execution_time < metrics.min_time:
                metrics.min_time = execution_time
            if execution_time > metrics.max_time:
                metrics.max_time = execution_time

            if not success:
                metrics.error_count += 1

            if cache_hit:
                metrics.cache_hits += 1
            else:
                metrics.cache_misses += 1

            # 发送事件（如果有事件服务）
            if self.event_service and metrics.call_count % 10 == 0:  # 每10次调用记录一次
                self.event_service.emit("performance_metrics", {
                    "method": method_name,
                    "call_count": metrics.call_count,
                    "avg_time": metrics.total_time / metrics.call_count,
                    "min_time": metrics.min_time,
                    "max_time": metrics.max_time,
                    "cache_hit_rate": metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) if (metrics.cache_hits + metrics.cache_misses) > 0 else 0,
                    "error_rate": metrics.error_count / metrics.call_count
                }, EventPriority.LOW)

    def get_metrics(self, method_name: Optional[str] = None) -> Dict[str, Any]:
        """获取性能指标"""
        with self._lock:
            if method_name:
                if method_name in self.metrics:
                    metrics = self.metrics[method_name]
                    return {
                        "method_name": metrics.method_name,
                        "call_count": metrics.call_count,
                        "total_time": metrics.total_time,
                        "avg_time": metrics.total_time / metrics.call_count if metrics.call_count > 0 else 0,
                        "min_time": metrics.min_time if metrics.min_time != float('inf') else 0,
                        "max_time": metrics.max_time,
                        "last_call_time": metrics.last_call_time,
                        "cache_hits": metrics.cache_hits,
                        "cache_misses": metrics.cache_misses,
                        "cache_hit_rate": metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses) if (metrics.cache_hits + metrics.cache_misses) > 0 else 0,
                        "error_count": metrics.error_count,
                        "error_rate": metrics.error_count / metrics.call_count if metrics.call_count > 0 else 0
                    }
                return {}

            return {
                name: self.get_metrics(name) for name in self.metrics.keys()
            }

    def reset_metrics(self, method_name: Optional[str] = None):
        """重置指标"""
        with self._lock:
            if method_name:
                if method_name in self.metrics:
                    del self.metrics[method_name]
            else:
                self.metrics.clear()


class BaseDecorator(ABC):
    """装饰器基类"""

    def __init__(self, func: Callable):
        self.func = func
        functools.update_wrapper(self, func)

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class PerformanceDecorator(BaseDecorator):
    """性能监控装饰器"""

    def __init__(self, func: Callable,
                 monitor: Optional[PerformanceMonitor] = None,
                 log_slow_calls: bool = True,
                 slow_threshold: float = 1.0):
        super().__init__(func)
        self.monitor = monitor or PerformanceMonitor()
        self.log_slow_calls = log_slow_calls
        self.slow_threshold = slow_threshold

    def __call__(self, *args, **kwargs):
        start_time = time.perf_counter()
        success = False
        result = None
        error = None

        try:
            result = self.func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            error = e
            raise
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            self.monitor.record_execution(
                method_name=self.func.__name__,
                execution_time=execution_time,
                success=success,
                cache_hit=False
            )

            # 记录慢调用
            if self.log_slow_calls and execution_time > self.slow_threshold:
                logging.warning(f"Slow call detected: {self.func.__name__} took {execution_time:.3f}s")

            if error and self.monitor.event_service:
                self.monitor.event_service.emit("method_error", {
                    "method": self.func.__name__,
                    "execution_time": execution_time,
                    "error": str(error),
                    "error_type": type(error).__name__
                }, EventPriority.HIGH)


class CacheDecorator(BaseDecorator):
    """缓存装饰器"""

    def __init__(self, func: Callable,
                 max_size: int = 128,
                 ttl: Optional[float] = None,
                 key_func: Optional[Callable] = None):
        super().__init__(func)
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.key_func = key_func or self._default_key_func
        self.monitor = PerformanceMonitor()

    def _default_key_func(self, *args, **kwargs) -> str:
        """默认键生成函数"""
        return str(args) + str(sorted(kwargs.items()))

    def _is_cache_valid(self, entry: Dict) -> bool:
        """检查缓存是否有效"""
        if self.ttl is None:
            return True
        return time.time() - entry['timestamp'] < self.ttl

    def __call__(self, *args, **kwargs):
        # 生成缓存键
        cache_key = self.key_func(*args, **kwargs)

        # 检查缓存
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if self._is_cache_valid(entry):
                self.monitor.record_execution(
                    method_name=self.func.__name__,
                    execution_time=0,
                    success=True,
                    cache_hit=True
                )
                return entry['value']
            else:
                # 缓存过期，删除
                del self.cache[cache_key]

        # 执行函数
        start_time = time.perf_counter()
        result = self.func(*args, **kwargs)
        execution_time = time.perf_counter() - start_time

        # 更新缓存
        self.cache[cache_key] = {
            'value': result,
            'timestamp': time.time()
        }

        # 缓存大小控制
        if len(self.cache) > self.max_size:
            oldest_key = min(self.cache.keys(),
                           key=lambda k: self.cache[k]['timestamp'])
            del self.cache[oldest_key]

        self.monitor.record_execution(
            method_name=self.func.__name__,
            execution_time=execution_time,
            success=True,
            cache_hit=False
        )

        return result

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()


class LoggingDecorator(BaseDecorator):
    """日志装饰器"""

    def __init__(self, func: Callable,
                 log_args: bool = True,
                 log_result: bool = True,
                 log_errors: bool = True):
        super().__init__(func)
        self.log_args = log_args
        self.log_result = log_result
        self.log_errors = log_errors

    def __call__(self, *args, **kwargs):
        # 记录参数
        if self.log_args:
            logging.info(f"Calling {self.func.__name__} with args: {args}, kwargs: {kwargs}")

        try:
            result = self.func(*args, **kwargs)

            # 记录结果
            if self.log_result:
                logging.info(f"{self.func.__name__} returned: {result}")

            return result

        except Exception as e:
            # 记录错误
            if self.log_errors:
                logging.error(f"{self.func.__name__} failed with error: {e}")
            raise


def performance_monitor(monitor: Optional[PerformanceMonitor] = None):
    """性能监控装饰器工厂"""
    def decorator(func: Callable) -> PerformanceDecorator:
        return PerformanceDecorator(func, monitor)
    return decorator


def cache_decorator(max_size: int = 128, ttl: Optional[float] = None):
    """缓存装饰器工厂"""
    def decorator(func: Callable) -> CacheDecorator:
        return CacheDecorator(func, max_size, ttl)
    return decorator


def logging_decorator(log_args: bool = True, log_result: bool = True):
    """日志装饰器工厂"""
    def decorator(func: Callable) -> LoggingDecorator:
        return LoggingDecorator(func, log_args, log_result)
    return decorator