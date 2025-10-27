"""Animation controller for RecordingOverlay"""

import math
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QBrush, QColor, QRadialGradient
from PyQt6.QtCore import Qt
from typing import TYPE_CHECKING
from ...utils import app_logger

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget


class AnimationController:
    """Controls animations for the recording overlay

    Manages:
    - Breathing animation for processing state
    - Fade in/out animations
    - Animation state synchronization
    """

    def __init__(self, widget: 'QWidget'):
        """Initialize animation controller

        Args:
            widget: The widget to apply animations to
        """
        self.widget = widget
        self.breathing_phase = 0
        self.is_processing = False

        # 呼吸动画定时器
        self.breathing_timer = QTimer()
        self.breathing_timer.timeout.connect(self.update_breathing)

        # 淡入淡出动画
        self.fade_animation = QPropertyAnimation(widget, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # 状态动画
        self.status_opacity = 1.0
        self.status_animation = QPropertyAnimation(widget, b"windowOpacity")
        self.status_animation.setDuration(1000)
        self.status_animation.setEasingCurve(QEasingCurve.Type.InOutSine)

        app_logger.log_audio_event("Animation controller initialized", {})

    def start_breathing_animation(self, interval: int = 80) -> None:
        """启动呼吸动画

        Args:
            interval: Animation update interval in milliseconds
        """
        self.is_processing = True
        if not self.breathing_timer.isActive():
            self.breathing_timer.start(interval)
            app_logger.log_audio_event("Breathing animation started", {"interval": interval})

    def stop_breathing_animation(self) -> None:
        """停止呼吸动画"""
        self.is_processing = False
        if self.breathing_timer.isActive():
            self.breathing_timer.stop()
            app_logger.log_audio_event("Breathing animation stopped", {})
        self.breathing_phase = 0

    def update_breathing(self) -> None:
        """更新呼吸效果"""
        # 状态同步检查：确保动画状态与处理状态一致
        if not self.is_processing or not self.breathing_timer.isActive():
            # 如果状态不一致，停止动画
            if self.breathing_timer.isActive():
                self.breathing_timer.stop()
            self.is_processing = False
            self.breathing_phase = 0
            return

        if self.is_processing:
            self.breathing_phase += 0.15  # 呼吸速度
            # 修复π精度：使用标准数学常量而非硬编码值
            if self.breathing_phase >= 2 * math.pi:  # 使用准确的2π
                self.breathing_phase = 0
            self.widget.update()  # 重绘界面

    def paint_breathing_effect(self, painter: QPainter, rect) -> None:
        """绘制呼吸发光效果

        Args:
            painter: QPainter instance for drawing
            rect: Widget rectangle to draw in
        """
        if not self.is_processing:
            return

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 计算呼吸效果的透明度
        breathing_intensity = (math.sin(self.breathing_phase) + 1) / 2  # 0 到 1
        # 确保透明度在有效范围内 (0-255)
        alpha = max(0, min(255, int(30 + 50 * breathing_intensity)))  # 透明度在30-80之间

        # 创建径向渐变效果 - 使用安全的颜色值
        width = rect.width()
        height = rect.height()
        gradient = QRadialGradient(width / 2, height / 2, min(width, height) / 2)

        # 确保所有RGB和Alpha值都在有效范围 (0-255)
        center_color = QColor(
            max(0, min(255, 76)),
            max(0, min(255, 175)),
            max(0, min(255, 80)),
            alpha
        )
        gradient.setColorAt(0, center_color)  # 中心亮绿色

        # 修复除法稳定性：确保边缘透明度不为零且在有效范围内
        edge_alpha = max(1, min(255, alpha // 3))  # 边缘淡绿色，确保至少为1
        edge_color = QColor(
            max(0, min(255, 76)),
            max(0, min(255, 175)),
            max(0, min(255, 80)),
            edge_alpha
        )
        gradient.setColorAt(0.7, edge_color)
        gradient.setColorAt(1, QColor(76, 175, 80, 0))  # 完全透明

        # 绘制呼吸发光效果
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(rect)

    def ensure_animation_state(self, should_animate: bool, context: str = "") -> None:
        """确保动画状态与期望状态一致

        Args:
            should_animate: Whether animation should be active
            context: Context description for logging
        """
        try:
            current_animating = self.breathing_timer.isActive()

            if should_animate and not current_animating:
                # 需要开始动画但当前没有动画
                self.start_breathing_animation()
                app_logger.log_audio_event(f"Animation started: {context}", {
                    "previous_state": current_animating,
                    "new_state": should_animate,
                    "is_processing": self.is_processing
                })
            elif not should_animate and current_animating:
                # 需要停止动画但当前有动画
                self.stop_breathing_animation()
                app_logger.log_audio_event(f"Animation stopped: {context}", {
                    "previous_state": current_animating,
                    "new_state": should_animate,
                    "is_processing": self.is_processing
                })

            # 延迟验证状态一致性，避免竞态条件
            def delayed_verification():
                try:
                    final_animating = self.breathing_timer.isActive()
                    # 检测并修复状态不一致
                    if final_animating != should_animate:
                        app_logger.log_audio_event(
                            f"Animation state mismatch in {context}: "
                            f"expected {should_animate}, got {final_animating} - fixing",
                            {
                                "expected": should_animate,
                                "actual": final_animating,
                                "context": context
                            }
                        )

                        # 修复状态不一致
                        if should_animate and not final_animating:
                            # 应该动画但没有动画 - 启动动画
                            self.start_breathing_animation()
                            app_logger.log_audio_event(f"Fixed: started animation for {context}", {})
                        elif not should_animate and final_animating:
                            # 不应该动画但有动画 - 停止动画
                            self.stop_breathing_animation()
                            app_logger.log_audio_event(f"Fixed: stopped animation for {context}", {})
                except Exception as e:
                    app_logger.log_error(e, f"delayed_verification_{context}")

            # 使用Qt单次定时器延迟验证，给信号处理时间
            QTimer.singleShot(50, delayed_verification)

        except Exception as e:
            app_logger.log_error(e, f"ensure_animation_state_{context}")

    def cleanup(self) -> None:
        """清理动画资源"""
        try:
            if self.breathing_timer.isActive():
                self.breathing_timer.stop()
            if self.fade_animation.state() == QPropertyAnimation.State.Running:
                self.fade_animation.stop()
            if self.status_animation.state() == QPropertyAnimation.State.Running:
                self.status_animation.stop()

            app_logger.log_audio_event("Animation controller cleaned up", {})
        except Exception as e:
            app_logger.log_error(e, "animation_controller_cleanup")
