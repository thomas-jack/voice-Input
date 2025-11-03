"""设置标签页模块

将 settings_window.py 中的各个标签页拆分成独立模块，提高可维护性。
"""

from .base_tab import BaseSettingsTab
from .general_tab import GeneralTab
from .hotkey_tab import HotkeyTab
from .transcription_tab import TranscriptionTab
from .ai_tab import AITab
from .audio_tab import AudioTab
from .input_tab import InputTab
from .ui_tab import UITab

__all__ = [
    "BaseSettingsTab",
    "GeneralTab",
    "HotkeyTab",
    "TranscriptionTab",
    "AITab",
    "AudioTab",
    "InputTab",
    "UITab",
]
