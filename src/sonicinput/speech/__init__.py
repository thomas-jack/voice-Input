"""语音识别模块初始化"""

from .whisper_engine import WhisperEngine
from .gpu_manager import GPUManager

__all__ = [
    'WhisperEngine',
    'GPUManager'
]