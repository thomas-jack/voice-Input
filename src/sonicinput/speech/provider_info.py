"""Provider Information and Registry

Simple provider metadata system to replace the complex provider interface.
Provides basic information about each transcription provider.
"""

from typing import Dict, Any, Optional
from ..core.interfaces import ISpeechService


class ProviderInfo:
    """Simple provider information container

    Replaces the complex provider interface with basic metadata.
    """

    def __init__(
        self,
        provider_id: str,
        display_name: str,
        description: str,
        provider_type: str,  # "local" or "cloud"
        provider_class: type,
        supports_gpu: bool = False,
        supports_streaming: bool = False,
        supports_language_detection: bool = True,
        max_audio_duration: Optional[int] = None,
        supported_languages: Optional[list] = None,
        **metadata,
    ):
        """Initialize provider information

        Args:
            provider_id: Unique provider identifier
            display_name: Human-readable name
            description: Provider description
            provider_type: "local" or "cloud"
            provider_class: The service class
            supports_gpu: Whether provider supports GPU
            supports_streaming: Whether provider supports streaming
            supports_language_detection: Whether provider supports auto language detection
            max_audio_duration: Maximum audio duration in seconds (None = unlimited)
            supported_languages: List of supported language codes (None = all)
            **metadata: Additional provider-specific metadata
        """
        self.provider_id = provider_id
        self.display_name = display_name
        self.description = description
        self.provider_type = provider_type
        self.provider_class = provider_class
        self.supports_gpu = supports_gpu
        self.supports_streaming = supports_streaming
        self.supports_language_detection = supports_language_detection
        self.max_audio_duration = max_audio_duration
        self.supported_languages = supported_languages
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for UI display

        Returns:
            Provider information as dictionary
        """
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "description": self.description,
            "provider_type": self.provider_type,
            "supports_gpu": self.supports_gpu,
            "supports_streaming": self.supports_streaming,
            "supports_language_detection": self.supports_language_detection,
            "max_audio_duration": self.max_audio_duration,
            "supported_languages": self.supported_languages,
            **self.metadata,
        }

    def __repr__(self) -> str:
        return f"ProviderInfo(id={self.provider_id}, name={self.display_name}, type={self.provider_type})"


# Simple provider registry
PROVIDER_REGISTRY: Dict[str, ProviderInfo] = {}


def register_provider(provider_info: ProviderInfo) -> None:
    """Register a provider in the registry

    Args:
        provider_info: Provider information to register
    """
    PROVIDER_REGISTRY[provider_info.provider_id] = provider_info


def get_provider_info(provider_id: str) -> Optional[ProviderInfo]:
    """Get provider information by ID

    Args:
        provider_id: Provider identifier

    Returns:
        Provider information or None if not found
    """
    return PROVIDER_REGISTRY.get(provider_id)


def get_all_providers() -> Dict[str, ProviderInfo]:
    """Get all registered providers

    Returns:
        Dictionary of all providers
    """
    return PROVIDER_REGISTRY.copy()


def get_providers_by_type(provider_type: str) -> Dict[str, ProviderInfo]:
    """Get providers by type

    Args:
        provider_type: "local" or "cloud"

    Returns:
        Dictionary of providers of the specified type
    """
    return {
        pid: info
        for pid, info in PROVIDER_REGISTRY.items()
        if info.provider_type == provider_type
    }


def create_provider_instance(provider_id: str, **kwargs) -> Optional[ISpeechService]:
    """Create provider instance by ID

    Args:
        provider_id: Provider identifier
        **kwargs: Constructor arguments

    Returns:
        Provider instance or None if not found
    """
    provider_info = get_provider_info(provider_id)
    if not provider_info:
        return None

    try:
        return provider_info.provider_class(**kwargs)
    except Exception as e:
        from ..utils import app_logger

        app_logger.log_error(e, f"create_provider_instance_{provider_id}")
        return None


# Auto-register providers on import
def _auto_register_providers() -> None:
    """Auto-register all available providers"""
    try:
        # Local sherpa-onnx engine
        from .sherpa_engine import SherpaEngine

        register_provider(
            ProviderInfo(
                provider_id="local",
                display_name="Local Sherpa-ONNX",
                description="Lightweight CPU-only transcription with Paraformer/Zipformer models",
                provider_type="local",
                provider_class=SherpaEngine,
                supports_gpu=False,  # CPU-only
                supports_streaming=True,  # 支持真正的流式转录
                supports_language_detection=False,  # 模型预训练语言
                supported_languages=["zh", "en"],  # 中英双语
            )
        )
    except Exception as e:
        from ..utils import app_logger

        app_logger.log_error(e, "Failed to register Local Sherpa-ONNX")

    try:
        # Groq Cloud service
        from .groq_speech_service import GroqSpeechService

        register_provider(
            ProviderInfo(
                provider_id="groq",
                display_name="Groq Cloud",
                description="Fast cloud-based transcription with Whisper models",
                provider_type="cloud",
                provider_class=GroqSpeechService,
                supports_gpu=False,
                supports_streaming=False,
                supports_language_detection=True,
                supported_languages=None,  # All Whisper languages
            )
        )
    except Exception as e:
        from ..utils import app_logger

        app_logger.log_error(e, "Failed to register Groq")

    try:
        # SiliconFlow service
        from .siliconflow_engine import SiliconFlowEngine

        register_provider(
            ProviderInfo(
                provider_id="siliconflow",
                display_name="SiliconFlow",
                description="Ultra-low latency cloud transcription with Chinese dialect support",
                provider_type="cloud",
                provider_class=SiliconFlowEngine,
                supports_gpu=False,
                supports_streaming=False,
                supports_language_detection=True,
                supported_languages=["zh", "en", "ja", "ko", "yue", "wuu", "nan"],
                max_audio_duration=300,  # 5 minutes
            )
        )
    except Exception as e:
        from ..utils import app_logger

        app_logger.log_error(e, "Failed to register SiliconFlow")

    try:
        # Qwen ASR service
        from .qwen_engine import QwenEngine

        register_provider(
            ProviderInfo(
                provider_id="qwen",
                display_name="Qwen ASR",
                description="Alibaba Cloud Qwen ASR with emotion and language detection",
                provider_type="cloud",
                provider_class=QwenEngine,
                supports_gpu=False,
                supports_streaming=False,
                supports_language_detection=True,
                supported_languages=None,  # Multi-language support
                max_audio_duration=None,  # Check Qwen docs for limits
            )
        )
    except Exception as e:
        from ..utils import app_logger

        app_logger.log_error(e, "Failed to register Qwen ASR")

    from ..utils import app_logger

    app_logger.log_audio_event(
        "Provider auto-registration completed",
        {
            "total_providers": len(PROVIDER_REGISTRY),
            "provider_ids": list(PROVIDER_REGISTRY.keys()),
        },
    )


# Auto-register on module import
_auto_register_providers()
