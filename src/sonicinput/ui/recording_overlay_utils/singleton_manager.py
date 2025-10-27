"""Singleton pattern manager for RecordingOverlay"""

import threading
from typing import Optional, Any
from ...utils import app_logger


class SingletonMixin:
    """Thread-safe singleton mixin for RecordingOverlay

    Provides thread-safe singleton pattern implementation with proper
    initialization handling and cleanup support.
    """

    _instance: Optional[Any] = None
    _initialized: bool = False
    _instance_lock: threading.Lock = threading.Lock()
    _init_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Thread-safe singleton pattern to prevent multiple overlay instances"""
        with cls._instance_lock:
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

    @classmethod
    def reset_singleton(cls) -> None:
        """强制重置单例实例（仅在极端情况下使用）

        Warning:
            This should only be used in extreme cases where the overlay
            needs to be completely recreated. Normal usage should rely
            on _reset_for_reuse() instead.
        """
        try:
            if cls._instance is not None:
                app_logger.log_audio_event("Force resetting overlay singleton", {})
                # 尝试清理现有实例
                try:
                    if hasattr(cls._instance, '_state_lock'):
                        with cls._instance._state_lock:
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
