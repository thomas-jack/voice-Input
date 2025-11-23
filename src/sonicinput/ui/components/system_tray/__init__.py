"""System tray component module

Provides a decoupled system tray implementation with clear separation
between UI rendering and business logic.
"""

from .tray_controller import TrayController
from .tray_widget import TrayWidget

__all__ = [
    "TrayWidget",
    "TrayController",
]
