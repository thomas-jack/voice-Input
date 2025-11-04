"""UI utilities"""

from .icon_utils import get_app_icon, create_app_icon
from .error_dialogs import (
    show_hotkey_conflict_error,
    show_hotkey_registration_error,
    show_error_with_details,
)

__all__ = [
    "get_app_icon",
    "create_app_icon",
    "show_hotkey_conflict_error",
    "show_hotkey_registration_error",
    "show_error_with_details",
]
