"""设置标签页模块

将 settings_window.py 中的各个标签页拆分成独立模块，提高可维护性。
"""

from .ai_tab import AITab
from .application_tab import ApplicationTab
from .audio_input_tab import AudioInputTab
from .base_tab import BaseSettingsTab
from .history_tab import HistoryTab
from .hotkey_tab import HotkeyTab
from .transcription_tab import TranscriptionTab

__all__ = [
    "BaseSettingsTab",
    "ApplicationTab",
    "HotkeyTab",
    "TranscriptionTab",
    "AITab",
    "AudioInputTab",
    "HistoryTab",
]
