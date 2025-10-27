"""Model loader dialog component

A decoupled model loading dialog with clean separation between
UI presentation and model loading logic.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                            QProgressBar, QTextEdit, QMessageBox, QHBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional
import time

from ....utils import app_logger


class ModelLoaderDialog(QDialog):
    """Model loader dialog component

    Pure UI component for model loading operations.
    Handles only UI presentation and user interaction forwarding.
    """

    # UI events (forwarded to controller)
    load_requested = pyqtSignal(str)  # model_name
    cancel_requested = pyqtSignal()
    dialog_closed = pyqtSignal()

    def __init__(self, model_name: str = "", parent: Optional[QDialog] = None):
        super().__init__(parent)

        self._model_name = model_name
        self._is_loading = False
        self._progress_value = 0

        # UI components
        self._status_label: Optional[QLabel] = None
        self._progress_bar: Optional[QProgressBar] = None
        self._log_text: Optional[QTextEdit] = None
        self._cancel_button: Optional[QPushButton] = None
        self._close_button: Optional[QPushButton] = None

        self._setup_dialog()
        self._setup_ui()

        app_logger.log_audio_event("Model loader dialog created", {
            "model_name": model_name
        })

    def _setup_dialog(self) -> None:
        """Setup dialog properties"""
        from ...utils import create_app_icon

        self.setWindowTitle("Loading Whisper Model")
        self.setWindowIcon(create_app_icon())
        self.setFixedSize(500, 400)
        self.setModal(True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

    def _setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Whisper Model Loader")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Model name label
        model_label = QLabel(f"Model: {self._model_name}")
        model_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(model_label)

        # Status label
        self._status_label = QLabel("Ready to load model...")
        self._status_label.setWordWrap(True)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        layout.addWidget(self._progress_bar)

        # Log text area
        log_label = QLabel("Loading Log:")
        layout.addWidget(log_label)

        self._log_text = QTextEdit()
        self._log_text.setMaximumHeight(150)
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet(
            "font-family: 'Courier New', monospace; "
            "font-size: 9px; "
            "background-color: #f5f5f5; "
            "border: 1px solid #ccc;"
        )
        layout.addWidget(self._log_text)

        # Button layout
        button_layout = QHBoxLayout()

        # Load button
        load_button = QPushButton("Load Model")
        load_button.clicked.connect(self._on_load_clicked)
        button_layout.addWidget(load_button)

        # Cancel button
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.clicked.connect(self._on_cancel_clicked)
        self._cancel_button.setEnabled(False)  # Disabled until loading starts
        button_layout.addWidget(self._cancel_button)

        # Close button
        self._close_button = QPushButton("Close")
        self._close_button.clicked.connect(self._on_close_clicked)
        button_layout.addWidget(self._close_button)

        layout.addLayout(button_layout)

    def _on_load_clicked(self) -> None:
        """Handle load button click"""
        if not self._is_loading:
            self.load_requested.emit(self._model_name)

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click"""
        if self._is_loading:
            self.cancel_requested.emit()

    def _on_close_clicked(self) -> None:
        """Handle close button click"""
        if self._is_loading:
            # Ask for confirmation if loading
            reply = QMessageBox.question(
                self,
                "Close Dialog",
                "Model loading is in progress. Are you sure you want to close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.dialog_closed.emit()
        self.accept()

    def closeEvent(self, event) -> None:
        """Handle dialog close event"""
        if self._is_loading:
            # Ask for confirmation if loading
            reply = QMessageBox.question(
                self,
                "Close Dialog",
                "Model loading is in progress. Are you sure you want to close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        self.dialog_closed.emit()
        event.accept()

    # ==================== Public Interface ====================

    def set_model_name(self, model_name: str) -> None:
        """Set the model name to load

        Args:
            model_name: Name of the model
        """
        self._model_name = model_name

    def set_loading_state(self, loading: bool) -> None:
        """Set the loading state

        Args:
            loading: Whether model is currently loading
        """
        self._is_loading = loading

        # Update UI state
        if self._cancel_button:
            self._cancel_button.setEnabled(loading)

        if self._close_button:
            self._close_button.setText("Cancel" if loading else "Close")

    def set_status(self, status: str) -> None:
        """Set the status message

        Args:
            status: Status message to display
        """
        if self._status_label:
            self._status_label.setText(status)

    def set_progress(self, value: int) -> None:
        """Set the progress value

        Args:
            value: Progress percentage (0-100)
        """
        self._progress_value = value
        if self._progress_bar:
            self._progress_bar.setValue(value)

    def set_indeterminate_progress(self, indeterminate: bool = True) -> None:
        """Set progress bar to indeterminate mode

        Args:
            indeterminate: Whether to use indeterminate progress
        """
        if self._progress_bar:
            if indeterminate:
                self._progress_bar.setRange(0, 0)  # Indeterminate
            else:
                self._progress_bar.setRange(0, 100)  # Determinate
                self._progress_bar.setValue(self._progress_value)

    def append_log(self, message: str) -> None:
        """Append a message to the log

        Args:
            message: Log message to append
        """
        if self._log_text:
            # Add timestamp
            timestamp = time.strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"

            # Append to log
            self._log_text.append(formatted_message)

            # Auto-scroll to bottom
            scrollbar = self._log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def clear_log(self) -> None:
        """Clear the log text"""
        if self._log_text:
            self._log_text.clear()

    def show_success_message(self, title: str, message: str) -> None:
        """Show a success message

        Args:
            title: Message title
            message: Message content
        """
        QMessageBox.information(self, title, message)

    def show_error_message(self, title: str, message: str) -> None:
        """Show an error message

        Args:
            title: Error title
            message: Error message
        """
        QMessageBox.critical(self, title, message)

    def show_warning_message(self, title: str, message: str) -> bool:
        """Show a warning message with Yes/No buttons

        Args:
            title: Warning title
            message: Warning message

        Returns:
            True if user clicked Yes, False if No
        """
        reply = QMessageBox.question(
            self,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def get_model_name(self) -> str:
        """Get the current model name

        Returns:
            Model name
        """
        return self._model_name

    def is_loading(self) -> bool:
        """Check if currently loading

        Returns:
            True if loading, False otherwise
        """
        return self._is_loading

    # ==================== Convenience Methods ====================

    def start_loading(self, status: str = "Loading model...") -> None:
        """Start loading state

        Args:
            status: Status message to show
        """
        self.set_loading_state(True)
        self.set_status(status)
        self.set_indeterminate_progress(True)
        self.clear_log()
        self.append_log("Starting model load...")

    def complete_loading(self, success: bool, message: str = "") -> None:
        """Complete loading state

        Args:
            success: Whether loading was successful
            message: Completion message
        """
        self.set_loading_state(False)
        self.set_indeterminate_progress(False)

        if success:
            self.set_status("Model loaded successfully!")
            self.set_progress(100)
            self.append_log("Model load completed successfully")
            if message:
                self.append_log(message)
        else:
            self.set_status("Model loading failed!")
            self.set_progress(0)
            self.append_log("Model load failed")
            if message:
                self.append_log(f"Error: {message}")

    def cancel_loading(self) -> None:
        """Cancel loading state"""
        self.set_loading_state(False)
        self.set_status("Loading cancelled")
        self.set_indeterminate_progress(False)
        self.set_progress(0)
        self.append_log("Model load cancelled by user")