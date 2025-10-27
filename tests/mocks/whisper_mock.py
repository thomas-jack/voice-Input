"""Mock Whisper 转录引擎"""
from voice_input_software.core.interfaces import ISpeechService


class MockWhisperEngine(ISpeechService):
    def __init__(self, return_text="这是测试文本"):
        self.return_text = return_text

    def transcribe(self, audio, language=None):
        return {"text": self.return_text}

    def is_model_loaded(self):
        return True

    def finalize_streaming_transcription(self, timeout=30):
        return self.return_text

    def start_streaming_mode(self):
        pass
