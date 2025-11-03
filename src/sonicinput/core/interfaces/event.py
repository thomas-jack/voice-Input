"""事件服务接口定义"""

from abc import ABC, abstractmethod
from typing import Callable, Any, TypeVar, Generic, List, Dict
from dataclasses import dataclass
from enum import Enum

# 定义事件数据类型
EventData = TypeVar("EventData")


class EventPriority(Enum):
    """事件优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event(Generic[EventData]):
    """类型安全的事件定义"""

    name: str
    data: EventData
    priority: EventPriority = EventPriority.NORMAL
    source: str = ""
    timestamp: float = 0.0


class IEventService(ABC):
    """事件服务接口

    提供类型安全的事件发布和订阅功能。
    """

    @abstractmethod
    def emit(
        self,
        event_name: str,
        data: Any = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> None:
        """发出事件

        Args:
            event_name: 事件名称
            data: 事件数据
            priority: 事件优先级
        """
        pass

    @abstractmethod
    def on(
        self,
        event_name: str,
        callback: Callable,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> str:
        """监听事件

        Args:
            event_name: 事件名称
            callback: 回调函数
            priority: 监听器优先级

        Returns:
            监听器ID，用于后续取消监听
        """
        pass

    @abstractmethod
    def off(self, event_name: str, listener_id: str) -> bool:
        """取消监听事件

        Args:
            event_name: 事件名称
            listener_id: 监听器ID

        Returns:
            是否成功取消监听
        """
        pass

    @abstractmethod
    def once(
        self,
        event_name: str,
        callback: Callable,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> str:
        """添加一次性事件监听器

        Args:
            event_name: 事件名称
            callback: 回调函数
            priority: 监听器优先级

        Returns:
            监听器ID
        """
        pass

    @abstractmethod
    def clear_listeners(self, event_name: str) -> int:
        """清除指定事件的所有监听器

        Args:
            event_name: 事件名称

        Returns:
            清除的监听器数量
        """
        pass

    @abstractmethod
    def clear_all_listeners(self) -> int:
        """清除所有事件监听器

        Returns:
            清除的监听器总数
        """
        pass

    @abstractmethod
    def get_event_names(self) -> List[str]:
        """获取所有已注册的事件名称

        Returns:
            事件名称列表
        """
        pass

    @abstractmethod
    def get_listener_count(self, event_name: str) -> int:
        """获取事件监听器数量

        Args:
            event_name: 事件名称

        Returns:
            监听器数量
        """
        pass

    @abstractmethod
    def get_event_stats(self) -> Dict[str, Any]:
        """获取事件统计信息

        Returns:
            事件统计信息，包含发出次数、监听器数量等
        """
        pass

    @property
    @abstractmethod
    def total_listeners(self) -> int:
        """总监听器数量"""
        pass

    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """事件系统是否启用"""
        pass
