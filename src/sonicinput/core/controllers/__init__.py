"""控制器模块

包含各个业务控制器的实现，用于拆分 VoiceInputApp 的职责。
"""

from .recording_controller import RecordingController
from .transcription_controller import TranscriptionController
from .ai_processing_controller import AIProcessingController
from .input_controller import InputController

__all__ = [
    "RecordingController",
    "TranscriptionController",
    "AIProcessingController",
    "InputController",
]
