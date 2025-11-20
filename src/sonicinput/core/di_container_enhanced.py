"""增强的依赖注入容器 - 解耦优化版本

主要改进：
1. 服务描述符模式 - 解耦服务创建逻辑
2. 生命周期管理 - 支持单例、瞬态、作用域
3. 装饰器模式 - 支持服务装饰和增强
4. 配置驱动 - 支持从配置文件注册服务
5. 循环依赖检测 - 自动检测和报告循环依赖
"""

import threading
import time
from typing import Dict, Type, Any, TypeVar, Callable, Optional, List, Set, Union
from enum import Enum
from dataclasses import dataclass, field
import inspect

# 导入新的配置重载组件
from .services.service_registry import ServiceRegistry as ConfigReloadServiceRegistry
from .services.config_reload_coordinator import ConfigReloadCoordinator

# 接口导入
from .interfaces.ai import IAIService
from .interfaces.audio import IAudioService
from .interfaces.config import IConfigService
from .interfaces.event import IEventService
from .interfaces.config_reload_service import IConfigReloadService
from .interfaces.application_orchestrator import IApplicationOrchestrator
from .interfaces.ui_event_bridge import IUIEventBridge
from .interfaces.hotkey import IHotkeyService
from .interfaces.input import IInputService
from .interfaces.speech import ISpeechService
from .interfaces.state import IStateManager
from .interfaces.history import IHistoryStorageService

# UI 服务接口
from .interfaces.ui_main_service import (
    IUIMainService,
    IUISettingsService,
    IUIModelService,
    IUIAudioService,
    IUIGPUService,
)

T = TypeVar("T")


class ServiceLifetime(Enum):
    """服务生命周期"""

    TRANSIENT = "transient"  # 每次请求都创建新实例
    SINGLETON = "singleton"  # 整个容器生命周期内只有一个实例
    SCOPED = "scoped"  # 在特定作用域内是单例


@dataclass
class ServiceDescriptor:
    """服务描述符"""

    interface: Type
    implementation: Optional[Type] = None
    factory: Optional[Callable] = None
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    dependencies: List[Type] = field(default_factory=list)
    decorators: List[Callable] = field(default_factory=list)
    lazy: bool = False
    name: Optional[str] = None

    def __post_init__(self):
        if self.name is None:
            self.name = self.interface.__name__


@dataclass
class ServiceCreationContext:
    """服务创建上下文"""

    creating: Set[Type] = field(default_factory=set)
    created: Dict[Type, Any] = field(default_factory=dict)
    depth: int = 0

    def is_creating(self, service_type: Type) -> bool:
        return service_type in self.creating

    def add_creating(self, service_type: Type):
        self.creating.add(service_type)

    def remove_creating(self, service_type: Type):
        self.creating.discard(service_type)

    def add_created(self, service_type: Type, instance: Any):
        self.created[service_type] = instance


class ServiceRegistry:
    """服务注册表 - 管理服务描述符"""

    def __init__(self):
        self._descriptors: Dict[Type, ServiceDescriptor] = {}
        self._named_descriptors: Dict[str, ServiceDescriptor] = {}
        self._lock = threading.RLock()

    def register(self, descriptor: ServiceDescriptor) -> "ServiceRegistry":
        """注册服务描述符"""
        with self._lock:
            self._descriptors[descriptor.interface] = descriptor
            if descriptor.name:
                self._named_descriptors[descriptor.name] = descriptor
        return self

    def register_transient(
        self,
        interface: Type[T],
        implementation: Type[T] = None,
        factory: Callable[[], T] = None,
        name: str = None,
    ) -> "ServiceRegistry":
        """注册瞬态服务"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.TRANSIENT,
            name=name,
        )
        return self.register(descriptor)

    def register_singleton(
        self,
        interface: Type[T],
        implementation: Type[T] = None,
        factory: Callable[[], T] = None,
        name: str = None,
    ) -> "ServiceRegistry":
        """注册单例服务"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.SINGLETON,
            name=name,
        )
        return self.register(descriptor)

    def register_scoped(
        self,
        interface: Type[T],
        implementation: Type[T] = None,
        factory: Callable[[], T] = None,
        name: str = None,
    ) -> "ServiceRegistry":
        """注册作用域服务"""
        descriptor = ServiceDescriptor(
            interface=interface,
            implementation=implementation,
            factory=factory,
            lifetime=ServiceLifetime.SCOPED,
            name=name,
        )
        return self.register(descriptor)

    def get_descriptor(self, interface: Type) -> Optional[ServiceDescriptor]:
        """获取服务描述符"""
        with self._lock:
            return self._descriptors.get(interface)

    def get_descriptor_by_name(self, name: str) -> Optional[ServiceDescriptor]:
        """根据名称获取服务描述符"""
        with self._lock:
            return self._named_descriptors.get(name)

    def get_all_descriptors(self) -> List[ServiceDescriptor]:
        """获取所有服务描述符"""
        with self._lock:
            return list(self._descriptors.values())

    def clear(self) -> None:
        """清空注册表"""
        with self._lock:
            self._descriptors.clear()
            self._named_descriptors.clear()


class ServiceDecorator:
    """服务装饰器基类"""

    def decorate(self, instance: Any, descriptor: ServiceDescriptor) -> Any:
        """装饰服务实例"""
        return instance


class PerformanceDecorator(ServiceDecorator):
    """性能监控装饰器"""

    def __init__(self, logger=None):
        self.logger = logger

    def decorate(self, instance: Any, descriptor: ServiceDescriptor) -> Any:
        """添加性能监控功能"""
        # Skip decoration for Mock objects (for testing)
        try:
            from unittest.mock import MagicMock, Mock

            if isinstance(instance, (MagicMock, Mock)):
                return instance
        except ImportError:
            pass

        # 为实例添加性能监控方法
        original_methods = {}

        for attr_name in dir(instance):
            if not attr_name.startswith("_"):
                attr = getattr(instance, attr_name)
                if callable(attr) and not isinstance(attr, type):
                    original_methods[attr_name] = attr

                    def make_wrapper(method, name):
                        def wrapper(*args, **kwargs):
                            start_time = time.time()
                            try:
                                result = method(*args, **kwargs)
                                duration = time.time() - start_time
                                # 性能监控：记录方法执行时间
                                if (
                                    self.logger and duration > 0.1
                                ):  # 仅记录超过100ms的调用
                                    self.logger.info(
                                        f"{descriptor.name}.{name} took {duration:.3f}s"
                                    )
                                return result
                            except Exception as e:
                                duration = time.time() - start_time
                                if self.logger:
                                    self.logger.error(
                                        f"{descriptor.name}.{name} failed after {duration:.3f}s: {e}"
                                    )
                                raise

                        return wrapper

                    setattr(instance, attr_name, make_wrapper(attr, attr_name))

        # 保存原始方法的引用
        instance._original_methods = original_methods

        return instance


class ErrorHandlingDecorator(ServiceDecorator):
    """错误处理装饰器"""

    def __init__(self, logger=None):
        self.logger = logger

    def decorate(self, instance: Any, descriptor: ServiceDescriptor) -> Any:
        """添加错误处理功能"""
        # Skip decoration for Mock objects (for testing)
        try:
            from unittest.mock import MagicMock, Mock

            if isinstance(instance, (MagicMock, Mock)):
                return instance
        except ImportError:
            pass

        # 为实例添加错误处理方法
        for attr_name in dir(instance):
            if not attr_name.startswith("_"):
                attr = getattr(instance, attr_name)
                if callable(attr) and not isinstance(attr, type):

                    def make_wrapper(method, name):
                        def wrapper(*args, **kwargs):
                            try:
                                return method(*args, **kwargs)
                            except Exception as e:
                                if self.logger:
                                    self.logger.error(
                                        f"Error in {descriptor.name}.{name}: {e}"
                                    )
                                raise

                        return wrapper

                    setattr(instance, attr_name, make_wrapper(attr, attr_name))

        return instance


class EnhancedDIContainer:
    """增强的依赖注入容器"""

    def __init__(self):
        self.registry = ServiceRegistry()
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._decorators: List[ServiceDecorator] = []
        self._lock = threading.RLock()
        self._creation_context_stack: List[ServiceCreationContext] = []

        # 清理优先级映射（数字越大越晚清理，与初始化顺序相反）
        self._cleanup_priorities: Dict[Type, int] = {}

        # 注册默认装饰器
        self.add_decorator(PerformanceDecorator())
        self.add_decorator(ErrorHandlingDecorator())

        # 获取logger
        try:
            from ...utils import app_logger

            self.logger = app_logger
        except ImportError:
            self.logger = None

    def add_decorator(self, decorator: ServiceDecorator) -> None:
        """添加服务装饰器"""
        self._decorators.append(decorator)

    def set_cleanup_priority(self, interface: Type, priority: int) -> None:
        """设置服务清理优先级

        Args:
            interface: 服务接口类型
            priority: 清理优先级（数字越大越晚清理，范围0-100）
        """
        with self._lock:
            self._cleanup_priorities[interface] = priority

    def register_transient(
        self,
        interface: Type[T],
        implementation: Type[T] = None,
        factory: Callable[[], T] = None,
        name: str = None,
    ) -> "EnhancedDIContainer":
        """注册瞬态服务"""
        self.registry.register_transient(interface, implementation, factory, name)
        return self

    def register_singleton(
        self,
        interface: Type[T],
        implementation: Type[T] = None,
        factory: Callable[[], T] = None,
        name: str = None,
    ) -> "EnhancedDIContainer":
        """注册单例服务"""
        self.registry.register_singleton(interface, implementation, factory, name)
        return self

    def register_scoped(
        self,
        interface: Type[T],
        implementation: Type[T] = None,
        factory: Callable[[], T] = None,
        name: str = None,
    ) -> "EnhancedDIContainer":
        """注册作用域服务"""
        self.registry.register_scoped(interface, implementation, factory, name)
        return self

    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[["EnhancedDIContainer"], T],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        name: str = None,
    ) -> "EnhancedDIContainer":
        """注册工厂方法"""
        descriptor = ServiceDescriptor(
            interface=interface, factory=factory, lifetime=lifetime, name=name
        )
        self.registry.register(descriptor)
        return self

    def get(self, interface: Type[T], scope_name: str = None) -> T:
        """获取服务实例"""
        with self._lock:
            descriptor = self.registry.get_descriptor(interface)
            if not descriptor:
                raise ValueError(f"No service registered for interface {interface}")

            # 检查循环依赖
            if self._creation_context_stack:
                current_context = self._creation_context_stack[-1]
                if current_context.is_creating(interface):
                    cycle_path = [t.__name__ for t in current_context.creating] + [
                        interface.__name__
                    ]
                    raise ValueError(
                        f"Circular dependency detected: {' -> '.join(cycle_path)}"
                    )

            # 根据生命周期获取实例
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                return self._get_singleton_instance(descriptor)
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                return self._get_scoped_instance(descriptor, scope_name or "default")
            else:  # TRANSIENT
                return self._create_instance(descriptor)

    def get_by_name(self, name: str, scope_name: str = None) -> Any:
        """根据名称获取服务实例"""
        with self._lock:
            descriptor = self.registry.get_descriptor_by_name(name)
            if not descriptor:
                raise ValueError(f"No service registered with name {name}")

            return self.get(descriptor.interface, scope_name)

    def _get_singleton_instance(self, descriptor: ServiceDescriptor) -> Any:
        """获取单例实例"""
        if descriptor.interface in self._singletons:
            return self._singletons[descriptor.interface]

        instance = self._create_instance(descriptor)
        self._singletons[descriptor.interface] = instance
        return instance

    def _get_scoped_instance(
        self, descriptor: ServiceDescriptor, scope_name: str
    ) -> Any:
        """获取作用域实例"""
        if scope_name not in self._scoped_instances:
            self._scoped_instances[scope_name] = {}

        scope_dict = self._scoped_instances[scope_name]
        if descriptor.interface in scope_dict:
            return scope_dict[descriptor.interface]

        instance = self._create_instance(descriptor)
        scope_dict[descriptor.interface] = instance
        return instance

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例"""
        # 创建或获取创建上下文
        if not self._creation_context_stack:
            context = ServiceCreationContext()
            self._creation_context_stack.append(context)
        else:
            context = self._creation_context_stack[-1]

        # Refactored to avoid try-finally with return for Nuitka compatibility
        instance = None
        try:
            # 添加到创建中列表
            context.add_creating(descriptor.interface)
            context.depth += 1

            start_time = time.time()

            # 创建实例
            if descriptor.factory:
                if self._takes_container(descriptor.factory):
                    instance = descriptor.factory(self)
                else:
                    instance = descriptor.factory()
            elif descriptor.implementation:
                instance = self._create_with_dependencies(
                    descriptor.implementation, descriptor
                )
            else:
                raise ValueError(
                    f"Neither factory nor implementation specified for {descriptor.interface}"
                )

            # 应用装饰器
            for decorator in self._decorators:
                instance = decorator.decorate(instance, descriptor)

            creation_time = time.time() - start_time

            # 性能监控：记录服务创建时间（仅记录超过100ms的）
            if self.logger and creation_time > 0.1:
                self.logger.info(f"Created {descriptor.name} in {creation_time:.3f}s")

            # 添加到已创建列表
            context.add_created(descriptor.interface, instance)

        except Exception as e:
            duration = time.time() - start_time
            if self.logger:
                self.logger.error(
                    f"Failed to create service '{descriptor.name}': {e}",
                    extra={
                        "service_name": descriptor.name,
                        "interface": descriptor.interface.__name__,
                        "dependencies": [
                            dep.__name__ for dep in descriptor.dependencies
                        ],
                        "time_elapsed": f"{duration:.2f}s",
                        "creation_depth": context.depth,
                    },
                )
            # Re-raise with enhanced context
            raise ValueError(
                f"Failed to create service '{descriptor.name}' (dependencies: {[dep.__name__ for dep in descriptor.dependencies]}, elapsed: {duration:.2f}s): {e}"
            ) from e

        finally:
            # 清理创建状态
            context.remove_creating(descriptor.interface)
            context.depth -= 1

            # 如果是最外层调用，清理上下文
            if context.depth == 0:
                self._creation_context_stack.clear()

        return instance

    def _create_with_dependencies(
        self, implementation: Type, descriptor: ServiceDescriptor
    ) -> Any:
        """创建实例并注入依赖"""
        # 获取构造函数参数
        constructor = implementation.__init__
        sig = inspect.signature(constructor)

        # 准备参数
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # 检查是否有类型注解
            if param.annotation != inspect.Parameter.empty:
                dependency_type = param.annotation

                # 检查是否为已注册的接口
                if self.registry.get_descriptor(dependency_type):
                    kwargs[param_name] = self.get(dependency_type)
                else:
                    # 尝试创建具体类型
                    if not inspect.isabstract(dependency_type):
                        kwargs[param_name] = self._create_concrete_type(dependency_type)
                    elif param.default != inspect.Parameter.empty:
                        kwargs[param_name] = param.default
                    else:
                        raise ValueError(
                            f"Cannot resolve dependency {param_name} of type {dependency_type}"
                        )
            elif param.default != inspect.Parameter.empty:
                kwargs[param_name] = param.default
            else:
                raise ValueError(
                    f"Cannot resolve parameter {param_name} without type annotation"
                )

        return implementation(**kwargs)

    def _create_concrete_type(self, concrete_type: Type) -> Any:
        """创建具体类型实例"""
        # 处理 Union 类型 (包括 Optional)
        if hasattr(concrete_type, "__origin__") and concrete_type.__origin__ is Union:
            # 对于 Union 类型，取第一个非 None 类型
            args = concrete_type.__args__
            for arg in args:
                if arg is not type(None):
                    # 检查是否为已注册的接口
                    if self.registry.get_descriptor(arg):
                        return self.get(arg)
                    else:
                        return self._create_concrete_type(arg)
            # 如果都是 None 类型，返回 None
            return None

        # 检查是否有无参构造函数
        try:
            return concrete_type()
        except TypeError:
            # 尝试递归创建
            constructor = concrete_type.__init__
            sig = inspect.signature(constructor)

            kwargs = {}
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue

                if param.annotation != inspect.Parameter.empty:
                    kwargs[param_name] = self._create_concrete_type(param.annotation)
                elif param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default

            return concrete_type(**kwargs)

    def _takes_container(self, func: Callable) -> bool:
        """检查函数是否接受容器参数"""
        sig = inspect.signature(func)
        return any(
            param.annotation == type(self)
            or param_name in ["container", "di_container"]
            for param_name, param in sig.parameters.items()
        )

    def create_scope(self, scope_name: str) -> "ServiceScope":
        """创建服务作用域"""
        return ServiceScope(self, scope_name)

    def clear_scope(self, scope_name: str) -> None:
        """清理服务作用域"""
        with self._lock:
            if scope_name in self._scoped_instances:
                scope_dict = self._scoped_instances[scope_name]

                # 调用清理方法
                for instance in scope_dict.values():
                    if hasattr(instance, "cleanup") and callable(
                        getattr(instance, "cleanup")
                    ):
                        try:
                            instance.cleanup()
                        except Exception as e:
                            if self.logger:
                                self.logger.error(
                                    f"Error cleaning up service instance: {e}"
                                )

                del self._scoped_instances[scope_name]

    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        with self._lock:
            descriptors = self.registry.get_all_descriptors()

            return {
                "total_services": len(descriptors),
                "singletons": len(
                    [d for d in descriptors if d.lifetime == ServiceLifetime.SINGLETON]
                ),
                "transients": len(
                    [d for d in descriptors if d.lifetime == ServiceLifetime.TRANSIENT]
                ),
                "scoped": len(
                    [d for d in descriptors if d.lifetime == ServiceLifetime.SCOPED]
                ),
                "active_singletons": len(self._singletons),
                "active_scopes": len(self._scoped_instances),
                "services": [
                    {
                        "name": d.name,
                        "interface": d.interface.__name__,
                        "lifetime": d.lifetime.value,
                        "lazy": d.lazy,
                        "dependencies": [dep.__name__ for dep in d.dependencies],
                    }
                    for d in descriptors
                ],
            }

    def validate_dependencies(self) -> List[str]:
        """验证依赖关系，返回问题列表"""
        problems = []
        descriptors = self.registry.get_all_descriptors()

        for descriptor in descriptors:
            # 检查循环依赖
            try:
                self._check_circular_dependency(descriptor, set())
            except ValueError as e:
                problems.append(str(e))

            # 检查依赖是否存在
            for dep in descriptor.dependencies:
                if not self.registry.get_descriptor(dep):
                    problems.append(
                        f"Service {descriptor.name} depends on unregistered service {dep.__name__}"
                    )

        return problems

    def _check_circular_dependency(
        self, descriptor: ServiceDescriptor, visited: Set[Type]
    ) -> None:
        """检查循环依赖"""
        if descriptor.interface in visited:
            cycle_path = [t.__name__ for t in visited] + [descriptor.interface.__name__]
            raise ValueError(f"Circular dependency detected: {' -> '.join(cycle_path)}")

        visited.add(descriptor.interface)

        for dep in descriptor.dependencies:
            dep_descriptor = self.registry.get_descriptor(dep)
            if dep_descriptor:
                self._check_circular_dependency(dep_descriptor, visited.copy())

    def cleanup(self) -> None:
        """清理容器资源（按优先级顺序）"""
        with self._lock:
            # 清理所有作用域
            for scope_name in list(self._scoped_instances.keys()):
                self.clear_scope(scope_name)

            # 按清理优先级排序单例（升序，数字小的先清理）
            sorted_singletons = sorted(
                self._singletons.items(),
                key=lambda item: self._cleanup_priorities.get(
                    item[0], 50
                ),  # 默认优先级50
            )

            # 按优先级顺序清理单例
            for interface, instance in sorted_singletons:
                if hasattr(instance, "cleanup") and callable(
                    getattr(instance, "cleanup")
                ):
                    priority = self._cleanup_priorities.get(interface, 50)
                    try:
                        if self.logger:
                            self.logger.info(
                                f"Cleaning up singleton {interface.__name__} (priority: {priority})"
                            )
                        instance.cleanup()
                    except Exception as e:
                        if self.logger:
                            self.logger.error(
                                f"Error cleaning up singleton {interface.__name__}: {e}"
                            )

            self._singletons.clear()
            self._cleanup_priorities.clear()
            self.registry.clear()

            if self.logger:
                self.logger.info("DIContainer cleaned up")


# 工厂函数
def create_container() -> "EnhancedDIContainer":
    """创建依赖注入容器实例并注册所有服务"""
    container = EnhancedDIContainer()

    # 创建配置重载服务注册中心（最先创建）
    config_reload_registry = ConfigReloadServiceRegistry()

    # 显式导入接口（避免import *）

    # 服务实现
    from .services.config_service import ConfigService
    from .services.state_manager import StateManager
    from .services.transcription_service import TranscriptionService
    from .services.dynamic_event_system import DynamicEventSystem
    from .services.application_orchestrator import ApplicationOrchestrator
    from .services.ui_event_bridge import UIEventBridge
    from ..audio import AudioRecorder
    from ..ai import AIClientFactory
    from ..input import SmartTextInput
    from .services.hotkey_service import HotkeyService

    # 事件服务 - 单例（最先创建，因为其他服务依赖它）
    container.register_singleton(IEventService, DynamicEventSystem)

    # 配置服务 - 单例（需要 EventService）
    container.register_singleton(IConfigService, ConfigService)

    # 状态管理器 - 单例（需要 EventService）
    container.register_singleton(IStateManager, StateManager)

    # 配置重载协调器 - 单例（替代旧的 ConfigReloadService）
    def create_config_reload_coordinator(container):
        events = container.get(IEventService)

        # 创建配置重载协调器（使用新的 ServiceRegistry）
        coordinator = ConfigReloadCoordinator(
            service_registry=config_reload_registry,
            event_service=events
        )

        return coordinator

    container.register_factory(
        IConfigReloadService, create_config_reload_coordinator, ServiceLifetime.SINGLETON
    )

    # 历史记录服务 - 单例
    def create_history_service(container):
        config = container.get(IConfigService)
        from .services.storage import HistoryStorageService

        service = HistoryStorageService(config)
        service.initialize({})  # 初始化服务
        return service

    container.register_factory(
        IHistoryStorageService, create_history_service, ServiceLifetime.SINGLETON
    )

    # 音频服务 - 瞬态
    def create_audio_service(container):
        config = container.get(IConfigService)
        sample_rate = config.get_setting("audio.sample_rate", 16000)
        channels = config.get_setting("audio.channels", 1)
        chunk_size = config.get_setting("audio.chunk_size", 1024)

        return AudioRecorder(
            sample_rate=sample_rate,
            channels=channels,
            chunk_size=chunk_size,
            config_service=config,
        )

    container.register_factory(
        IAudioService, create_audio_service, ServiceLifetime.TRANSIENT
    )

    # 语音服务 - 单例（最复杂的服务）
    def create_speech_service(container):
        config = container.get(IConfigService)
        event_service = container.get(IEventService)

        # 智能检测：如果配置是 local 但环境不支持，自动切换到云服务
        provider = config.get_setting("transcription.provider", "local")

        if provider == "local":
            try:
                # 检测 sherpa-onnx 是否可用
                import sherpa_onnx  # noqa: F401
            except ImportError:
                # sherpa-onnx 不可用，自动切换到云服务
                from ..utils import app_logger

                # 查找第一个配置了 API key 的云服务
                cloud_providers = ["qwen", "groq", "siliconflow"]
                switched_to = None

                for cloud_provider in cloud_providers:
                    api_key = config.get_setting(
                        f"transcription.{cloud_provider}.api_key", ""
                    )
                    if api_key and api_key.strip():
                        switched_to = cloud_provider
                        config.set_setting("transcription.provider", cloud_provider)
                        break

                if switched_to:
                    app_logger.log_audio_event(
                        "Auto-switched from local to cloud provider",
                        {
                            "original_provider": "local",
                            "new_provider": switched_to,
                            "reason": "sherpa-onnx not installed",
                            "suggestion": "Install sherpa-onnx for local transcription",
                        },
                    )
                    # 更新 provider 变量
                    provider = switched_to
                else:
                    app_logger.log_audio_event(
                        "Local provider unavailable and no cloud provider configured",
                        {
                            "original_provider": "local",
                            "reason": "sherpa-onnx not installed",
                            "action": "Will use stub service",
                            "suggestion": "Configure a cloud provider API key or install sherpa-onnx",
                        },
                    )

        # 使用 SpeechServiceFactory 从配置创建服务
        from ..speech import SpeechServiceFactory

        # 创建 SpeechService 工厂函数
        def speech_service_factory():
            # 使用工厂从配置创建服务（自动选择 local 或 cloud）
            service = SpeechServiceFactory.create_from_config(config)
            if service is None:
                # Fallback 到默认的 SherpaEngine（仅在本地模式）
                from ..speech.sherpa_engine import SherpaEngine

                return SherpaEngine(model_name="paraformer", language="zh")
            return service

        # 关键修复：只有本地提供商才包装到 TranscriptionService（提供流式支持）
        # 云提供商直接返回（已实现 ISpeechService.transcribe()）
        if provider == "local":
            # 使用TranscriptionService包装,提供线程隔离和流式转录（传递 config 用于流式模式配置）
            transcription_service = TranscriptionService(
                speech_service_factory, event_service, config_service=config
            )

            # 启动TranscriptionService
            transcription_service.start()

            # 注册到配置重载服务注册中心（带工厂）
            config_reload_registry.register(
                "transcription_service",
                transcription_service,
                factory=lambda: create_speech_service(container)
            )

            return transcription_service
        else:
            # 云提供商直接返回（Groq/SiliconFlow/Qwen 已实现完整的 ISpeechService）
            cloud_service = speech_service_factory()

            # 云服务也加载模型（虽然只是标记为已加载）
            if hasattr(cloud_service, "load_model"):
                cloud_service.load_model()

            from ..utils import app_logger
            app_logger.log_audio_event(
                "Cloud speech service created (no TranscriptionService wrapper)",
                {
                    "provider": provider,
                    "service_type": type(cloud_service).__name__,
                },
            )

            # 注册到配置重载服务注册中心（带工厂）
            config_reload_registry.register(
                "transcription_service",
                cloud_service,
                factory=lambda: create_speech_service(container)
            )

            return cloud_service

    container.register_factory(
        ISpeechService, create_speech_service, ServiceLifetime.SINGLETON
    )

    # AI服务 - 瞬态
    def create_ai_service(container):
        config = container.get(IConfigService)
        # 使用工厂从配置创建客户端
        client = AIClientFactory.create_from_config(config)

        # 如果工厂返回 None，创建默认的 OpenRouter 客户端
        if client is None:
            from ..ai import OpenRouterClient

            api_key = config.get_setting("ai.openrouter.api_key", "")
            return OpenRouterClient(api_key)

        return client

    container.register_factory(IAIService, create_ai_service, ServiceLifetime.TRANSIENT)

    # 输入服务 - 瞬态
    def create_input_service(container):
        config_service = container.get(IConfigService)
        return SmartTextInput(config_service)

    container.register_factory(
        IInputService, create_input_service, ServiceLifetime.TRANSIENT
    )

    # 快捷键服务 - 单例（需要热重载支持）
    def create_hotkey_service(container):
        # 读取配置以确定使用哪个后端
        config = container.get(IConfigService)

        # 创建一个回调函数（调用录音控制器）
        # 注意：此时录音控制器可能还未创建，所以使用延迟绑定
        def hotkey_callback(action: str):
            # 通过事件系统触发，而不是直接调用录音控制器
            # 这样可以解耦 HotkeyService 和 VoiceInputApp
            event_service = container.get(IEventService)
            event_service.emit("hotkey_triggered", {"action": action})

        # 使用 HotkeyService 包装器（支持配置热重载）
        hotkey_service = HotkeyService(config, hotkey_callback)

        # 初始化服务 (传入空的配置字典，因为 HotkeyService 从 config_service 读取配置)
        hotkey_service.initialize({})

        # 注册到配置重载服务注册中心（带工厂）
        config_reload_registry.register(
            "hotkey_service",
            hotkey_service,
            factory=lambda: create_hotkey_service(container)
        )

        return hotkey_service

    container.register_factory(
        IHotkeyService, create_hotkey_service, ServiceLifetime.SINGLETON
    )

    # 应用编排器 - 单例（依赖多个核心服务）
    def create_application_orchestrator(container):
        config = container.get(IConfigService)
        events = container.get(IEventService)
        state = container.get(IStateManager)

        return ApplicationOrchestrator(
            config_service=config,
            event_service=events,
            state_manager=state,
        )

    container.register_factory(
        IApplicationOrchestrator,
        create_application_orchestrator,
        ServiceLifetime.SINGLETON,
    )

    # UI事件桥接器 - 单例（依赖事件服务）
    def create_ui_event_bridge(container):
        events = container.get(IEventService)
        return UIEventBridge(event_service=events)

    container.register_factory(
        IUIEventBridge, create_ui_event_bridge, ServiceLifetime.SINGLETON
    )

    # ========================================================================
    # UI 服务 - 为UI层提供专门的服务接口（不依赖VoiceInputApp）
    # ========================================================================

    # UI主窗口服务 - 单例
    def create_ui_main_service(container):
        config = container.get(IConfigService)
        events = container.get(IEventService)
        state = container.get(IStateManager)

        from .services.ui_services import UIMainService

        return UIMainService(
            config_service=config, event_service=events, state_manager=state
        )

    container.register_factory(
        IUIMainService, create_ui_main_service, ServiceLifetime.SINGLETON
    )

    # UI设置服务 - 单例
    def create_ui_settings_service(container):
        config = container.get(IConfigService)
        events = container.get(IEventService)
        history = container.get(IHistoryStorageService)

        # 尝试获取转录服务和AI控制器(可能还未注册)
        transcription_service = None
        ai_processing_controller = None
        try:
            transcription_service = container.get(ISpeechService)
        except Exception as e:
            from ..utils import app_logger

            app_logger.log_audio_event(
                "ISpeechService not yet registered",
                {
                    "context": "Optional dependency for UISettingsService",
                    "error": str(e),
                },
            )

        # AI controller在这个阶段可能还未注册,留空

        from .services.ui_services import UISettingsService

        return UISettingsService(
            config_service=config,
            event_service=events,
            history_service=history,
            transcription_service=transcription_service,
            ai_processing_controller=ai_processing_controller,
        )

    container.register_factory(
        IUISettingsService, create_ui_settings_service, ServiceLifetime.SINGLETON
    )

    # UI模型管理服务 - 单例
    def create_ui_model_service(container):
        speech = container.get(ISpeechService)

        from .services.ui_services import UIModelService

        return UIModelService(speech_service=speech)

    container.register_factory(
        IUIModelService, create_ui_model_service, ServiceLifetime.SINGLETON
    )

    # UI音频服务 - 单例（无依赖）
    def create_ui_audio_service(container):
        from .services.ui_services import UIAudioService

        return UIAudioService()

    container.register_factory(
        IUIAudioService, create_ui_audio_service, ServiceLifetime.SINGLETON
    )

    # UI GPU服务 - 单例（无依赖）
    def create_ui_gpu_service(container):
        from .services.ui_services import UIGPUService

        return UIGPUService()

    container.register_factory(
        IUIGPUService, create_ui_gpu_service, ServiceLifetime.SINGLETON
    )

    # ========================================================================
    # 设置清理优先级（数字越大越晚清理，与初始化顺序相反）
    # ========================================================================

    # UI层 - 最早清理 (5-20)
    container.set_cleanup_priority(IUIMainService, 5)
    container.set_cleanup_priority(IUISettingsService, 10)
    container.set_cleanup_priority(IUIModelService, 12)
    container.set_cleanup_priority(IUIAudioService, 14)
    container.set_cleanup_priority(IUIGPUService, 16)
    container.set_cleanup_priority(IUIEventBridge, 18)

    # 业务服务层 - 中等优先级 (40-60)
    container.set_cleanup_priority(IAudioService, 40)  # 音频服务较早清理
    container.set_cleanup_priority(IInputService, 45)  # 输入服务
    container.set_cleanup_priority(IHotkeyService, 48)  # 快捷键服务
    container.set_cleanup_priority(ISpeechService, 50)  # 语音服务
    container.set_cleanup_priority(IAIService, 52)  # AI服务

    # 应用编排层 - 较高优先级 (70-80)
    container.set_cleanup_priority(IHistoryStorageService, 70)  # 历史记录服务
    container.set_cleanup_priority(IApplicationOrchestrator, 75)  # 应用编排器
    container.set_cleanup_priority(IConfigReloadService, 78)  # 配置重载服务

    # 核心基础服务 - 最后清理 (90-100)
    container.set_cleanup_priority(IStateManager, 90)  # 状态管理器
    container.set_cleanup_priority(IConfigService, 95)  # 配置服务（倒数第二）
    container.set_cleanup_priority(IEventService, 100)  # 事件服务（最后清理）

    return container


def create_enhanced_container() -> "EnhancedDIContainer":
    """创建增强版依赖注入容器实例（别名）"""
    return create_container()


class ServiceScope:
    """服务作用域"""

    def __init__(self, container: EnhancedDIContainer, scope_name: str):
        self.container = container
        self.scope_name = scope_name

    def get(self, interface: Type[T]) -> T:
        """在作用域内获取服务"""
        return self.container.get(interface, self.scope_name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.container.clear_scope(self.scope_name)
