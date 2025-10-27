"""文本输入服务接口定义"""

from abc import ABC, abstractmethod


class IInputService(ABC):
    """文本输入服务接口

    提供多种方式的文本输入功能。
    """

    @abstractmethod
    def input_text(self, text: str) -> bool:
        """输入文本到当前活跃窗口

        Args:
            text: 要输入的文本

        Returns:
            是否成功输入
        """
        pass

    @abstractmethod
    def set_preferred_method(self, method: str) -> None:
        """设置首选输入方法

        Args:
            method: 输入方法名称 ('clipboard', 'sendinput', 'smart')
        """
        pass

    # 移除的方法（不必需）：
    # - get_available_methods: 输入方法列表在实际使用中不需要
    # - test_input_method: 输入方法测试可在内部处理
    # - get_method_info: 输入方法信息在实际使用中不需要
    # - current_method: 当前方法信息可在内部跟踪
    # - is_ready: 就绪状态可在异常中体现