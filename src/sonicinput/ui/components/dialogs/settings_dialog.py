"""Settings dialog component

A decoupled settings dialog with clean separation between
UI presentation and configuration logic.
"""

from PySide6.QtWidgets import (QDialog, QWidget, QVBoxLayout,
                            QTabWidget, QMessageBox, QDialogButtonBox,
                            QCheckBox, QComboBox, QSpinBox, QDoubleSpinBox,
                            QSlider, QLineEdit)
from PySide6.QtCore import Signal, Qt
from typing import Dict, Any, Optional

from ....utils import app_logger
from .tabs import (GeneralTab, AudioTab, SpeechTab, HotkeysTab,
                  ApiTab, UiTab, LoggingTab)


class SettingsDialog(QDialog):
    """Settings dialog component

    Pure UI component for application settings.
    Handles only UI presentation and user interaction forwarding.
    """

    # UI events (forwarded to controller)
    setting_changed = Signal(str, object)  # key, value
    test_requested = Signal(str)  # test type
    reset_requested = Signal()
    apply_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        # Current configuration state (for UI display)
        self._current_config: Dict[str, Any] = {}
        self._original_config: Dict[str, Any] = {}

        # UI components
        self._tabs: Optional[QTabWidget] = None
        self._controls: Dict[str, QWidget] = {}

        # Setup dialog
        self._setup_dialog()
        self._setup_ui()

        app_logger.log_audio_event("Settings dialog created", {})

    def _setup_dialog(self) -> None:
        """Setup dialog properties"""
        from ...utils import create_app_icon

        self.setWindowTitle("Voice Input Software - Settings")
        self.setWindowIcon(create_app_icon())
        self.setFixedSize(800, 600)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setModal(True)

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)

        # Create tabs
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Create tab instances
        general_tab = GeneralTab(self._on_setting_changed)
        audio_tab = AudioTab(self._on_setting_changed)
        speech_tab = SpeechTab(self._on_setting_changed)
        hotkeys_tab = HotkeysTab(self._on_setting_changed)
        api_tab = ApiTab(self._on_setting_changed)
        ui_tab = UiTab(self._on_setting_changed)
        logging_tab = LoggingTab(self._on_setting_changed)

        # Connect test signals from tabs
        speech_tab.test_requested.connect(self.test_requested.emit)
        hotkeys_tab.test_requested.connect(self.test_requested.emit)
        api_tab.test_requested.connect(self.test_requested.emit)

        # Add tabs to tab widget
        self._tabs.addTab(general_tab, "General")
        self._tabs.addTab(audio_tab, "Audio")
        self._tabs.addTab(speech_tab, "Speech")
        self._tabs.addTab(hotkeys_tab, "Hotkeys")
        self._tabs.addTab(api_tab, "API")
        self._tabs.addTab(ui_tab, "UI")
        self._tabs.addTab(logging_tab, "Logging")

        # Collect all controls from tabs
        for tab in [general_tab, audio_tab, speech_tab, hotkeys_tab, api_tab, ui_tab, logging_tab]:
            self._controls.update(tab.get_controls())

        # Store reference to logging tab for category checkboxes
        self._logging_tab = logging_tab

        # Create button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply |
            QDialogButtonBox.StandardButton.RestoreDefaults
        )

        # Connect button signals
        button_box.accepted.connect(self._on_ok_clicked)
        button_box.rejected.connect(self._on_cancel_clicked)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply_clicked)
        button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._on_reset_clicked)

        layout.addWidget(button_box)

    # ==================== Event Handlers ====================

    def _on_setting_changed(self, key: str, value: Any) -> None:
        """Handle setting change

        Args:
            key: Setting key
            value: New value
        """
        self._current_config[key] = value
        self.setting_changed.emit(key, value)

    def _on_ok_clicked(self) -> None:
        """Handle OK button click"""
        self.apply_requested.emit()
        self.accept()

    def _on_cancel_clicked(self) -> None:
        """Handle Cancel button click"""
        self.cancel_requested.emit()
        self.reject()

    def _on_apply_clicked(self) -> None:
        """Handle Apply button click"""
        self.apply_requested.emit()

    def _on_reset_clicked(self) -> None:
        """Handle Reset to Defaults button click"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.reset_requested.emit()

    # ==================== Public Interface ====================

    def load_configuration(self, config: Dict[str, Any]) -> None:
        """Load configuration into UI

        Args:
            config: Configuration dictionary
        """
        self._current_config = config.copy()
        self._original_config = config.copy()

        # Update UI controls
        for key, value in config.items():
            if key in self._controls:
                control = self._controls[key]
                self._set_control_value(control, value)
            elif key == "logging.enabled_categories":
                # Special handling for logging categories
                category_checkboxes = self._logging_tab.get_category_checkboxes()
                for cat, cb in category_checkboxes.items():
                    cb.blockSignals(True)
                    cb.setChecked(cat in value)
                    cb.blockSignals(False)

    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration from UI

        Returns:
            Configuration dictionary
        """
        return self._current_config.copy()

    def _set_control_value(self, control: QWidget, value: Any) -> None:
        """Set control value without triggering signals

        Args:
            control: UI control
            value: Value to set
        """
        # Block signals to avoid triggering change events
        control.blockSignals(True)

        try:
            if isinstance(control, QCheckBox):
                control.setChecked(bool(value))
            elif isinstance(control, QComboBox):
                index = control.findText(str(value))
                if index >= 0:
                    control.setCurrentIndex(index)
            elif isinstance(control, QSpinBox):
                control.setValue(int(value))
            elif isinstance(control, QDoubleSpinBox):
                control.setValue(float(value))
            elif isinstance(control, QSlider):
                if isinstance(value, float):
                    control.setValue(int(value * 100))
                else:
                    control.setValue(int(value))
            elif isinstance(control, QLineEdit):
                control.setText(str(value))

        finally:
            control.blockSignals(False)

    def show_status_message(self, message: str, timeout: int = 3000) -> None:
        """Show a status message

        Args:
            message: Message to show
            timeout: Message timeout in milliseconds
        """
        # For now, just log the message
        # Could be enhanced with a status bar in the future
        app_logger.log_audio_event("Settings status message", {
            "message": message
        })

    def show_error_message(self, title: str, message: str) -> None:
        """Show an error message

        Args:
            title: Error title
            message: Error message
        """
        QMessageBox.critical(self, title, message)

    def show_success_message(self, title: str, message: str) -> None:
        """Show a success message

        Args:
            title: Success title
            message: Success message
        """
        QMessageBox.information(self, title, message)