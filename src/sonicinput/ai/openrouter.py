"""OpenRouter API客户端"""

from typing import Any, Dict, List

from ..utils import OpenRouterAPIError
from .base_client import BaseAIClient


class OpenRouterClient(BaseAIClient):
    """OpenRouter API 集成客户端

    使用 BaseAIClient 提供的通用功能，添加以下 OpenRouter 特有功能：
    - 自定义请求头（HTTP-Referer, X-Title）
    - 获取可用模型列表
    - 获取使用统计
    - 估算 API 调用成本
    """

    def get_base_url(self) -> str:
        """返回 OpenRouter API 端点"""
        return "https://openrouter.ai/api/v1"

    def get_provider_name(self) -> str:
        """返回提供商名称"""
        return "OpenRouter"

    def get_default_model(self) -> str:
        """返回默认模型"""
        return "anthropic/claude-3-sonnet"

    def _create_api_error(self, message: str) -> Exception:
        """创建 OpenRouter 特定的异常"""
        return OpenRouterAPIError(message)

    def get_extra_headers(self) -> Dict[str, str]:
        """返回 OpenRouter 特定的请求头"""
        return {
            "HTTP-Referer": "https://github.com/user/sonic-input",
            "X-Title": "Sonic Input",
        }

    # ========== OpenRouter 独特功能 ==========

    def get_available_models(self) -> List[Dict[str, Any]]:
        """获取可用模型列表

        Returns:
            适合文本优化的模型列表，包含模型 ID、名称、描述、定价等信息
        """
        try:
            response = self.session.get(
                f"{self.get_base_url()}/models", timeout=self.timeout
            )

            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get("data", [])

                # 过滤适合文本优化的模型
                suitable_models = []
                for model in models:
                    model_id = model.get("id", "")
                    # 选择常用的高质量模型
                    if any(
                        provider in model_id.lower()
                        for provider in [
                            "anthropic",
                            "openai",
                            "google",
                            "meta-llama",
                            "mistralai",
                        ]
                    ):
                        suitable_models.append(
                            {
                                "id": model_id,
                                "name": model.get("name", model_id),
                                "description": model.get("description", ""),
                                "pricing": model.get("pricing", {}),
                                "context_length": model.get("context_length", 0),
                            }
                        )

                from ..utils import app_logger

                app_logger.log_api_call("OpenRouter", 0, True)
                return suitable_models
            else:
                from ..utils import app_logger

                app_logger.log_api_call("OpenRouter", 0, False, response.text)
                return []

        except Exception as e:
            from ..utils import app_logger

            app_logger.log_error(e, "get_available_models")
            return []

    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计（如果API支持）

        Returns:
            使用统计信息字典，如果获取失败则返回空字典
        """
        try:
            response = self.session.get(
                f"{self.get_base_url()}/auth/key", timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {}

        except Exception as e:
            from ..utils import app_logger

            app_logger.log_error(e, "get_usage_stats")
            return {}

    def estimate_cost(self, text: str, model: str) -> Dict[str, float]:
        """估算 API 调用成本

        Args:
            text: 要处理的文本
            model: 模型 ID

        Returns:
            包含成本估算的字典
        """
        # 简单的token估算（约4个字符=1个token）
        estimated_tokens = len(text) // 4 + 100  # 加上提示词的tokens

        # 模型价格映射（每1M tokens的美元价格）
        model_pricing = {
            "anthropic/claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "anthropic/claude-3-haiku": {"input": 0.25, "output": 1.25},
            "openai/gpt-4o": {"input": 5.0, "output": 15.0},
            "openai/gpt-4o-mini": {"input": 0.15, "output": 0.6},
            "openai/gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
            "google/gemini-pro": {"input": 0.5, "output": 1.5},
            "mistralai/mistral-7b-instruct": {"input": 0.25, "output": 0.25},
        }

        pricing = model_pricing.get(model, {"input": 1.0, "output": 2.0})

        input_cost = (estimated_tokens / 1000000) * pricing["input"]
        output_cost = (estimated_tokens / 1000000) * pricing[
            "output"
        ]  # 假设输出长度相似

        return {
            "estimated_input_tokens": estimated_tokens,
            "estimated_output_tokens": estimated_tokens,
            "input_cost_usd": input_cost,
            "output_cost_usd": output_cost,
            "total_cost_usd": input_cost + output_cost,
        }
