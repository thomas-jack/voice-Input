"""动画控制器 - 单一职责：管理所有动画效果"""

import math
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget

from ...utils import app_logger


class AnimationController:
    """动画控制器 - 管理RecordingOverlay的所有动画

    职责：
    1. 淡入淡出动画
    2. 呼吸动画（处理状态）
    3. 状态动画
    """

    def __init__(self, parent_widget: QWidget):
        """初始化动画控制器

        Args:
            parent_widget: 父窗口组件（用于窗口透明度动画）
        """
        self.parent = parent_widget

        # 淡入淡出动画
        self.fade_animation = QPropertyAnimation(self.parent, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # 呼吸动画（用于处理状态）
        self.breathing_phase = 0
        self.breathing_timer = QTimer()
        self.breathing_timer.timeout.connect(self._update_breathing)
        self.is_processing = False

        # 状态动画
        self.status_opacity = 1.0
        self.status_animation = QPropertyAnimation(self.parent, b"windowOpacity")
        self.status_animation.setDuration(1000)
        self.status_animation.setEasingCurve(QEasingCurve.Type.InOutSine)

        app_logger.log_audio_event("AnimationController initialized", {})

    def start_fade_in(self) -> None:
        """启动淡入动画"""
        try:
            self.fade_animation.stop()
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.start()
        except Exception as e:
            app_logger.log_error(e, "animation_fade_in")

    def start_fade_out(self, callback=None) -> None:
        """启动淡出动画

        Args:
            callback: 动画完成后的回调函数
        """
        try:
            self.fade_animation.stop()
            if callback:
                self.fade_animation.finished.connect(callback)
            self.fade_animation.setStartValue(1.0)
            self.fade_animation.setEndValue(0.0)
            self.fade_animation.start()
        except Exception as e:
            app_logger.log_error(e, "animation_fade_out")

    def start_breathing_animation(self) -> None:
        """启动呼吸动画（用于处理状态）"""
        try:
            self.is_processing = True
            if not self.breathing_timer.isActive():
                self.breathing_timer.start(80)  # 80ms间隔
                app_logger.log_audio_event("Breathing animation started", {})
        except Exception as e:
            app_logger.log_error(e, "breathing_animation_start")

    def stop_breathing_animation(self) -> None:
        """停止呼吸动画"""
        try:
            self.is_processing = False
            if self.breathing_timer.isActive():
                self.breathing_timer.stop()
            self.breathing_phase = 0
            # 请求重绘以清除动画效果
            if hasattr(self.parent, 'update'):
                self.parent.update()
            app_logger.log_audio_event("Breathing animation stopped", {})
        except Exception as e:
            app_logger.log_error(e, "breathing_animation_stop")

    def _update_breathing(self) -> None:
        """更新呼吸效果（内部方法）"""
        # 状态同步检查
        if not self.is_processing or not self.breathing_timer.isActive():
            if self.breathing_timer.isActive():
                self.breathing_timer.stop()
            self.is_processing = False
            self.breathing_phase = 0
            return

        if self.is_processing:
            self.breathing_phase += 0.15  # 呼吸速度
            if self.breathing_phase >= 2 * math.pi:
                self.breathing_phase = 0

            # 请求重绘
            if hasattr(self.parent, 'update'):
                self.parent.update()

    def get_breathing_intensity(self) -> float:
        """获取当前呼吸动画强度（用于绘制）

        Returns:
            0.0-1.0之间的强度值
        """
        if not self.is_processing:
            return 0.0

        # 使用正弦函数生成平滑的呼吸效果
        intensity = (math.sin(self.breathing_phase) + 1) / 2  # 0.0-1.0
        return intensity

    def is_animation_active(self) -> bool:
        """检查是否有动画正在运行

        Returns:
            是否有动画活跃
        """
        return (self.fade_animation.state() == QPropertyAnimation.State.Running or
                self.breathing_timer.isActive() or
                self.status_animation.state() == QPropertyAnimation.State.Running)

    def stop_all_animations(self) -> None:
        """停止所有动画"""
        try:
            # 停止淡入淡出动画
            if self.fade_animation.state() == QPropertyAnimation.State.Running:
                self.fade_animation.stop()

            # 停止呼吸动画
            if self.breathing_timer.isActive():
                self.breathing_timer.stop()
                self.is_processing = False
                self.breathing_phase = 0

            # 停止状态动画
            if self.status_animation.state() == QPropertyAnimation.State.Running:
                self.status_animation.stop()

            app_logger.log_audio_event("All animations stopped", {})

        except Exception as e:
            app_logger.log_error(e, "stop_all_animations")

    def cleanup(self) -> None:
        """清理资源"""
        try:
            self.stop_all_animations()

            # 停止并清理定时器
            if self.breathing_timer.isActive():
                self.breathing_timer.stop()

            # 尝试断开信号连接
            try:
                self.breathing_timer.timeout.disconnect()
            except:
                pass

            app_logger.log_audio_event("AnimationController cleaned up", {})

        except Exception as e:
            app_logger.log_error(e, "animation_controller_cleanup")
