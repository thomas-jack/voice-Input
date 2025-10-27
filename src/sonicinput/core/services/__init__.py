"""核心服务模块

包含应用程序的核心业务服务,实现高内聚、低耦合的服务架构。
"""

from .event_bus import EventBus, Events
from .config_service import ConfigService
from .state_manager import StateManager
from .lifecycle_manager import LifecycleManager
from .transcription_service import TranscriptionService, TranscriptionResult

__all__ = [
    'EventBus',
    'Events',
    'ConfigService',
    'StateManager',
    'LifecycleManager',
    'TranscriptionService',
    'TranscriptionResult',
]