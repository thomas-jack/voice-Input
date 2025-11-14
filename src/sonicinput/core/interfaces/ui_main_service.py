"""UI主窗口服务接口

定义UI主窗口所需的核心服务接口，实现UI层与业务逻辑的解耦。
"""

from typing import Protocol, Dict, Any, Optional
from .event import IEventService


class IUIMainService(Protocol):
    """UI主窗口服务接口

    提供UI主窗口所需的核心功能，包括录音控制、状态管理、设置访问等。
    UI组件通过此接口访问业务逻辑，不直接依赖具体实现。
    """

    def is_recording(self) -> bool:
        """检查是否正在录音

        Returns:
            bool: 是否正在录音
        """
        ...

    def start_recording(self) -> None:
        """开始录音"""
        ...

    def stop_recording(self) -> None:
        """停止录音"""
        ...

    def get_current_status(self) -> str:
        """获取当前状态文本

        Returns:
            str: 状态描述文本
        """
        ...

    def get_event_service(self) -> IEventService:
        """获取事件服务

        Returns:
            IEventService: 事件服务实例
        """
        ...

    def show_settings(self) -> None:
        """显示设置窗口"""
        ...

    def reload_hotkeys(self) -> None:
        """重新加载快捷键配置"""
        ...

    def get_whisper_engine(self) -> Optional[Any]:
        """获取Whisper引擎（用于模型管理）

        Returns:
            Optional[Any]: Whisper引擎实例，如果不可用则返回None
        """
        ...

    def cleanup(self) -> None:
        """清理资源"""
        ...


class IUISettingsService(Protocol):
    """UI设置服务接口

    提供设置窗口所需的功能，包括配置管理、模型管理、设备管理等。
    """

    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置

        Returns:
            Dict[str, Any]: 完整配置字典
        """
        ...

    def set_setting(self, key: str, value: Any) -> None:
        """设置单个配置项

        Args:
            key: 配置键
            value: 配置值
        """
        ...

    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取单个配置项

        Args:
            key: 配置键
            default: 默认值

        Returns:
            Any: 配置值
        """
        ...

    def save_settings(self) -> None:
        """保存设置到文件"""
        ...

    def export_config(self, file_path: str) -> None:
        """导出配置到文件

        Args:
            file_path: 导出文件路径
        """
        ...

    def import_config(self, file_path: str) -> None:
        """从文件导入配置

        Args:
            file_path: 导入文件路径
        """
        ...

    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        ...

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置

        Returns:
            Dict[str, Any]: 默认配置字典
        """
        ...

    def get_event_service(self) -> IEventService:
        """获取事件服务

        Returns:
            IEventService: 事件服务实例
        """
        ...


class IUIModelService(Protocol):
    """UI模型管理服务接口

    提供模型加载、卸载、测试等功能。
    """

    def is_model_loaded(self) -> bool:
        """检查模型是否已加载

        Returns:
            bool: 模型是否已加载
        """
        ...

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息

        Returns:
            Dict[str, Any]: 模型信息字典
        """
        ...

    def load_model(self, model_name: str) -> bool:
        """加载模型

        Args:
            model_name: 模型名称

        Returns:
            bool: 加载是否成功
        """
        ...

    def unload_model(self) -> None:
        """卸载模型"""
        ...

    def test_model(self) -> Dict[str, Any]:
        """测试模型

        Returns:
            Dict[str, Any]: 测试结果
        """
        ...


class IUIAudioService(Protocol):
    """UI音频服务接口

    提供音频设备管理等功能。
    """

    def get_audio_devices(self) -> list:
        """获取可用音频设备列表

        Returns:
            list: 音频设备列表
        """
        ...

    def refresh_audio_devices(self) -> None:
        """刷新音频设备列表"""
        ...


class IUIGPUService(Protocol):
    """UI GPU服务接口

    提供GPU信息查询等功能。
    """

    def get_gpu_info(self) -> Dict[str, Any]:
        """获取GPU信息

        Returns:
            Dict[str, Any]: GPU信息字典
        """
        ...

    def check_gpu_availability(self) -> bool:
        """检查GPU是否可用

        Returns:
            bool: GPU是否可用
        """
        ...