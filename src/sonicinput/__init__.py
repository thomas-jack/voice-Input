"""Voice Input Software - Windows语音输入软件

一个基于Whisper和AI优化的Windows语音转文本输入解决方案
"""

__version__ = "0.1.0"
__author__ = "Voice Input Software Team"
__description__ = "Windows语音输入软件"

from .core.voice_input_app import VoiceInputApp
from .utils import app_logger

__all__ = ["VoiceInputApp", "app_logger"]
