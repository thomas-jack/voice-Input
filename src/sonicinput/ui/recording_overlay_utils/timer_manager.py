"""Timer lifecycle management for RecordingOverlay"""

from PySide6.QtCore import QTimer
from typing import Callable, Optional
from ...utils import app_logger


class TimerManager:
    """Manages QTimer lifecycle with safe connection/disconnection

    Provides utilities for safely starting, stopping, and reconnecting
    timers to prevent memory leaks and signal connection issues.
    """

    @staticmethod
    def safe_timer_connect(
        timer: QTimer, target_method: Callable, description: str = ""
    ) -> None:
        """安全地连接定时器，防止重复连接

        Args:
            timer: QTimer instance to connect
            target_method: Method to connect to timer.timeout signal
            description: Optional description for logging
        """
        try:
            # 先尝试断开现有连接（如果有的话）
            timer.timeout.disconnect(target_method)
        except (TypeError, RuntimeError):
            pass  # 如果没有连接则忽略（TypeError: signal未连接, RuntimeError: C++ object已删除）

        # 重新连接
        timer.timeout.connect(target_method)

        if description:
            app_logger.log_audio_event(
                f"Timer connected: {description}", {"timer_active": timer.isActive()}
            )

    @staticmethod
    def safe_timer_start(
        timer: QTimer, interval: int, target_method: Callable, description: str = ""
    ) -> None:
        """安全地启动定时器

        Args:
            timer: QTimer instance to start
            interval: Timer interval in milliseconds
            target_method: Method to connect to timer.timeout signal
            description: Optional description for logging
        """
        try:
            # 停止现有定时器
            if timer.isActive():
                timer.stop()

            # 确保连接正确
            TimerManager.safe_timer_connect(
                timer, target_method, f"{description}_connect"
            )

            # 启动定时器
            timer.start(interval)

            if description:
                app_logger.log_audio_event(
                    f"Timer started: {description}",
                    {"interval": interval, "timer_active": timer.isActive()},
                )
        except Exception as e:
            app_logger.log_error(e, f"safe_timer_start_{description}")

    @staticmethod
    def safe_timer_stop(
        timer: QTimer, target_method: Callable, description: str = ""
    ) -> None:
        """安全地停止定时器

        Args:
            timer: QTimer instance to stop
            target_method: Method connected to timer.timeout signal
            description: Optional description for logging
        """
        try:
            if timer.isActive():
                timer.stop()

                # 断开特定连接
                try:
                    timer.timeout.disconnect(target_method)
                except (TypeError, RuntimeError):
                    pass  # 如果没有连接则忽略

                if description:
                    app_logger.log_audio_event(
                        f"Timer stopped: {description}",
                        {"timer_active": timer.isActive()},
                    )
        except Exception as e:
            app_logger.log_error(e, f"safe_timer_stop_{description}")

    @staticmethod
    def cleanup_all_timers(
        timers_with_callbacks: list[tuple[str, Optional[str], Optional[QTimer]]],
    ) -> None:
        """彻底清理所有定时器

        Args:
            timers_with_callbacks: List of (timer_name, callback_name, timer_object) tuples
        """
        try:
            for timer_name, callback_name, timer in timers_with_callbacks:
                if timer:
                    try:
                        if hasattr(timer, "isActive") and timer.isActive():
                            timer.stop()
                            app_logger.log_audio_event(f"Stopped {timer_name}", {})

                        # 断开信号连接
                        if callback_name and hasattr(timer, "timeout"):
                            try:
                                timer.timeout.disconnect()
                            except (TypeError, RuntimeError):
                                pass  # 信号未连接或对象已删除
                    except Exception as e:
                        app_logger.log_error(e, f"cleanup_timer_{timer_name}")

            app_logger.log_audio_event("All timers cleaned up", {})

        except Exception as e:
            app_logger.log_error(e, "cleanup_all_timers")
