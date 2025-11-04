"""Hotkeys settings tab"""

from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QHBoxLayout,
    QComboBox,
    QLabel,
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

        # Hotkey backend selection
        backend_combo = QComboBox()
        backend_combo.addItem("Auto (Recommended)", "auto")
        backend_combo.addItem("Win32 RegisterHotKey (No admin needed)", "win32")
        backend_combo.addItem("Pynput (Admin recommended)", "pynput")
        backend_combo.currentIndexChanged.connect(
            lambda: self._on_backend_changed(backend_combo)
        )
        self._controls["hotkey_backend"] = backend_combo

        # Backend info label
        backend_info_label = QLabel()
        backend_info_label.setWordWrap(True)
        backend_info_label.setStyleSheet("color: #888; font-size: 10px;")
        self._backend_info_label = backend_info_label

        hotkeys_layout.addRow("Hotkey Backend:", backend_combo)
        hotkeys_layout.addRow("", backend_info_label)

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

    def _on_backend_changed(self, combo: QComboBox) -> None:
        """Handle backend selection change"""
        backend = combo.currentData()

        # Update info label
        backend_info = self._get_backend_info(backend)
        self._backend_info_label.setText(backend_info)

        # Notify setting change
        self._on_setting_changed("hotkeys.backend", backend)

    def _get_backend_info(self, backend: str) -> str:
        """Get information text for selected backend"""
        info_map = {
            "auto": "Automatically selects the best backend (currently: Win32). No admin privileges required.",
            "win32": "Uses Windows RegisterHotKey API. Works without admin privileges but cannot suppress hotkey events.",
            "pynput": "Uses low-level keyboard hooks. Requires admin privileges for reliable operation across all windows.",
        }
        return info_map.get(backend, "")
