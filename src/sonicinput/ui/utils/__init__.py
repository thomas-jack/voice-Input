"""UI utilities"""

from .error_dialogs import (
    show_error_with_details,
    show_hotkey_conflict_error,
    show_hotkey_registration_error,
)
from .icon_utils import create_app_icon, get_app_icon

__all__ = [
    "get_app_icon",
    "create_app_icon",
    "show_hotkey_conflict_error",
    "show_hotkey_registration_error",
    "show_error_with_details",
]
