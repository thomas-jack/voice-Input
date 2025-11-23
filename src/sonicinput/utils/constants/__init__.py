"""Constants module for SonicInput

Centralizes magic numbers and configuration values used throughout the codebase.
"""

# Import the legacy constants module from the parent directory
# Using importlib to avoid circular import issues with the constants package
import importlib

# Import constants.py as a module under a unique name
# This works in both development and Nuitka packaging
_constants_module = importlib.import_module("sonicinput.utils.constants_legacy")

# Import all classes from the constants module
AppInfo = _constants_module.AppInfo
Paths = _constants_module.Paths
ConfigKeys = _constants_module.ConfigKeys
Defaults = _constants_module.Defaults
Limits = _constants_module.Limits
UI = _constants_module.UI
AudioLegacy = _constants_module.Audio
Whisper = _constants_module.Whisper
InputMethods = _constants_module.InputMethods
Events = _constants_module.Events
ErrorMessages = _constants_module.ErrorMessages
SuccessMessages = _constants_module.SuccessMessages
Timing = _constants_module.Timing
Patterns = _constants_module.Patterns
Versions = _constants_module.Versions

# Export Audio as both AudioLegacy and Audio for backward compatibility
Audio = AudioLegacy

# Clean up the temporary reference
del _constants_module

from .audio import (
    AUDIO_CLEANUP_TIMEOUT,
    # Audio Levels
    AUDIO_LEVEL_LOW_THRESHOLD,
    AUDIO_LEVEL_MED_THRESHOLD,
    AUDIO_LEVEL_QUIET,
    # Timeouts
    AUDIO_THREAD_JOIN_TIMEOUT,
    AUDIO_THREAD_JOIN_TIMEOUT_LONG,
    # Chunk Sizes
    CHUNK_SIZE_DEFAULT,
    CHUNK_SIZE_LARGE,
    CHUNK_SIZE_SMALL,
    FRAME_LENGTH_MS,
    HOP_LENGTH_MS,
    # Audio Conversion
    INT16_MAX,
    INT16_MAX_INT,
    INT32_MAX,
    NORMALIZATION_MAX_GAIN,
    # Audio Processing
    NORMALIZATION_TARGET_LEVEL,
    RESAMPLE_CHUNK_SIZE,
    # Resampling
    RESAMPLE_LARGE_AUDIO_THRESHOLD,
    RESAMPLE_RATIO_TOLERANCE,
    # Sample Rates
    SAMPLE_RATE_16KHZ,
    SAMPLE_RATE_44KHZ,
    SAMPLE_RATE_48KHZ,
    SILENCE_MIN_DURATION,
    SILENCE_THRESHOLD_DEFAULT,
    # Streaming
    STREAMING_CHUNK_DURATION_DEFAULT,
    STREAMING_CHUNK_DURATION_LONG,
    STREAMING_CHUNK_DURATION_SHORT,
)
from .hotkeys import (
    # Configuration
    ALLOWED_SINGLE_KEYS,
    HOTKEY_REGISTRATION_TIMEOUT,
    # Timing Constants
    HOTKEY_TIME_WINDOW_MS,
    HOTKEY_TIMEOUT_CLEANUP_MS,
    # Windows Modifiers
    MOD_ALT,
    MOD_CONTROL,
    MOD_SHIFT,
    MOD_WIN,
    SYSTEM_RESERVED_HOTKEYS,
    # Virtual Key Code Mappings
    VK_FUNCTION_KEYS,
    VK_LCONTROL,
    # Virtual Key Codes - Modifiers
    VK_LMENU,
    VK_LSHIFT,
    VK_LWIN,
    VK_RCONTROL,
    VK_RMENU,
    VK_RSHIFT,
    VK_RWIN,
    VK_SPECIAL_KEYS,
    WM_HOTKEY,
    # Windows Messages
    WM_KEYDOWN,
    WM_KEYUP,
    WM_NULL,
    WM_QUIT,
    WM_SYSKEYDOWN,
    WM_SYSKEYUP,
)

__all__ = [
    # Legacy constant classes
    "AppInfo",
    "Paths",
    "ConfigKeys",
    "Defaults",
    "Limits",
    "UI",
    "Audio",
    "AudioLegacy",
    "Whisper",
    "InputMethods",
    "Events",
    "ErrorMessages",
    "SuccessMessages",
    "Timing",
    "Patterns",
    "Versions",
    # Audio constants
    "SAMPLE_RATE_16KHZ",
    "SAMPLE_RATE_44KHZ",
    "SAMPLE_RATE_48KHZ",
    "CHUNK_SIZE_DEFAULT",
    "CHUNK_SIZE_LARGE",
    "CHUNK_SIZE_SMALL",
    "INT16_MAX",
    "INT16_MAX_INT",
    "INT32_MAX",
    "STREAMING_CHUNK_DURATION_DEFAULT",
    "STREAMING_CHUNK_DURATION_SHORT",
    "STREAMING_CHUNK_DURATION_LONG",
    "NORMALIZATION_TARGET_LEVEL",
    "NORMALIZATION_MAX_GAIN",
    "SILENCE_THRESHOLD_DEFAULT",
    "SILENCE_MIN_DURATION",
    "FRAME_LENGTH_MS",
    "HOP_LENGTH_MS",
    "AUDIO_LEVEL_LOW_THRESHOLD",
    "AUDIO_LEVEL_MED_THRESHOLD",
    "AUDIO_LEVEL_QUIET",
    "RESAMPLE_LARGE_AUDIO_THRESHOLD",
    "RESAMPLE_CHUNK_SIZE",
    "RESAMPLE_RATIO_TOLERANCE",
    "AUDIO_THREAD_JOIN_TIMEOUT",
    "AUDIO_THREAD_JOIN_TIMEOUT_LONG",
    "AUDIO_CLEANUP_TIMEOUT",
    # Hotkey constants
    "MOD_ALT",
    "MOD_CONTROL",
    "MOD_SHIFT",
    "MOD_WIN",
    "WM_KEYDOWN",
    "WM_KEYUP",
    "WM_SYSKEYDOWN",
    "WM_SYSKEYUP",
    "WM_HOTKEY",
    "WM_NULL",
    "WM_QUIT",
    "VK_LMENU",
    "VK_RMENU",
    "VK_LCONTROL",
    "VK_RCONTROL",
    "VK_LSHIFT",
    "VK_RSHIFT",
    "VK_LWIN",
    "VK_RWIN",
    "VK_FUNCTION_KEYS",
    "VK_SPECIAL_KEYS",
    "HOTKEY_TIME_WINDOW_MS",
    "HOTKEY_TIMEOUT_CLEANUP_MS",
    "HOTKEY_REGISTRATION_TIMEOUT",
    "ALLOWED_SINGLE_KEYS",
    "SYSTEM_RESERVED_HOTKEYS",
]
