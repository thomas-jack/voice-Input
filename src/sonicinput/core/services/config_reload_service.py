"""配置热重载服务实现

负责处理配置变更的监听和热重载逻辑，从VoiceInputApp中提取出来
以提高代码的内聚性和可维护性。
"""

from typing import Callable, Dict, Any, Optional
from ..interfaces import (
    IConfigService,
    IEventService,
    IStateManager,
    ISpeechService,
    IAudioService,
    IHotkeyService,
)
from ...utils import app_logger, logger


class ConfigReloadService:
    """配置热重载服务实现

    处理以下配置变更：
    1. 日志配置重新加载
    2. 快捷键重新加载
    3. 音频设备重新加载
    4. Whisper GPU配置重新加载
    """

    def __init__(
        self,
        config: IConfigService,
        events: IEventService,
        state: IStateManager,
        speech_service: Optional[ISpeechService] = None,
        audio_service: Optional[IAudioService] = None,
        hotkey_service: Optional[IHotkeyService] = None,
    ):
        """初始化配置重载服务

        Args:
            config: 配置服务
            events: 事件服务
            state: 状态管理器
            speech_service: 语音服务（可选）
            audio_service: 音频服务（可选）
            hotkey_service: 快捷键服务（可选）
        """
        self.config = config
        self.events = events
        self.state = state
        self._speech_service = speech_service
        self._audio_service = audio_service
        self._hotkey_service = hotkey_service

        self._reload_callbacks: list[Callable[[Dict[str, Any]], None]] = []
        self._is_monitoring = False

    def setup_config_watcher(self) -> None:
        """设置配置文件监听器"""
        try:
            # 注册配置变更事件监听器
            self.events.on("config.changed", self.handle_config_change)
            app_logger.log_audio_event("Config reload watcher set up", {})
        except Exception as e:
            app_logger.log_error(e, "setup_config_watcher")

    def register_reload_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册配置重载回调函数

        Args:
            callback: 配置变更时的回调函数，接收配置数据
        """
        if callback not in self._reload_callbacks:
            self._reload_callbacks.append(callback)
            app_logger.log_audio_event("Config reload callback registered", {})

    def start_monitoring(self) -> None:
        """开始监控配置变更"""
        if not self._is_monitoring:
            self.setup_config_watcher()
            self._is_monitoring = True
            app_logger.log_audio_event("Config reload monitoring started", {})

    def stop_monitoring(self) -> None:
        """停止监控配置变更"""
        if self._is_monitoring:
            # 移除事件监听器
            try:
                self.events.off("config.changed", self.handle_config_change)
            except Exception:
                pass  # 某些事件系统可能不支持移除监听器

            self._is_monitoring = False
            app_logger.log_audio_event("Config reload monitoring stopped", {})

    def is_monitoring(self) -> bool:
        """检查是否正在监控配置变更"""
        return self._is_monitoring

    def handle_config_change(self, data: Dict[str, Any]) -> None:
        """处理配置变更

        Args:
            data: 包含配置变更信息的数据
        """
        try:
            new_config = data.get("config", {})
            app_logger.log_audio_event(
                "Config changed, reloading...", {"timestamp": data.get("timestamp")}
            )

            # 1. 重新加载日志配置
            self._reload_logging_config(new_config)

            # 2. 重新加载快捷键
            self._reload_hotkeys(new_config)

            # 3. 重新加载音频设备（如果未录音）
            self._reload_audio_device(new_config)

            # 4. 处理 Whisper GPU 配置变更
            self._reload_whisper_gpu_config(new_config)

            # 5. 处理转录提供商配置变更
            self._reload_transcription_provider(new_config)

            # 6. 调用注册的回调函数
            self._notify_callbacks(new_config)

            app_logger.log_audio_event("Config hot reload completed", {})

        except Exception as e:
            app_logger.log_error(e, "handle_config_change")

    def _reload_logging_config(self, config: Dict[str, Any]) -> None:
        """重新加载日志配置"""
        if "logging" in config:
            logger.set_config_service(self.config)
            app_logger.log_audio_event(
                "Logger config reloaded",
                {
                    "level": config["logging"].get("level"),
                    "console_output": config["logging"].get("console_output"),
                },
            )

    def _reload_hotkeys(self, config: Dict[str, Any]) -> None:
        """重新加载快捷键"""
        if "hotkeys" in config or "hotkey" in config:
            if self._hotkey_service and hasattr(self._hotkey_service, "reload"):
                try:
                    self._hotkey_service.reload()
                    app_logger.log_audio_event("Hotkeys reloaded", {})
                except Exception as e:
                    app_logger.log_error(e, "reload_hotkeys")

    def _reload_audio_device(self, config: Dict[str, Any]) -> None:
        """重新加载音频设备"""
        if "audio" in config and not self.state.is_recording():
            device_id = config["audio"].get("device_id")
            if device_id is not None and self._audio_service:
                if hasattr(self._audio_service, "set_audio_device"):
                    self._audio_service.set_audio_device(device_id)
                    app_logger.log_audio_event(
                        "Audio device reloaded", {"device_id": device_id}
                    )

    def _reload_whisper_gpu_config(self, config: Dict[str, Any]) -> None:
        """重新加载Whisper GPU配置"""
        if "whisper" in config:
            whisper_config = config["whisper"]

            # 检查 use_gpu 配置是否变更
            if "use_gpu" in whisper_config:
                new_use_gpu = whisper_config["use_gpu"]

                # 安全地获取当前 GPU 设置
                current_use_gpu = self._get_current_gpu_setting()

                # 只有在配置真正改变时才重载
                if current_use_gpu is not None and new_use_gpu != current_use_gpu:
                    app_logger.log_audio_event(
                        "GPU setting changed, reloading model...",
                        {
                            "old_use_gpu": current_use_gpu,
                            "new_use_gpu": new_use_gpu,
                        },
                    )

                    # 只有在未录音且未处理时才重载
                    if (
                        not self.state.is_recording()
                        and not self.state.is_processing()
                    ):
                        self._reload_model_with_gpu_setting(new_use_gpu)
                    else:
                        app_logger.log_audio_event(
                            "Cannot reload model during recording/processing",
                            {
                                "is_recording": self.state.is_recording(),
                                "is_processing": self.state.is_processing(),
                            },
                        )

    def _get_current_gpu_setting(self) -> Optional[bool]:
        """安全地获取当前GPU设置"""
        try:
            if self._speech_service and hasattr(self._speech_service, "model_manager"):
                # 通过model_manager获取whisper_engine
                whisper_engine = (
                    self._speech_service.model_manager.get_whisper_engine()
                )
                # 只在 whisper_engine 不为 None 时才尝试访问 use_gpu
                if whisper_engine is not None:
                    return getattr(whisper_engine, "use_gpu", None)
        except (AttributeError, RuntimeError) as e:
            app_logger.log_audio_event(
                "Warning: Could not retrieve current GPU setting",
                {
                    "error": str(e),
                    "action": "proceeding with config change",
                },
            )
        return None

    def _reload_model_with_gpu_setting(self, use_gpu: bool) -> None:
        """使用新的 GPU 设置重新加载模型

        Args:
            use_gpu: 是否使用 GPU
        """
        if self._speech_service and hasattr(self._speech_service, "reload_model"):

            def on_success(success: bool, error: str):
                # 安全地获取重加载后的设备信息
                device_info = "unknown"
                try:
                    if hasattr(self._speech_service, "model_manager"):
                        whisper_engine = (
                            self._speech_service.model_manager.get_whisper_engine()
                        )
                        if whisper_engine is not None:
                            device_info = getattr(whisper_engine, "device", "unknown")
                except (AttributeError, RuntimeError):
                    pass  # 继续记录事件，即使无法获取设备信息

                app_logger.log_audio_event(
                    "Model reloaded with new GPU setting",
                    {"use_gpu": use_gpu, "device": device_info},
                )

                # 获取模型详细信息并发送事件
                model_info = {}
                if hasattr(self._speech_service, "get_model_info"):
                    model_info = self._speech_service.get_model_info()
                else:
                    model_info = {
                        "model_name": self.config.get_setting(
                            "whisper.model", "Unknown"
                        ),
                        "is_loaded": True,
                        "device": device_info,
                    }
                self.events.emit("model.loading.completed", model_info)

            def on_error(error_msg: str):
                app_logger.log_error(Exception(error_msg), "reload_model_with_gpu")

            self._speech_service.reload_model(
                use_gpu=use_gpu, callback=on_success, error_callback=on_error
            )
        else:
            app_logger.log_audio_event("Speech service does not support hot reload", {})

    def _reload_transcription_provider(self, config: Dict[str, Any]) -> None:
        """重新加载转录提供商配置

        Args:
            config: 新的配置字典
        """
        if "transcription" in config:
            transcription_config = config["transcription"]

            # 检查 provider 配置是否变更
            if "provider" in transcription_config:
                new_provider = transcription_config["provider"]

                # 获取当前 provider
                current_provider = self.config.get_setting("transcription.provider", "local")

                # 只有在配置真正改变时才重载
                if new_provider != current_provider:
                    app_logger.log_audio_event(
                        "Transcription provider changed, reloading service...",
                        {
                            "old_provider": current_provider,
                            "new_provider": new_provider,
                        },
                    )

                    # 只有在未录音且未处理时才重载
                    if (
                        not self.state.is_recording()
                        and not self.state.is_processing()
                    ):
                        self._reload_transcription_service(new_provider)
                    else:
                        app_logger.log_audio_event(
                            "Cannot reload transcription service during recording/processing",
                            {
                                "is_recording": self.state.is_recording(),
                                "is_processing": self.state.is_processing(),
                            },
                        )

    def _reload_transcription_service(self, provider: str) -> None:
        """重新加载转录服务

        Args:
            provider: 新的转录提供商
        """
        if self._speech_service and hasattr(self._speech_service, "reload_service"):
            try:
                # 调用转录服务的重载方法
                self._speech_service.reload_service()
                app_logger.log_audio_event(
                    "Transcription service reloaded",
                    {"provider": provider},
                )
            except Exception as e:
                app_logger.log_error(e, "reload_transcription_service")
        else:
            app_logger.log_audio_event(
                "Transcription service reload not supported, please restart application",
                {"provider": provider},
            )

    def _notify_callbacks(self, config: Dict[str, Any]) -> None:
        """通知所有注册的回调函数"""
        for callback in self._reload_callbacks:
            try:
                callback(config)
            except Exception as e:
                app_logger.log_error(e, "config_reload_callback")

    # 设置器方法，用于服务依赖注入
    def set_speech_service(self, service: ISpeechService) -> None:
        """设置语音服务"""
        self._speech_service = service

    def set_audio_service(self, service: IAudioService) -> None:
        """设置音频服务"""
        self._audio_service = service

    def set_hotkey_service(self, service: IHotkeyService) -> None:
        """设置快捷键服务"""
        self._hotkey_service = service