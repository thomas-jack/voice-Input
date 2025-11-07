"""设置标签页模块

将 settings_window.py 中的各个标签页拆分成独立模块，提高可维护性。
"""

from .base_tab import BaseSettingsTab
from .application_tab import ApplicationTab
from .hotkey_tab import HotkeyTab
from .transcription_tab import TranscriptionTab
from .ai_tab import AITab
from .audio_input_tab import AudioInputTab
from .history_tab import HistoryTab

__all__ = [
    "BaseSettingsTab",
    "ApplicationTab",
    "HotkeyTab",
    "TranscriptionTab",
    "AITab",
    "AudioInputTab",
    "HistoryTab",
]
