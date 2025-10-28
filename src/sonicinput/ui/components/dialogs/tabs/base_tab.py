"""Base class for settings dialog tabs"""

from PySide6.QtWidgets import QWidget
from typing import Dict, Any, Callable


class BaseSettingsTab(QWidget):
    """Base class for settings dialog tabs

    Provides common functionality for all settings tabs.
    """

    def __init__(self, on_setting_changed: Callable[[str, Any], None], parent: QWidget = None):
        """Initialize base tab

        Args:
            on_setting_changed: Callback for setting changes
            parent: Parent widget
        """
        super().__init__(parent)
        self._on_setting_changed = on_setting_changed
        self._controls: Dict[str, QWidget] = {}

    def get_controls(self) -> Dict[str, QWidget]:
        """Get all controls in this tab

        Returns:
            Dictionary of control key to widget
        """
        return self._controls
