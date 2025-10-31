"""RecordingOverlay单元测试

测试RecordingOverlay的各项功能，包括：
- 显示能力测试
- 输入处理测试
- 位置管理测试
- UI组件测试
- 动画系统测试
- 定时器管理测试
- 信号系统测试
"""

import pytest
import math
from unittest.mock import Mock, patch, MagicMock
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication

from sonicinput.ui.recording_overlay import RecordingOverlay
from sonicinput.ui.overlay import StatusIndicator


@pytest.fixture
def qapp():
    """提供QApplication实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # 不要quit，因为其他测试可能还需要


@pytest.fixture
def overlay(qapp):
    """提供RecordingOverlay实例"""
    # 重置单例确保干净的测试环境
    RecordingOverlay.reset_singleton()
    overlay_instance = RecordingOverlay()
    yield overlay_instance
    # 清理
    try:
        overlay_instance.cleanup()
    except:
        pass


class TestRecordingOverlayDisplay:
    """测试显示能力"""

    def test_display_capability(self, overlay):
        """测试overlay是否能正确显示"""
        # 检查QApplication存在
        app = QApplication.instance()
        assert app is not None, "QApplication实例不存在"

        # 检查主屏幕可用性
        screen = QGuiApplication.primaryScreen()
        assert screen is not None, "主屏幕不可用"

        screen_geometry = screen.geometry()
        assert screen_geometry.width() > 0, "屏幕宽度无效"
        assert screen_geometry.height() > 0, "屏幕高度无效"

        # 检查widget是窗口
        assert overlay.isWindow(), "Overlay不是窗口"

        # 检查窗口标志
        flags = overlay.windowFlags()
        expected_flags = [
            Qt.WindowType.FramelessWindowHint,
            Qt.WindowType.WindowStaysOnTopHint,
            Qt.WindowType.Tool
        ]

        for flag in expected_flags:
            assert flags & flag, f"缺少必需的窗口标志: {flag}"

    def test_widget_size(self, overlay):
        """测试widget尺寸设置"""
        # Material Design紧凑横向布局
        assert overlay.width() == 200, "宽度应为200"
        assert overlay.height() == 50, "高度应为50"

    def test_window_attributes(self, overlay):
        """测试窗口属性"""
        # 检查透明背景属性
        assert overlay.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground), \
            "应该设置透明背景属性"


class TestRecordingOverlayInputHandling:
    """测试输入处理"""

    def test_event_handlers_exist(self, overlay):
        """测试事件处理方法是否存在"""
        required_methods = ['keyPressEvent', 'mousePressEvent', 'mouseMoveEvent', 'mouseReleaseEvent']
        for method_name in required_methods:
            assert hasattr(overlay, method_name), f"缺少事件处理方法: {method_name}"

    def test_signals_exist(self, overlay):
        """测试所有信号是否存在"""
        required_signals = [
            'show_recording_requested',
            'hide_recording_requested',
            'show_processing_requested',
            'show_completed_requested',
            'set_status_requested',
            'update_waveform_requested',
            'update_audio_level_requested',
            'start_processing_animation_requested',
            'stop_processing_animation_requested',
            'hide_recording_delayed_requested'
        ]

        for signal_name in required_signals:
            assert hasattr(overlay, signal_name), f"缺少信号: {signal_name}"


class TestRecordingOverlayPositioning:
    """测试位置管理"""

    def test_position_manager_exists(self, overlay):
        """测试位置管理器是否初始化"""
        assert hasattr(overlay, 'position_manager'), "缺少位置管理器"
        assert overlay.position_manager is not None, "位置管理器未初始化"

    def test_center_positioning(self, overlay):
        """测试居中定位"""
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()

        overlay.position_manager.center_on_screen()
        center_pos = overlay.pos()

        expected_x = (screen_geometry.width() - overlay.width()) // 2
        expected_y = (screen_geometry.height() - overlay.height()) // 2

        # 允许10像素的误差
        tolerance = 10
        assert abs(center_pos.x() - expected_x) <= tolerance, \
            f"X坐标偏差过大: 期望{expected_x}, 实际{center_pos.x()}"
        assert abs(center_pos.y() - expected_y) <= tolerance, \
            f"Y坐标偏差过大: 期望{expected_y}, 实际{center_pos.y()}"

    def test_position_presets(self, overlay):
        """测试预设位置"""
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()

        positions = ["center", "top_left", "top_right", "bottom_left", "bottom_right"]

        for position in positions:
            overlay.set_position(position)
            widget_rect = overlay.geometry()

            # 验证位置在屏幕边界内
            assert screen_geometry.contains(widget_rect.topLeft()) or \
                   screen_geometry.intersects(widget_rect), \
                   f"位置{position}超出屏幕边界"


class TestRecordingOverlayUIComponents:
    """测试UI组件"""

    def test_required_components_exist(self, overlay):
        """测试必需的UI组件是否存在"""
        # 修正后的组件名称
        required_attrs = [
            'status_indicator',  # 修正：原测试错误地检查status_label
            'time_label',
            'close_button',      # 修正：原测试错误地检查stop_button
            'update_timer',
            'fade_animation',
            'audio_level_bars'
        ]

        for attr in required_attrs:
            assert hasattr(overlay, attr), f"缺少UI组件: {attr}"
            assert getattr(overlay, attr) is not None, f"UI组件未初始化: {attr}"

    def test_status_indicator(self, overlay):
        """测试状态指示器"""
        assert isinstance(overlay.status_indicator, StatusIndicator), \
            "status_indicator应该是StatusIndicator实例"

        # 测试状态切换（使用state而不是current_state）
        overlay.status_indicator.set_state(StatusIndicator.STATE_RECORDING)
        assert overlay.status_indicator.state == StatusIndicator.STATE_RECORDING

        overlay.status_indicator.set_state(StatusIndicator.STATE_PROCESSING)
        assert overlay.status_indicator.state == StatusIndicator.STATE_PROCESSING

        overlay.status_indicator.set_state(StatusIndicator.STATE_COMPLETED)
        assert overlay.status_indicator.state == StatusIndicator.STATE_COMPLETED

    def test_audio_level_bars(self, overlay):
        """测试音频级别条"""
        assert len(overlay.audio_level_bars) == 5, "应该有5个音频级别条"

        for bar in overlay.audio_level_bars:
            assert bar is not None, "音频级别条未初始化"
            assert bar.width() == 4, "级别条宽度应为4"
            assert bar.height() == 18, "级别条高度应为18"

    def test_timer_initial_state(self, overlay):
        """测试定时器初始状态"""
        # 初始时定时器不应该激活
        assert not overlay.update_timer.isActive(), "update_timer初始不应激活"

        if hasattr(overlay, 'breathing_timer'):
            assert not overlay.breathing_timer.isActive(), "breathing_timer初始不应激活"


class TestRecordingOverlayAnimations:
    """测试动画系统"""

    def test_fade_animation_properties(self, overlay):
        """测试淡入淡出动画属性"""
        assert overlay.fade_animation.duration() == 300, "淡入淡出动画时长应为300ms"
        assert overlay.fade_animation.targetObject() == overlay, "动画目标应该是overlay自身"

    def test_breathing_animation(self, overlay):
        """测试呼吸动画"""
        assert hasattr(overlay, 'breathing_phase'), "缺少breathing_phase属性"
        assert hasattr(overlay, 'breathing_timer'), "缺少breathing_timer属性"
        assert hasattr(overlay, 'is_processing'), "缺少is_processing属性"

        # 初始状态
        assert overlay.breathing_phase == 0, "呼吸相位初始值应为0"
        assert not overlay.is_processing, "is_processing初始应为False"

    def test_animation_state_management(self, overlay):
        """测试动画状态管理"""
        # 启动处理动画
        overlay._start_processing_animation_impl()
        assert overlay.is_processing, "启动后is_processing应为True"
        assert overlay.breathing_timer.isActive(), "breathing_timer应该激活"

        # 停止处理动画
        overlay._stop_processing_animation_impl()
        assert not overlay.is_processing, "停止后is_processing应为False"
        assert not overlay.breathing_timer.isActive(), "breathing_timer应该停止"
        assert overlay.breathing_phase == 0, "停止后相位应重置为0"


class TestRecordingOverlayTimerManagement:
    """测试定时器管理"""

    def test_safe_timer_operations(self, overlay):
        """测试定时器安全操作（通过TimerManager）"""
        # _safe_timer_*方法已迁移到TimerManager组件
        # 测试TimerManager的存在
        assert hasattr(overlay, 'timer_manager'), "应该有timer_manager组件"
        assert overlay.timer_manager is not None, "timer_manager应该已初始化"

        # 测试TimerManager的方法
        timer = QTimer()
        callback = Mock()

        # 测试safe_connect
        overlay.timer_manager.safe_connect(timer, callback, "test_timer")

        # 测试safe_start
        overlay.timer_manager.safe_start(timer, 100, callback, "test_timer")
        assert timer.isActive(), "定时器应该启动"

        # 测试safe_stop
        overlay.timer_manager.safe_stop(timer, callback, "test_timer")
        assert not timer.isActive(), "定时器应该停止"

    def test_update_timer_lifecycle(self, overlay):
        """测试update_timer生命周期"""
        # 显示录音时应该启动
        overlay._show_recording_impl()
        assert overlay.update_timer.isActive(), "显示录音时update_timer应启动"

        # 隐藏时应该停止
        overlay._hide_recording_impl()
        assert not overlay.update_timer.isActive(), "隐藏时update_timer应停止"


class TestRecordingOverlayStateManagement:
    """测试状态管理"""

    def test_recording_state(self, overlay):
        """测试录音状态管理"""
        assert not overlay.is_recording, "初始不应在录音"

        # 开始录音
        overlay._show_recording_impl()
        assert overlay.is_recording, "开始录音后状态应更新"
        assert overlay.recording_duration == 0, "录音时长应重置为0"

        # 停止录音
        overlay._hide_recording_impl()
        assert not overlay.is_recording, "停止录音后状态应更新"

    def test_status_transitions(self, overlay):
        """测试状态转换"""
        # 测试录音状态
        overlay._show_recording_impl()
        assert overlay.status_indicator.state == StatusIndicator.STATE_RECORDING

        # 测试处理状态
        overlay._show_processing_impl()
        assert overlay.status_indicator.state == StatusIndicator.STATE_PROCESSING

        # 测试完成状态
        overlay._show_completed_impl(500)
        assert overlay.status_indicator.state == StatusIndicator.STATE_COMPLETED


class TestRecordingOverlayAudioVisualization:
    """测试音频可视化"""

    def test_audio_level_update(self, overlay):
        """测试音频级别更新"""
        # 需要先设置录音状态，因为AudioVisualizer只在录音时更新级别
        overlay.is_recording = True

        # 测试低音量（AudioVisualizer会对级别进行标准化处理）
        overlay._update_audio_level_impl(0.2)
        # 验证级别已更新（使用get_current_level获取）
        assert overlay.audio_visualizer.current_audio_level > 0

        # 测试中等音量
        overlay._update_audio_level_impl(0.5)
        assert overlay.audio_visualizer.current_audio_level > 0

        # 测试高音量（将被限制在1.0）
        overlay._update_audio_level_impl(0.9)
        assert overlay.audio_visualizer.current_audio_level > 0
        assert overlay.audio_visualizer.current_audio_level <= 1.0

    def test_audio_level_bars_update(self, overlay):
        """测试音频级别条更新（通过AudioVisualizer）"""
        # _update_audio_level_bars已迁移到AudioVisualizer组件
        # 测试AudioVisualizer的存在
        assert hasattr(overlay, 'audio_visualizer'), "应该有audio_visualizer组件"
        assert overlay.audio_visualizer is not None, "audio_visualizer应该已初始化"

        # 设置录音状态
        overlay.is_recording = True

        # 设置不同的音量级别
        levels = [0.2, 0.4, 0.6, 0.8, 1.0]

        for level in levels:
            # 通过AudioVisualizer的公共方法更新级别条
            overlay.audio_visualizer.update_audio_level(level, is_recording=True)
            # 验证级别已更新
            assert overlay.audio_visualizer.current_audio_level > 0
            # 无法直接验证样式，但可以确保方法执行无异常


class TestRecordingOverlaySingleton:
    """测试单例模式"""

    def test_singleton_creation(self, qapp):
        """测试单例创建"""
        RecordingOverlay.reset_singleton()

        overlay1 = RecordingOverlay()
        overlay2 = RecordingOverlay()

        assert overlay1 is overlay2, "应该返回同一个实例"

    def test_singleton_reset(self, qapp):
        """测试单例重置"""
        overlay1 = RecordingOverlay()
        instance_id_1 = id(overlay1)

        RecordingOverlay.reset_singleton()

        overlay2 = RecordingOverlay()
        instance_id_2 = id(overlay2)

        assert instance_id_1 != instance_id_2, "重置后应该创建新实例"


class TestRecordingOverlayCleanup:
    """测试资源清理"""

    def test_cleanup_resources(self, overlay):
        """测试资源清理"""
        # 启动一些资源
        overlay._show_recording_impl()
        overlay._start_processing_animation_impl()

        # 清理资源
        overlay.cleanup_resources()

        # 验证定时器停止或已被删除
        if overlay.update_timer is not None:
            assert not overlay.update_timer.isActive(), "清理后update_timer应停止"

        if hasattr(overlay, 'breathing_timer') and overlay.breathing_timer is not None:
            assert not overlay.breathing_timer.isActive(), "清理后breathing_timer应停止"

    def test_cleanup(self, overlay):
        """测试完整清理"""
        overlay._show_recording_impl()

        overlay.cleanup()

        # 验证清理后状态（cleanup主要是清理资源，不一定重置所有状态）
        # cleanup会隐藏窗口并停止定时器
        assert not overlay.isVisible(), "清理后窗口应该隐藏"

        # 验证定时器已停止
        if overlay.update_timer is not None:
            assert not overlay.update_timer.isActive(), "清理后定时器应停止"


class TestRecordingOverlayThreadSafety:
    """测试线程安全性"""

    def test_signal_based_methods(self, overlay):
        """测试基于信号的线程安全方法"""
        # Qt信号的emit是只读的，不能patch
        # 改为连接槽函数来验证信号是否被发射

        # 测试show_recording信号
        mock_slot = Mock()
        overlay.show_recording_requested.connect(mock_slot)
        overlay.show_recording()
        # 给Qt一点时间处理信号
        QApplication.processEvents()
        mock_slot.assert_called_once()
        overlay.show_recording_requested.disconnect(mock_slot)

        # 测试hide_recording信号
        mock_slot = Mock()
        overlay.hide_recording_requested.connect(mock_slot)
        overlay.hide_recording()
        QApplication.processEvents()
        mock_slot.assert_called()  # 可能被调用多次
        overlay.hide_recording_requested.disconnect(mock_slot)

        # 测试show_processing信号
        mock_slot = Mock()
        overlay.show_processing_requested.connect(mock_slot)
        overlay.show_processing()
        QApplication.processEvents()
        mock_slot.assert_called_once()
        overlay.show_processing_requested.disconnect(mock_slot)

        # 测试start_processing_animation信号
        mock_slot = Mock()
        overlay.start_processing_animation_requested.connect(mock_slot)
        overlay.start_processing_animation()
        QApplication.processEvents()
        mock_slot.assert_called_once()
        overlay.start_processing_animation_requested.disconnect(mock_slot)

        # 测试stop_processing_animation信号
        mock_slot = Mock()
        overlay.stop_processing_animation_requested.connect(mock_slot)
        overlay.stop_processing_animation()
        QApplication.processEvents()
        mock_slot.assert_called_once()
        overlay.stop_processing_animation_requested.disconnect(mock_slot)


# 综合测试
def test_comprehensive_overlay_functionality(overlay):
    """综合测试overlay功能"""
    # 模拟完整的使用流程
    # 1. 显示录音
    overlay._show_recording_impl()
    assert overlay.isVisible(), "显示录音后应可见"
    assert overlay.is_recording, "应处于录音状态"

    # 2. 更新音频级别（AudioVisualizer会对级别进行标准化处理）
    overlay._update_audio_level_impl(0.7)
    # 验证AudioVisualizer的级别已更新（可能被标准化或限制）
    assert overlay.audio_visualizer.current_audio_level > 0, "音频级别应已更新"
    assert overlay.audio_visualizer.current_audio_level <= 1.0, "音频级别应不超过1.0"

    # 3. 显示处理状态
    overlay._show_processing_impl()
    # _show_processing_impl设置状态指示器，但不启动动画
    assert overlay.status_indicator.state == StatusIndicator.STATE_PROCESSING, "状态应为处理中"

    # 如果要检查is_processing，需要启动处理动画
    overlay._start_processing_animation_impl()
    assert overlay.is_processing, "启动动画后应处于处理状态"

    # 4. 显示完成
    overlay._show_completed_impl(100)
    assert overlay.status_indicator.state == StatusIndicator.STATE_COMPLETED

    # 5. 清理
    overlay.cleanup()
    assert not overlay.isVisible(), "清理后窗口应隐藏"
    # cleanup不会重置所有状态，只是清理资源
