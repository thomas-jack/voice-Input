"""Mock 音频录制服务"""
import numpy as np
from sonicinput.core.interfaces import IAudioService


class MockAudioRecorder(IAudioService):
    def __init__(self):
        self.is_recording = False
        self.callback = None
        self.fake_audio_data = np.random.random(16000 * 5)  # 5秒假音频

    def start_recording(self, device_id=None):
        self.is_recording = True

    def stop_recording(self):
        self.is_recording = False
        return self.fake_audio_data

    def set_callback(self, callback):
        self.callback = callback

    def list_devices(self):
        return [{"id": 0, "name": "Mock Microphone"}]
