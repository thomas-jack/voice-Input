"""语音识别服务接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import numpy as np


class ISpeechService(ABC):
    """语音识别服务接口

    提供语音转文本功能，支持多种语言和模型。
    """

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> Dict[str, Any]:
        """转录音频数据

        Args:
            audio_data: 音频数据
            language: 语言代码，None 表示自动检测

        Returns:
            转录结果，包含文本、置信度等信息
        """
        pass

    @abstractmethod
    def load_model(self, model_name: Optional[str] = None) -> bool:
        """加载语音识别模型

        Args:
            model_name: 模型名称，None 表示使用默认模型

        Returns:
            是否加载成功
        """
        pass

    @abstractmethod
    def unload_model(self) -> None:
        """卸载当前模型"""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表

        Returns:
            模型名称列表
        """
        pass

    @property
    @abstractmethod
    def is_model_loaded(self) -> bool:
        """模型是否已加载"""
        pass

    # 移除的方法（不必需）：
    # - get_supported_languages: 静态信息，可在其他地方提供
    # - set_progress_callback: UI特定功能，不属于核心服务
    # - current_model: 可通过其他方式获取
    # - is_gpu_available: 可从GPU管理器获取
    # - model_loading_progress: UI特定功能