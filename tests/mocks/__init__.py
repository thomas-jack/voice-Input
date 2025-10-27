"""Mock 对象库"""
from .audio_mock import MockAudioRecorder
from .whisper_mock import MockWhisperEngine
from .ai_mock import MockAIService
from .input_mock import MockInputService

__all__ = [
    'MockAudioRecorder',
    'MockWhisperEngine',
    'MockAIService',
    'MockInputService'
]
