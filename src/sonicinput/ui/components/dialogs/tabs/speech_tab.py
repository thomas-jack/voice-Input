"""Speech recognition settings tab"""

from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QGroupBox,
    QComboBox,
    QPushButton,
    QDoubleSpinBox,
)
from PySide6.QtCore import Signal
from typing import Callable, Any

from .base_tab import BaseSettingsTab
from .....utils.constants import ConfigKeys


class SpeechTab(BaseSettingsTab):
    """Speech recognition settings tab"""

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

        # Model settings group
        model_group = QGroupBox("Speech Recognition Model")
        model_layout = QFormLayout(model_group)

        # Model selection
        model_combo = QComboBox()
        model_combo.addItems(
            ["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo", "turbo"]
        )
        model_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed(ConfigKeys.WHISPER_MODEL, text)
        )
        self._controls[ConfigKeys.WHISPER_MODEL] = model_combo
        model_layout.addRow("Whisper Model:", model_combo)

        # Language
        language_combo = QComboBox()
        language_combo.addItems(["auto", "en", "zh", "es", "fr", "de", "ja", "ko"])
        language_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed(ConfigKeys.SPEECH_LANGUAGE, text)
        )
        self._controls[ConfigKeys.SPEECH_LANGUAGE] = language_combo
        model_layout.addRow("Language:", language_combo)

        # Test model button
        test_model_btn = QPushButton("Test Model")
        test_model_btn.clicked.connect(lambda: self.test_requested.emit("model"))
        model_layout.addRow("", test_model_btn)

        layout.addWidget(model_group)

        # Recognition settings group
        recognition_group = QGroupBox("Recognition Settings")
        recognition_layout = QFormLayout(recognition_group)

        # Temperature
        temperature_spin = QDoubleSpinBox()
        temperature_spin.setRange(0.0, 1.0)
        temperature_spin.setSingleStep(0.1)
        temperature_spin.setDecimals(1)
        temperature_spin.valueChanged.connect(
            lambda value: self._on_setting_changed(
                ConfigKeys.WHISPER_TEMPERATURE, value
            )
        )
        self._controls[ConfigKeys.WHISPER_TEMPERATURE] = temperature_spin
        recognition_layout.addRow("Temperature:", temperature_spin)

        layout.addWidget(recognition_group)
