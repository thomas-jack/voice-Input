"""AI服务接口定义"""

from abc import ABC, abstractmethod


class IAIService(ABC):
    """AI服务接口

    提供文本优化和AI处理功能。
    """

    @abstractmethod
    def refine_text(self, text: str, prompt_template: str, model: str) -> str:
        """优化文本

        Args:
            text: 要优化的文本
            prompt_template: 提示模板
            model: 使用的AI模型

        Returns:
            优化后的文本

        Raises:
            AIServiceError: AI服务调用失败时
        """
        pass

    @abstractmethod
    def set_api_key(self, api_key: str) -> None:
        """设置API密钥

        Args:
            api_key: API密钥
        """
        pass

    # 移除的方法（不必需）：
    # - get_available_models: 在实际使用中不需要获取模型列表
    # - validate_api_key: API密钥验证可在内部处理
    # - get_model_info: 模型信息在实际使用中不需要
    # - test_connection: 连接测试可在内部处理
    # - api_key_configured: 可通过其他方式检查
    # - service_status: 状态信息可在异常中提供