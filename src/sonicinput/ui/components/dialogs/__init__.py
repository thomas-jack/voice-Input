"""Dialog components module

Provides various dialog components with clean separation
between UI and business logic.
"""

from .settings_dialog import SettingsDialog
from .model_loader_dialog import ModelLoaderDialog

__all__ = [
    'SettingsDialog',
    'ModelLoaderDialog',
]