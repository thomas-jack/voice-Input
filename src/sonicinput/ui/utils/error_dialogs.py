"""Error dialog utilities

Provides user-friendly error dialogs with actionable suggestions
"""

from typing import Optional, List
from PySide6.QtWidgets import QMessageBox, QWidget
from PySide6.QtCore import Qt


def show_hotkey_conflict_error(
    parent: Optional[QWidget],
    conflicting_hotkey: str,
    suggestions: List[str],
) -> None:
    """Show user-friendly hotkey conflict error dialog

    Args:
        parent: Parent widget
        conflicting_hotkey: The hotkey that conflicted
        suggestions: List of suggested alternative hotkeys
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle("Hotkey Conflict")

    # Build message
    message = f"The hotkey '{conflicting_hotkey}' is already in use by another application."
    message += "\n\n"
    message += "This could be:"
    message += "\n- Your web browser (F12 is common for developer tools)"
    message += "\n- Another application with global hotkeys"
    message += "\n- System shortcuts"

    if suggestions:
        message += "\n\n"
        message += "Suggested alternatives:"
        for i, suggestion in enumerate(suggestions, 1):
            message += f"\n{i}. {suggestion.upper()}"

    message += "\n\n"
    message += "You can change the hotkey in Settings > Hotkeys tab."

    msg_box.setText(message)

    # Add buttons
    msg_box.addButton("Open Settings", QMessageBox.AcceptRole)
    msg_box.addButton("Close", QMessageBox.RejectRole)

    msg_box.setDefaultButton(msg_box.button(QMessageBox.AcceptRole))

    # Show dialog
    result = msg_box.exec()

    # If user chose to open settings, emit signal or return value
    # (Implementation depends on how settings are opened)
    # For now, we'll just show the dialog
    return result == QMessageBox.AcceptRole


def show_hotkey_registration_error(
    parent: Optional[QWidget],
    error_message: str,
    recovery_suggestions: Optional[List[str]] = None,
) -> None:
    """Show generic hotkey registration error dialog

    Args:
        parent: Parent widget
        error_message: Error message to display
        recovery_suggestions: Optional list of recovery suggestions
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowTitle("Hotkey Registration Error")

    message = error_message

    if recovery_suggestions:
        message += "\n\n"
        message += "Suggestions:"
        for i, suggestion in enumerate(recovery_suggestions, 1):
            message += f"\n{i}. {suggestion}"

    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()


def show_error_with_details(
    parent: Optional[QWidget],
    title: str,
    message: str,
    detailed_text: Optional[str] = None,
) -> None:
    """Show error dialog with optional detailed text

    Args:
        parent: Parent widget
        title: Dialog title
        message: Main error message
        detailed_text: Optional detailed technical information
    """
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)

    if detailed_text:
        msg_box.setDetailedText(detailed_text)

    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec()
