"""Default values for legacy flat configuration keys."""


class Defaults:
    """Default values used by legacy helpers and validators."""

    DEFAULT_HOTKEY = "ctrl+shift+v"

    DEFAULT_WHISPER_MODEL = "large-v3-turbo"
    DEFAULT_WHISPER_LANGUAGE = "auto"
    DEFAULT_WHISPER_TEMPERATURE = 0.0

    DEFAULT_SAMPLE_RATE = 16000
    DEFAULT_CHANNELS = 1
    DEFAULT_CHUNK_SIZE = 1024

    DEFAULT_OVERLAY_POSITION_MODE = "preset"
    DEFAULT_OVERLAY_POSITION_PRESET = "center"
    DEFAULT_THEME = "dark"

    DEFAULT_INPUT_METHOD = "clipboard"
    DEFAULT_CLIPBOARD_RESTORE_DELAY = 2.0
    DEFAULT_TYPING_DELAY = 0.01

    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3

    DEFAULT_GPU_MEMORY_FRACTION = 0.8
    DEFAULT_MAX_LOG_SIZE_MB = 10
    DEFAULT_KEEP_LOGS_DAYS = 7
