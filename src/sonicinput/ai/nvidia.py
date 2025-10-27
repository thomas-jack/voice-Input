"""NVIDIA API客户端"""

from ..utils.exceptions import NVIDIAAPIError
from .base_client import BaseAIClient


class NvidiaClient(BaseAIClient):
    """NVIDIA API 集成客户端 (NIM - NVIDIA Inference Microservices)

    使用 BaseAIClient 提供的通用功能，仅需实现提供商特定配置。
    """

    def get_base_url(self) -> str:
        """返回 NVIDIA API 端点"""
        return "https://integrate.api.nvidia.com/v1"

    def get_provider_name(self) -> str:
        """返回提供商名称"""
        return "NVIDIA"

    def get_default_model(self) -> str:
        """返回默认模型"""
        return "meta/llama-3.1-8b-instruct"

    def _create_api_error(self, message: str) -> Exception:
        """创建 NVIDIA 特定的异常"""
        return NVIDIAAPIError(message)
