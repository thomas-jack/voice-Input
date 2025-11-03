"""定时器管理器 - 单一职责：管理所有定时器"""

import warnings
from typing import Callable
from PySide6.QtCore import QTimer

from ...utils import app_logger


class TimerManager:
    """定时器管理器 - 管理RecordingOverlay的所有定时器

    职责：
    1. 录音计时器（update_timer）
    2. 延迟隐藏定时器（delayed_hide_timer）
    3. 定时器的安全启动/停止
    4. 定时器生命周期管理
    """

    def __init__(self):
        """初始化定时器管理器"""
        # 录音计时器（每秒更新录音时间）
        self.update_timer = QTimer()

        # 延迟隐藏定时器（单次触发）
        self.delayed_hide_timer = QTimer()
        self.delayed_hide_timer.setSingleShot(True)

        app_logger.log_audio_event("TimerManager initialized", {})

    def safe_connect(
        self, timer: QTimer, callback: Callable, description: str = ""
    ) -> None:
        """安全地连接定时器到回调函数

        Args:
            timer: QTimer对象
            callback: 回调函数
            description: 定时器描述（用于日志）
        """
        try:
            # 先尝试断开现有连接（如果有的话）
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    timer.timeout.disconnect()
                except (TypeError, RuntimeError):
                    pass  # 没有连接则忽略

            # 重新连接
            timer.timeout.connect(callback)

            if description:
                app_logger.log_audio_event(
                    f"Timer connected: {description}",
                    {"timer_active": timer.isActive()},
                )

        except Exception as e:
            app_logger.log_error(e, f"safe_timer_connect_{description}")

    def safe_start(
        self, timer: QTimer, interval: int, callback: Callable, description: str = ""
    ) -> None:
        """安全地启动定时器

        Args:
            timer: QTimer对象
            interval: 定时器间隔（毫秒）
            callback: 回调函数
            description: 定时器描述（用于日志）
        """
        try:
            # 停止现有定时器
            if timer.isActive():
                timer.stop()

            # 确保连接正确
            self.safe_connect(timer, callback, f"{description}_connect")

            # 启动定时器
            timer.start(interval)

            if description:
                app_logger.log_audio_event(
                    f"Timer started: {description}",
                    {"interval": interval, "timer_active": timer.isActive()},
                )

        except Exception as e:
            app_logger.log_error(e, f"safe_timer_start_{description}")

    def safe_stop(
        self, timer: QTimer, callback: Callable, description: str = ""
    ) -> None:
        """安全地停止定时器

        Args:
            timer: QTimer对象
            callback: 回调函数（用于断开连接）
            description: 定时器描述（用于日志）
        """
        try:
            if timer.isActive():
                timer.stop()

                # 断开特定连接
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    try:
                        timer.timeout.disconnect(callback)
                    except (TypeError, RuntimeError):
                        pass  # 如果没有连接则忽略

                if description:
                    app_logger.log_audio_event(
                        f"Timer stopped: {description}",
                        {"timer_active": timer.isActive()},
                    )

        except Exception as e:
            app_logger.log_error(e, f"safe_timer_stop_{description}")

    def start_update_timer(self, callback: Callable) -> None:
        """启动录音时间更新定时器

        Args:
            callback: 更新录音时间的回调函数
        """
        self.safe_start(self.update_timer, 1000, callback, "recording_timer")

    def stop_update_timer(self, callback: Callable) -> None:
        """停止录音时间更新定时器

        Args:
            callback: 更新录音时间的回调函数
        """
        self.safe_stop(self.update_timer, callback, "recording_timer")

    def start_delayed_hide_timer(self, delay_ms: int, callback: Callable) -> None:
        """启动延迟隐藏定时器

        Args:
            delay_ms: 延迟时间（毫秒）
            callback: 隐藏回调函数
        """
        self.safe_start(self.delayed_hide_timer, delay_ms, callback, "delayed_hide")

    def stop_delayed_hide_timer(self, callback: Callable) -> None:
        """停止延迟隐藏定时器

        Args:
            callback: 隐藏回调函数
        """
        self.safe_stop(self.delayed_hide_timer, callback, "delayed_hide")

    def stop_all_timers(self) -> None:
        """停止所有定时器"""
        try:
            if self.update_timer.isActive():
                self.update_timer.stop()

            if self.delayed_hide_timer.isActive():
                self.delayed_hide_timer.stop()

            app_logger.log_audio_event("All timers stopped", {})

        except Exception as e:
            app_logger.log_error(e, "stop_all_timers")

    def is_any_timer_active(self) -> bool:
        """检查是否有定时器正在运行

        Returns:
            是否有定时器活跃
        """
        return self.update_timer.isActive() or self.delayed_hide_timer.isActive()

    def cleanup(self) -> None:
        """清理所有定时器资源"""
        try:
            # 停止所有定时器
            self.stop_all_timers()

            # 断开所有信号连接
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                try:
                    self.update_timer.timeout.disconnect()
                except:
                    pass

                try:
                    self.delayed_hide_timer.timeout.disconnect()
                except:
                    pass

            app_logger.log_audio_event("TimerManager cleaned up", {})

        except Exception as e:
            app_logger.log_error(e, "timer_manager_cleanup")
