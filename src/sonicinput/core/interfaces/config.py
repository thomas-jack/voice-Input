"""配置服务接口定义"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Union
from pathlib import Path

T = TypeVar('T')


class IConfigService(ABC):
    """配置服务接口

    提供类型安全的配置管理功能，包括配置的加载、保存、验证和自动修复。
    """

    @abstractmethod
    def get_setting(self, key: str, default: Optional[T] = None) -> T:
        """获取配置项

        Args:
            key: 配置项键名，支持嵌套路径 (例如: "whisper.model")
            default: 默认值

        Returns:
            配置项的值，如果不存在则返回默认值

        Raises:
            ConfigurationError: 配置项无效或类型不匹配时
        """
        pass

    @abstractmethod
    def set_setting(self, key: str, value: Any) -> None:
        """设置配置项

        Args:
            key: 配置项键名，支持嵌套路径
            value: 要设置的值

        Raises:
            ConfigurationError: 配置项无效或类型不匹配时
        """
        pass

    @abstractmethod
    def save_config(self) -> bool:
        """保存配置到文件

        Returns:
            是否保存成功
        """
        pass

    @abstractmethod
    def load_config(self) -> bool:
        """从文件加载配置

        Returns:
            是否加载成功
        """
        pass

    @abstractmethod
    def reset_to_default(self, key: Optional[str] = None) -> None:
        """重置配置到默认值

        Args:
            key: 要重置的配置项键名，None 表示重置所有配置
        """
        pass

    @abstractmethod
    def validate_config(self) -> Dict[str, Any]:
        """验证配置完整性

        Returns:
            验证结果，包含错误信息和修复建议
        """
        pass

    @abstractmethod
    def get_config_path(self) -> Path:
        """获取配置文件路径

        Returns:
            配置文件的路径
        """
        pass

    @abstractmethod
    def export_config(self, target_path: Union[str, Path]) -> bool:
        """导出配置到指定路径

        Args:
            target_path: 目标文件路径

        Returns:
            是否导出成功
        """
        pass

    @abstractmethod
    def import_config(self, source_path: Union[str, Path]) -> bool:
        """从指定路径导入配置

        Args:
            source_path: 源文件路径

        Returns:
            是否导入成功
        """
        pass