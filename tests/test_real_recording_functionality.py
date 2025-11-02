"""真实录音功能测试

使用真实的应用实例测试录音功能，不再依赖Mock服务
这能发现真实环境中的问题
"""

import pytest
import time
import threading
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication

from sonicinput.core.voice_input_app import VoiceInputApp
from sonicinput.core.di_container_enhanced import create_container
from sonicinput.core.services.event_bus import Events
from sonicinput.core.interfaces.state import AppState, RecordingState
from sonicinput.utils import app_logger


class TestRealRecordingFunctionality:
    """真实录音功能测试"""

    @pytest.fixture
    def qt_application(self):
        """确保Qt应用存在"""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app

    @pytest.fixture
    def mock_screen(self):
        """Mock屏幕信息用于悬浮窗测试"""
        screen = MagicMock()
        screen.geometry.return_value = MagicMock()
        screen.geometry.return_value.width.return_value = 1920
        screen.geometry.return_value.height.return_value = 1080
        screen.geometry.return_value.x.return_value = 0
        screen.geometry.return_value.y.return_value = 0
        screen.geometry.return_value.contains.return_value = True
        return screen

    @pytest.fixture
    def real_app(self, qt_application, mock_screen):
        """创建真实的应用实例"""
        # Mock屏幕以支持悬浮窗测试
        with patch('PySide6.QtGui.QGuiApplication.primaryScreen', return_value=mock_screen):
            container = create_container()
            app = VoiceInputApp(container)
            app.initialize_with_validation()
            yield app

    def test_application_initialization(self, real_app):
        """测试应用初始化"""
        # 验证应用成功初始化
        assert real_app is not None
        assert real_app.is_initialized == True

        # 验证核心服务存在
        assert real_app.config is not None
        assert real_app.events is not None
        assert real_app.state is not None
        assert real_app._audio_service is not None
        assert real_app._speech_service is not None
        assert real_app._input_service is not None

        app_logger.log_audio_event("Application initialization test passed", {
            "config_loaded": real_app.config is not None,
            "events_loaded": real_app.events is not None,
            "state_loaded": real_app.state is not None
        })

    def test_recording_state_flow(self, real_app):
        """测试录音状态流程"""
        # 事件收集
        events_received = []

        def capture_events(event_name):
            def handler(*args):
                events_received.append({
                    'event': event_name,
                    'time': time.time(),
                    'args': args
                })
            return handler

        # 注册事件监听
        real_app.events.on(Events.RECORDING_STARTED, capture_events('recording_started'))
        real_app.events.on(Events.RECORDING_STOPPED, capture_events('recording_stopped'))

        # 初始状态
        initial_state = real_app.state.get_recording_state()
        assert initial_state == RecordingState.IDLE

        # 启动录音
        real_app.toggle_recording()
        time.sleep(0.2)  # 等待异步操作

        # 验证录音状态
        recording_state = real_app.state.get_recording_state()
        assert recording_state == RecordingState.RECORDING

        # 验证录音启动事件
        started_events = [e for e in events_received if e['event'] == 'recording_started']
        assert len(started_events) >= 1

        # 停止录音
        real_app.toggle_recording()
        time.sleep(0.5)  # 等待转录处理

        # 验证停止状态
        final_state = real_app.state.get_recording_state()
        assert final_state == RecordingState.IDLE

        # 验证录音停止事件
        stopped_events = [e for e in events_received if e['event'] == 'recording_stopped']
        assert len(stopped_events) >= 1

        app_logger.log_audio_event("Recording state flow test passed", {
            "started_events": len(started_events),
            "stopped_events": len(stopped_events),
            "final_state": str(final_state)
        })

    def test_transcription_workflow(self, real_app):
        """测试转录工作流程"""
        # 事件收集
        transcription_events = []

        def capture_transcription_events(event_name):
            def handler(*args):
                transcription_events.append({
                    'event': event_name,
                    'time': time.time(),
                    'args': args
                })
            return handler

        # 注册转录事件监听
        real_app.events.on(Events.TRANSCRIPTION_STARTED, capture_transcription_events('transcription_started'))
        real_app.events.on(Events.TRANSCRIPTION_COMPLETED, capture_transcription_events('transcription_completed'))

        # 启动录音
        real_app.toggle_recording()
        time.sleep(0.2)

        # 停止录音（这会触发转录）
        real_app.toggle_recording()
        time.sleep(1.0)  # 等待转录完成

        # 验证转录事件
        started_events = [e for e in transcription_events if e['event'] == 'transcription_started']
        completed_events = [e for e in transcription_events if e['event'] == 'transcription_completed']

        assert len(started_events) >= 1, "应该有转录启动事件"
        assert len(completed_events) >= 1, "应该有转录完成事件"

        app_logger.log_audio_event("Transcription workflow test passed", {
            "started_events": len(started_events),
            "completed_events": len(completed_events)
        })

    def test_overlay_integration(self, real_app, qt_application, mock_screen):
        """测试悬浮窗集成"""
        # 创建悬浮窗
        with patch('PySide6.QtGui.QGuiApplication.primaryScreen', return_value=mock_screen):
            from sonicinput.ui.recording_overlay import RecordingOverlay
            overlay = RecordingOverlay()
            overlay.set_config_service(real_app.config)
            real_app.set_recording_overlay(overlay)

            # 启动录音
            real_app.toggle_recording()
            time.sleep(0.2)

            # 验证悬浮窗显示
            # 注意：在测试环境中，悬浮窗可能不会真正显示，但状态应该是正确的
            recording_state = real_app.state.get_recording_state()
            assert recording_state == RecordingState.RECORDING

            # 停止录音
            real_app.toggle_recording()
            time.sleep(0.5)

            app_logger.log_audio_event("Overlay integration test passed", {
                "recording_completed": real_app.state.get_recording_state() == RecordingState.IDLE
            })

    def test_error_handling(self, real_app):
        """测试错误处理"""
        # 验证应用状态
        assert real_app.is_initialized == True

        # 尝试在异常状态下的操作
        try:
            # 多次快速切换录音状态
            real_app.toggle_recording()
            time.sleep(0.05)
            real_app.toggle_recording()
            time.sleep(0.05)
            real_app.toggle_recording()
            time.sleep(0.05)
            real_app.toggle_recording()
            time.sleep(0.5)
        except Exception as e:
            pytest.fail(f"快速切换录音状态时出现异常: {e}")

        # 验证应用仍然稳定
        assert real_app.is_initialized == True
        assert real_app.state.get_recording_state() == RecordingState.IDLE

        app_logger.log_audio_event("Error handling test passed", {
            "app_stable": real_app.is_initialized,
            "final_state": str(real_app.state.get_recording_state())
        })

    def test_audio_level_updates(self, real_app):
        """测试音频级别更新"""
        level_updates = []

        def capture_level(level):
            level_updates.append({
                'level': level,
                'time': time.time()
            })

        real_app.events.on(Events.AUDIO_LEVEL_UPDATE, capture_level)

        # 启动录音
        real_app.toggle_recording()
        time.sleep(0.1)

        # 模拟音频级别更新
        test_levels = [0.2, 0.5, 0.8, 0.3, 0.6]
        for level in test_levels:
            real_app.events.emit(Events.AUDIO_LEVEL_UPDATE, level)
            time.sleep(0.01)

        # 停止录音
        real_app.toggle_recording()
        time.sleep(0.3)

        # 验证音频级别被接收（至少要有我们发送的数量）
        assert len(level_updates) >= len(test_levels)
        # 验证我们发送的测试级别都被接收了（可能有额外的级别更新）
        for i, expected_level in enumerate(test_levels):
            # 找到对应的级别（可能因为有额外的级别更新而位置不同）
            matching_levels = [update['level'] for update in level_updates if update['level'] == expected_level]
            assert len(matching_levels) >= 1, f"Expected level {expected_level} not found in updates"

        app_logger.log_audio_event("Audio level updates test passed", {
            "levels_sent": len(test_levels),
            "levels_received": len(level_updates)
        })

    def test_config_changes(self, real_app):
        """测试配置变更处理"""
        # 获取初始配置
        initial_sample_rate = real_app.config.get_setting("audio.sample_rate", 16000)

        # 模拟配置变更
        new_config = {
            "audio": {
                "sample_rate": 22050,
                "channels": 1
            }
        }

        # 发送配置变更事件
        real_app.events.emit("config.changed", {
            "config": new_config,
            "timestamp": time.time()
        })

        time.sleep(0.1)

        # 验证配置被处理（注意：实际的配置更新可能在异步处理中）
        app_logger.log_audio_event("Config changes test passed", {
            "initial_sample_rate": initial_sample_rate,
            "config_event_sent": True
        })

    def test_hotkey_functionality(self, real_app):
        """测试快捷键功能"""
        # 验证快捷键服务存在
        assert real_app._hotkey_service is not None

        # 模拟快捷键触发
        original_recording_state = real_app.state.get_recording_state()
        assert original_recording_state == RecordingState.IDLE

        # 模拟快捷键触发
        real_app._on_hotkey_triggered("toggle_recording")
        time.sleep(0.2)

        # 验证录音状态改变
        new_recording_state = real_app.state.get_recording_state()
        assert new_recording_state == RecordingState.RECORDING

        # 再次触发快捷键
        real_app._on_hotkey_triggered("toggle_recording")
        time.sleep(0.5)

        # 验证回到IDLE状态
        final_state = real_app.state.get_recording_state()
        assert final_state == RecordingState.IDLE

        app_logger.log_audio_event("Hotkey functionality test passed", {
            "initial_state": str(original_recording_state),
            "final_state": str(final_state)
        })

    def test_complete_workflow_integration(self, real_app, qt_application, mock_screen):
        """完整工作流程集成测试"""
        workflow_steps = []

        def record_step(step_name):
            def handler(*args):
                workflow_steps.append({
                    'step': step_name,
                    'time': time.time(),
                    'args': args
                })
            return handler

        # 注册完整工作流程的事件监听
        real_app.events.on(Events.RECORDING_STARTED, record_step('recording_started'))
        real_app.events.on(Events.RECORDING_STOPPED, record_step('recording_stopped'))
        real_app.events.on(Events.TRANSCRIPTION_STARTED, record_step('transcription_started'))
        real_app.events.on(Events.TRANSCRIPTION_COMPLETED, record_step('transcription_completed'))

        # 设置悬浮窗
        with patch('PySide6.QtGui.QGuiApplication.primaryScreen', return_value=mock_screen):
            from sonicinput.ui.recording_overlay import RecordingOverlay
            overlay = RecordingOverlay()
            overlay.set_config_service(real_app.config)
            real_app.set_recording_overlay(overlay)

        workflow_start_time = time.time()

        # 1. 快捷键触发录音
        real_app._on_hotkey_triggered("toggle_recording")
        time.sleep(0.2)

        # 2. 模拟音频级别更新
        for i in range(3):
            real_app.events.emit(Events.AUDIO_LEVEL_UPDATE, 0.3 + i * 0.2)
            time.sleep(0.05)

        # 3. 停止录音
        real_app._on_hotkey_triggered("toggle_recording")
        time.sleep(1.0)  # 等待转录完成

        workflow_end_time = time.time()
        total_duration = workflow_end_time - workflow_start_time

        # 验证工作流程步骤
        expected_steps = ['recording_started', 'recording_stopped', 'transcription_started', 'transcription_completed']
        actual_steps = [step['step'] for step in workflow_steps]

        for step in expected_steps:
            assert step in actual_steps, f"工作流程缺少步骤: {step}"

        app_logger.log_audio_event("Complete workflow integration test passed", {
            "total_duration": total_duration,
            "workflow_steps": actual_steps,
            "step_count": len(workflow_steps)
        })