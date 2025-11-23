"""音频服务接口定义"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

import numpy as np


class IAudioService(ABC):
    """音频服务接口

    提供音频录制、播放和处理功能。
    """

    @abstractmethod
    def start_recording(self, device_id: Optional[int] = None) -> bool:
        """开始录音

        Args:
            device_id: 音频设备ID，None 表示使用默认设备

        Returns:
            是否成功开始录音
        """
        pass

    @abstractmethod
    def stop_recording(self) -> Optional[np.ndarray]:
        """停止录音并返回音频数据

        Returns:
            录制的音频数据，None 表示录音失败
        """
        pass

    @abstractmethod
    def set_audio_callback(self, callback: Callable[[np.ndarray], None]) -> None:
        """设置音频数据回调

        Args:
            callback: 音频数据处理回调函数
        """
        pass

    @abstractmethod
    def get_audio_devices(self) -> List[Dict[str, Any]]:
        """获取可用的音频设备列表

        Returns:
            音频设备信息列表，包含设备ID、名称等
        """
        pass

    @abstractmethod
    def set_audio_device(self, device_id: int) -> bool:
        """设置音频设备

        Args:
            device_id: 音频设备ID

        Returns:
            是否设置成功
        """
        pass

    @property
    @abstractmethod
    def is_recording(self) -> bool:
        """是否正在录音"""
        pass

    @property
    @abstractmethod
    def current_device_id(self) -> Optional[int]:
        """当前使用的音频设备ID"""
        pass

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """采样率"""
        pass

    @abstractmethod
    def get_audio_level(self) -> float:
        """获取当前音频电平

        Returns:
            音频电平 (0.0 - 1.0)
        """
        pass
