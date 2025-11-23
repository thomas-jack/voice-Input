"""Error dialog utilities

Provides user-friendly error dialogs with actionable suggestions
"""

from typing import List, Optional

from PySide6.QtWidgets import QMessageBox, QWidget


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
    message = (
        f"The hotkey '{conflicting_hotkey}' is already in use by another application."
    )
    message += "\n\n"
    message += "Common causes:"
    message += "\n- Web browser developer tools (F12 is commonly used)"
    message += "\n- Another application running with administrator privileges"
    message += "\n- Game launchers or recording software"
    message += "\n- System shortcuts"
    message += "\n\n"
    message += "Solutions:"
    message += "\n1. Change the hotkey in Settings (recommended)"
    message += "\n2. Run SonicInput as administrator (if the conflicting app is admin)"
    message += "\n3. Close the conflicting application"

    if suggestions:
        message += "\n\n"
        message += "Suggested alternative hotkeys:"
        for i, suggestion in enumerate(suggestions, 1):
            message += f"\n  - {suggestion.upper()}"

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
