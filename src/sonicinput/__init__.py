"""Voice Input Software - Windows语音输入软件

一个基于Whisper和AI优化的Windows语音转文本输入解决方案
"""

__version__ = "0.1.3"
__author__ = "Oxidane"
__description__ = "SonicInput"

from .core.voice_input_app import VoiceInputApp
from .utils import app_logger

__all__ = ["VoiceInputApp", "app_logger"]
