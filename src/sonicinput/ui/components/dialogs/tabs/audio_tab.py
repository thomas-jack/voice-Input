"""Audio settings tab"""

from PyQt6.QtWidgets import (QWidget, QFormLayout, QGroupBox,
                            QComboBox, QCheckBox, QSpinBox, QSlider)
from PyQt6.QtCore import Qt
from typing import Callable, Any

from .base_tab import BaseSettingsTab
from .....utils.constants import ConfigKeys


class AudioTab(BaseSettingsTab):
    """Audio settings tab"""

    def __init__(self, on_setting_changed: Callable[[str, Any], None], parent: QWidget = None):
        super().__init__(on_setting_changed, parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QFormLayout(self)

        # Audio device group
        device_group = QGroupBox("Audio Device Settings")
        device_layout = QFormLayout(device_group)

        # Input device
        input_device_combo = QComboBox()
        input_device_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed(ConfigKeys.AUDIO_INPUT_DEVICE, text)
        )
        self._controls[ConfigKeys.AUDIO_INPUT_DEVICE] = input_device_combo
        device_layout.addRow("Input Device:", input_device_combo)

        # Sample rate
        sample_rate_combo = QComboBox()
        sample_rate_combo.addItems(["16000", "22050", "44100", "48000"])
        sample_rate_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed(ConfigKeys.AUDIO_SAMPLE_RATE, int(text))
        )
        self._controls[ConfigKeys.AUDIO_SAMPLE_RATE] = sample_rate_combo
        device_layout.addRow("Sample Rate:", sample_rate_combo)

        # Channels
        channels_spin = QSpinBox()
        channels_spin.setRange(1, 2)
        channels_spin.valueChanged.connect(
            lambda value: self._on_setting_changed(ConfigKeys.AUDIO_CHANNELS, value)
        )
        self._controls[ConfigKeys.AUDIO_CHANNELS] = channels_spin
        device_layout.addRow("Channels:", channels_spin)

        layout.addWidget(device_group)

        # Audio processing group
        processing_group = QGroupBox("Audio Processing")
        processing_layout = QFormLayout(processing_group)

        # Noise reduction
        noise_reduction_cb = QCheckBox("Enable noise reduction")
        noise_reduction_cb.stateChanged.connect(
            lambda state: self._on_setting_changed(ConfigKeys.NOISE_REDUCTION_ENABLED, state == Qt.CheckState.Checked)
        )
        self._controls[ConfigKeys.NOISE_REDUCTION_ENABLED] = noise_reduction_cb
        processing_layout.addRow("Noise Reduction:", noise_reduction_cb)

        # Volume threshold
        volume_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        volume_threshold_slider.setRange(0, 100)
        volume_threshold_slider.valueChanged.connect(
            lambda value: self._on_setting_changed(ConfigKeys.VOLUME_THRESHOLD, value / 100.0)
        )
        self._controls[ConfigKeys.VOLUME_THRESHOLD] = volume_threshold_slider
        processing_layout.addRow("Volume Threshold:", volume_threshold_slider)

        layout.addWidget(processing_group)
