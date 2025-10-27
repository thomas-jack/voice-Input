"""Mock 文本输入服务"""
from sonicinput.core.interfaces import IInputService


class MockInputService(IInputService):
    def __init__(self):
        self.last_text = None
        self.input_count = 0

    def input_text(self, text):
        self.last_text = text
        self.input_count += 1
        return True

    def set_preferred_method(self, method):
        pass
