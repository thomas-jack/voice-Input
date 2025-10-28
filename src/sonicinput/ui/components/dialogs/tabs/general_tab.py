"""General settings tab"""

from PySide6.QtWidgets import (QWidget, QFormLayout, QGroupBox,
                            QCheckBox, QComboBox, QSpinBox)
from PySide6.QtCore import Qt
from typing import Callable, Any

from .base_tab import BaseSettingsTab
from .....utils.constants import ConfigKeys


class GeneralTab(BaseSettingsTab):
    """General settings tab"""

    def __init__(self, on_setting_changed: Callable[[str, Any], None], parent: QWidget = None):
        super().__init__(on_setting_changed, parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QFormLayout(self)

        # Application settings group
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)

        # Auto-start
        auto_start_cb = QCheckBox("Start with Windows")
        auto_start_cb.stateChanged.connect(
            lambda state: self._on_setting_changed(ConfigKeys.AUTO_START, state == Qt.CheckState.Checked)
        )
        self._controls[ConfigKeys.AUTO_START] = auto_start_cb
        app_layout.addRow("Auto Start:", auto_start_cb)

        # Notifications
        notifications_cb = QCheckBox("Enable notifications")
        notifications_cb.stateChanged.connect(
            lambda state: self._on_setting_changed(ConfigKeys.NOTIFICATIONS_ENABLED, state == Qt.CheckState.Checked)
        )
        self._controls[ConfigKeys.NOTIFICATIONS_ENABLED] = notifications_cb
        app_layout.addRow("Notifications:", notifications_cb)

        # Log level
        log_level_combo = QComboBox()
        log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_level_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed(ConfigKeys.LOG_LEVEL, text)
        )
        self._controls[ConfigKeys.LOG_LEVEL] = log_level_combo
        app_layout.addRow("Log Level:", log_level_combo)

        layout.addWidget(app_group)

        # Behavior settings group
        behavior_group = QGroupBox("Behavior Settings")
        behavior_layout = QFormLayout(behavior_group)

        # Recording timeout
        timeout_spin = QSpinBox()
        timeout_spin.setRange(1, 60)
        timeout_spin.setSuffix(" seconds")
        timeout_spin.valueChanged.connect(
            lambda value: self._on_setting_changed(ConfigKeys.RECORDING_TIMEOUT, value)
        )
        self._controls[ConfigKeys.RECORDING_TIMEOUT] = timeout_spin
        behavior_layout.addRow("Recording Timeout:", timeout_spin)

        layout.addWidget(behavior_group)
