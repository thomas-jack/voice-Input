"""核心服务接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from enum import Enum
import numpy as np


class EventPriority(Enum):
    """事件优先级"""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class IAudioService(ABC):
    """音频服务接口"""

    @abstractmethod
    def start_recording(self, device_id: Optional[int] = None) -> None:
        """开始录音"""
        pass

    @abstractmethod
    def stop_recording(self) -> np.ndarray:
        """停止录音并返回音频数据"""
        pass

    @abstractmethod
    def set_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """设置音频数据回调"""
        pass

    @property
    @abstractmethod
    def is_recording(self) -> bool:
        """是否正在录音"""
        pass


class ISpeechService(ABC):
    """语音识别服务接口"""

    @abstractmethod
    def transcribe(
        self, audio_data: np.ndarray, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """转录音频数据"""
        pass

    @abstractmethod
    def load_model(self) -> None:
        """加载模型"""
        pass

    @abstractmethod
    def unload_model(self) -> None:
        """卸载模型"""
        pass

    @property
    @abstractmethod
    def is_model_loaded(self) -> bool:
        """模型是否已加载"""
        pass


class IAIService(ABC):
    """AI优化服务接口"""

    @abstractmethod
    def refine_text(self, text: str, prompt_template: str, model: str) -> str:
        """优化文本"""
        pass

    @abstractmethod
    def set_api_key(self, api_key: str) -> None:
        """设置API密钥"""
        pass

    # 移除的方法（不必需）：
    # - get_available_models: 在实际使用中不需要获取模型列表
    # - validate_api_key: API密钥验证可在内部处理
    # - get_model_info: 模型信息在实际使用中不需要
    # - test_connection: 连接测试可在内部处理
    # - api_key_configured: 可通过其他方式检查
    # - service_status: 状态信息可在异常中提供


class IInputService(ABC):
    """文本输入服务接口"""

    @abstractmethod
    def input_text(self, text: str) -> bool:
        """输入文本到当前活跃窗口"""
        pass

    @abstractmethod
    def set_preferred_method(self, method: str) -> None:
        """设置首选输入方法"""
        pass

    # 移除的方法（不必需）：
    # - get_available_methods: 输入方法列表在实际使用中不需要
    # - test_input_method: 输入方法测试可在内部处理
    # - get_method_info: 输入方法信息在实际使用中不需要
    # - current_method: 当前方法信息可在内部跟踪
    # - is_ready: 就绪状态可在异常中体现


class IHotkeyService(ABC):
    """快捷键服务接口"""

    @abstractmethod
    def register_hotkey(self, hotkey: str, action: str) -> bool:
        """注册快捷键"""
        pass

    @abstractmethod
    def unregister_hotkey(self, hotkey: str) -> bool:
        """注销快捷键"""
        pass

    @abstractmethod
    def unregister_all_hotkeys(self) -> None:
        """注销所有快捷键"""
        pass

    @abstractmethod
    def start_listening(self) -> bool:
        """开始监听"""
        pass

    @abstractmethod
    def stop_listening(self) -> None:
        """停止监听"""
        pass

    @abstractmethod
    def get_registered_hotkeys(self) -> Dict[str, str]:
        """获取已注册的快捷键"""
        pass

    @property
    @abstractmethod
    def is_listening(self) -> bool:
        """是否正在监听"""
        pass

    # 移除的方法（不必需）：
    # - is_hotkey_available: 复杂且很少需要的功能
    # - registered_count: 可通过len(get_registered_hotkeys())计算
    # - validate_hotkey_format: 可在实现中内部处理


class IConfigService(ABC):
    """配置服务接口"""

    @abstractmethod
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        pass

    @abstractmethod
    def set_setting(self, key: str, value: Any) -> None:
        """设置配置项"""
        pass

    @abstractmethod
    def save_config(self) -> None:
        """保存配置"""
        pass


class IEventService(ABC):
    """事件服务接口"""

    @abstractmethod
    def emit(self, event: str, data: Any = None) -> None:
        """发出事件"""
        pass

    @abstractmethod
    def on(self, event: str, callback: Callable) -> None:
        """监听事件"""
        pass

    @abstractmethod
    def off(self, event: str, callback: Callable) -> None:
        """取消监听"""
        pass
