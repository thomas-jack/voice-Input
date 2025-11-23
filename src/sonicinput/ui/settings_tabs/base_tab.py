"""基础设置标签页类

提供所有设置标签页的通用功能和接口。
"""

from typing import Any, Dict, Optional

from PySide6.QtWidgets import QWidget


class BaseSettingsTab:
    """设置标签页基类

    所有设置标签页都应继承此类，提供统一的接口和通用功能。
    """

    def __init__(self, config_manager, parent_window):
        """初始化标签页

        Args:
            config_manager: 配置管理器
            parent_window: 父窗口（SettingsWindow实例）
        """
        self.config_manager = config_manager
        self.parent_window = parent_window
        self.widget: Optional[QWidget] = None
        self.controls: Dict[str, Any] = {}  # 存储UI控件的引用

    def create(self) -> QWidget:
        """创建标签页UI

        Returns:
            QWidget: 标签页的根widget
        """
        if self.widget is None:
            self.widget = QWidget()
            self._setup_ui()
        return self.widget

    def _setup_ui(self) -> None:
        """设置UI - 子类必须实现"""
        raise NotImplementedError("子类必须实现 _setup_ui 方法")

    def load_config(self, config: Dict[str, Any]) -> None:
        """从配置加载UI状态

        Args:
            config: 配置字典
        """
        raise NotImplementedError("子类必须实现 load_config 方法")

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        raise NotImplementedError("子类必须实现 save_config 方法")

    def _get_nested_config(self, config: Dict[str, Any], *keys, default=None) -> Any:
        """安全获取嵌套配置值

        Args:
            config: 配置字典
            *keys: 嵌套键路径
            default: 默认值

        Returns:
            配置值或默认值
        """
        result = config
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            else:
                return default
        return result if result is not None else default

    def _set_nested_config(self, config: Dict[str, Any], value: Any, *keys) -> None:
        """设置嵌套配置值

        Args:
            config: 配置字典
            value: 要设置的值
            *keys: 嵌套键路径
        """
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
