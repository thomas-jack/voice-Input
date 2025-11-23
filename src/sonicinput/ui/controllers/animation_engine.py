"""动画引擎

统一管理所有UI动画效果，提供流畅的视觉体验。
支持淡入淡出、滑动、弹跳等动画效果。
"""

from enum import Enum
from typing import Callable, Dict, Optional

from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation, Signal
from PySide6.QtWidgets import QGraphicsOpacityEffect, QWidget

from ...utils import app_logger
from ...utils.constants import UI


class AnimationType(Enum):
    """动画类型枚举"""

    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    SLIDE_IN = "slide_in"
    SLIDE_OUT = "slide_out"
    BOUNCE = "bounce"
    PULSE = "pulse"
    SCALE = "scale"


class AnimationDirection(Enum):
    """动画方向枚举"""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class AnimationEngine(QObject):
    """UI动画引擎

    统一管理所有UI组件的动画效果。
    提供流畅、性能优化的动画体验。
    """

    # 动画完成信号
    animation_finished = Signal(str)  # animation_id

    def __init__(self, parent: Optional[QObject] = None):
        """初始化动画引擎

        Args:
            parent: 父对象
        """
        super().__init__(parent)
        self._active_animations: Dict[str, QPropertyAnimation] = {}
        self._animation_counter = 0

        app_logger.log_audio_event("AnimationEngine initialized", {})

    def fade_in(
        self, widget: QWidget, duration: int = None, callback: Optional[Callable] = None
    ) -> str:
        """淡入动画

        Args:
            widget: 要执行动画的组件
            duration: 动画持续时间（毫秒）
            callback: 动画完成回调

        Returns:
            动画ID
        """
        duration = duration or UI.FADE_DURATION
        return self._create_opacity_animation(
            widget, 0.0, 1.0, duration, AnimationType.FADE_IN, callback
        )

    def fade_out(
        self, widget: QWidget, duration: int = None, callback: Optional[Callable] = None
    ) -> str:
        """淡出动画

        Args:
            widget: 要执行动画的组件
            duration: 动画持续时间（毫秒）
            callback: 动画完成回调

        Returns:
            动画ID
        """
        duration = duration or UI.FADE_DURATION
        return self._create_opacity_animation(
            widget, 1.0, 0.0, duration, AnimationType.FADE_OUT, callback
        )

    def slide_in(
        self,
        widget: QWidget,
        direction: AnimationDirection = AnimationDirection.UP,
        duration: int = None,
        callback: Optional[Callable] = None,
    ) -> str:
        """滑入动画

        Args:
            widget: 要执行动画的组件
            direction: 滑入方向
            duration: 动画持续时间（毫秒）
            callback: 动画完成回调

        Returns:
            动画ID
        """
        duration = duration or UI.SLIDE_DURATION
        return self._create_slide_animation(widget, direction, True, duration, callback)

    def slide_out(
        self,
        widget: QWidget,
        direction: AnimationDirection = AnimationDirection.DOWN,
        duration: int = None,
        callback: Optional[Callable] = None,
    ) -> str:
        """滑出动画

        Args:
            widget: 要执行动画的组件
            direction: 滑出方向
            duration: 动画持续时间（毫秒）
            callback: 动画完成回调

        Returns:
            动画ID
        """
        duration = duration or UI.SLIDE_DURATION
        return self._create_slide_animation(
            widget, direction, False, duration, callback
        )

    def bounce(
        self,
        widget: QWidget,
        intensity: float = 1.2,
        duration: int = None,
        callback: Optional[Callable] = None,
    ) -> str:
        """弹跳动画

        Args:
            widget: 要执行动画的组件
            intensity: 弹跳强度（缩放倍数）
            duration: 动画持续时间（毫秒）
            callback: 动画完成回调

        Returns:
            动画ID
        """
        duration = duration or UI.BOUNCE_DURATION
        return self._create_bounce_animation(widget, intensity, duration, callback)

    def pulse(
        self,
        widget: QWidget,
        cycles: int = 3,
        intensity: float = 0.7,
        callback: Optional[Callable] = None,
    ) -> str:
        """脉冲动画

        Args:
            widget: 要执行动画的组件
            cycles: 脉冲循环次数
            intensity: 脉冲强度（最小透明度）
            callback: 动画完成回调

        Returns:
            动画ID
        """
        return self._create_pulse_animation(widget, cycles, intensity, callback)

    def scale_animation(
        self,
        widget: QWidget,
        from_scale: float,
        to_scale: float,
        duration: int = None,
        callback: Optional[Callable] = None,
    ) -> str:
        """缩放动画

        Args:
            widget: 要执行动画的组件
            from_scale: 起始缩放倍数
            to_scale: 结束缩放倍数
            duration: 动画持续时间（毫秒）
            callback: 动画完成回调

        Returns:
            动画ID
        """
        duration = duration or UI.FADE_DURATION
        return self._create_scale_animation(
            widget, from_scale, to_scale, duration, callback
        )

    def stop_animation(self, animation_id: str) -> bool:
        """停止指定动画

        Args:
            animation_id: 动画ID

        Returns:
            是否成功停止
        """
        try:
            if animation_id in self._active_animations:
                animation = self._active_animations[animation_id]
                animation.stop()
                del self._active_animations[animation_id]

                app_logger.log_audio_event(
                    "Animation stopped", {"animation_id": animation_id}
                )
                return True
            return False

        except Exception as e:
            app_logger.log_error(e, f"stop_animation_{animation_id}")
            return False

    def stop_all_animations(self) -> int:
        """停止所有动画

        Returns:
            停止的动画数量
        """
        try:
            count = len(self._active_animations)
            for animation in list(self._active_animations.values()):
                animation.stop()
            self._active_animations.clear()

            app_logger.log_audio_event(
                "All animations stopped", {"stopped_count": count}
            )
            return count

        except Exception as e:
            app_logger.log_error(e, "stop_all_animations")
            return 0

    def get_active_animations(self) -> Dict[str, str]:
        """获取活跃的动画

        Returns:
            动画ID到状态的映射
        """
        try:
            return {
                animation_id: animation.state().name
                for animation_id, animation in self._active_animations.items()
            }
        except Exception as e:
            app_logger.log_error(e, "get_active_animations")
            return {}

    def _create_opacity_animation(
        self,
        widget: QWidget,
        start_opacity: float,
        end_opacity: float,
        duration: int,
        animation_type: AnimationType,
        callback: Optional[Callable] = None,
    ) -> str:
        """创建透明度动画

        Args:
            widget: 目标组件
            start_opacity: 起始透明度
            end_opacity: 结束透明度
            duration: 持续时间
            animation_type: 动画类型
            callback: 完成回调

        Returns:
            动画ID
        """
        try:
            # 确保组件有透明度效果
            if widget.graphicsEffect() is None or not isinstance(
                widget.graphicsEffect(), QGraphicsOpacityEffect
            ):
                effect = QGraphicsOpacityEffect()
                widget.setGraphicsEffect(effect)
            else:
                effect = widget.graphicsEffect()

            # 创建动画
            animation_id = self._generate_animation_id(animation_type.value)
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(duration)
            animation.setStartValue(start_opacity)
            animation.setEndValue(end_opacity)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)

            # 设置完成回调
            def on_finished():
                self._on_animation_finished(animation_id, callback)

            animation.finished.connect(on_finished)

            # 启动动画
            self._active_animations[animation_id] = animation
            animation.start()

            app_logger.log_audio_event(
                "Opacity animation started",
                {
                    "animation_id": animation_id,
                    "type": animation_type.value,
                    "duration": duration,
                },
            )

            return animation_id

        except Exception as e:
            app_logger.log_error(e, "create_opacity_animation")
            return ""

    def _create_slide_animation(
        self,
        widget: QWidget,
        direction: AnimationDirection,
        slide_in: bool,
        duration: int,
        callback: Optional[Callable] = None,
    ) -> str:
        """创建滑动动画

        Args:
            widget: 目标组件
            direction: 滑动方向
            slide_in: 是否为滑入
            duration: 持续时间
            callback: 完成回调

        Returns:
            动画ID
        """
        try:
            # 计算起始和结束位置
            current_pos = widget.pos()

            if slide_in:
                end_pos = current_pos
                if direction == AnimationDirection.UP:
                    start_pos = (
                        current_pos + widget.parent().rect().bottomLeft() - current_pos
                    )
                elif direction == AnimationDirection.DOWN:
                    start_pos = (
                        current_pos - widget.parent().rect().topLeft() + current_pos
                    )
                elif direction == AnimationDirection.LEFT:
                    start_pos = (
                        current_pos + widget.parent().rect().topRight() - current_pos
                    )
                else:  # RIGHT
                    start_pos = (
                        current_pos + widget.parent().rect().topLeft() - current_pos
                    )
            else:
                start_pos = current_pos
                if direction == AnimationDirection.UP:
                    end_pos = (
                        current_pos - widget.parent().rect().topLeft() + current_pos
                    )
                elif direction == AnimationDirection.DOWN:
                    end_pos = (
                        current_pos + widget.parent().rect().bottomLeft() - current_pos
                    )
                elif direction == AnimationDirection.LEFT:
                    end_pos = (
                        current_pos + widget.parent().rect().topLeft() - current_pos
                    )
                else:  # RIGHT
                    end_pos = (
                        current_pos + widget.parent().rect().topRight() - current_pos
                    )

            # 创建位置动画
            animation_id = self._generate_animation_id("slide")
            animation = QPropertyAnimation(widget, b"pos")
            animation.setDuration(duration)
            animation.setStartValue(start_pos)
            animation.setEndValue(end_pos)
            animation.setEasingCurve(QEasingCurve.Type.OutExpo)

            # 设置完成回调
            def on_finished():
                self._on_animation_finished(animation_id, callback)

            animation.finished.connect(on_finished)

            # 启动动画
            self._active_animations[animation_id] = animation
            widget.move(start_pos)
            animation.start()

            return animation_id

        except Exception as e:
            app_logger.log_error(e, "create_slide_animation")
            return ""

    def _create_bounce_animation(
        self,
        widget: QWidget,
        intensity: float,
        duration: int,
        callback: Optional[Callable] = None,
    ) -> str:
        """创建弹跳动画

        Args:
            widget: 目标组件
            intensity: 弹跳强度
            duration: 持续时间
            callback: 完成回调

        Returns:
            动画ID
        """
        try:
            # 这里使用简化的弹跳效果，通过缩放实现
            animation_id = self._generate_animation_id("bounce")

            # 创建缩放动画序列
            def create_bounce_sequence():
                # 第一阶段：放大
                scale_up = QPropertyAnimation(widget, b"geometry")
                scale_up.setDuration(duration // 3)
                scale_up.setStartValue(widget.geometry())

                enlarged_rect = widget.geometry()
                center = enlarged_rect.center()
                enlarged_rect.setSize(widget.size() * intensity)
                enlarged_rect.moveCenter(center)
                scale_up.setEndValue(enlarged_rect)
                scale_up.setEasingCurve(QEasingCurve.Type.OutBack)

                # 第二阶段：恢复
                scale_down = QPropertyAnimation(widget, b"geometry")
                scale_down.setDuration(duration * 2 // 3)
                scale_down.setStartValue(enlarged_rect)
                scale_down.setEndValue(widget.geometry())
                scale_down.setEasingCurve(QEasingCurve.Type.InBack)

                # 连接动画
                def start_scale_down():
                    scale_down.start()
                    self._active_animations[animation_id] = scale_down

                def on_finished():
                    self._on_animation_finished(animation_id, callback)

                scale_up.finished.connect(start_scale_down)
                scale_down.finished.connect(on_finished)

                # 启动第一阶段
                self._active_animations[animation_id] = scale_up
                scale_up.start()

            create_bounce_sequence()
            return animation_id

        except Exception as e:
            app_logger.log_error(e, "create_bounce_animation")
            return ""

    def _create_pulse_animation(
        self,
        widget: QWidget,
        cycles: int,
        intensity: float,
        callback: Optional[Callable] = None,
    ) -> str:
        """创建脉冲动画

        Args:
            widget: 目标组件
            cycles: 循环次数
            intensity: 强度
            callback: 完成回调

        Returns:
            动画ID
        """
        try:
            animation_id = self._generate_animation_id("pulse")

            # 确保组件有透明度效果
            if widget.graphicsEffect() is None or not isinstance(
                widget.graphicsEffect(), QGraphicsOpacityEffect
            ):
                effect = QGraphicsOpacityEffect()
                widget.setGraphicsEffect(effect)
            else:
                effect = widget.graphicsEffect()

            # 创建脉冲动画
            animation = QPropertyAnimation(effect, b"opacity")
            animation.setDuration(600 * cycles)  # 每个周期600ms
            animation.setStartValue(1.0)
            animation.setKeyValueAt(0.5, intensity)
            animation.setEndValue(1.0)
            animation.setLoopCount(cycles)
            animation.setEasingCurve(QEasingCurve.Type.InOutSine)

            # 设置完成回调
            def on_finished():
                self._on_animation_finished(animation_id, callback)

            animation.finished.connect(on_finished)

            # 启动动画
            self._active_animations[animation_id] = animation
            animation.start()

            return animation_id

        except Exception as e:
            app_logger.log_error(e, "create_pulse_animation")
            return ""

    def _create_scale_animation(
        self,
        widget: QWidget,
        from_scale: float,
        to_scale: float,
        duration: int,
        callback: Optional[Callable] = None,
    ) -> str:
        """创建缩放动画

        Args:
            widget: 目标组件
            from_scale: 起始缩放
            to_scale: 结束缩放
            duration: 持续时间
            callback: 完成回调

        Returns:
            动画ID
        """
        try:
            animation_id = self._generate_animation_id("scale")

            # 计算几何形状
            original_rect = widget.geometry()
            center = original_rect.center()

            from_rect = original_rect.scaled(from_scale, from_scale)
            from_rect.moveCenter(center)

            to_rect = original_rect.scaled(to_scale, to_scale)
            to_rect.moveCenter(center)

            # 创建几何动画
            animation = QPropertyAnimation(widget, b"geometry")
            animation.setDuration(duration)
            animation.setStartValue(from_rect)
            animation.setEndValue(to_rect)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)

            # 设置完成回调
            def on_finished():
                self._on_animation_finished(animation_id, callback)

            animation.finished.connect(on_finished)

            # 启动动画
            self._active_animations[animation_id] = animation
            widget.setGeometry(from_rect)
            animation.start()

            return animation_id

        except Exception as e:
            app_logger.log_error(e, "create_scale_animation")
            return ""

    def _generate_animation_id(self, prefix: str) -> str:
        """生成动画ID

        Args:
            prefix: ID前缀

        Returns:
            唯一的动画ID
        """
        self._animation_counter += 1
        return f"{prefix}_{self._animation_counter}"

    def _on_animation_finished(
        self, animation_id: str, callback: Optional[Callable] = None
    ) -> None:
        """动画完成处理

        Args:
            animation_id: 动画ID
            callback: 完成回调
        """
        try:
            # 从活跃动画列表中移除
            if animation_id in self._active_animations:
                del self._active_animations[animation_id]

            # 发出完成信号
            self.animation_finished.emit(animation_id)

            # 执行回调
            if callback:
                callback()

            app_logger.log_audio_event(
                "Animation finished", {"animation_id": animation_id}
            )

        except Exception as e:
            app_logger.log_error(e, f"animation_finished_{animation_id}")
