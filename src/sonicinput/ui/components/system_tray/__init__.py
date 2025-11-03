"""System tray component module

Provides a decoupled system tray implementation with clear separation
between UI rendering and business logic.
"""

from .tray_widget import TrayWidget
from .tray_controller import TrayController

__all__ = [
    "TrayWidget",
    "TrayController",
]
