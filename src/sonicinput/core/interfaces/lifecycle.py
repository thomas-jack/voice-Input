"""生命周期管理接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from enum import Enum


class ComponentState(Enum):
    """组件状态枚举"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    DESTROYED = "destroyed"


class ILifecycleManaged(ABC):
    """生命周期管理接口

    所有需要生命周期管理的组件都应该实现此接口。
    """

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化组件

        Args:
            config: 初始化配置

        Returns:
            是否初始化成功
        """
        pass

    @abstractmethod
    def start(self) -> bool:
        """启动组件

        Returns:
            是否启动成功
        """
        pass

    @abstractmethod
    def stop(self) -> bool:
        """停止组件

        Returns:
            是否停止成功
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass

    @abstractmethod
    def get_state(self) -> ComponentState:
        """获取组件状态

        Returns:
            当前组件状态
        """
        pass

    @abstractmethod
    def get_component_name(self) -> str:
        """获取组件名称

        Returns:
            组件名称
        """
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """健康检查

        Returns:
            健康状态信息
        """
        pass


class ILifecycleManager(ABC):
    """生命周期管理器接口

    负责管理所有组件的生命周期。
    """

    @abstractmethod
    def register_component(self, component: ILifecycleManaged, priority: int = 0) -> bool:
        """注册组件

        Args:
            component: 要注册的组件
            priority: 优先级，数字越大优先级越高

        Returns:
            是否注册成功
        """
        pass

    @abstractmethod
    def unregister_component(self, component_name: str) -> bool:
        """注销组件

        Args:
            component_name: 组件名称

        Returns:
            是否注销成功
        """
        pass

    @abstractmethod
    def initialize_all(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """初始化所有组件

        Args:
            config: 初始化配置

        Returns:
            各组件初始化结果
        """
        pass

    @abstractmethod
    def start_all(self) -> Dict[str, bool]:
        """启动所有组件

        Returns:
            各组件启动结果
        """
        pass

    @abstractmethod
    def stop_all(self) -> Dict[str, bool]:
        """停止所有组件

        Returns:
            各组件停止结果
        """
        pass

    @abstractmethod
    def cleanup_all(self) -> None:
        """清理所有组件资源"""
        pass

    @abstractmethod
    def get_component(self, component_name: str) -> Optional[ILifecycleManaged]:
        """获取组件实例

        Args:
            component_name: 组件名称

        Returns:
            组件实例，不存在时返回None
        """
        pass

    @abstractmethod
    def get_component_state(self, component_name: str) -> Optional[ComponentState]:
        """获取组件状态

        Args:
            component_name: 组件名称

        Returns:
            组件状态，不存在时返回None
        """
        pass

    @abstractmethod
    def get_all_components(self) -> List[str]:
        """获取所有已注册的组件名称

        Returns:
            组件名称列表
        """
        pass

    @abstractmethod
    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """对所有组件进行健康检查

        Returns:
            各组件健康状态
        """
        pass

    @abstractmethod
    def set_state_change_callback(self, callback: Callable[[str, ComponentState, ComponentState], None]) -> None:
        """设置状态变更回调

        Args:
            callback: 回调函数，参数为 (组件名称, 旧状态, 新状态)
        """
        pass

    @abstractmethod
    def restart_component(self, component_name: str) -> bool:
        """重启组件

        Args:
            component_name: 组件名称

        Returns:
            是否重启成功
        """
        pass

    @property
    @abstractmethod
    def total_components(self) -> int:
        """已注册的组件总数"""
        pass

    @property
    @abstractmethod
    def running_components(self) -> int:
        """正在运行的组件数量"""
        pass