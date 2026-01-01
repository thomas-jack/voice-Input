"""User-facing message constants."""


class ErrorMessages:
    """Error message strings."""

    CONFIG_LOAD_FAILED = "Failed to load configuration file"
    CONFIG_SAVE_FAILED = "Failed to save configuration file"
    CONFIG_INVALID_FORMAT = "Configuration file format is invalid"
    CONFIG_PERMISSION_DENIED = "Permission denied when accessing configuration file"

    AUDIO_DEVICE_NOT_FOUND = "Audio device not found"
    AUDIO_PERMISSION_DENIED = "Microphone permission denied"
    AUDIO_RECORDING_FAILED = "Audio recording failed"
    AUDIO_FORMAT_UNSUPPORTED = "Unsupported audio format"

    MODEL_LOAD_FAILED = "Failed to load Whisper model"
    MODEL_NOT_FOUND = "Whisper model not found"
    TRANSCRIPTION_FAILED = "Speech transcription failed"
    GPU_NOT_AVAILABLE = "GPU is not available for acceleration"

    NETWORK_CONNECTION_FAILED = "Network connection failed"
    API_KEY_INVALID = "API key is invalid"
    API_QUOTA_EXCEEDED = "API quota exceeded"
    API_REQUEST_TIMEOUT = "API request timeout"

    WINDOW_CREATE_FAILED = "Failed to create window"
    OVERLAY_POSITION_INVALID = "Invalid overlay position"
    TRAY_ICON_FAILED = "Failed to create system tray icon"

    INPUT_METHOD_FAILED = "Text input method failed"
    CLIPBOARD_ACCESS_DENIED = "Clipboard access denied"
    KEYBOARD_SIMULATION_FAILED = "Keyboard simulation failed"

    HOTKEY_REGISTER_FAILED = "Failed to register hotkey"
    HOTKEY_ALREADY_REGISTERED = "Hotkey is already registered by another application"
    HOTKEY_INVALID_FORMAT = "Invalid hotkey format"


class SuccessMessages:
    """Success message strings."""

    CONFIG_LOADED = "Configuration loaded successfully"
    CONFIG_SAVED = "Configuration saved successfully"
    AUDIO_DEVICE_CONNECTED = "Audio device connected successfully"
    MODEL_LOADED = "Whisper model loaded successfully"
    TRANSCRIPTION_COMPLETED = "Speech transcription completed"
    TEXT_INPUT_COMPLETED = "Text input completed successfully"
    HOTKEY_REGISTERED = "Hotkey registered successfully"
