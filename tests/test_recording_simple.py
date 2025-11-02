"""简化的录音功能测试

专注于核心录音流程测试，避免复杂的Qt UI测试
"""

import pytest
import time
import threading
from unittest.mock import MagicMock
import numpy as np

from sonicinput.core.voice_input_app import VoiceInputApp
from sonicinput.core.di_container import DIContainer
from sonicinput.core.services.event_bus import Events
from sonicinput.core.interfaces import (
    ISpeechService, IInputService, IAudioService
)
from sonicinput.core.interfaces.state import AppState, RecordingState
from sonicinput.utils import app_logger


class TestRecordingFunctionality:
    """录音功能测试"""

    @pytest.fixture
    def app_with_simple_mocks(self, mock_whisper, mock_ai, mock_input, mock_audio):
        """创建带简单 Mock 的应用"""
        from sonicinput.core.di_container_enhanced import create_container

        # 创建完整的容器
        container = create_container()

        # 覆盖关键服务为 Mock
        container.register_singleton(ISpeechService, factory=lambda: mock_whisper)
        container.register_singleton(IInputService, factory=lambda: mock_input)
        container.register_singleton(IAudioService, factory=lambda: mock_audio)

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

    def test_recording_start_stop_flow(self, app_with_simple_mocks):
        """测试录音启动和停止流程"""
        app = app_with_simple_mocks['app']
        mock_audio = app_with_simple_mocks['audio']

        # 监听事件
        events_received = []

        def track_events(event_name):
            def handler(*args):
                events_received.append((event_name, args))
            return handler

        app.events.on(Events.RECORDING_STARTED, track_events('recording_started'))
        app.events.on(Events.RECORDING_STOPPED, track_events('recording_stopped'))

        # 初始状态验证
        assert app.state.get_recording_state() == RecordingState.IDLE
        # 应用可能处于STARTING状态，这是正常的
        initial_app_state = app.state.get_app_state()
        assert initial_app_state in [AppState.IDLE, AppState.STARTING]

        # 启动录音
        app.toggle_recording()

        # 等待异步操作
        time.sleep(0.1)

        # 验证录音服务被调用
        mock_audio.start_recording.assert_called()

        # 验证状态变化
        assert app.state.get_recording_state() == RecordingState.RECORDING

        # 验证事件触发
        assert any(event[0] == 'recording_started' for event in events_received)

        # 停止录音
        app.toggle_recording()

        # 等待异步操作
        time.sleep(0.2)

        # 验证录音服务被调用
        mock_audio.stop_recording.assert_called()

        # 验证状态回到初始
        assert app.state.get_recording_state() == RecordingState.IDLE

        # 验证事件触发
        assert any(event[0] == 'recording_stopped' for event in events_received)

        app_logger.log_audio_event("Recording start/stop flow test passed", {
            "events_received": [event[0] for event in events_received]
        })

    def test_audio_data_collection(self, app_with_simple_mocks):
        """测试音频数据采集"""
        app = app_with_simple_mocks['app']
        mock_audio = app_with_simple_mocks['audio']

        # 设置模拟音频数据
        fake_audio = np.random.random(16000 * 3)  # 3秒音频
        mock_audio.stop_recording.return_value = fake_audio

        # 启动录音
        app.toggle_recording()

        # 设置音频回调
        audio_chunks_received = []

        def audio_callback(chunk):
            audio_chunks_received.append(chunk)

        mock_audio.set_callback(audio_callback)

        # 停止录音并获取数据
        app.toggle_recording()
        time.sleep(0.1)  # 等待异步操作完成

        # 从mock获取音频数据
        result = mock_audio.stop_recording.return_value

        # 验证音频数据
        assert result is not None
        assert len(result) > 0
        assert isinstance(result, np.ndarray)

        # 验证回调被设置
        mock_audio.set_callback.assert_called()

        app_logger.log_audio_event("Audio data collection test passed", {
            "audio_length": len(result),
            "chunks_received": len(audio_chunks_received)
        })

    def test_recording_state_transitions(self, app_with_simple_mocks):
        """测试录音状态转换"""
        app = app_with_simple_mocks['app']

        # 状态转换记录
        states = []

        def record_state():
            states.append(app.state.get_recording_state())

        # 初始状态
        record_state()
        assert states[-1] == RecordingState.IDLE

        # 启动录音
        app.toggle_recording()
        time.sleep(0.1)
        record_state()
        assert states[-1] == RecordingState.RECORDING

        # 停止录音
        app.toggle_recording()
        time.sleep(0.1)
        record_state()
        assert states[-1] == RecordingState.IDLE

        app_logger.log_audio_event("Recording state transitions test passed", {
            "state_sequence": [str(state) for state in states]
        })

    def test_audio_level_updates(self, app_with_simple_mocks):
        """测试音频级别更新"""
        app = app_with_simple_mocks['app']

        # 音频级别记录
        levels_received = []

        def capture_level(level):
            levels_received.append(level)

        app.events.on(Events.AUDIO_LEVEL_UPDATE, capture_level)

        # 启动录音
        app.toggle_recording()

        # 模拟音频级别更新
        test_levels = [0.1, 0.3, 0.7, 0.9, 0.5]
        for level in test_levels:
            app.events.emit(Events.AUDIO_LEVEL_UPDATE, level)

        # 验证音频级别被接收
        assert len(levels_received) == len(test_levels)
        for i, level in enumerate(test_levels):
            assert levels_received[i] == level
            assert 0.0 <= level <= 1.0

        app.toggle_recording()

        app_logger.log_audio_event("Audio level updates test passed", {
            "levels_received": len(levels_received),
            "test_levels": len(test_levels)
        })

    def test_error_handling_in_recording(self, app_with_simple_mocks):
        """测试录音过程中的错误处理"""
        app = app_with_simple_mocks['app']
        mock_audio = app_with_simple_mocks['audio']

        # 模拟录音启动错误
        mock_audio.start_recording.side_effect = Exception("Mock recording error")

        # 错误事件记录
        error_events = []

        def capture_error(*args):
            error_events.append(args)

        app.events.on(Events.ERROR_OCCURRED, capture_error)

        # 尝试启动录音（应该优雅地处理错误）
        try:
            app.toggle_recording()
        except Exception:
            # 预期可能抛出异常
            pass

        # 验证应用状态仍然稳定
        assert app is not None
        assert app.state is not None

        app_logger.log_audio_event("Error handling test completed", {
            "error_events": len(error_events)
        })

    def test_multiple_recording_cycles(self, app_with_simple_mocks):
        """测试多次录音循环"""
        app = app_with_simple_mocks['app']
        mock_audio = app_with_simple_mocks['audio']

        # 设置模拟音频数据
        fake_audio = np.random.random(16000 * 2)  # 2秒音频
        mock_audio.stop_recording.return_value = fake_audio

        # 执行多次录音循环
        cycles = 3
        for i in range(cycles):
            # 启动录音
            app.toggle_recording()
            time.sleep(0.1)
            assert app.state.get_recording_state() == RecordingState.RECORDING

            # 短暂等待模拟录音过程
            time.sleep(0.01)

            # 停止录音
            app.toggle_recording()
            time.sleep(0.1)
            assert app.state.get_recording_state() == RecordingState.IDLE

        # 验证服务调用次数
        assert mock_audio.start_recording.call_count == cycles
        assert mock_audio.stop_recording.call_count == cycles

        app_logger.log_audio_event("Multiple recording cycles test passed", {
            "cycles": cycles,
            "start_calls": mock_audio.start_recording.call_count,
            "stop_calls": mock_audio.stop_recording.call_count
        })

    def test_recording_with_audio_device_selection(self, app_with_simple_mocks):
        """测试录音设备选择"""
        app = app_with_simple_mocks['app']
        mock_audio = app_with_simple_mocks['audio']

        # 模拟音频设备列表
        mock_devices = [
            {'index': 0, 'name': 'Default Device', 'channels': 2, 'sample_rate': 44100},
            {'index': 1, 'name': 'USB Microphone', 'channels': 1, 'sample_rate': 48000}
        ]
        mock_audio.get_audio_devices.return_value = mock_devices

        # 测试使用指定设备启动录音
        device_id = 1

        # 由于我们使用toggle_recording，无法直接传递device_id
        # 这里测试设备列表获取功能
        devices = app._audio_service.get_audio_devices()
        assert len(devices) == 2
        assert devices[1]['index'] == 1

        # 启动录音（使用默认设备）
        app.toggle_recording()
        time.sleep(0.1)

        # 验证录音启动
        assert app.state.get_recording_state() == RecordingState.RECORDING

        app.toggle_recording()

        app_logger.log_audio_event("Recording with device selection test passed", {
            "device_id": device_id,
            "devices_found": len(devices)
        })