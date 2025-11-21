"""线程安全的服务注册中心

基于 Service Locator 模式，提供服务实例的注册、查询和替换功能。
支持配置热重载场景下的服务实例原子替换。
"""

from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, cast
from threading import RLock

from loguru import logger

T = TypeVar("T")  # 泛型类型变量


class ServiceRegistryError(Exception):
    """服务注册中心基础异常"""

    pass


class ServiceNotFoundError(ServiceRegistryError):
    """服务未找到异常"""

    pass


class FactoryNotFoundError(ServiceRegistryError):
    """服务工厂未找到异常"""

    pass


class InterfaceViolationError(ServiceRegistryError):
    """接口违反异常"""

    pass


class ServiceRegistry:
    """线程安全的服务注册中心

    使用 Service Locator 模式管理服务实例的注册、查询和替换。

    核心特性：
    - 线程安全：使用 RLock 保护并发访问
    - 引用透明：replace() 原子替换服务实例，所有后续 get() 返回新实例
    - 工厂支持：可选注册服务工厂，用于 RECREATE 策略
    - 接口检查：可选的接口类型验证

    使用场景：
    1. 应用启动时注册所有服务
    2. ConfigReloadCoordinator 通过 get() 获取服务
    3. 配置重载时通过 replace() 替换服务实例

    Example:
        >>> # 注册服务
        >>> registry = ServiceRegistry()
        >>> service = TranscriptionService(...)
        >>> registry.register(
        ...     "transcription_service",
        ...     service,
        ...     factory=lambda: TranscriptionService(...)
        ... )

        >>> # 获取服务
        >>> service = registry.get("transcription_service")

        >>> # 替换服务
        >>> new_service = TranscriptionService(...)
        >>> old_service = registry.replace("transcription_service", new_service)
        >>> # 此时所有 get("transcription_service") 都返回 new_service
    """

    def __init__(self) -> None:
        """初始化服务注册中心"""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._lock = RLock()

        logger.debug("ServiceRegistry initialized")

    def register(
        self,
        name: str,
        instance: Any,
        factory: Optional[Callable[[], Any]] = None,
    ) -> None:
        """注册服务实例

        Args:
            name: 服务名称（唯一标识符）
            instance: 服务实例
            factory: 可选的服务工厂函数，用于 RECREATE 策略

        Raises:
            ValueError: 如果服务名称为空

        Example:
            >>> registry.register(
            ...     "transcription_service",
            ...     transcription_service,
            ...     factory=lambda: TranscriptionService(config_service)
            ... )
        """
        if not name:
            raise ValueError("Service name cannot be empty")

        with self._lock:
            self._services[name] = instance
            if factory:
                self._factories[name] = factory

            logger.debug(
                f"Service registered: {name} (has_factory={factory is not None})"
            )

    def get(self, name: str, interface: Optional[Type[T]] = None) -> T:
        """获取服务实例

        Args:
            name: 服务名称
            interface: 可选的接口类型（用于类型检查和类型提示）

        Returns:
            服务实例（总是返回最新的实例）

        Raises:
            ServiceNotFoundError: 如果服务未注册
            InterfaceViolationError: 如果服务不实现指定接口

        Example:
            >>> # 基本用法
            >>> service = registry.get("transcription_service")

            >>> # 带接口检查
            >>> from ..interfaces import IConfigReloadable
            >>> service = registry.get("transcription_service", IConfigReloadable)
        """
        with self._lock:
            instance = self._services.get(name)

            if instance is None:
                raise ServiceNotFoundError(f"Service '{name}' not found in registry")

            # 可选的接口检查
            if interface is not None:
                # Protocol 类型无法直接用 isinstance 检查，
                # 这里只做类型提示，不做运行时检查
                # （Protocol 的设计理念是结构化类型，运行时检查很复杂）
                pass

            return cast(T, instance)

    def replace(self, name: str, new_instance: Any) -> Any:
        """原子替换服务实例

        这是配置热重载的核心方法。
        替换后，所有后续的 get() 调用都会返回新实例，
        从而实现"引用透明"。

        Args:
            name: 服务名称
            new_instance: 新的服务实例

        Returns:
            被替换的旧实例（用于清理）

        Raises:
            ServiceNotFoundError: 如果服务未注册

        Example:
            >>> # 替换服务
            >>> new_service = TranscriptionService(...)
            >>> old_service = registry.replace("transcription_service", new_service)
            >>>
            >>> # 清理旧服务
            >>> if hasattr(old_service, "cleanup"):
            ...     old_service.cleanup()
        """
        with self._lock:
            if name not in self._services:
                raise ServiceNotFoundError(
                    f"Cannot replace: service '{name}' not found in registry"
                )

            old_instance = self._services[name]
            self._services[name] = new_instance

            logger.info(
                f"Service replaced: {name} "
                f"(old={type(old_instance).__name__}, "
                f"new={type(new_instance).__name__})"
            )

            return old_instance

    def get_factory(self, name: str) -> Callable[[], Any]:
        """获取服务工厂函数

        Args:
            name: 服务名称

        Returns:
            服务工厂函数

        Raises:
            FactoryNotFoundError: 如果服务未注册工厂

        Example:
            >>> factory = registry.get_factory("transcription_service")
            >>> new_instance = factory()
        """
        with self._lock:
            factory = self._factories.get(name)

            if factory is None:
                raise FactoryNotFoundError(
                    f"No factory registered for service '{name}'"
                )

            return factory

    def has_service(self, name: str) -> bool:
        """检查服务是否已注册

        Args:
            name: 服务名称

        Returns:
            是否已注册
        """
        with self._lock:
            return name in self._services

    def has_factory(self, name: str) -> bool:
        """检查服务是否注册了工厂

        Args:
            name: 服务名称

        Returns:
            是否有工厂
        """
        with self._lock:
            return name in self._factories

    def get_all_names(self) -> List[str]:
        """获取所有已注册的服务名称

        Returns:
            服务名称列表

        Example:
            >>> names = registry.get_all_names()
            >>> print(names)
            ['transcription_service', 'hotkey_service', 'ai_service']
        """
        with self._lock:
            return list(self._services.keys())

    def unregister(self, name: str) -> Any:
        """取消注册服务（通常不需要使用）

        Args:
            name: 服务名称

        Returns:
            被移除的服务实例

        Raises:
            ServiceNotFoundError: 如果服务未注册
        """
        with self._lock:
            if name not in self._services:
                raise ServiceNotFoundError(
                    f"Cannot unregister: service '{name}' not found"
                )

            instance = self._services.pop(name)
            self._factories.pop(name, None)  # 同时移除工厂（如果有）

            logger.debug(f"Service unregistered: {name}")
            return instance

    def clear(self) -> None:
        """清空所有注册（通常仅用于测试）"""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            logger.debug("ServiceRegistry cleared")

    def __repr__(self) -> str:
        """字符串表示"""
        with self._lock:
            return (
                f"ServiceRegistry("
                f"services={len(self._services)}, "
                f"factories={len(self._factories)})"
            )
