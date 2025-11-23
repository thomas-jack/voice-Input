"""AI 客户端工厂

统一 AI 提供商的创建逻辑，支持动态切换和配置参数传递。
"""

from typing import Optional

from ..core.interfaces import IAIService, IConfigService
from ..core.services.config import ConfigKeys
from ..utils import app_logger


class AIClientFactory:
    """AI 客户端工厂类

    职责：
    - 根据配置创建不同的 AI 客户端
    - 统一参数传递（timeout, max_retries）
    - 延迟导入优化性能
    - 提供清晰的错误信息
    """

    @staticmethod
    def create_client(
        provider: str,
        api_key: str = "",
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        filter_thinking: bool = True,
    ) -> IAIService:
        """创建 AI 客户端实例

        Args:
            provider: 提供商名称 ("groq", "nvidia", "openai_compatible", "openrouter")
            api_key: API 密钥
            base_url: 基础 URL（仅 openai_compatible 需要）
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            filter_thinking: 是否过滤 AI 思考标签

        Returns:
            IAIService: AI 服务实例

        Raises:
            ValueError: 不支持的提供商
            ImportError: 客户端模块导入失败
        """
        provider_lower = provider.lower()

        try:
            if provider_lower == "groq":
                from .groq import GroqClient

                return GroqClient(api_key, timeout, max_retries, filter_thinking)

            elif provider_lower == "nvidia":
                from .nvidia import NvidiaClient

                return NvidiaClient(api_key, timeout, max_retries, filter_thinking)

            elif provider_lower == "openai_compatible":
                from .openai_compatible import OpenAICompatibleClient

                # openai_compatible 需要 base_url
                if base_url is None:
                    base_url = "http://localhost:1234/v1"
                return OpenAICompatibleClient(
                    api_key, base_url, timeout, max_retries, filter_thinking
                )

            elif provider_lower == "openrouter":
                from .openrouter import OpenRouterClient

                return OpenRouterClient(api_key, timeout, max_retries, filter_thinking)

            else:
                error_msg = f"Unsupported AI provider: {provider}"
                app_logger.log_audio_event(
                    "AI client creation failed",
                    {"provider": provider, "error": error_msg},
                )
                raise ValueError(error_msg)

        except ImportError as e:
            error_msg = f"Failed to import {provider} client: {str(e)}"
            app_logger.log_error(e, "AIClientFactory.create_client")
            raise ImportError(error_msg)

    @staticmethod
    def create_from_config(config: IConfigService) -> Optional[IAIService]:
        """从配置服务创建 AI 客户端

        Args:
            config: 配置服务实例

        Returns:
            IAIService: AI 服务实例，失败返回 None
        """
        try:
            # 读取通用配置
            provider = config.get_setting(ConfigKeys.AI_PROVIDER, "openrouter")
            timeout = config.get_setting(ConfigKeys.AI_TIMEOUT, 30)
            max_retries = config.get_setting(ConfigKeys.AI_RETRIES, 3)
            filter_thinking = config.get_setting(ConfigKeys.AI_FILTER_THINKING, True)

            # 读取提供商特定配置
            if provider == "groq":
                api_key = config.get_setting(ConfigKeys.AI_GROQ_API_KEY, "")
                return AIClientFactory.create_client(
                    provider, api_key, None, timeout, max_retries, filter_thinking
                )

            elif provider == "nvidia":
                api_key = config.get_setting(ConfigKeys.AI_NVIDIA_API_KEY, "")
                return AIClientFactory.create_client(
                    provider, api_key, None, timeout, max_retries, filter_thinking
                )

            elif provider == "openai_compatible":
                api_key = config.get_setting(
                    ConfigKeys.AI_OPENAI_COMPATIBLE_API_KEY, ""
                )
                base_url = config.get_setting(
                    ConfigKeys.AI_OPENAI_COMPATIBLE_BASE_URL, "http://localhost:1234/v1"
                )
                return AIClientFactory.create_client(
                    provider, api_key, base_url, timeout, max_retries, filter_thinking
                )

            else:  # openrouter (default)
                api_key = config.get_setting(ConfigKeys.AI_OPENROUTER_API_KEY, "")
                return AIClientFactory.create_client(
                    provider, api_key, None, timeout, max_retries, filter_thinking
                )

        except Exception as e:
            app_logger.log_error(e, "AIClientFactory.create_from_config")
            return None
