"""Settings dialog tabs package"""

from .base_tab import BaseSettingsTab
from .general_tab import GeneralTab
from .audio_tab import AudioTab
from .speech_tab import SpeechTab
from .hotkeys_tab import HotkeysTab
from .api_tab import ApiTab
from .ui_tab import UiTab
from .logging_tab import LoggingTab

__all__ = [
    "BaseSettingsTab",
    "GeneralTab",
    "AudioTab",
    "SpeechTab",
    "HotkeysTab",
    "ApiTab",
    "UiTab",
    "LoggingTab",
]
