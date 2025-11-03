"""Hotkeys settings tab"""

from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal
from typing import Callable, Any

from .base_tab import BaseSettingsTab
from .....utils.constants import ConfigKeys


class HotkeysTab(BaseSettingsTab):
    """Hotkeys settings tab"""

    # Signal for test request
    test_requested = Signal(str)

    def __init__(
        self, on_setting_changed: Callable[[str, Any], None], parent: QWidget = None
    ):
        super().__init__(on_setting_changed, parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QFormLayout(self)

        # Hotkeys group
        hotkeys_group = QGroupBox("Global Hotkeys")
        hotkeys_layout = QFormLayout(hotkeys_group)

        # Recording hotkey
        recording_hotkey_edit = QLineEdit()
        recording_hotkey_edit.setReadOnly(True)
        recording_hotkey_edit.setPlaceholderText("Click 'Set' to configure")
        self._controls[ConfigKeys.RECORDING_HOTKEY] = recording_hotkey_edit

        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(recording_hotkey_edit)

        set_hotkey_btn = QPushButton("Set")
        set_hotkey_btn.clicked.connect(lambda: self.test_requested.emit("hotkey"))
        hotkey_layout.addWidget(set_hotkey_btn)

        hotkeys_layout.addRow("Recording Hotkey:", hotkey_layout)

        # Enable global hotkeys
        enable_hotkeys_cb = QCheckBox("Enable global hotkeys")
        enable_hotkeys_cb.stateChanged.connect(
            lambda state: self._on_setting_changed(
                ConfigKeys.HOTKEYS_ENABLED, state == Qt.CheckState.Checked
            )
        )
        self._controls[ConfigKeys.HOTKEYS_ENABLED] = enable_hotkeys_cb
        hotkeys_layout.addRow("Enable Hotkeys:", enable_hotkeys_cb)

        layout.addWidget(hotkeys_group)
