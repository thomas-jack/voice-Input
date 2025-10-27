"""Groq API客户端"""

from ..utils.exceptions import GroqAPIError
from .base_client import BaseAIClient


class GroqClient(BaseAIClient):
    """Groq API 集成客户端

    使用 BaseAIClient 提供的通用功能，仅需实现提供商特定配置。
    """

    def get_base_url(self) -> str:
        """返回 Groq API 端点"""
        return "https://api.groq.com/openai/v1"

    def get_provider_name(self) -> str:
        """返回提供商名称"""
        return "Groq"

    def get_default_model(self) -> str:
        """返回默认模型

        Note: llama3-8b-8192 已被淘汰（2024年已下线）
        推荐使用 llama-3.3-70b-versatile 或其他当前可用模型
        参考: https://console.groq.com/docs/deprecations
        """
        return "llama-3.3-70b-versatile"

    def _create_api_error(self, message: str) -> Exception:
        """创建 Groq 特定的异常"""
        return GroqAPIError(message)
