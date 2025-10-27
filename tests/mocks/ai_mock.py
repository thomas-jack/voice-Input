"""Mock AI 优化服务"""

class MockAIService:
    def __init__(self, return_text="优化后的文本。"):
        self.return_text = return_text

    def optimize_text(self, text):
        return self.return_text
