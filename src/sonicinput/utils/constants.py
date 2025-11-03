"""应用程序常量定义

统一管理所有魔法数字、字符串常量和配置项键名。
消除代码中的硬编码值，提高代码可维护性。
"""


# ==================== 应用程序信息 ====================
class AppInfo:
    """应用程序基本信息"""

    NAME = "Voice Input Software"
    VERSION = "1.0.0"
    DESCRIPTION = "AI-powered voice input software with speech recognition"
    AUTHOR = "Voice Input Team"
    COPYRIGHT = "© 2024 Voice Input Software"


# ==================== 文件路径 ====================
class Paths:
    """文件路径常量"""

    # 配置文件
    CONFIG_DIR_NAME = "SonicInput"
    CONFIG_FILE_NAME = "config.json"
    LOG_FILE_NAME = "app.log"

    # 备份目录
    BACKUP_DIR_NAME = "backups"

    # 临时文件
    TEMP_AUDIO_PREFIX = "voice_input_"
    TEMP_AUDIO_SUFFIX = ".wav"

    # 资源文件
    ICON_DIR = "resources/icons"
    THEMES_DIR = "resources/themes"
    MODELS_DIR = "models"


# ==================== 配置项键名 ====================
class ConfigKeys:
    """配置项键名常量"""

    # 顶层配置
    HOTKEY = "hotkey"

    # Whisper 配置
    WHISPER_MODEL = "whisper.model"
    WHISPER_LANGUAGE = "whisper.language"
    WHISPER_USE_GPU = "whisper.use_gpu"
    WHISPER_AUTO_LOAD = "whisper.auto_load"
    WHISPER_TEMPERATURE = "whisper.temperature"
    WHISPER_DEVICE = "whisper.device"
    WHISPER_COMPUTE_TYPE = "whisper.compute_type"

    # OpenRouter 配置
    OPENROUTER_API_KEY = "openrouter.api_key"
    OPENROUTER_MODEL = "openrouter.model"
    OPENROUTER_SIMPLE_MODEL_ID = "openrouter.simple_model_id"
    OPENROUTER_SIMPLE_PROMPT = "openrouter.simple_prompt"
    OPENROUTER_ENABLED = "openrouter.enabled"
    OPENROUTER_TIMEOUT = "openrouter.timeout"
    OPENROUTER_MAX_RETRIES = "openrouter.max_retries"

    # 音频配置
    AUDIO_SAMPLE_RATE = "audio.sample_rate"
    AUDIO_CHANNELS = "audio.channels"
    AUDIO_DEVICE_ID = "audio.device_id"
    AUDIO_CHUNK_SIZE = "audio.chunk_size"

    # UI 配置
    UI_SHOW_OVERLAY = "ui.show_overlay"
    UI_OVERLAY_POSITION_MODE = "ui.overlay_position.mode"
    UI_OVERLAY_POSITION_PRESET = "ui.overlay_position.preset"
    UI_OVERLAY_POSITION_CUSTOM_X = "ui.overlay_position.custom.x"
    UI_OVERLAY_POSITION_CUSTOM_Y = "ui.overlay_position.custom.y"
    UI_OVERLAY_POSITION_AUTO_SAVE = "ui.overlay_position.auto_save"
    UI_OVERLAY_ALWAYS_ON_TOP = "ui.overlay_always_on_top"
    UI_TRAY_NOTIFICATIONS = "ui.tray_notifications"
    UI_START_MINIMIZED = "ui.start_minimized"
    UI_AUTO_START = "ui.auto_start"
    UI_THEME = "ui.theme"

    # 输入配置
    INPUT_PREFERRED_METHOD = "input.preferred_method"
    INPUT_FALLBACK_ENABLED = "input.fallback_enabled"
    INPUT_AUTO_DETECT_TERMINAL = "input.auto_detect_terminal"
    INPUT_CLIPBOARD_RESTORE_DELAY = "input.clipboard_restore_delay"
    INPUT_TYPING_DELAY = "input.typing_delay"

    # 日志配置
    LOGGING_LEVEL = "logging.level"
    LOGGING_CONSOLE_OUTPUT = "logging.console_output"
    LOGGING_MAX_LOG_SIZE_MB = "logging.max_log_size_mb"
    LOGGING_KEEP_LOGS_DAYS = "logging.keep_logs_days"

    # 新增UI配置键
    NOTIFICATIONS_ENABLED = "ui.notifications_enabled"
    AUTO_START = "ui.auto_start"
    LOG_LEVEL = "logging.level"
    RECORDING_TIMEOUT = "recording.timeout"
    AUDIO_INPUT_DEVICE = "audio.input_device"
    NOISE_REDUCTION_ENABLED = "audio.noise_reduction_enabled"
    VOLUME_THRESHOLD = "audio.volume_threshold"
    SPEECH_LANGUAGE = "speech.language"
    HOTKEYS_ENABLED = "hotkeys.enabled"
    RECORDING_HOTKEY = "hotkeys.recording"
    TEXT_OPTIMIZATION_ENABLED = "text.optimization_enabled"
    OVERLAY_ENABLED = "ui.overlay.enabled"
    OVERLAY_POSITION = "ui.overlay.position"
    OVERLAY_OPACITY = "ui.overlay.opacity"
    ADVANCED_AUDIO_NORMALIZE = "advanced.audio_processing.normalize_audio"
    ADVANCED_AUDIO_REMOVE_SILENCE = "advanced.audio_processing.remove_silence"
    ADVANCED_AUDIO_NOISE_REDUCTION = "advanced.audio_processing.noise_reduction"
    ADVANCED_PERFORMANCE_PRELOAD_MODEL = "advanced.performance.preload_model"
    ADVANCED_PERFORMANCE_CACHE_AUDIO = "advanced.performance.cache_audio"
    ADVANCED_PERFORMANCE_PARALLEL_PROCESSING = (
        "advanced.performance.parallel_processing"
    )


# ==================== 默认值 ====================
class Defaults:
    """默认值常量"""

    # 应用程序默认值
    DEFAULT_HOTKEY = "ctrl+shift+v"

    # Whisper 默认值
    DEFAULT_WHISPER_MODEL = "large-v3-turbo"
    DEFAULT_WHISPER_LANGUAGE = "auto"
    DEFAULT_WHISPER_TEMPERATURE = 0.0

    # 音频默认值
    DEFAULT_SAMPLE_RATE = 16000
    DEFAULT_CHANNELS = 1
    DEFAULT_CHUNK_SIZE = 1024

    # UI 默认值
    DEFAULT_OVERLAY_POSITION_MODE = "preset"
    DEFAULT_OVERLAY_POSITION_PRESET = "center"
    DEFAULT_THEME = "dark"

    # 输入默认值
    DEFAULT_INPUT_METHOD = "clipboard"
    DEFAULT_CLIPBOARD_RESTORE_DELAY = 2.0
    DEFAULT_TYPING_DELAY = 0.01

    # 网络默认值
    DEFAULT_TIMEOUT = 30
    DEFAULT_MAX_RETRIES = 3

    # 性能默认值
    DEFAULT_GPU_MEMORY_FRACTION = 0.8
    DEFAULT_MAX_LOG_SIZE_MB = 10
    DEFAULT_KEEP_LOGS_DAYS = 7


# ==================== 限制值 ====================
class Limits:
    """限制值常量"""

    # 音频限制
    MIN_SAMPLE_RATE = 8000
    MAX_SAMPLE_RATE = 48000
    MIN_CHUNK_SIZE = 256
    MAX_CHUNK_SIZE = 8192

    # 网络限制
    MIN_TIMEOUT = 5
    MAX_TIMEOUT = 120
    MIN_RETRIES = 1
    MAX_RETRIES = 10

    # UI 限制
    MIN_WINDOW_WIDTH = 300
    MIN_WINDOW_HEIGHT = 200
    MAX_OVERLAY_SIZE = 1000

    # 文本限制
    MAX_TRANSCRIPTION_LENGTH = 10000
    MAX_ERROR_MESSAGE_LENGTH = 500

    # 性能限制
    MIN_GPU_MEMORY_FRACTION = 0.1
    MAX_GPU_MEMORY_FRACTION = 1.0
    MAX_HISTORY_ENTRIES = 1000
    MAX_LOG_SIZE_MB = 100


# ==================== UI 相关常量 ====================
class UI:
    """UI 相关常量"""

    # 窗口尺寸
    OVERLAY_WIDTH = 400
    OVERLAY_HEIGHT = 100
    MAIN_WINDOW_WIDTH = 800
    MAIN_WINDOW_HEIGHT = 600
    SETTINGS_WINDOW_WIDTH = 600
    SETTINGS_WINDOW_HEIGHT = 500

    # 位置预设
    POSITION_PRESETS = {
        "top_left": (50, 50),
        "top_center": (0, 50),  # 0 表示水平居中
        "top_right": (-50, 50),  # 负数表示从右边计算
        "center_left": (50, 0),  # 0 表示垂直居中
        "center": (0, 0),  # 完全居中
        "center_right": (-50, 0),
        "bottom_left": (50, -50),  # 负数表示从底部计算
        "bottom_center": (0, -50),
        "bottom_right": (-50, -50),
    }

    # 动画时长（毫秒）
    FADE_DURATION = 300
    SLIDE_DURATION = 250
    BOUNCE_DURATION = 400

    # 颜色主题
    COLORS = {
        "primary": "#007ACC",
        "secondary": "#005A9E",
        "success": "#28A745",
        "warning": "#FFC107",
        "error": "#DC3545",
        "info": "#17A2B8",
        "light": "#F8F9FA",
        "dark": "#343A40",
    }

    # 状态颜色
    STATUS_COLORS = {
        "idle": "#6C757D",
        "recording": "#FF4444",
        "processing": "#FFC107",
        "completed": "#28A745",
        "error": "#DC3545",
    }


# ==================== 音频相关常量 ====================
class Audio:
    """音频相关常量"""

    # 采样率选项
    SAMPLE_RATES = [8000, 16000, 22050, 44100, 48000]

    # 音频格式
    SUPPORTED_FORMATS = [".wav", ".mp3", ".m4a", ".flac", ".ogg"]

    # 录音限制
    MIN_RECORDING_DURATION = 0.5  # 秒
    MAX_RECORDING_DURATION = 300  # 秒

    # 音频处理
    SILENCE_THRESHOLD = 0.01
    NOISE_GATE_THRESHOLD = 0.005

    # 可视化
    WAVEFORM_SAMPLES = 100
    WAVEFORM_UPDATE_INTERVAL = 50  # 毫秒


# ==================== Whisper 相关常量 ====================
class Whisper:
    """Whisper 相关常量"""

    # 可用模型
    AVAILABLE_MODELS = [
        "tiny",
        "base",
        "small",
        "medium",
        "large-v3",
        "large-v3-turbo",
        "turbo",
    ]

    # 语言代码
    LANGUAGE_CODES = {
        "auto": "Automatic Detection",
        "en": "English",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ar": "Arabic",
    }

    # 计算类型
    COMPUTE_TYPES = ["int8", "int8_float16", "int16", "float16", "float32"]

    # 设备类型
    DEVICE_TYPES = ["auto", "cpu", "cuda"]


# ==================== 输入方法常量 ====================
class InputMethods:
    """输入方法常量"""

    # 可用方法
    CLIPBOARD = "clipboard"
    SENDINPUT = "sendinput"
    SMART = "smart"

    AVAILABLE_METHODS = [CLIPBOARD, SENDINPUT, SMART]

    # 方法描述
    METHOD_DESCRIPTIONS = {
        CLIPBOARD: "Clipboard-based input (most compatible)",
        SENDINPUT: "Direct input simulation (faster)",
        SMART: "Smart method selection (recommended)",
    }


# ==================== 事件名称常量 ====================
class Events:
    """事件名称常量 - 与 event_bus.py 中的 Events 类保持一致"""

    # 录音相关事件
    RECORDING_STARTED = "recording_started"
    RECORDING_STOPPED = "recording_stopped"
    RECORDING_ERROR = "recording_error"
    AUDIO_LEVEL_UPDATE = "audio_level_update"

    # 转录相关事件
    TRANSCRIPTION_STARTED = "transcription_started"
    TRANSCRIPTION_COMPLETED = "transcription_completed"
    TRANSCRIPTION_ERROR = "transcription_error"

    # AI优化相关事件
    AI_PROCESSING_STARTED = "ai_processing_started"
    AI_PROCESSING_COMPLETED = "ai_processing_completed"
    AI_PROCESSING_ERROR = "ai_processing_error"

    # 文本输入相关事件
    TEXT_INPUT_STARTED = "text_input_started"
    TEXT_INPUT_COMPLETED = "text_input_completed"
    TEXT_INPUT_ERROR = "text_input_error"

    # 快捷键相关事件
    HOTKEY_TRIGGERED = "hotkey_triggered"
    HOTKEY_REGISTERED = "hotkey_registered"
    HOTKEY_UNREGISTERED = "hotkey_unregistered"

    # 配置相关事件
    CONFIG_CHANGED = "config_changed"
    CONFIG_LOADED = "config_loaded"
    CONFIG_SAVED = "config_saved"
    CONFIG_RESET = "config_reset"
    CONFIG_IMPORTED = "config_imported"

    # UI相关事件
    WINDOW_SHOWN = "window_shown"
    WINDOW_HIDDEN = "window_hidden"
    TRAY_CLICKED = "tray_clicked"
    OVERLAY_POSITION_CHANGED = "overlay_position_changed"

    # 应用程序生命周期事件
    APP_STARTED = "app_started"
    APP_STOPPING = "app_stopping"
    APP_ERROR = "app_error"

    # 组件生命周期事件
    COMPONENT_REGISTERED = "component_registered"
    COMPONENT_UNREGISTERED = "component_unregistered"
    COMPONENT_INITIALIZED = "component_initialized"
    COMPONENT_STARTED = "component_started"
    COMPONENT_STOPPED = "component_stopped"
    COMPONENT_ERROR = "component_error"
    COMPONENT_STATE_CHANGED = "component_state_changed"

    # 模型相关事件
    MODEL_LOADING_STARTED = "model_loading_started"
    MODEL_LOADING_COMPLETED = "model_loading_completed"
    MODEL_LOADING_ERROR = "model_loading_error"
    MODEL_UNLOADED = "model_unloaded"

    # 状态变更事件
    STATE_CHANGED = "state_changed"
    APP_STATE_CHANGED = "app_state_changed"
    RECORDING_STATE_CHANGED = "recording_state_changed"

    # 网络相关事件
    NETWORK_ERROR = "network_error"
    API_RATE_LIMITED = "api_rate_limited"

    # GPU相关事件
    GPU_STATUS_CHANGED = "gpu_status_changed"
    GPU_MEMORY_WARNING = "gpu_memory_warning"


# ==================== 错误消息常量 ====================
class ErrorMessages:
    """错误消息常量"""

    # 配置错误
    CONFIG_LOAD_FAILED = "Failed to load configuration file"
    CONFIG_SAVE_FAILED = "Failed to save configuration file"
    CONFIG_INVALID_FORMAT = "Configuration file format is invalid"
    CONFIG_PERMISSION_DENIED = "Permission denied when accessing configuration file"

    # 音频错误
    AUDIO_DEVICE_NOT_FOUND = "Audio device not found"
    AUDIO_PERMISSION_DENIED = "Microphone permission denied"
    AUDIO_RECORDING_FAILED = "Audio recording failed"
    AUDIO_FORMAT_UNSUPPORTED = "Unsupported audio format"

    # Whisper错误
    MODEL_LOAD_FAILED = "Failed to load Whisper model"
    MODEL_NOT_FOUND = "Whisper model not found"
    TRANSCRIPTION_FAILED = "Speech transcription failed"
    GPU_NOT_AVAILABLE = "GPU is not available for acceleration"

    # 网络错误
    NETWORK_CONNECTION_FAILED = "Network connection failed"
    API_KEY_INVALID = "API key is invalid"
    API_QUOTA_EXCEEDED = "API quota exceeded"
    API_REQUEST_TIMEOUT = "API request timeout"

    # UI错误
    WINDOW_CREATE_FAILED = "Failed to create window"
    OVERLAY_POSITION_INVALID = "Invalid overlay position"
    TRAY_ICON_FAILED = "Failed to create system tray icon"

    # 输入错误
    INPUT_METHOD_FAILED = "Text input method failed"
    CLIPBOARD_ACCESS_DENIED = "Clipboard access denied"
    KEYBOARD_SIMULATION_FAILED = "Keyboard simulation failed"

    # 热键错误
    HOTKEY_REGISTER_FAILED = "Failed to register hotkey"
    HOTKEY_ALREADY_REGISTERED = "Hotkey is already registered by another application"
    HOTKEY_INVALID_FORMAT = "Invalid hotkey format"


# ==================== 成功消息常量 ====================
class SuccessMessages:
    """成功消息常量"""

    CONFIG_LOADED = "Configuration loaded successfully"
    CONFIG_SAVED = "Configuration saved successfully"
    AUDIO_DEVICE_CONNECTED = "Audio device connected successfully"
    MODEL_LOADED = "Whisper model loaded successfully"
    TRANSCRIPTION_COMPLETED = "Speech transcription completed"
    TEXT_INPUT_COMPLETED = "Text input completed successfully"
    HOTKEY_REGISTERED = "Hotkey registered successfully"


# ==================== 时间常量 ====================
class Timing:
    """时间相关常量（毫秒）"""

    # UI 更新间隔
    UI_UPDATE_INTERVAL = 50
    AUDIO_LEVEL_UPDATE_INTERVAL = 100
    STATUS_UPDATE_INTERVAL = 200

    # 超时设置
    MODEL_LOAD_TIMEOUT = 30000  # 30秒
    TRANSCRIPTION_TIMEOUT = 120000  # 2分钟
    API_REQUEST_TIMEOUT = 30000  # 30秒

    # 延迟设置
    STARTUP_DELAY = 1000  # 1秒
    SHUTDOWN_DELAY = 2000  # 2秒
    OVERLAY_HIDE_DELAY = 3000  # 3秒

    # 重试间隔
    RETRY_DELAY = 1000  # 1秒
    EXPONENTIAL_BACKOFF_BASE = 2


# ==================== 正则表达式常量 ====================
class Patterns:
    """正则表达式模式常量"""

    # 热键格式验证
    HOTKEY_PATTERN = r"^(ctrl\+)?(shift\+)?(alt\+)?\w+$"

    # API密钥格式
    OPENROUTER_API_KEY_PATTERN = r"^sk-[a-zA-Z0-9]{32,}$"

    # 文件名验证
    SAFE_FILENAME_PATTERN = r"^[a-zA-Z0-9_\-\.]+$"

    # 语言代码验证
    LANGUAGE_CODE_PATTERN = r"^[a-z]{2}(-[A-Z]{2})?$"


# ==================== 版本相关常量 ====================
class Versions:
    """版本相关常量"""

    CONFIG_VERSION = "1.0"
    MIN_WHISPER_VERSION = "20231117"  # 最小Whisper版本
    MIN_PYTHON_VERSION = (3, 8)  # 最小Python版本
    MIN_PYTORCH_VERSION = "2.0.0"  # 最小PyTorch版本
