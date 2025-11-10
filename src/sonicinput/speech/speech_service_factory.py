"""Speech Service Factory

Unified speech service creation logic, supporting dynamic switching between providers.
"""

from typing import Optional
from ..core.interfaces import ISpeechService, IConfigService
from ..utils import app_logger


class SpeechServiceFactory:
    """Speech service factory class

    Responsibilities:
    - Create different speech services based on configuration
    - Unified parameter passing
    - Lazy import for performance optimization
    - Provide clear error messages
    """

    @staticmethod
    def _is_local_available() -> bool:
        """Check if local transcription (sherpa-onnx) is available

        Returns:
            bool: True if sherpa-onnx is installed, False otherwise
        """
        try:
            import importlib.util

            spec = importlib.util.find_spec("sherpa_onnx")
            return spec is not None
        except ImportError:
            return False

    @staticmethod
    def create_service(
        provider: str,
        api_key: str = "",
        model: str = "large-v3-turbo",
        use_gpu: Optional[bool] = None,
        base_url: Optional[str] = None,
        enable_itn: bool = True,
    ) -> ISpeechService:
        """Create speech service instance

        Args:
            provider: Provider name ("local", "groq", "siliconflow", "qwen")
            api_key: API key (for cloud providers)
            model: Model name
            use_gpu: Use GPU for local provider (None = auto-detect)
            base_url: Custom base URL for cloud providers (optional)
            enable_itn: Enable Inverse Text Normalization for Qwen (optional)

        Returns:
            ISpeechService: Speech service instance

        Raises:
            ValueError: Unsupported provider
            ImportError: Service module import failed
        """
        provider_lower = provider.lower()

        try:
            if provider_lower == "local":
                from .sherpa_engine import SherpaEngine

                # sherpa-onnx 不使用 use_gpu 参数，始终使用 CPU
                # model 参数应该是 sherpa 模型名称 (paraformer | zipformer-small)
                return SherpaEngine(model_name=model)

            elif provider_lower == "groq":
                from .groq_speech_service import GroqSpeechService

                if not api_key:
                    raise ValueError("Groq provider requires API key")
                return GroqSpeechService(
                    api_key=api_key, model=model, base_url=base_url
                )

            elif provider_lower == "siliconflow":
                from .siliconflow_engine import SiliconFlowEngine

                if not api_key:
                    raise ValueError("SiliconFlow provider requires API key")
                return SiliconFlowEngine(
                    api_key=api_key, model_name=model, base_url=base_url
                )

            elif provider_lower == "qwen":
                from .qwen_engine import QwenEngine

                if not api_key:
                    raise ValueError("Qwen provider requires API key")
                return QwenEngine(
                    api_key=api_key, model=model, base_url=base_url, enable_itn=enable_itn
                )

            else:
                error_msg = f"Unsupported speech provider: {provider}"
                app_logger.log_audio_event(
                    "Speech service creation failed",
                    {"provider": provider, "error": error_msg},
                )
                raise ValueError(error_msg)

        except ImportError as e:
            error_msg = f"Failed to import {provider} speech service: {str(e)}"
            app_logger.log_error(e, "SpeechServiceFactory.create_service")
            raise ImportError(error_msg)

    @staticmethod
    def create_from_config(config: IConfigService) -> Optional[ISpeechService]:
        """Create speech service from configuration

        Args:
            config: Configuration service instance

        Returns:
            ISpeechService: Speech service instance, None if failed
        """
        try:
            # Read transcription provider (with fallback to legacy whisper config)
            provider = config.get_setting("transcription.provider", "local")

            if provider == "local":
                # Read local (sherpa-onnx) configuration
                model = config.get_setting(
                    "transcription.local.model",
                    "paraformer",  # 默认使用 paraformer 模型
                )
                # sherpa-onnx 不需要 use_gpu 参数，始终使用 CPU
                return SpeechServiceFactory.create_service(
                    provider="local", model=model
                )

            elif provider == "groq":
                # Read Groq configuration
                api_key = config.get_setting("transcription.groq.api_key", "")
                model = config.get_setting(
                    "transcription.groq.model", "whisper-large-v3-turbo"
                )
                base_url = config.get_setting(
                    "transcription.groq.base_url", "https://api.groq.com/openai/v1"
                )

                if not api_key:
                    app_logger.log_audio_event(
                        "Groq provider selected but no API key configured", {}
                    )

                    # Only fallback to local if sherpa-onnx is available
                    if SpeechServiceFactory._is_local_available():
                        app_logger.log_audio_event("Falling back to local provider", {})
                        return SpeechServiceFactory.create_from_config_local_fallback(
                            config
                        )
                    else:
                        app_logger.log_audio_event(
                            "Cannot fallback: sherpa-onnx not installed",
                            {
                                "suggestion": "Install with: uv sync --extra local"
                            },
                        )
                        return None

                # Only pass base_url if it's not the default (to use SDK's default)
                if base_url == "https://api.groq.com/openai/v1":
                    return SpeechServiceFactory.create_service(
                        provider="groq", api_key=api_key, model=model, base_url=None
                    )
                else:
                    return SpeechServiceFactory.create_service(
                        provider="groq", api_key=api_key, model=model, base_url=base_url
                    )

            elif provider == "siliconflow":
                # Read SiliconFlow configuration
                api_key = config.get_setting("transcription.siliconflow.api_key", "")
                model = config.get_setting(
                    "transcription.siliconflow.model", "FunAudioLLM/SenseVoiceSmall"
                )
                base_url = config.get_setting(
                    "transcription.siliconflow.base_url",
                    "https://api.siliconflow.cn/v1",
                )

                if not api_key:
                    app_logger.log_audio_event(
                        "SiliconFlow provider selected but no API key configured",
                        {"suggestion": "Configure API key in settings"},
                    )
                    return None

                # Only pass base_url if it's not the default (to use engine's default)
                if base_url == "https://api.siliconflow.cn/v1":
                    return SpeechServiceFactory.create_service(
                        provider="siliconflow",
                        api_key=api_key,
                        model=model,
                        base_url=None,
                    )
                else:
                    return SpeechServiceFactory.create_service(
                        provider="siliconflow",
                        api_key=api_key,
                        model=model,
                        base_url=base_url,
                    )

            elif provider == "qwen":
                # Read Qwen configuration
                api_key = config.get_setting("transcription.qwen.api_key", "")
                model = config.get_setting(
                    "transcription.qwen.model", "qwen3-asr-flash"
                )
                base_url = config.get_setting(
                    "transcription.qwen.base_url",
                    "https://dashscope.aliyuncs.com",
                )
                enable_itn = config.get_setting(
                    "transcription.qwen.enable_itn", True
                )

                if not api_key:
                    app_logger.log_audio_event(
                        "Qwen provider selected but no API key configured",
                        {"suggestion": "Configure DashScope API key in settings"},
                    )
                    return None

                # Only pass base_url if it's not the default (to use engine's default)
                if base_url == "https://dashscope.aliyuncs.com":
                    return SpeechServiceFactory.create_service(
                        provider="qwen",
                        api_key=api_key,
                        model=model,
                        base_url=None,
                        enable_itn=enable_itn,
                    )
                else:
                    return SpeechServiceFactory.create_service(
                        provider="qwen",
                        api_key=api_key,
                        model=model,
                        base_url=base_url,
                        enable_itn=enable_itn,
                    )

            else:
                app_logger.log_audio_event("Unknown provider", {"provider": provider})

                # Only fallback to local if sherpa-onnx is available
                if SpeechServiceFactory._is_local_available():
                    app_logger.log_audio_event("Falling back to local provider", {})
                    return SpeechServiceFactory.create_from_config_local_fallback(
                        config
                    )
                else:
                    app_logger.log_audio_event(
                        "Cannot fallback: sherpa-onnx not installed",
                        {
                            "suggestion": "Install with: uv sync --extra local"
                        },
                    )
                    return None

        except Exception as e:
            app_logger.log_error(e, "SpeechServiceFactory.create_from_config")

            # Only try to fallback to local if sherpa-onnx is available
            if SpeechServiceFactory._is_local_available():
                try:
                    app_logger.log_audio_event(
                        "Attempting fallback to local provider", {}
                    )
                    return SpeechServiceFactory.create_from_config_local_fallback(
                        config
                    )
                except Exception as fallback_error:
                    app_logger.log_error(
                        fallback_error, "SpeechServiceFactory.fallback"
                    )
                    return None
            else:
                app_logger.log_audio_event(
                    "Cannot fallback: sherpa-onnx not installed",
                    {
                        "original_error": str(e),
                        "suggestion": "Install with: uv sync --extra local",
                    },
                )
                return None

    @staticmethod
    def create_from_config_local_fallback(config: IConfigService) -> ISpeechService:
        """Create local speech service as fallback

        Args:
            config: Configuration service instance

        Returns:
            ISpeechService: Local speech service instance
        """
        model = config.get_setting(
            "transcription.local.model",
            "paraformer",  # 默认使用 paraformer 模型
        )
        # sherpa-onnx 不需要 use_gpu 参数
        return SpeechServiceFactory.create_service(
            provider="local", model=model
        )
