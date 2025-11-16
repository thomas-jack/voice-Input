"""应用编排器接口

负责：
- 应用启动编排
- 服务依赖协调
- 生命周期管理
- 初始化阶段控制
"""

from typing import Protocol


class IApplicationOrchestrator(Protocol):
    """应用编排器接口"""

    def orchestrate_startup(self) -> None:
        """编排应用启动流程"""
        ...

    def orchestrate_shutdown(self) -> None:
        """编排应用关闭流程"""
        ...

    def get_initialization_phase(self) -> str:
        """获取当前初始化阶段"""
        ...

    def is_startup_complete(self) -> bool:
        """检查启动是否完成"""
        ...

    def register_startup_callback(self, phase: str, callback) -> None:
        """注册启动阶段回调"""
        ...

    def register_shutdown_callback(self, callback) -> None:
        """注册关闭回调"""
        ...
