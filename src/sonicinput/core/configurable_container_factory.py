"""可配置容器工厂

负责：
- 创建配置驱动的DI容器
- 支持外部配置文件
- 提供灵活的服务注册机制
"""

import os
from typing import Optional
from .di_container_enhanced import EnhancedDIContainer
from .services.service_registry_config import ServiceRegistryConfig
from .services.configurable_service_registry import ConfigurableServiceRegistry
from ..utils import app_logger


class ConfigurableContainerFactory:
    """可配置容器工厂

    职责：
- 根据配置创建DI容器
- 支持从配置文件加载服务定义
- 提供默认配置回退
- 管理容器生命周期
    """

    @staticmethod
    def create_container(
        config_path: Optional[str] = None,
        use_default_config: bool = True
    ) -> EnhancedDIContainer:
        """创建配置驱动的DI容器

        Args:
            config_path: 服务配置文件路径
            use_default_config: 是否使用默认配置作为回退

        Returns:
            配置好的DI容器实例
        """
        try:
            app_logger.log_audio_event("Creating configurable container", {
                "config_path": config_path,
                "use_default_config": use_default_config
            })

            # 创建容器实例
            container = EnhancedDIContainer()

            # 创建服务配置
            if config_path and os.path.exists(config_path):
                service_config = ServiceRegistryConfig(config_path)
                app_logger.log_audio_event("Service config loaded from file", {
                    "config_path": config_path
                })
            else:
                if config_path:
                    app_logger.log_audio_event("Config file not found, using default config", {
                        "config_path": config_path
                    })

                if use_default_config:
                    service_config = ServiceRegistryConfig()
                    app_logger.log_audio_event("Using default service config", {})
                else:
                    raise ValueError("No valid configuration available")

            # 创建并配置服务注册器
            registry = ConfigurableServiceRegistry(container, service_config)

            # 注册所有服务
            registry.register_all_services()

            # 将配置和注册器存储在容器中，供后续使用
            container._service_config = service_config
            container._service_registry = registry

            app_logger.log_audio_event("Configurable container created successfully", {
                "services_registered": len(service_config.get_all_service_configs())
            })

            return container

        except Exception as e:
            app_logger.log_error(e, "create_configurable_container")
            raise

    @staticmethod
    def create_container_with_env_config() -> EnhancedDIContainer:
        """根据环境变量创建容器

        Returns:
            配置好的DI容器实例
        """
        # 尝试从环境变量获取配置路径
        config_path = os.getenv("SONICINPUT_SERVICE_CONFIG_PATH")

        # 默认配置文件位置
        if not config_path:
            app_data_dir = os.getenv("APPDATA", "")
            if app_data_dir:
                config_path = os.path.join(app_data_dir, "SonicInput", "services.json")
            else:
                config_path = None

        return ConfigurableContainerFactory.create_container(
            config_path=config_path,
            use_default_config=True
        )

    @staticmethod
    def save_service_config(
        container: EnhancedDIContainer,
        config_path: Optional[str] = None
    ) -> None:
        """保存服务配置到文件

        Args:
            container: DI容器实例
            config_path: 保存路径，可选
        """
        if not hasattr(container, '_service_config'):
            raise ValueError("Container does not have service configuration")

        service_config = container._service_config
        service_config.save_config_to_file(config_path)

    @staticmethod
    def reload_service_config(
        container: EnhancedDIContainer,
        config_path: Optional[str] = None
    ) -> EnhancedDIContainer:
        """重新加载服务配置并创建新容器

        Args:
            container: 当前容器实例
            config_path: 新的配置文件路径，可选

        Returns:
            重新配置的容器实例
        """
        # 获取当前配置路径
        if config_path is None and hasattr(container, '_service_config'):
            config_path = container._service_config.config_path

        # 清理当前容器
        container.cleanup()

        # 创建新容器
        return ConfigurableContainerFactory.create_container(
            config_path=config_path,
            use_default_config=True
        )


# 便捷函数
def create_configurable_container(
    config_path: Optional[str] = None,
    use_default_config: bool = True
) -> EnhancedDIContainer:
    """创建配置驱动的DI容器（便捷函数）

    Args:
        config_path: 服务配置文件路径
        use_default_config: 是否使用默认配置作为回退

    Returns:
        配置好的DI容器实例
    """
    return ConfigurableContainerFactory.create_container(
        config_path=config_path,
        use_default_config=use_default_config
    )


def create_container_from_env() -> EnhancedDIContainer:
    """根据环境变量创建容器（便捷函数）

    Returns:
        配置好的DI容器实例
    """
    return ConfigurableContainerFactory.create_container_with_env_config()