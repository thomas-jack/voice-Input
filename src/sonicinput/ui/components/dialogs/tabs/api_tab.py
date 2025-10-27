"""API settings tab"""

from PyQt6.QtWidgets import (QWidget, QFormLayout, QGroupBox,
                            QLineEdit, QComboBox, QPushButton, QCheckBox)
from PyQt6.QtCore import pyqtSignal, Qt
from typing import Callable, Any

from .base_tab import BaseSettingsTab
from .....utils.constants import ConfigKeys


class ApiTab(BaseSettingsTab):
    """API settings tab"""

    # Signal for test request
    test_requested = pyqtSignal(str)

    def __init__(self, on_setting_changed: Callable[[str, Any], None], parent: QWidget = None):
        super().__init__(on_setting_changed, parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QFormLayout(self)

        # OpenRouter API group
        api_group = QGroupBox("OpenRouter API Settings")
        api_layout = QFormLayout(api_group)

        # API key
        api_key_edit = QLineEdit()
        api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_key_edit.textChanged.connect(
            lambda text: self._on_setting_changed(ConfigKeys.OPENROUTER_API_KEY, text)
        )
        self._controls[ConfigKeys.OPENROUTER_API_KEY] = api_key_edit
        api_layout.addRow("API Key:", api_key_edit)

        # Model
        api_model_combo = QComboBox()
        api_model_combo.addItems([
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo"
        ])
        api_model_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed(ConfigKeys.OPENROUTER_MODEL, text)
        )
        self._controls[ConfigKeys.OPENROUTER_MODEL] = api_model_combo
        api_layout.addRow("Model:", api_model_combo)

        # Test API button
        test_api_btn = QPushButton("Test API")
        test_api_btn.clicked.connect(lambda: self.test_requested.emit("api"))
        api_layout.addRow("", test_api_btn)

        layout.addWidget(api_group)

        # Text processing group
        processing_group = QGroupBox("Text Processing")
        processing_layout = QFormLayout(processing_group)

        # Enable optimization
        optimize_cb = QCheckBox("Enable text optimization")
        optimize_cb.stateChanged.connect(
            lambda state: self._on_setting_changed(ConfigKeys.TEXT_OPTIMIZATION_ENABLED, state == Qt.CheckState.Checked)
        )
        self._controls[ConfigKeys.TEXT_OPTIMIZATION_ENABLED] = optimize_cb
        processing_layout.addRow("Optimization:", optimize_cb)

        layout.addWidget(processing_group)
