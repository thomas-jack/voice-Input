"""配置热重载服务接口

负责处理配置变更的监听和热重载逻辑。
"""

from typing import Protocol, Callable, Dict, Any


class IConfigReloadService(Protocol):
    """配置热重载服务接口"""

    def setup_config_watcher(self) -> None:
        """设置配置文件监听器"""
        ...

    def register_reload_callback(
        self, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """注册配置重载回调函数

        Args:
            callback: 配置变更时的回调函数，接收配置数据
        """
        ...

    def start_monitoring(self) -> None:
        """开始监控配置变更"""
        ...

    def stop_monitoring(self) -> None:
        """停止监控配置变更"""
        ...

    def is_monitoring(self) -> bool:
        """检查是否正在监控配置变更"""
        ...

    def handle_config_change(self, config_data: Dict[str, Any]) -> None:
        """处理配置变更

        Args:
            config_data: 变更的配置数据
        """
        ...
