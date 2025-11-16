"""Hotkey and keyboard input constants"""

from typing import Dict

try:
    import win32con

    # Windows Modifier Keys
    MOD_ALT = win32con.MOD_ALT
    MOD_CONTROL = win32con.MOD_CONTROL
    MOD_SHIFT = win32con.MOD_SHIFT
    MOD_WIN = win32con.MOD_WIN

    # Windows Message Constants
    WM_HOTKEY = win32con.WM_HOTKEY
    WM_NULL = win32con.WM_NULL
    WM_QUIT = win32con.WM_QUIT
except ImportError:
    # Fallback values if win32con not available
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_WIN = 0x0008
    WM_HOTKEY = 0x0312
    WM_NULL = 0x0000
    WM_QUIT = 0x0012

# Windows Message Constants (keyboard events)
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104  # Alt combination keys
WM_SYSKEYUP = 0x0105

# Virtual Key Codes - Modifiers
VK_LMENU = 0xA4  # Left Alt
VK_RMENU = 0xA5  # Right Alt
VK_LCONTROL = 0xA2  # Left Ctrl
VK_RCONTROL = 0xA3  # Right Ctrl
VK_LSHIFT = 0xA0  # Left Shift
VK_RSHIFT = 0xA1  # Right Shift
VK_LWIN = 0x5B  # Left Windows
VK_RWIN = 0x5C  # Right Windows

# Virtual Key Codes - Function Keys
VK_FUNCTION_KEYS: Dict[str, int] = {
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
}

# Virtual Key Codes - Special Keys
VK_SPECIAL_KEYS: Dict[str, int] = {
    "space": 0x20,
    "esc": 0x1B,
    "enter": 0x0D,
    "tab": 0x09,
    "backspace": 0x08,
    "delete": 0x2E,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "pause": 0x13,
    "print_screen": 0x2C,
    "scroll_lock": 0x91,
}

# Hotkey Timing Constants (milliseconds)
HOTKEY_TIME_WINDOW_MS = 500  # Max time between keys for combo
HOTKEY_TIMEOUT_CLEANUP_MS = 2000  # Cleanup stuck keys after 2s

# Hotkey Registration Timeout (seconds)
HOTKEY_REGISTRATION_TIMEOUT = 2.0

# Allowed Single-Key Hotkeys (without modifiers)
ALLOWED_SINGLE_KEYS = [
    "f1",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "f10",
    "f11",
    "f12",
    "esc",
    "space",
    "pause",
    "print_screen",
    "scroll_lock",
]

# System Reserved Hotkeys (Do Not Use)
SYSTEM_RESERVED_HOTKEYS = [
    "ctrl+alt+del",
    "ctrl+shift+esc",
    "win+l",
    "win+d",
    "alt+tab",
    "alt+f4",
]
