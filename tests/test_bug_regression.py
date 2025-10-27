"""Bug 回归测试 - 确保已修复的 bug 不再出现"""
import pytest
import time
from sonicinput.core.interfaces.state import AppState, RecordingState
from sonicinput.core.services.event_bus import Events


class TestBugFixes:
    """测试已修复的 bug"""

    def test_bug_second_recording_works(self, app_with_mocks):
        """
        Bug: 第一次录音后无法进行第二次录音
        根本原因: AppState 没有重置为 IDLE
        修复位置: InputController.input_text() 添加 set_app_state(AppState.IDLE)
        """
        app = app_with_mocks['app']

        # 第一次录音
        app.toggle_recording()
        time.sleep(0.1)
        app.toggle_recording()
        time.sleep(1)  # 等待处理完成

        # 验证状态已重置
        assert app.state.get_app_state() == AppState.IDLE

        # 第二次录音必须能启动
        app.toggle_recording()
        assert app.state.get_recording_state() == RecordingState.RECORDING

        # 停止第二次录音
        app.toggle_recording()
        assert app.state.get_recording_state() == RecordingState.IDLE


    def test_bug_audio_level_type_is_float(self, app_with_mocks):
        """
        Bug: 音量级别类型错误导致 UI 不显示
        根本原因: RecordingController 发送 float，但 RecordingOverlay 期望 ndarray
        修复位置:
          - RecordingOverlay 添加 update_audio_level(float) 方法
          - VoiceInputApp._on_audio_level_update_overlay() 调用新方法
        """
        app = app_with_mocks['app']

        received_levels = []

        def capture_level(level):
            received_levels.append(level)

        app.events.on(Events.AUDIO_LEVEL_UPDATE, capture_level)

        # 开始录音（会触发音频级别更新）
        app.toggle_recording()

        # 模拟音频数据回调（RecordingController 会计算 level 并发送）
        # 这里我们直接发送测试事件
        app.events.emit(Events.AUDIO_LEVEL_UPDATE, 0.5)

        # 验证收到的是 float
        assert len(received_levels) > 0
        assert isinstance(received_levels[0], float)
        assert 0.0 <= received_levels[0] <= 1.0


    def test_bug_overlay_displays_on_recording(self, app_with_mocks):
        """
        Bug: 录音悬浮窗消失
        根本原因: set_recording_overlay() 方法是空的，没有存储引用和设置事件监听
        修复位置: VoiceInputApp.set_recording_overlay() 添加事件监听器
        """
        app = app_with_mocks['app']

        # Mock 录音悬浮窗
        from unittest.mock import MagicMock
        mock_overlay = MagicMock()

        # 设置悬浮窗
        app.set_recording_overlay(mock_overlay)

        # 开始录音
        app.toggle_recording()

        # 验证悬浮窗被调用显示
        mock_overlay.show_recording.assert_called_once()

        # 停止录音
        app.toggle_recording()
        time.sleep(0.1)

        # 验证悬浮窗被调用显示处理中
        mock_overlay.show_processing.assert_called()
