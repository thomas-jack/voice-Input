"""服务注册配置接口

负责：
- 服务注册配置定义
- 配置驱动的服务管理
- 动态服务注册支持
"""

from typing import Protocol, Dict, Any, List, Optional


class IServiceRegistryConfig(Protocol):
    """服务注册配置接口"""

    def get_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取特定服务的配置"""
        ...

    def get_all_service_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务配置"""
        ...

    def load_config_from_file(self, config_path: str) -> None:
        """从文件加载服务配置"""
        ...

    def save_config_to_file(self, config_path: str) -> None:
        """保存服务配置到文件"""
        ...

    def register_service_config(self, service_name: str, config: Dict[str, Any]) -> None:
        """注册服务配置"""
        ...

    def get_service_dependencies(self, service_name: str) -> List[str]:
        """获取服务依赖列表"""
        ...

    def validate_config(self) -> List[str]:
        """验证配置完整性，返回错误列表"""
        ...

    def get_registration_order(self) -> List[str]:
        """获取服务注册顺序（根据依赖关系）"""
        ...