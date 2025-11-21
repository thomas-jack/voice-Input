"""事件服务接口定义"""

from abc import ABC, abstractmethod
from typing import Callable, Any
from enum import Enum


class EventPriority(Enum):
    """事件优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class IEventService(ABC):
    """事件服务接口"""

    @abstractmethod
    def emit(self, event: str, data: Any = None) -> None:
        """发出事件"""
        pass

    @abstractmethod
    def on(self, event: str, callback: Callable) -> None:
        """监听事件"""
        pass

    @abstractmethod
    def off(self, event: str, callback: Callable) -> None:
        """取消监听"""
        pass


__all__ = ["EventPriority", "IEventService"]
