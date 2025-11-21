"""pytest 配置和全局 fixtures"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock
import numpy as np

# 添加 src 到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sonicinput.core.di_container import DIContainer
from sonicinput.core.voice_input_app import VoiceInputApp
from sonicinput.core.interfaces import (
    ISpeechService, IInputService, IAudioService
)
from sonicinput.core.services.event_bus import Events
from sonicinput.core.interfaces.state import AppState, RecordingState


# ============= Mock Fixtures =============

@pytest.fixture
def mock_whisper():
    """Mock Whisper 转录引擎"""
    # 不使用 spec，因为接口可能不完整
    whisper = MagicMock()
    whisper.transcribe.return_value = {"text": "这是测试文本"}
    whisper.is_model_loaded.return_value = True
    # 旧方法名（向后兼容）
    whisper.finalize_streaming_transcription.return_value = {"text": "这是测试文本", "stats": {}}
    whisper.start_streaming_mode.return_value = None
    # 新 API 流式转录支持
    whisper.start_streaming.return_value = None
    whisper.add_streaming_chunk.return_value = None
    whisper.stop_streaming.return_value = {"text": "这是测试文本", "stats": {}}
    whisper.load_model.return_value = True
    return whisper


@pytest.fixture
def mock_ai():
    """Mock AI 优化服务"""
    ai = MagicMock()
    # 兼容不同的AI客户端接口
    ai.optimize_text.return_value = "优化后的测试文本。"
    ai.refine_text.return_value = "优化后的测试文本。"
    ai.test_connection.return_value = True
    ai.health_check.return_value = True
    return ai


@pytest.fixture
def mock_input():
    """Mock 输入服务（记录输入的文本）"""
    input_svc = MagicMock()
    input_svc.input_text.return_value = True
    input_svc.last_text = None

    def capture_text(text):
        input_svc.last_text = text
        return True

    input_svc.input_text.side_effect = capture_text
    return input_svc


@pytest.fixture
def mock_audio():
    """Mock 音频录制服务"""
    audio = MagicMock()
    # 模拟录音停止返回 5 秒的假音频
    fake_audio = np.random.random(16000 * 5)  # 5秒 @ 16kHz
    audio.stop_recording = MagicMock(return_value=fake_audio)
    audio.start_recording = MagicMock(return_value=None)
    audio.set_callback = MagicMock(return_value=None)
    audio.get_audio_devices = MagicMock(return_value=[])
    return audio


# ============= 应用 Fixtures =============

@pytest.fixture
def app_with_mocks(mock_whisper, mock_ai, mock_input, mock_audio):
    """创建带 Mock 的完整应用"""
    from sonicinput.core.di_container import create_container

    # 创建完整的容器
    container = create_container()

    # 覆盖关键服务为 Mock（使用新的API）
    container.register_singleton(ISpeechService, factory=lambda: mock_whisper)
    container.register_singleton(IInputService, factory=lambda: mock_input)
    container.register_singleton(IAudioService, factory=lambda: mock_audio)

    # 注入 Mock AI（需要找到正确的接口）
    from sonicinput.ai.groq import GroqClient
    container.register_singleton(GroqClient, factory=lambda: mock_ai)

    app = VoiceInputApp(container)
    app.initialize_with_validation()

    return {
        'app': app,
        'whisper': mock_whisper,
        'ai': mock_ai,
        'input': mock_input,
        'audio': mock_audio,
        'container': container
    }


# ============= 辅助函数 =============

@pytest.fixture
def wait_for_event():
    """等待事件触发的辅助函数"""
    def _wait(app, event_name, timeout=5):
        import time
        received = []

        def handler(*args):
            received.append(args)

        app.events.on(event_name, handler)

        start = time.time()
        while not received and time.time() - start < timeout:
            time.sleep(0.01)

        if not received:
            raise TimeoutError(f"Event {event_name} not received within {timeout}s")

        return received[0] if received else None

    return _wait
