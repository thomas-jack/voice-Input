"""UI settings tab"""

from PySide6.QtWidgets import (
    QWidget,
    QFormLayout,
    QGroupBox,
    QCheckBox,
    QComboBox,
    QSlider,
)
from PySide6.QtCore import Qt
from typing import Callable, Any

from .base_tab import BaseSettingsTab
from .....utils.constants import ConfigKeys


class UiTab(BaseSettingsTab):
    """UI settings tab"""

    def __init__(
        self, on_setting_changed: Callable[[str, Any], None], parent: QWidget = None
    ):
        super().__init__(on_setting_changed, parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QFormLayout(self)

        # Overlay settings group
        overlay_group = QGroupBox("Overlay Settings")
        overlay_layout = QFormLayout(overlay_group)

        # Show overlay
        show_overlay_cb = QCheckBox("Show recording overlay")
        show_overlay_cb.stateChanged.connect(
            lambda state: self._on_setting_changed(
                ConfigKeys.OVERLAY_ENABLED, state == Qt.CheckState.Checked
            )
        )
        self._controls[ConfigKeys.OVERLAY_ENABLED] = show_overlay_cb
        overlay_layout.addRow("Show Overlay:", show_overlay_cb)

        # Overlay position
        position_combo = QComboBox()
        position_combo.addItems(
            ["top_left", "top_right", "bottom_left", "bottom_right", "center"]
        )
        position_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed(ConfigKeys.OVERLAY_POSITION, text)
        )
        self._controls[ConfigKeys.OVERLAY_POSITION] = position_combo
        overlay_layout.addRow("Position:", position_combo)

        # Overlay opacity
        opacity_slider = QSlider(Qt.Orientation.Horizontal)
        opacity_slider.setRange(10, 100)
        opacity_slider.valueChanged.connect(
            lambda value: self._on_setting_changed(
                ConfigKeys.OVERLAY_OPACITY, value / 100.0
            )
        )
        self._controls[ConfigKeys.OVERLAY_OPACITY] = opacity_slider
        overlay_layout.addRow("Opacity:", opacity_slider)

        layout.addWidget(overlay_group)

        # Theme settings group
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QFormLayout(theme_group)

        # Theme selection
        theme_combo = QComboBox()
        theme_combo.addItems(["light", "dark", "auto"])
        theme_combo.currentTextChanged.connect(
            lambda text: self._on_setting_changed(ConfigKeys.UI_THEME, text)
        )
        self._controls[ConfigKeys.UI_THEME] = theme_combo
        theme_layout.addRow("Theme:", theme_combo)

        layout.addWidget(theme_group)
