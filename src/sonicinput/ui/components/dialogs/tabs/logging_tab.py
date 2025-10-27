"""Logging settings tab"""

from PyQt6.QtWidgets import (QWidget, QFormLayout, QGroupBox, QVBoxLayout,
                            QComboBox, QCheckBox, QSpinBox, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt
from typing import Callable, Any, Dict

from .base_tab import BaseSettingsTab


class LoggingTab(BaseSettingsTab):
    """Logging settings tab"""

    def __init__(self, on_setting_changed: Callable[[str, Any], None], parent: QWidget = None):
        super().__init__(on_setting_changed, parent)
        self._category_checkboxes: Dict[str, QCheckBox] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QFormLayout(self)

        # Log Level Settings Group
        level_group = QGroupBox("Log Level Settings")
        level_layout = QFormLayout(level_group)

        # Log level selection
        level_combo = QComboBox()
        level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        level_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed("logging.level", text)
        )
        self._controls["logging.level"] = level_combo
        level_layout.addRow("Log Level:", level_combo)

        # Console output
        console_output_cb = QCheckBox("Enable console output")
        console_output_cb.stateChanged.connect(
            lambda state: self._on_setting_changed("logging.console_output", state == Qt.CheckState.Checked)
        )
        self._controls["logging.console_output"] = console_output_cb
        level_layout.addRow("Console Output:", console_output_cb)

        layout.addWidget(level_group)

        # Category Filter Group
        category_group = QGroupBox("Log Categories")
        category_layout = QVBoxLayout(category_group)

        # Create checkboxes for each category
        categories = ["audio", "api", "ui", "model", "hotkey", "gpu", "startup", "error", "performance"]

        for category in categories:
            cb = QCheckBox(category.upper())
            cb.setChecked(True)  # Default all enabled
            cb.stateChanged.connect(lambda state, cat=category: self._on_category_changed())
            self._category_checkboxes[category] = cb
            category_layout.addWidget(cb)

        layout.addWidget(category_group)

        # File Management Group
        file_group = QGroupBox("Log File Management")
        file_layout = QFormLayout(file_group)

        # Max log file size
        max_size_spin = QSpinBox()
        max_size_spin.setRange(1, 100)
        max_size_spin.setSuffix(" MB")
        max_size_spin.valueChanged.connect(
            lambda value: self._on_setting_changed("logging.max_log_size_mb", value)
        )
        self._controls["logging.max_log_size_mb"] = max_size_spin
        file_layout.addRow("Max File Size:", max_size_spin)

        # Keep logs days
        keep_days_spin = QSpinBox()
        keep_days_spin.setRange(1, 365)
        keep_days_spin.setSuffix(" days")
        keep_days_spin.valueChanged.connect(
            lambda value: self._on_setting_changed("logging.keep_logs_days", value)
        )
        self._controls["logging.keep_logs_days"] = keep_days_spin
        file_layout.addRow("Keep Logs For:", keep_days_spin)

        # Open logs folder button
        open_logs_btn = QPushButton("Open Logs Folder")
        open_logs_btn.clicked.connect(self._on_open_logs_folder)
        file_layout.addRow("", open_logs_btn)

        layout.addWidget(file_group)

    def _on_category_changed(self) -> None:
        """Handle category checkbox change"""
        enabled_categories = [
            cat for cat, cb in self._category_checkboxes.items()
            if cb.isChecked()
        ]
        self._on_setting_changed("logging.enabled_categories", enabled_categories)

    def _on_open_logs_folder(self) -> None:
        """Open the logs folder in file explorer"""
        import os
        log_dir = os.path.join(os.getenv('APPDATA', '.'), 'SonicInput', 'logs')
        try:
            if os.path.exists(log_dir):
                # Use os.startfile() for Windows - safer than subprocess with shell
                os.startfile(log_dir)
            else:
                QMessageBox.warning(self, "Logs Folder Not Found",
                                  f"Logs folder does not exist: {log_dir}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open logs folder: {e}")

    def get_category_checkboxes(self) -> Dict[str, QCheckBox]:
        """Get category checkboxes

        Returns:
            Dictionary of category to checkbox
        """
        return self._category_checkboxes
