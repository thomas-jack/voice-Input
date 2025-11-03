"""快捷键服务接口定义"""

from abc import ABC, abstractmethod
from typing import Dict


class IHotkeyService(ABC):
    """快捷键服务接口

    提供全局快捷键注册和管理功能。
    """

    @abstractmethod
    def register_hotkey(self, hotkey: str, action: str) -> bool:
        """注册快捷键

        Args:
            hotkey: 快捷键组合 (例如: "ctrl+shift+v")
            action: 动作名称
            callback: 回调函数

        Returns:
            是否注册成功
        """
        pass

    @abstractmethod
    def unregister_hotkey(self, hotkey: str) -> bool:
        """注销快捷键

        Args:
            hotkey: 快捷键组合

        Returns:
            是否注销成功
        """
        pass

    @abstractmethod
    def unregister_all_hotkeys(self) -> None:
        """注销所有快捷键"""
        pass

    @abstractmethod
    def start_listening(self) -> bool:
        """开始监听快捷键

        Returns:
            是否成功开始监听
        """
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        """停止监听快捷键"""
        pass

    @abstractmethod
    def get_registered_hotkeys(self) -> Dict[str, str]:
        """获取已注册的快捷键

        Returns:
            快捷键映射，键为快捷键组合，值为动作名称
        """
        pass

    @property
    @abstractmethod
    def is_listening(self) -> bool:
        """是否正在监听快捷键"""
        pass

    # 移除的方法（不必需）：
    # - is_hotkey_available: 复杂且很少需要的功能
    # - registered_count: 可通过len(get_registered_hotkeys())计算
    # - validate_hotkey_format: 可在实现中内部处理
