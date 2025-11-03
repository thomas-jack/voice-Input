"""UI组件接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, Callable
from PySide6.QtWidgets import QWidget


class IUIComponent(ABC):
    """UI组件基础接口

    所有UI组件的基础接口，定义通用的UI操作。
    """

    @abstractmethod
    def show(self) -> None:
        """显示组件"""
        pass

    @abstractmethod
    def hide(self) -> None:
        """隐藏组件"""
        pass

    @abstractmethod
    def is_visible(self) -> bool:
        """组件是否可见

        Returns:
            是否可见
        """
        pass

    @abstractmethod
    def set_enabled(self, enabled: bool) -> None:
        """设置组件启用状态

        Args:
            enabled: 是否启用
        """
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """组件是否启用

        Returns:
            是否启用
        """
        pass

    @abstractmethod
    def get_widget(self) -> Optional[QWidget]:
        """获取底层Qt组件

        Returns:
            Qt组件实例，None表示组件未初始化
        """
        pass


class IOverlayComponent(IUIComponent):
    """悬浮窗组件接口

    专门用于悬浮窗组件的接口定义。
    """

    @abstractmethod
    def set_position(self, x: int, y: int) -> None:
        """设置悬浮窗位置

        Args:
            x: X坐标
            y: Y坐标
        """
        pass

    @abstractmethod
    def get_position(self) -> Tuple[int, int]:
        """获取悬浮窗位置

        Returns:
            (x, y) 坐标元组
        """
        pass

    @abstractmethod
    def save_position(self) -> bool:
        """保存当前位置到配置

        Returns:
            是否保存成功
        """
        pass

    @abstractmethod
    def restore_position(self) -> bool:
        """从配置恢复位置

        Returns:
            是否恢复成功
        """
        pass

    @abstractmethod
    def set_status(self, status: str) -> None:
        """设置状态显示

        Args:
            status: 状态字符串 ('idle', 'recording', 'processing', 'error')
        """
        pass

    @abstractmethod
    def update_waveform(self, audio_data: Any) -> None:
        """更新波形显示

        Args:
            audio_data: 音频数据
        """
        pass

    @abstractmethod
    def set_always_on_top(self, on_top: bool) -> None:
        """设置窗口置顶

        Args:
            on_top: 是否置顶
        """
        pass

    @abstractmethod
    def animate_show(self) -> None:
        """动画显示"""
        pass

    @abstractmethod
    def animate_hide(self) -> None:
        """动画隐藏"""
        pass


class ITrayComponent(IUIComponent):
    """系统托盘组件接口

    专门用于系统托盘组件的接口定义。
    """

    @abstractmethod
    def set_icon(self, icon_path: str) -> None:
        """设置托盘图标

        Args:
            icon_path: 图标文件路径
        """
        pass

    @abstractmethod
    def set_tooltip(self, tooltip: str) -> None:
        """设置托盘提示文本

        Args:
            tooltip: 提示文本
        """
        pass

    @abstractmethod
    def show_message(self, title: str, message: str, timeout: int = 3000) -> None:
        """显示托盘消息

        Args:
            title: 消息标题
            message: 消息内容
            timeout: 显示时间（毫秒）
        """
        pass

    @abstractmethod
    def set_context_menu(self, menu_items: Dict[str, Callable]) -> None:
        """设置右键菜单

        Args:
            menu_items: 菜单项字典，键为菜单文本，值为回调函数
        """
        pass

    @abstractmethod
    def add_menu_item(
        self, text: str, callback: Callable, separator_before: bool = False
    ) -> None:
        """添加菜单项

        Args:
            text: 菜单文本
            callback: 回调函数
            separator_before: 在此项前添加分隔符
        """
        pass

    @abstractmethod
    def remove_menu_item(self, text: str) -> bool:
        """移除菜单项

        Args:
            text: 菜单文本

        Returns:
            是否成功移除
        """
        pass
