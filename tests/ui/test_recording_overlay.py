"""RecordingOverlay UI测试套件

测试RecordingOverlay的基础功能和信号处理,不涉及配置文件操作。
"""
import pytest
from PySide6.QtCore import Qt
import numpy as np


@pytest.mark.gui
class TestRecordingOverlayBasics:
    """RecordingOverlay基础功能测试"""

    def test_overlay_creation(self, qtbot, recording_overlay):
        """测试overlay可以被创建"""
        assert recording_overlay is not None
        assert not recording_overlay.isVisible()
        assert recording_overlay.is_recording is False

    def test_overlay_singleton(self, qtbot, recording_overlay):
        """测试单例模式"""
        from sonicinput.ui.recording_overlay import RecordingOverlay

        overlay2 = RecordingOverlay()
        assert overlay2 is recording_overlay

    def test_window_flags(self, qtbot, recording_overlay):
        """测试无框架和透明窗口属性"""
        flags = recording_overlay.windowFlags()

        # 验证窗口标志
        assert flags & Qt.WindowType.FramelessWindowHint
        assert flags & Qt.WindowType.WindowStaysOnTopHint
        assert flags & Qt.WindowType.Tool

        # 验证透明背景
        assert recording_overlay.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def test_initial_state(self, qtbot, recording_overlay):
        """测试初始状态"""
        assert recording_overlay.is_recording is False
        assert recording_overlay.current_status == "Ready"
        assert recording_overlay.recording_duration == 0


@pytest.mark.gui
class TestRecordingOverlaySignals:
    """RecordingOverlay信号测试"""

    def test_show_recording_signal(self, qtbot, recording_overlay):
        """测试显示录音信号"""
        with qtbot.waitSignal(recording_overlay.show_recording_requested, timeout=1000):
            recording_overlay.show_recording_requested.emit()

    def test_hide_recording_signal(self, qtbot, recording_overlay):
        """测试隐藏录音信号"""
        with qtbot.waitSignal(recording_overlay.hide_recording_requested, timeout=1000):
            recording_overlay.hide_recording_requested.emit()

    def test_status_update_signal(self, qtbot, recording_overlay):
        """测试状态更新信号"""
        with qtbot.waitSignal(recording_overlay.set_status_requested, timeout=1000) as blocker:
            recording_overlay.set_status_requested.emit("Recording...")

        assert blocker.args == ["Recording..."]

    def test_audio_level_signal(self, qtbot, recording_overlay):
        """测试音频级别更新信号"""
        with qtbot.waitSignal(recording_overlay.update_audio_level_requested, timeout=1000) as blocker:
            recording_overlay.update_audio_level_requested.emit(0.75)

        assert blocker.args == [0.75]

    def test_waveform_signal(self, qtbot, recording_overlay):
        """测试波形数据信号"""
        fake_audio = np.random.random(1024)

        with qtbot.waitSignal(recording_overlay.update_waveform_requested, timeout=1000):
            recording_overlay.update_waveform_requested.emit(fake_audio)

    def test_processing_signals(self, qtbot, recording_overlay):
        """测试处理动画信号"""
        # 启动处理动画
        with qtbot.waitSignal(recording_overlay.start_processing_animation_requested, timeout=1000):
            recording_overlay.start_processing_animation_requested.emit()

        # 停止处理动画
        with qtbot.waitSignal(recording_overlay.stop_processing_animation_requested, timeout=1000):
            recording_overlay.stop_processing_animation_requested.emit()

    def test_show_completed_signal(self, qtbot, recording_overlay):
        """测试显示完成状态信号"""
        with qtbot.waitSignal(recording_overlay.show_completed_requested, timeout=1000) as blocker:
            recording_overlay.show_completed_requested.emit(500)

        assert blocker.args == [500]

    def test_show_warning_signal(self, qtbot, recording_overlay):
        """测试显示警告状态信号"""
        with qtbot.waitSignal(recording_overlay.show_warning_requested, timeout=1000) as blocker:
            recording_overlay.show_warning_requested.emit(1000)

        assert blocker.args == [1000]

    def test_show_error_signal(self, qtbot, recording_overlay):
        """测试显示错误状态信号"""
        with qtbot.waitSignal(recording_overlay.show_error_requested, timeout=1000) as blocker:
            recording_overlay.show_error_requested.emit(1500)

        assert blocker.args == [1500]

    def test_delayed_hide_signal(self, qtbot, recording_overlay):
        """测试延迟隐藏信号"""
        with qtbot.waitSignal(recording_overlay.hide_recording_delayed_requested, timeout=1000) as blocker:
            recording_overlay.hide_recording_delayed_requested.emit(300)

        assert blocker.args == [300]


@pytest.mark.gui
class TestRecordingOverlayStates:
    """RecordingOverlay状态转换测试"""

    def test_show_hide_workflow(self, qtbot, recording_overlay):
        """测试显示/隐藏工作流"""
        # 初始状态:隐藏
        assert not recording_overlay.isVisible()

        # 显示
        recording_overlay.show_recording_requested.emit()
        qtbot.waitUntil(lambda: recording_overlay.isVisible(), timeout=2000)
        assert recording_overlay.isVisible()

        # 隐藏
        recording_overlay.hide_recording_requested.emit()
        qtbot.waitUntil(lambda: not recording_overlay.isVisible(), timeout=2000)
        assert not recording_overlay.isVisible()

    def test_keyboard_escape(self, qtbot, recording_overlay):
        """测试ESC键关闭overlay"""
        # 显示overlay
        recording_overlay.show()
        qtbot.waitExposed(recording_overlay, timeout=1000)

        # 模拟ESC键按下
        qtbot.keyPress(recording_overlay, Qt.Key.Key_Escape)

        # 验证overlay隐藏
        qtbot.waitUntil(lambda: not recording_overlay.isVisible(), timeout=2000)
        assert not recording_overlay.isVisible()


@pytest.mark.gui
class TestRecordingOverlayComponents:
    """RecordingOverlay组件测试"""

    def test_status_indicator_exists(self, qtbot, recording_overlay):
        """测试状态指示器存在"""
        assert hasattr(recording_overlay, 'status_indicator')
        assert recording_overlay.status_indicator is not None

    def test_audio_level_bars_exists(self, qtbot, recording_overlay):
        """测试音频级别条存在"""
        assert hasattr(recording_overlay, 'audio_level_bars')
        assert recording_overlay.audio_level_bars is not None

    def test_time_label_exists(self, qtbot, recording_overlay):
        """测试时间标签存在"""
        assert hasattr(recording_overlay, 'time_label')
        assert recording_overlay.time_label is not None

    def test_close_button_exists(self, qtbot, recording_overlay):
        """测试关闭按钮存在"""
        assert hasattr(recording_overlay, 'close_button')
        assert recording_overlay.close_button is not None

    def test_close_button_click(self, qtbot, recording_overlay):
        """测试关闭按钮点击"""
        # 显示overlay
        recording_overlay.show()
        qtbot.waitExposed(recording_overlay, timeout=1000)

        # 点击关闭按钮 (使用qtbot.mouseClick因为是自定义组件)
        qtbot.mouseClick(recording_overlay.close_button, Qt.MouseButton.LeftButton)

        # 验证overlay隐藏
        qtbot.waitUntil(lambda: not recording_overlay.isVisible(), timeout=2000)
        assert not recording_overlay.isVisible()


@pytest.mark.gui
@pytest.mark.slow
class TestRecordingOverlayDelayedOperations:
    """RecordingOverlay延迟操作测试"""

    def test_delayed_hide_timing(self, qtbot, recording_overlay):
        """测试延迟隐藏时间"""
        # 显示overlay
        recording_overlay.show_recording_requested.emit()
        qtbot.waitUntil(lambda: recording_overlay.isVisible(), timeout=2000)

        # 触发延迟隐藏(500ms)
        delay_ms = 500
        recording_overlay.hide_recording_delayed_requested.emit(delay_ms)

        # 应该仍然可见
        assert recording_overlay.isVisible()

        # 等待延迟时间 + 缓冲
        qtbot.wait(delay_ms + 200)

        # 现在应该隐藏
        assert not recording_overlay.isVisible()
