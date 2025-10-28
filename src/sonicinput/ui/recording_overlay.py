"""Recording Overlay Window"""

import math
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QFrame, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor
from ..utils import app_logger
from ..core.interfaces import IConfigService
from .overlay import StatusIndicator, CloseButton
from .recording_overlay_utils.position_manager import PositionManager


class RecordingOverlay(QWidget):
    """Recording Overlay Window with Qt-safe singleton pattern"""

    # Qt-safe singleton implementation (no locks needed - Qt main thread only)
    _instance = None
    _initialized = False

    # 信号 (移除stop_recording_requested，因为用ESC键代替)

    # 线程安全信号
    show_recording_requested = Signal()
    hide_recording_requested = Signal()
    set_status_requested = Signal(str)
    update_waveform_requested = Signal(object)
    update_audio_level_requested = Signal(float)  # 音频级别更新
    start_processing_animation_requested = Signal()
    stop_processing_animation_requested = Signal()
    hide_recording_delayed_requested = Signal(int)  # 延迟隐藏（毫秒）

    def __new__(cls, parent=None):
        """Qt-safe singleton pattern (main thread only, no lock needed)"""
        if cls._instance is None:
            try:
                app_logger.log_audio_event("Creating new RecordingOverlay singleton instance", {})
                cls._instance = super().__new__(cls)
                app_logger.log_audio_event("RecordingOverlay singleton instance created successfully", {})
            except Exception as e:
                app_logger.log_error(e, "RecordingOverlay_singleton_creation")
                # 即使创建失败，也不要让整个应用崩溃
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, parent=None):
        """Qt-safe initialization (no locks needed - main thread only)"""
        # Prevent re-initialization
        if self._initialized:
            app_logger.log_audio_event("RecordingOverlay already initialized, resetting for reuse", {})
            try:
                self._reset_for_reuse()
            except Exception as e:
                app_logger.log_error(e, "RecordingOverlay_reset_for_reuse")
            return

        try:
            app_logger.log_audio_event("Starting RecordingOverlay initialization", {})
            super().__init__(parent)
            self._initialized = True
            app_logger.log_audio_event("RecordingOverlay parent initialization completed", {})
        except Exception as e:
            app_logger.log_error(e, "RecordingOverlay_parent_initialization")
            # 尝试基本的初始化
            try:
                super().__init__(parent)
                self._initialized = True
            except Exception as e2:
                app_logger.log_error(e2, "RecordingOverlay_fallback_initialization")
                raise

        try:
            app_logger.log_audio_event("Setting up RecordingOverlay state variables", {})
            self.is_recording = False
            self.current_status = "Ready"
            self.recording_duration = 0
            app_logger.log_audio_event("RecordingOverlay state variables initialized", {})
        except Exception as e:
            app_logger.log_error(e, "RecordingOverlay_state_setup")
            raise

        try:
            app_logger.log_audio_event("Setting up RecordingOverlay window attributes", {})
            # 设置窗口属性
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool |
                Qt.WindowType.WindowDoesNotAcceptFocus
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            app_logger.log_audio_event("RecordingOverlay window attributes configured", {})
        except Exception as e:
            app_logger.log_error(e, "RecordingOverlay_window_attributes")
            raise

        try:
            app_logger.log_audio_event("Starting RecordingOverlay UI setup", {})
            # 初始化UI
            self.setup_overlay_ui()
            app_logger.log_audio_event("RecordingOverlay UI setup completed", {})
        except Exception as e:
            app_logger.log_error(e, "RecordingOverlay_UI_setup")
            raise

        try:
            app_logger.log_audio_event("Setting up RecordingOverlay timers and animations", {})
            # 定时器
            self.update_timer = QTimer()
            self.update_timer.timeout.connect(self.update_recording_time)

            # 动画
            self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
            self.fade_animation.setDuration(300)
            self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            app_logger.log_audio_event("RecordingOverlay timers and animations configured", {})
        except Exception as e:
            app_logger.log_error(e, "RecordingOverlay_timers_animations")
            # 这些组件失败不应该阻止基本功能
            pass

        try:
            app_logger.log_audio_event("Setting up RecordingOverlay advanced animations", {})
            # 呼吸动画（用于处理状态） - 替换旋转动画
            self.breathing_phase = 0
            self.breathing_timer = QTimer()
            self.breathing_timer.timeout.connect(self.update_breathing)
            self.is_processing = False

            # 现代化状态指示器动画
            self.status_opacity = 1.0
            self.status_animation = QPropertyAnimation(self, b"windowOpacity")
            self.status_animation.setDuration(1000)
            self.status_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
            app_logger.log_audio_event("RecordingOverlay advanced animations configured", {})
        except Exception as e:
            app_logger.log_error(e, "RecordingOverlay_advanced_animations")
            # 动画失败不应该阻止基本功能
            pass

        try:
            app_logger.log_audio_event("Connecting RecordingOverlay thread-safe signals", {})
            # 连接线程安全信号
            self.show_recording_requested.connect(self._show_recording_impl)
            self.hide_recording_requested.connect(self._hide_recording_impl)
            self.set_status_requested.connect(self._set_status_text_impl)
            self.update_waveform_requested.connect(self._update_waveform_impl)
            self.update_audio_level_requested.connect(self._update_audio_level_impl)
            self.start_processing_animation_requested.connect(self._start_processing_animation_impl)
            self.stop_processing_animation_requested.connect(self._stop_processing_animation_impl)
            self.hide_recording_delayed_requested.connect(self._hide_recording_delayed_impl)
            app_logger.log_audio_event("RecordingOverlay all thread-safe signals connected", {})
        except Exception as e:
            app_logger.log_error(e, "thread_safe_signals_connection")

        app_logger.log_audio_event("Recording overlay initialized successfully", {
            "singleton_id": id(self)
        })

    # ==================== 定时器生命周期管理 ====================

    def _safe_timer_connect(self, timer, target_method, description=""):
        """安全地连接定时器，防止重复连接"""
        import warnings

        try:
            # 先尝试断开现有连接（如果有的话）
            # PySide6: disconnect() 不抛异常，而是发出 RuntimeWarning
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                timer.timeout.disconnect(target_method)
        except (TypeError, RuntimeError):
            pass  # 如果没有连接则忽略（TypeError: signal未连接, RuntimeError: C++ object已删除）

        # 重新连接
        timer.timeout.connect(target_method)

        if description:
            app_logger.log_audio_event(f"Timer connected: {description}", {
                "timer_active": timer.isActive()
            })

    def _safe_timer_start(self, timer, interval, target_method, description=""):
        """安全地启动定时器"""
        try:
            # 停止现有定时器
            if timer.isActive():
                timer.stop()

            # 确保连接正确
            self._safe_timer_connect(timer, target_method, f"{description}_connect")

            # 启动定时器
            timer.start(interval)

            if description:
                app_logger.log_audio_event(f"Timer started: {description}", {
                    "interval": interval,
                    "timer_active": timer.isActive()
                })
        except Exception as e:
            app_logger.log_error(e, f"safe_timer_start_{description}")

    def _safe_timer_stop(self, timer, target_method, description=""):
        """安全地停止定时器"""
        import warnings

        try:
            if hasattr(self, timer.objectName()) and timer.isActive():
                timer.stop()

                # 断开特定连接
                # PySide6: disconnect() 不抛异常，而是发出 RuntimeWarning
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", RuntimeWarning)
                        timer.timeout.disconnect(target_method)
                except (TypeError, RuntimeError):
                    pass  # 如果没有连接则忽略

                if description:
                    app_logger.log_audio_event(f"Timer stopped: {description}", {
                        "timer_active": timer.isActive()
                    })
        except Exception as e:
            app_logger.log_error(e, f"safe_timer_stop_{description}")

    def _ensure_animation_state(self, should_animate: bool, context: str = ""):
        """确保动画状态与期望状态一致"""
        try:
            current_animating = hasattr(self, 'breathing_timer') and self.breathing_timer.isActive()

            if should_animate and not current_animating:
                # 需要开始动画但当前没有动画
                self._start_processing_animation_impl()
                app_logger.log_audio_event(f"Animation started: {context}", {
                    "previous_state": current_animating,
                    "new_state": should_animate,
                    "is_processing": self.is_processing
                })
            elif not should_animate and current_animating:
                # 需要停止动画但当前有动画
                self._stop_processing_animation_impl()
                app_logger.log_audio_event(f"Animation stopped: {context}", {
                    "previous_state": current_animating,
                    "new_state": should_animate,
                    "is_processing": self.is_processing
                })

            # 延迟验证状态一致性，避免竞态条件
            def delayed_verification():
                try:
                    final_animating = hasattr(self, 'breathing_timer') and self.breathing_timer.isActive()
                    # 检测并修复状态不一致
                    if final_animating != should_animate:
                        app_logger.log_audio_event(f"Animation state mismatch in {context}: expected {should_animate}, got {final_animating} - fixing", {
                            "expected": should_animate,
                            "actual": final_animating,
                            "context": context
                        })

                        # 修复状态不一致
                        if should_animate and not final_animating:
                            # 应该动画但没有动画 - 启动动画
                            self._start_processing_animation_impl()
                            app_logger.log_audio_event(f"Fixed: started animation for {context}", {})
                        elif not should_animate and final_animating:
                            # 不应该动画但有动画 - 停止动画
                            self._stop_processing_animation_impl()
                            app_logger.log_audio_event(f"Fixed: stopped animation for {context}", {})
                except Exception as e:
                    app_logger.log_error(e, f"delayed_verification_{context}")

            # 使用Qt单次定时器延迟验证，给信号处理时间
            QTimer.singleShot(50, delayed_verification)

        except Exception as e:
            app_logger.log_error(e, f"ensure_animation_state_{context}")

    def set_config_service(self, config_service: IConfigService) -> None:
        """设置配置服务"""
        self.config_service = config_service
        # 传递给PositionManager
        if hasattr(self, 'position_manager'):
            self.position_manager.set_config_service(config_service)
        app_logger.log_audio_event("Config service set for overlay", {})

    def _reset_for_reuse(self) -> None:
        """重置overlay状态以支持稳定的多次使用（Qt main thread only）"""
        try:
            app_logger.log_audio_event("Starting overlay reset for reuse", {
                "singleton_id": id(self),
                "is_visible": self.isVisible() if hasattr(self, 'isVisible') else False
            })

            # 首先隐藏窗口，避免在重置过程中出现闪烁
            if self.isVisible():
                self.hide()
                app_logger.log_audio_event("Overlay hidden during reset", {})

            # 停止并彻底清理所有定时器
            self._cleanup_all_timers()

            # 重置所有状态变量
            self.is_recording = False
            self.current_status = "Ready"
            self.recording_duration = 0
            self.breathing_phase = 0
            self.is_processing = False

            # 清理音频级别条状态
            if hasattr(self, 'audio_level_bars'):
                try:
                    for bar in self.audio_level_bars:
                        if bar:
                            bar.setStyleSheet("""
                                QLabel {
                                    background-color: rgba(80, 80, 90, 100);
                                    border-radius: 2px;
                                }
                            """)
                except Exception as e:
                    app_logger.log_error(e, "reset_audio_level_bars")

            # 重新连接所有信号（确保信号连接正确）
            self._reconnect_signals()

            # 重置窗口属性
            self._reset_window_properties()

            app_logger.log_audio_event("Recording overlay reset for reuse completed", {
                "singleton_id": id(self)
            })

        except Exception as e:
            app_logger.log_error(e, "overlay_reset_for_reuse")
            # 如果重置失败，尝试强制重置到基本状态
            try:
                self.is_recording = False
                self.current_status = "Ready"
                if self.isVisible():
                    self.hide()
            except (RuntimeError, AttributeError):
                pass  # 忽略Qt对象已删除或属性不存在的错误

    def _cleanup_all_timers(self) -> None:
        """彻底清理所有定时器"""
        try:
            timers_to_cleanup = [
                ('update_timer', 'update_recording_time'),
                ('breathing_timer', 'update_breathing'),
                ('status_animation', None)  # QPropertyAnimation
            ]

            for timer_name, callback_name in timers_to_cleanup:
                if hasattr(self, timer_name):
                    timer = getattr(self, timer_name)
                    if timer:
                        try:
                            if hasattr(timer, 'isActive') and timer.isActive():
                                timer.stop()
                                app_logger.log_audio_event(f"Stopped {timer_name}", {})

                            # 断开信号连接
                            if callback_name and hasattr(timer, 'timeout'):
                                try:
                                    timer.timeout.disconnect()
                                except (TypeError, RuntimeError):
                                    pass  # 信号未连接或对象已删除
                        except Exception as e:
                            app_logger.log_error(e, f"cleanup_timer_{timer_name}")

            app_logger.log_audio_event("All timers cleaned up", {})

        except Exception as e:
            app_logger.log_error(e, "cleanup_all_timers")

    def _reconnect_signals(self) -> None:
        """重新连接所有信号"""
        try:
            # 重新连接线程安全信号
            signal_connections = [
                (self.show_recording_requested, self._show_recording_impl),
                (self.hide_recording_requested, self._hide_recording_impl),
                (self.set_status_requested, self._set_status_text_impl),
                (self.update_waveform_requested, self._update_waveform_impl),
                (self.update_audio_level_requested, self._update_audio_level_impl),
                (self.start_processing_animation_requested, self._start_processing_animation_impl),
                (self.stop_processing_animation_requested, self._stop_processing_animation_impl),
                (self.hide_recording_delayed_requested, self._hide_recording_delayed_impl),
            ]

            for signal, slot in signal_connections:
                try:
                    # 先断开所有连接
                    signal.disconnect()
                except (TypeError, RuntimeError):
                    pass  # 信号未连接或对象已删除

                try:
                    # 重新连接
                    signal.connect(slot)
                except Exception as e:
                    app_logger.log_error(e, f"reconnect_signal_{signal}")

            app_logger.log_audio_event("Signals reconnected", {})

        except Exception as e:
            app_logger.log_error(e, "reconnect_signals")

    def _reset_window_properties(self) -> None:
        """重置窗口属性到初始状态"""
        try:
            # 重置窗口属性
            self.setWindowOpacity(1.0)

            # 重置样式
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText("Ready")
                self.status_label.setStyleSheet("color: #CCCCCC; font-weight: bold;")

            # 确保窗口标志正确
            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool |
                Qt.WindowType.WindowDoesNotAcceptFocus
            )

            app_logger.log_audio_event("Window properties reset", {})

        except Exception as e:
            app_logger.log_error(e, "reset_window_properties")

    @classmethod
    def reset_singleton(cls) -> None:
        """强制重置单例实例（仅在极端情况下使用，Qt main thread only）"""
        try:
            if cls._instance is not None:
                app_logger.log_audio_event("Force resetting overlay singleton", {})
                # 尝试清理现有实例
                try:
                    if hasattr(cls._instance, 'update_timer'):
                        cls._instance.update_timer.stop()
                    if hasattr(cls._instance, 'breathing_timer'):
                        cls._instance.breathing_timer.stop()
                    if cls._instance.isVisible():
                        cls._instance.hide()
                except (RuntimeError, AttributeError):
                    pass  # 忽略清理错误（对象已删除或属性不存在）

                cls._instance = None
                cls._initialized = False
                app_logger.log_audio_event("Overlay singleton reset completed", {})
        except Exception as e:
            app_logger.log_error(e, "force_reset_singleton")
    
    def setup_overlay_ui(self) -> None:
        """Setup overlay UI"""
        # 主布局 - 更紧凑的间距
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)
        
        # 创建Material Design背景框架
        self.background_frame = QFrame()
        self.background_frame.setObjectName("recordingOverlayFrame")
        # 设置Material Design深色背景，确保关闭按钮有足够对比度
        self.background_frame.setStyleSheet("""
            QFrame#recordingOverlayFrame {
                background-color: #303030;
                border-radius: 12px;
            }
        """)
        
        # 横向布局 - Windows 原生风格
        frame_layout = QHBoxLayout(self.background_frame)
        frame_layout.setContentsMargins(8, 6, 8, 6)
        frame_layout.setSpacing(8)

        # 录音状态指示器 (真正的圆形红点 + 圆角矩形背景)
        self.status_indicator = StatusIndicator(self)
        # 使用布局对齐确保指示器在容器中完美居中
        frame_layout.addWidget(self.status_indicator, 0, Qt.AlignmentFlag.AlignCenter)

        # 极简音频级别条 (替代复杂波形)
        self.audio_level_bars = []
        self.current_audio_level = 0.0

        # 创建5个音频级别条 - Material Design风格
        for i in range(5):
            bar = QLabel()
            bar.setFixedSize(4, 18)
            # 简化样式，统一圆角，无描边
            bar.setStyleSheet("""
                QLabel {
                    border-radius: 2px;
                }
            """)
            self.audio_level_bars.append(bar)
            frame_layout.addWidget(bar)

        # 弹性空间
        frame_layout.addStretch()

        # 录音时间标签 - 极简样式
        self.time_label = QLabel("00:00")
        self.time_label.setFont(QFont("Segoe UI", 9))
        self.time_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                background: transparent;
            }
        """)
        frame_layout.addWidget(self.time_label)

        # 关闭按钮 - 使用自定义绘制确保完美居中
        self.close_button = CloseButton(self)

        # 实现点击事件
        def close_button_click(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.hide_recording()
        self.close_button.mousePressEvent = close_button_click

        # 使用布局对齐确保关闭按钮在容器中完美居中
        frame_layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignCenter)
        
        # 添加到主布局
        main_layout.addWidget(self.background_frame)
        self.setLayout(main_layout)

        # 添加Material Design阴影效果 (Elevation 8)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))  # Material Elevation 8
        self.background_frame.setGraphicsEffect(shadow)

        # 设置固定大小 - Material Design紧凑横向布局
        self.setFixedSize(200, 50)

        # 确保悬浮窗本身透明背景
        self.setStyleSheet("""
            RecordingOverlay {
                background: transparent;
            }
        """)

        # 位置管理器（使用已有的PositionManager服务）
        self.position_manager = PositionManager(self, config_service=None)
        self.config_service = None  # 将在set_config_service中设置

        # 初始隐藏
        self.hide()
    
    def show_recording(self) -> None:
        """Show recording status - Thread-safe public interface"""
        self.show_recording_requested.emit()

    def _show_recording_impl(self) -> None:
        """Show recording status - Internal implementation (Qt main thread only)"""
        if self.is_recording:
            return  # Already recording

        self.is_recording = True
        self.recording_duration = 0

        # 更新状态指示器为录音状态（红色）
        try:
            self.status_indicator.set_state(StatusIndicator.STATE_RECORDING)
            self.time_label.setText("00:00")
        except Exception as e:
            app_logger.log_error(e, "status_update_show")

        # 安全地启动计时器
        try:
            if hasattr(self, 'update_timer'):
                self._safe_timer_start(self.update_timer, 1000, self.update_recording_time, "recording_timer")
        except Exception as e:
            app_logger.log_error(e, "timer_start_show")

        # 恢复位置（在显示窗口前）
        if self.config_service:
            self.position_manager.restore_position()

        # 显示窗口
        try:
            self.show()
            self.raise_()
            # self.activateWindow()
        except Exception as e:
            app_logger.log_error(e, "widget_show")

        # 淡入动画
        try:
            if hasattr(self, 'fade_animation'):
                self.fade_animation.stop()
                self.fade_animation.setStartValue(0.0)
                self.fade_animation.setEndValue(1.0)
                self.fade_animation.start()
        except Exception as e:
            app_logger.log_error(e, "fade_animation_show")

        app_logger.log_audio_event("Recording overlay shown", {})
    
    def hide_recording(self) -> None:
        """Hide recording status - Thread-safe public interface"""
        self.hide_recording_requested.emit()

    def show_completed(self, delay_ms: int = 500) -> None:
        """显示完成状态，然后延迟隐藏

        Args:
            delay_ms: 延迟隐藏的毫秒数，默认500ms（0.5秒）
        """
        try:
            # 切换到完成状态（绿色）
            self.status_indicator.set_state(StatusIndicator.STATE_COMPLETED)
            # 延迟隐藏
            QTimer.singleShot(delay_ms, self._hide_recording_impl)
        except Exception as e:
            app_logger.log_error(e, "show_completed")

    def show_processing(self) -> None:
        """显示AI处理状态（黄色）"""
        try:
            # 设置处理状态（黄色）
            self.status_indicator.set_state(StatusIndicator.STATE_PROCESSING)

            # 停止录音计时器（录音已结束）
            self.is_recording = False
            if hasattr(self, 'update_timer'):
                self._safe_timer_stop(self.update_timer, self.update_recording_time, "recording_timer_processing")

            # 添加超时自动隐藏（5秒后），防止转录/AI/输入失败时悬浮窗永久显示
            # 如果处理成功，show_completed() 会在 500ms 时提前触发隐藏
            self.hide_recording_delayed_requested.emit(5000)
        except Exception as e:
            app_logger.log_error(e, "show_processing")

    def _hide_recording_impl(self) -> None:
        """Hide recording status - Internal implementation (Qt main thread only)"""
        # 检查窗口是否真的可见，而不是检查 is_recording 状态
        if not self.isVisible():
            # 窗口已经隐藏，无需重复操作
            app_logger.log_audio_event("Hide skipped: overlay already hidden", {})
            return

        self.is_recording = False

        # 安全地停止所有计时器
        try:
            if hasattr(self, 'update_timer'):
                self._safe_timer_stop(self.update_timer, self.update_recording_time, "recording_timer_hide")

            if hasattr(self, 'breathing_timer'):
                self._safe_timer_stop(self.breathing_timer, self.update_breathing, "breathing_timer_hide")
        except Exception as e:
            app_logger.log_error(e, "timer_cleanup_hide")

        # 重置所有状态
        self.recording_duration = 0
        self.breathing_phase = 0
        self.is_processing = False

        # 重置音频级别条显示
        try:
            for bar in self.audio_level_bars:
                bar.setStyleSheet("""
                    QLabel {
                        background-color: rgba(80, 80, 90, 100);
                        border-radius: 2px;
                    }
                """)
            self.current_audio_level = 0.0
        except Exception as e:
            app_logger.log_error(e, "audio_bars_reset_hide")

        # 重置计时器显示
        try:
            self.time_label.setText("00:00")
        except Exception as e:
            app_logger.log_error(e, "time_label_reset_hide")

        # 不重置状态指示器 - 状态由下次 show_recording 或 show_completed 设置

        # 直接隐藏窗口，不使用淡出动画
        # 移除复杂的淡出动画逻辑以避免信号竞态条件导致的闪退
        try:
            self._safe_hide()
        except Exception as e:
            app_logger.log_error(e, "direct_hide")
            # 强制隐藏
            self.hide()

        app_logger.log_audio_event("Recording overlay hidden", {})

        # 保存位置（如果有配置服务且开启自动保存）
        if self.config_service and self.config_service.get_setting("ui.overlay_position.auto_save", True):
            self.position_manager.save_position()

    def _safe_hide(self) -> None:
        """Safely hide the widget with error handling"""
        try:
            if self.isVisible():
                self.hide()
        except Exception as e:
            app_logger.log_error(e, "safe_hide_widget")

    def hide_recording_delayed(self, delay_ms: int = 1000) -> None:
        """延迟隐藏录音状态 - Thread-safe public interface"""
        self.hide_recording_delayed_requested.emit(delay_ms)

    def _hide_recording_delayed_impl(self, delay_ms: int) -> None:
        """延迟隐藏录音状态 - Internal implementation"""
        QTimer.singleShot(delay_ms, self._hide_recording_impl)

    def update_waveform(self, audio_data) -> None:
        """Update waveform display - Thread-safe public interface"""
        self.update_waveform_requested.emit(audio_data)

    def _update_waveform_impl(self, audio_data) -> None:
        """Update audio level display - Internal implementation"""
        if self.is_recording and audio_data is not None:
            try:
                import numpy as np
                # 计算音频级别 (RMS)
                if hasattr(audio_data, '__len__') and len(audio_data) > 0:
                    if isinstance(audio_data, np.ndarray):
                        level = float(np.sqrt(np.mean(audio_data**2)))
                    else:
                        level = float(abs(sum(audio_data)) / len(audio_data))

                    # 标准化到 0-1 范围 - 大幅提高敏感度让正常说话音量也能显示
                    level = min(1.0, max(0.0, level * 20))  # 提高敏感度到20倍（从8倍）
                    self.current_audio_level = level

                    # 调试日志：每秒记录一次音量级别（已禁用，避免日志洪流）
                    # if not hasattr(self, '_last_audio_log_time'):
                    #     self._last_audio_log_time = 0
                    # import time
                    # current_time = time.time()
                    # if current_time - self._last_audio_log_time >= 1.0:
                    #     app_logger.log_audio_event("Audio level update", {
                    #         "raw_level": f"{raw_level:.6f}",
                    #         "normalized_level": f"{level:.4f}",
                    #         "sensitivity_multiplier": 20
                    #     })
                    #     self._last_audio_log_time = current_time

                    # 更新音频级别条
                    self._update_audio_level_bars(level)
            except Exception:
                # 如果计算失败，使用默认的随机级别模拟
                pass

    def _update_audio_level_bars(self, level: float) -> None:
        """更新音频级别条显示"""
        try:
            # 计算应该点亮的级别条数量
            active_bars = int(level * len(self.audio_level_bars))

            # 更新每个级别条
            for i, bar in enumerate(self.audio_level_bars):
                if i < active_bars:
                    # 活跃的级别条 - 绿色渐变
                    intensity = (i + 1) / len(self.audio_level_bars)
                    if intensity < 0.6:
                        color = "#4CAF50"  # 绿色
                    elif intensity < 0.8:
                        color = "#FFC107"  # 黄色
                    else:
                        color = "#FF5722"  # 红色

                    bar.setStyleSheet(f"""
                        QLabel {{
                            background-color: {color};
                            border-radius: 2px;
                        }}
                    """)
                else:
                    # 非活跃的级别条 - 灰色
                    bar.setStyleSheet("""
                        QLabel {
                            background-color: rgba(80, 80, 90, 100);
                            border-radius: 2px;
                        }
                    """)
        except Exception:
            pass

    def update_audio_level(self, level: float) -> None:
        """Update audio level display - Thread-safe public interface"""
        self.update_audio_level_requested.emit(level)

    def _update_audio_level_impl(self, level: float) -> None:
        """Update audio level bars - Internal implementation"""
        if self.is_recording:
            try:
                # 标准化到 0-1 范围 - 大幅提高敏感度让正常说话音量也能显示
                normalized_level = min(1.0, max(0.0, level * 20))  # 提高敏感度到20倍（从8倍）
                self.current_audio_level = normalized_level

                # 调试日志：每秒记录一次音量级别（已禁用，避免日志洪流）
                # if not hasattr(self, '_last_audio_log_time_direct'):
                #     self._last_audio_log_time_direct = 0
                # import time
                # current_time = time.time()
                # if current_time - self._last_audio_log_time_direct >= 1.0:
                #     app_logger.log_audio_event("Audio level update (direct)", {
                #         "raw_level": f"{raw_level:.6f}",
                #         "normalized_level": f"{normalized_level:.4f}",
                #         "sensitivity_multiplier": 20
                #     })
                #     self._last_audio_log_time_direct = current_time

                # 更新音频级别条
                self._update_audio_level_bars(normalized_level)
            except Exception as e:
                app_logger.log_error(e, "_update_audio_level_impl")

    def set_status_text(self, text: str) -> None:
        """Set status text - Thread-safe public interface"""
        self.set_status_requested.emit(text)

    def _set_status_text_impl(self, text: str) -> None:
        """Set status text - Internal implementation (Qt main thread only)"""
        self.current_status = text
        # 新设计中不显示文本，只通过颜色指示状态

        # 根据状态改变颜色和启动/停止动画，包括定时器管理
        # 状态管理：确保动画状态与文本状态同步
        if "error" in text.lower():
            self._ensure_animation_state(False, "error_state")
            self._stop_timer_if_needed()
        elif "processing" in text.lower() or "ai" in text.lower():
            self._ensure_animation_state(True, "processing_state")
            self._stop_timer_if_needed()  # 处理时停止录音计时
        elif "recording" in text.lower():
            self._ensure_animation_state(False, "recording_state")
            # 录音状态保持计时器运行
        elif "inputting" in text.lower():
            self._ensure_animation_state(True, "inputting_state")
            self._stop_timer_if_needed()  # 输入时停止录音计时
        elif "completed" in text.lower():
            self._ensure_animation_state(False, "completed_state")
            self._stop_timer_if_needed()  # 完成时停止录音计时
        elif "stopped" in text.lower() or "idle" in text.lower():
            self._ensure_animation_state(False, "idle_state")
            self._stop_timer_if_needed()  # 停止时停止录音计时
        else:
            self._ensure_animation_state(False, "default_state")
            self._stop_timer_if_needed()

        # 状态指示器现在由 set_state(), show_processing(), show_completed() 直接管理
        # 不再通过文本推断状态

    def _stop_timer_if_needed(self) -> None:
        """Stop recording timer when not in recording state"""
        try:
            if hasattr(self, 'update_timer') and self.update_timer.isActive():
                if not self.is_recording or "recording" not in self.current_status.lower():
                    self.update_timer.stop()
                    # 断开计时器连接
                    try:
                        self.update_timer.timeout.disconnect(self.update_recording_time)
                    except (TypeError, RuntimeError):
                        pass  # 信号未连接或对象已删除
        except Exception as e:
            app_logger.log_error(e, "stop_timer_if_needed")
    
    def update_recording_time(self) -> None:
        """Update recording time (Qt main thread only)"""
        if self.is_recording:
            self.recording_duration += 1
            minutes = self.recording_duration // 60
            seconds = self.recording_duration % 60
            try:
                self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
            except Exception as e:
                app_logger.log_error(e, "update_recording_time")
        else:
            # If not recording, stop the timer immediately
            try:
                if hasattr(self, 'update_timer') and self.update_timer.isActive():
                    self.update_timer.stop()
                    try:
                        self.update_timer.timeout.disconnect(self.update_recording_time)
                    except (TypeError, RuntimeError):
                        pass  # 信号未连接或对象已删除
            except Exception as e:
                app_logger.log_error(e, "stop_timer_in_update")
    
    def center_on_screen(self) -> None:
        """Center on screen - Delegate to PositionManager"""
        self.position_manager.center_on_screen()
    
    def set_position(self, position: str) -> None:
        """Set window position - Delegate to PositionManager"""
        self.position_manager.set_preset_position(position)
    
    def mousePressEvent(self, event):
        """鼠标按下事件 - 用于拖拽窗口"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件 - 拖拽窗口"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件 - 拖拽结束后保存位置"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 拖拽结束后保存位置
            if self.config_service and self.config_service.get_setting("ui.overlay_position.auto_save", True):
                self.position_manager.save_position()
            event.accept()

    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key.Key_Escape:
            self.hide_recording()
        elif event.key() == Qt.Key.Key_Space:
            self.hide_recording()  # Space键也可以关闭悬浮窗
    
    def test_display_capability(self) -> bool:
        """Test if overlay can be displayed properly"""
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtGui import QGuiApplication
            
            app_logger.log_audio_event("Testing overlay display capability", {})
            
            # Check if QApplication exists
            app = QApplication.instance()
            if app is None:
                app_logger.log_audio_event("No QApplication instance for overlay test", {})
                return False
            
            # Test screen availability
            screen = QGuiApplication.primaryScreen()
            if screen is None:
                app_logger.log_audio_event("No primary screen available for overlay", {})
                return False
            
            screen_geometry = screen.geometry()
            if screen_geometry.width() <= 0 or screen_geometry.height() <= 0:
                app_logger.log_audio_event("Invalid screen geometry for overlay", {
                    "width": screen_geometry.width(),
                    "height": screen_geometry.height()
                })
                return False
            
            # Test widget creation and basic properties
            if not self.isWindow():
                app_logger.log_audio_event("Overlay widget is not a window", {})
                return False
            
            # Test window flags
            flags = self.windowFlags()
            expected_flags = [
                Qt.WindowType.FramelessWindowHint,
                Qt.WindowType.WindowStaysOnTopHint,
                Qt.WindowType.Tool
            ]
            
            for flag in expected_flags:
                if not (flags & flag):
                    app_logger.log_audio_event("Missing required window flag", {"flag": str(flag)})
                    return False
            
            app_logger.log_audio_event("Overlay display capability test passed", {
                "screen_size": f"{screen_geometry.width()}x{screen_geometry.height()}",
                "widget_size": f"{self.width()}x{self.height()}"
            })
            return True
            
        except Exception as e:
            app_logger.log_error(e, "overlay_display_capability_test")
            return False
    
    def validate_input_handling(self) -> bool:
        """Test if overlay can handle input events properly"""
        try:
            app_logger.log_audio_event("Testing overlay input handling", {})
            
            # Test if widget can accept focus
            if not self.isActiveWindow():
                # Try to activate
                self.activateWindow()
                self.raise_()
            
            # Test if widget has proper focus policy
            focus_policy = self.focusPolicy()
            if focus_policy == Qt.FocusPolicy.NoFocus:
                app_logger.log_audio_event("Overlay has no focus policy", {})
                return False
            
            # Test event handling capability by checking methods exist
            required_methods = ['keyPressEvent', 'mousePressEvent', 'mouseMoveEvent']
            for method_name in required_methods:
                if not hasattr(self, method_name):
                    app_logger.log_audio_event("Missing input handler method", {"method": method_name})
                    return False
            
            # Test signal connections (检查基本信号)
            if not hasattr(self, 'show_recording_requested'):
                app_logger.log_audio_event("Missing show_recording_requested signal", {})
                return False
            
            app_logger.log_audio_event("Overlay input handling validation passed", {
                "focus_policy": str(focus_policy),
                "is_active": self.isActiveWindow()
            })
            return True
            
        except Exception as e:
            app_logger.log_error(e, "overlay_input_handling_validation")
            return False
    
    def test_overlay_positioning(self) -> bool:
        """Test overlay positioning functionality"""
        try:
            app_logger.log_audio_event("Testing overlay positioning", {})
            
            from PySide6.QtGui import QGuiApplication
            
            screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.geometry()
            
            # Test different positions
            positions_to_test = ["center", "top_left", "top_right", "bottom_left", "bottom_right"]
            
            for position in positions_to_test:
                try:
                    self.set_position(position)
                    
                    # Verify position is within screen bounds
                    widget_rect = self.geometry()
                    if not screen_geometry.contains(widget_rect):
                        app_logger.log_audio_event("Position test failed - out of bounds", {
                            "position": position,
                            "widget_rect": f"{widget_rect.x()},{widget_rect.y()},{widget_rect.width()},{widget_rect.height()}",
                            "screen_rect": f"{screen_geometry.x()},{screen_geometry.y()},{screen_geometry.width()},{screen_geometry.height()}"
                        })
                        return False
                        
                except Exception as pos_error:
                    app_logger.log_error(pos_error, f"overlay_position_test_{position}")
                    return False
            
            # Test center positioning specifically
            self.position_manager.center_on_screen()
            center_pos = self.pos()
            expected_x = (screen_geometry.width() - self.width()) // 2
            expected_y = (screen_geometry.height() - self.height()) // 2
            
            # Allow some tolerance for positioning
            tolerance = 10
            if (abs(center_pos.x() - expected_x) > tolerance or 
                abs(center_pos.y() - expected_y) > tolerance):
                app_logger.log_audio_event("Center positioning test failed", {
                    "actual": f"{center_pos.x()},{center_pos.y()}",
                    "expected": f"{expected_x},{expected_y}",
                    "tolerance": tolerance
                })
                return False
            
            app_logger.log_audio_event("Overlay positioning test passed", {
                "positions_tested": len(positions_to_test),
                "final_position": f"{center_pos.x()},{center_pos.y()}"
            })
            return True
            
        except Exception as e:
            app_logger.log_error(e, "overlay_positioning_test")
            return False
    
    def run_comprehensive_overlay_test(self) -> dict:
        """Run comprehensive overlay functionality tests"""
        app_logger.log_audio_event("Starting comprehensive overlay test", {})
        
        test_results = {
            "display_capability": False,
            "input_handling": False,
            "positioning": False,
            "ui_components": False,
            "animation_system": False,
            "overall_success": False
        }
        
        try:
            # Test display capability
            test_results["display_capability"] = self.test_display_capability()
            
            # Test input handling
            test_results["input_handling"] = self.validate_input_handling()
            
            # Test positioning
            test_results["positioning"] = self.test_overlay_positioning()
            
            # Test UI components
            test_results["ui_components"] = self._test_ui_components()
            
            # Test animation system
            test_results["animation_system"] = self._test_animation_system()
            
            # Overall success
            test_results["overall_success"] = all([
                test_results["display_capability"],
                test_results["input_handling"],
                test_results["positioning"],
                test_results["ui_components"]
            ])
            
            app_logger.log_audio_event("Comprehensive overlay test completed", {
                "success": test_results["overall_success"],
                "passed_tests": sum(test_results.values()),
                "total_tests": len(test_results) - 1  # Exclude overall_success
            })
            
        except Exception as e:
            app_logger.log_error(e, "comprehensive_overlay_test")
            test_results["error"] = str(e)
        
        return test_results
    
    def _test_ui_components(self) -> bool:
        """Test UI components are properly initialized"""
        try:
            # Check required attributes exist
            required_attrs = [
                'status_label', 'time_label', 'stop_button',
                'update_timer', 'fade_animation'
            ]
            
            for attr in required_attrs:
                if not hasattr(self, attr):
                    app_logger.log_audio_event("Missing UI component", {"component": attr})
                    return False
            
            # Test timer functionality
            if self.update_timer.isActive():  # Should not be active initially
                app_logger.log_audio_event("Timer in unexpected state", {})
                return False
            
            app_logger.log_audio_event("UI components test passed", {})
            return True
            
        except Exception as e:
            app_logger.log_error(e, "ui_components_test")
            return False
    
    def _test_animation_system(self) -> bool:
        """Test animation system functionality"""
        try:
            # Test fade animation properties
            if self.fade_animation.duration() != 300:
                app_logger.log_audio_event("Animation duration incorrect", {
                    "expected": 300,
                    "actual": self.fade_animation.duration()
                })
                return False
            
            # Test animation target
            if self.fade_animation.targetObject() != self:
                app_logger.log_audio_event("Animation target incorrect", {})
                return False
            
            app_logger.log_audio_event("Animation system test passed", {})
            return True
            
        except Exception as e:
            app_logger.log_error(e, "animation_system_test")
            return False

    def start_processing_animation(self) -> None:
        """启动处理动画 - Thread-safe public interface"""
        self.start_processing_animation_requested.emit()

    def _start_processing_animation_impl(self) -> None:
        """启动呼吸动画 - Internal implementation"""
        self.is_processing = True
        if hasattr(self, 'breathing_timer'):
            self._safe_timer_start(self.breathing_timer, 80, self.update_breathing, "breathing_animation")

    def stop_processing_animation(self) -> None:
        """停止处理动画 - Thread-safe public interface"""
        self.stop_processing_animation_requested.emit()

    def _stop_processing_animation_impl(self) -> None:
        """停止呼吸动画 - Internal implementation"""
        self.is_processing = False
        if hasattr(self, 'breathing_timer'):
            self._safe_timer_stop(self.breathing_timer, self.update_breathing, "breathing_animation")
        self.breathing_phase = 0

    def update_breathing(self) -> None:
        """更新呼吸效果"""
        # 状态同步检查：确保动画状态与处理状态一致
        if not self.is_processing or not hasattr(self, 'breathing_timer') or not self.breathing_timer.isActive():
            # 如果状态不一致，停止动画
            if hasattr(self, 'breathing_timer') and self.breathing_timer.isActive():
                self._safe_timer_stop(self.breathing_timer, self.update_breathing, "breathing_sync_stop")
            self.is_processing = False
            self.breathing_phase = 0
            return

        if self.is_processing:
            self.breathing_phase += 0.15  # 呼吸速度
            # 修复π精度：使用标准数学常量而非硬编码值
            if self.breathing_phase >= 2 * math.pi:  # 使用准确的2π
                self.breathing_phase = 0
            self.update()  # 重绘界面

    def paintEvent(self, event):
        """重写绘制事件以添加呼吸发光效果"""
        super().paintEvent(event)

        # 如果正在处理，绘制呼吸发光效果
        if self.is_processing:
            from PySide6.QtGui import QPainter, QBrush, QColor, QRadialGradient
            import math

            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # 计算呼吸效果的透明度
            breathing_intensity = (math.sin(self.breathing_phase) + 1) / 2  # 0 到 1
            # 确保透明度在有效范围内 (0-255)
            alpha = max(0, min(255, int(30 + 50 * breathing_intensity)))  # 透明度在30-80之间

            # 创建径向渐变效果 - 使用安全的颜色值
            gradient = QRadialGradient(self.width() / 2, self.height() / 2, min(self.width(), self.height()) / 2)

            # 确保所有RGB和Alpha值都在有效范围 (0-255)
            center_color = QColor(max(0, min(255, 76)), max(0, min(255, 175)), max(0, min(255, 80)), alpha)
            gradient.setColorAt(0, center_color)  # 中心亮绿色

            # 修复除法稳定性：确保边缘透明度不为零且在有效范围内
            edge_alpha = max(1, min(255, alpha // 3))  # 边缘淡绿色，确保至少为1
            edge_color = QColor(max(0, min(255, 76)), max(0, min(255, 175)), max(0, min(255, 80)), edge_alpha)
            gradient.setColorAt(0.7, edge_color)
            gradient.setColorAt(1, QColor(76, 175, 80, 0))  # 完全透明

            # 绘制呼吸发光效果
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.rect())

            # 确保正确关闭画家
            painter.end()

    # Position management methods delegated to PositionManager
    # See recording_overlay_utils/position_manager.py for implementation
