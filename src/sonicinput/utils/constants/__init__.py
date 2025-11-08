"""Constants module for SonicInput

Centralizes magic numbers and configuration values used throughout the codebase.
"""

# Import existing constants from parent module
import sys
from pathlib import Path

# Add parent utils directory to path to import constants.py
parent_utils = Path(__file__).parent.parent
if str(parent_utils) not in sys.path:
    sys.path.insert(0, str(parent_utils))

# Import all classes from the original constants.py
try:
    from constants import (
        AppInfo,
        Paths,
        ConfigKeys,
        Defaults,
        Limits,
        UI,
        Audio as AudioLegacy,
        Whisper,
        InputMethods,
        Events,
        ErrorMessages,
        SuccessMessages,
        Timing,
        Patterns,
        Versions,
    )
except ImportError:
    # Fallback if direct import fails
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "constants_legacy",
        parent_utils / "constants.py"
    )
    constants_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(constants_module)

    AppInfo = constants_module.AppInfo
    Paths = constants_module.Paths
    ConfigKeys = constants_module.ConfigKeys
    Defaults = constants_module.Defaults
    Limits = constants_module.Limits
    UI = constants_module.UI
    AudioLegacy = constants_module.Audio
    Whisper = constants_module.Whisper
    InputMethods = constants_module.InputMethods
    Events = constants_module.Events
    ErrorMessages = constants_module.ErrorMessages
    SuccessMessages = constants_module.SuccessMessages
    Timing = constants_module.Timing
    Patterns = constants_module.Patterns
    Versions = constants_module.Versions

from .audio import (
    # Sample Rates
    SAMPLE_RATE_16KHZ,
    SAMPLE_RATE_44KHZ,
    SAMPLE_RATE_48KHZ,
    # Chunk Sizes
    CHUNK_SIZE_DEFAULT,
    CHUNK_SIZE_LARGE,
    CHUNK_SIZE_SMALL,
    # Audio Conversion
    INT16_MAX,
    INT16_MAX_INT,
    INT32_MAX,
    # Streaming
    STREAMING_CHUNK_DURATION_DEFAULT,
    STREAMING_CHUNK_DURATION_SHORT,
    STREAMING_CHUNK_DURATION_LONG,
    # Audio Processing
    NORMALIZATION_TARGET_LEVEL,
    NORMALIZATION_MAX_GAIN,
    SILENCE_THRESHOLD_DEFAULT,
    SILENCE_MIN_DURATION,
    FRAME_LENGTH_MS,
    HOP_LENGTH_MS,
    # Audio Levels
    AUDIO_LEVEL_LOW_THRESHOLD,
    AUDIO_LEVEL_MED_THRESHOLD,
    AUDIO_LEVEL_QUIET,
    # Resampling
    RESAMPLE_LARGE_AUDIO_THRESHOLD,
    RESAMPLE_CHUNK_SIZE,
    RESAMPLE_RATIO_TOLERANCE,
    # Timeouts
    AUDIO_THREAD_JOIN_TIMEOUT,
    AUDIO_THREAD_JOIN_TIMEOUT_LONG,
    AUDIO_CLEANUP_TIMEOUT,
)

from .hotkeys import (
    # Windows Modifiers
    MOD_ALT,
    MOD_CONTROL,
    MOD_SHIFT,
    MOD_WIN,
    # Windows Messages
    WM_KEYDOWN,
    WM_KEYUP,
    WM_SYSKEYDOWN,
    WM_SYSKEYUP,
    WM_HOTKEY,
    WM_NULL,
    WM_QUIT,
    # Virtual Key Codes - Modifiers
    VK_LMENU,
    VK_RMENU,
    VK_LCONTROL,
    VK_RCONTROL,
    VK_LSHIFT,
    VK_RSHIFT,
    VK_LWIN,
    VK_RWIN,
    # Virtual Key Code Mappings
    VK_FUNCTION_KEYS,
    VK_SPECIAL_KEYS,
    # Timing Constants
    HOTKEY_TIME_WINDOW_MS,
    HOTKEY_TIMEOUT_CLEANUP_MS,
    HOTKEY_REGISTRATION_TIMEOUT,
    # Configuration
    ALLOWED_SINGLE_KEYS,
    SYSTEM_RESERVED_HOTKEYS,
)

__all__ = [
    # Legacy constant classes
    "AppInfo",
    "Paths",
    "ConfigKeys",
    "Defaults",
    "Limits",
    "UI",
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
