"""依赖注入容器 - 重构后的新实现

重构目标：
- 使用服务描述符模式，支持多种生命周期
- 支持循环依赖检测
- 支持服务装饰和配置驱动注册
- 简化使用方式

新的特性：
1. ServiceLifetime - 支持单例、瞬态、作用域
2. ServiceDescriptor - 描述服务配置
3. 自动依赖注入 - 支持构造函数注入
4. 插件化 - 支持服务装饰器

使用方法：
```python
# 创建容器
container = EnhancedDIContainer()

# 注册服务
container.register_singleton(IEventService, EventBus)
container.register_transient(IAIService, GroqClient)

# 获取服务
event_service = container.get(IEventService)
ai_service = container.get(IAIService)

# 创建作用域
with container.create_scope() as scope:
    scoped_service = scope.get(IScopedService)
```

注意：新的API与旧版本不同，设计更简洁现代。
"""

# 直接导入增强版实现
from .di_container_enhanced import (
    EnhancedDIContainer,
    ServiceLifetime,
    ServiceDescriptor,
    ServiceScope,
    ServiceRegistry,
)

# 主要API - 直接使用增强版实现
DIContainer = EnhancedDIContainer

# 导出工厂函数
from .di_container_enhanced import create_container, create_enhanced_container
from .configurable_container_factory import (
    ConfigurableContainerFactory,
    create_configurable_container,
    create_container_from_env,
)

__all__ = [
    "DIContainer",
    "EnhancedDIContainer",
    # 核心类型
    "ServiceLifetime",
    "ServiceDescriptor",
    "ServiceScope",
    "ServiceRegistry",
    # 工厂函数
    "create_container",
    "create_enhanced_container",
    "ConfigurableContainerFactory",
    "create_configurable_container",
    "create_container_from_env",
]
