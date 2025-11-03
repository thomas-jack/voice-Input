"""主应用协调器

职责：
- 协调各个控制器
- 管理应用生命周期
- 提供简单的对外接口
- 不再直接处理业务逻辑
"""

from typing import Optional, Any
from .di_container import DIContainer
from .controllers import (
    RecordingController,
    TranscriptionController,
    AIProcessingController,
    InputController,
)
from .interfaces import (
    IConfigService,
    IEventService,
    IStateManager,
    IAudioService,
    ISpeechService,
    IInputService,
    IHotkeyService,
)
from .services.event_bus import Events
from ..utils import app_logger, logger, VoiceInputError


class VoiceInputApp:
    """应用协调器

    架构改进：
    - 使用控制器模式拆分职责
    - 通过事件总线解耦组件
    - 使用 StateManager 统一状态管理
    - UI 层通过事件通信
    """

    def __init__(self, container: Optional[DIContainer] = None):
        # 依赖注入容器
        self.container = container or DIContainer()

        # 核心服务
        self.config: IConfigService = self.container.get(IConfigService)
        self.events: IEventService = self.container.get(IEventService)
        self.state: IStateManager = self.container.get(IStateManager)

        # 业务服务（延迟初始化）
        self._audio_service: Optional[IAudioService] = None
        self._speech_service: Optional[ISpeechService] = None
        self._input_service: Optional[IInputService] = None
        self._hotkey_service: Optional[IHotkeyService] = None

        # 控制器（延迟初始化）
        self._recording_controller: Optional[RecordingController] = None
        self._transcription_controller: Optional[TranscriptionController] = None
        self._ai_controller: Optional[AIProcessingController] = None
        self._input_controller: Optional[InputController] = None

        # 应用状态
        self.is_initialized = False

        # UI 组件（向后兼容）
        self.recording_overlay = None

        app_logger.log_audio_event("VoiceInputApp initialized", {})

    @property
    def whisper_engine(self) -> Optional[ISpeechService]:
        """向后兼容属性 - MainWindow 期望此属性存在"""
        return self._speech_service

    def initialize(self) -> None:
        """初始化应用"""
        if self.is_initialized:
            return

        try:
            # 配置日志系统
            logger.set_config_service(self.config)

            app_logger.log_audio_event("Initializing voice input app", {})

            # 初始化核心服务
            self._audio_service = self.container.get(IAudioService)
            self._speech_service = self.container.get(ISpeechService)
            self._input_service = self.container.get(IInputService)

            # 初始化控制器
            self._init_controllers()

            # 初始化快捷键服务（仅使用久经测试的 legacy 实现）
            # 注意：GlobalHotkeys 新实现已被禁用，确保稳定性
            from .hotkey_manager import HotkeyManager

            self._hotkey_service = HotkeyManager(self._on_hotkey_triggered)
            app_logger.log_audio_event("Using legacy HotkeyManager (stable)", {})

            # 支持多快捷键：优先读取 "hotkeys" 数组，回退到单个 "hotkey"
            hotkeys = self.config.get_setting("hotkeys", None)
            if hotkeys is None:  # 向后兼容单个 hotkey
                single_hotkey = self.config.get_setting("hotkey", "ctrl+shift+v")
                hotkeys = [single_hotkey]

            # 注册所有快捷键
            for hotkey in hotkeys:
                if hotkey and hotkey.strip():  # 跳过空字符串
                    self._hotkey_service.register_hotkey(
                        hotkey.strip(), "toggle_recording"
                    )

            self._hotkey_service.start_listening()

            # 注册配置热重载监听器
            self.events.on("config.changed", self._on_config_changed)
            app_logger.log_audio_event("Config hot reload enabled", {})

            # 自动加载模型（如果配置启用）
            if self._should_enable_auto_load():
                model_name = self.config.get_setting("whisper.model", "large-v3-turbo")
                app_logger.log_audio_event(
                    "Auto-loading model on startup", {"model_name": model_name}
                )
                self._load_model_async()

            self.is_initialized = True
            self.events.emit(Events.APP_STARTED)

            app_logger.log_audio_event("Voice input app initialized", {})

        except Exception as e:
            app_logger.log_error(e, "initialize")
            self.events.emit(Events.APP_ERROR, str(e))
            raise VoiceInputError(f"Failed to initialize app: {e}")

    def initialize_with_validation(self) -> None:
        """向后兼容方法 - main.py 中环境验证已在外部完成

        注意: main.py 已经在调用此方法前完成了环境验证，
        因此这里只需调用 initialize()
        """
        self.initialize()

    def _init_controllers(self) -> None:
        """初始化所有控制器"""
        # 录音控制器
        self._recording_controller = RecordingController(
            audio_service=self._audio_service,
            config_service=self.config,
            event_service=self.events,
            state_manager=self.state,
            speech_service=self._speech_service,
        )

        # 转录控制器
        self._transcription_controller = TranscriptionController(
            speech_service=self._speech_service,
            config_service=self.config,
            event_service=self.events,
            state_manager=self.state,
        )

        # AI处理控制器
        self._ai_controller = AIProcessingController(
            config_service=self.config,
            event_service=self.events,
            state_manager=self.state,
        )

        # 输入控制器
        self._input_controller = InputController(
            input_service=self._input_service,
            config_service=self.config,
            event_service=self.events,
            state_manager=self.state,
        )

        app_logger.log_audio_event("All controllers initialized", {})

    def _should_enable_auto_load(self) -> bool:
        """判断是否应该启用自动加载"""
        # 检查转录提供商
        provider = self.config.get_setting("transcription.provider", "local")

        # 如果使用云端转录，不自动加载本地模型
        if provider != "local":
            return False

        # 否则根据配置决定
        return self.config.get_setting(
            "transcription.local.auto_load",
            self.config.get_setting("whisper.auto_load", True),
        )

    def _load_model_async(self) -> None:
        """异步加载语音模型"""
        model_name = self.config.get_setting("whisper.model", "large-v3-turbo")
        self.events.emit(Events.MODEL_LOADING_STARTED)

        def on_success(success: bool, error: str):
            app_logger.log_audio_event(
                "Model loaded successfully", {"model": model_name}
            )
            # 获取模型详细信息并发送事件
            model_info = {}
            if hasattr(self._speech_service, "get_model_info"):
                model_info = self._speech_service.get_model_info()
            else:
                model_info = {
                    "model_name": model_name,
                    "is_loaded": True,
                    "device": getattr(self._speech_service, "device", "Unknown"),
                }
            self.events.emit(Events.MODEL_LOADING_COMPLETED, model_info)

        def on_error(error_msg: str):
            app_logger.log_error(Exception(error_msg), "load_model_async")
            self.events.emit(Events.MODEL_LOADING_ERROR, error_msg)

        self._speech_service.load_model_async(
            model_name=model_name, callback=on_success, error_callback=on_error
        )

    def _on_hotkey_triggered(self, action: str) -> None:
        """快捷键触发处理"""
        if action == "toggle_recording":
            self.toggle_recording()

    def toggle_recording(self) -> None:
        """切换录音状态"""
        if self._recording_controller:
            self._recording_controller.toggle_recording()

    def set_recording_overlay(self, recording_overlay) -> None:
        """设置录音悬浮窗 (向后兼容方法)

        注意: 在重构架构中，UI 应该通过事件通信，
        但为了向后兼容，我们保留此方法并设置事件监听
        """
        self.recording_overlay = recording_overlay

        # 设置事件监听以控制悬浮窗
        if recording_overlay:
            # 成功事件
            self.events.on(Events.RECORDING_STARTED, self._on_recording_started_overlay)
            self.events.on(Events.RECORDING_STOPPED, self._on_recording_stopped_overlay)
            self.events.on(Events.AI_PROCESSING_STARTED, self._on_ai_started_overlay)
            self.events.on(
                Events.AI_PROCESSING_COMPLETED, self._on_ai_completed_overlay
            )
            self.events.on(
                Events.TEXT_INPUT_COMPLETED, self._on_input_completed_overlay
            )
            self.events.on(
                Events.AUDIO_LEVEL_UPDATE, self._on_audio_level_update_overlay
            )

            # 错误事件 - 关闭悬浮窗
            self.events.on(Events.TRANSCRIPTION_ERROR, self._on_error_overlay)
            self.events.on(Events.AI_PROCESSING_ERROR, self._on_error_overlay)
            self.events.on(Events.TEXT_INPUT_ERROR, self._on_error_overlay)

    def _on_recording_started_overlay(self, data: Any = None) -> None:
        """录音开始时显示悬浮窗"""
        if self.recording_overlay:
            self.recording_overlay.show_recording()

    def _on_recording_stopped_overlay(self, data: dict) -> None:
        """录音停止时更新悬浮窗状态"""
        if self.recording_overlay:
            self.recording_overlay.show_processing()

    def _on_ai_started_overlay(self, data: Any = None) -> None:
        """AI处理开始时更新悬浮窗状态"""
        if self.recording_overlay:
            self.recording_overlay.set_status_text("AI Processing...")

    def _on_ai_completed_overlay(self, data: Any = None) -> None:
        """AI处理完成时更新悬浮窗状态为完成（绿色）"""
        if self.recording_overlay:
            from ..ui.overlay import StatusIndicator

            self.recording_overlay.status_indicator.set_state(
                StatusIndicator.STATE_COMPLETED
            )

    def _on_input_completed_overlay(self, text: str) -> None:
        """输入完成时隐藏悬浮窗"""
        if self.recording_overlay:
            self.recording_overlay.show_completed(delay_ms=500)

    def _on_error_overlay(self, error_msg: str) -> None:
        """处理错误时隐藏悬浮窗"""
        if self.recording_overlay:
            # 显示完成状态，然后快速隐藏（1秒后）
            self.recording_overlay.show_completed(delay_ms=1000)

    def _on_audio_level_update_overlay(self, level: float) -> None:
        """音频级别更新时更新悬浮窗音量条"""
        if self.recording_overlay:
            self.recording_overlay.update_audio_level(level)

    def reload_hotkeys(self) -> bool:
        """重新加载快捷键配置（支持多快捷键）"""
        try:
            if self._hotkey_service:
                # 注销所有旧快捷键
                self._hotkey_service.unregister_all_hotkeys()

                # 从配置读取新快捷键列表
                hotkeys = self.config.get_setting("hotkeys", None)
                if hotkeys is None:  # 向后兼容单个hotkey
                    single_hotkey = self.config.get_setting("hotkey", "ctrl+shift+v")
                    hotkeys = [single_hotkey]

                # 注册所有新快捷键
                registered_count = 0
                for hotkey in hotkeys:
                    if hotkey and hotkey.strip():
                        self._hotkey_service.register_hotkey(
                            hotkey.strip(), "toggle_recording"
                        )
                        registered_count += 1

                app_logger.log_audio_event(
                    "Hotkeys reloaded", {"hotkeys": hotkeys, "count": registered_count}
                )
                return True
            return False

        except Exception as e:
            app_logger.log_error(e, "reload_hotkeys")
            return False

    def _on_config_changed(self, data: dict) -> None:
        """配置变更事件处理器 - 热重载配置"""
        try:
            new_config = data.get("config", {})
            app_logger.log_audio_event(
                "Config changed, reloading...", {"timestamp": data.get("timestamp")}
            )

            # 1. 重新加载日志配置
            if "logging" in new_config:
                logger.set_config_service(self.config)
                app_logger.log_audio_event(
                    "Logger config reloaded",
                    {
                        "level": new_config["logging"].get("level"),
                        "console_output": new_config["logging"].get("console_output"),
                    },
                )

            # 2. 重新加载快捷键
            if "hotkeys" in new_config or "hotkey" in new_config:
                self.reload_hotkeys()

            # 3. 重新加载音频设备（如果未录音）
            if "audio" in new_config and not self.state.is_recording():
                device_id = new_config["audio"].get("device_id")
                if device_id is not None and self._audio_service:
                    if hasattr(self._audio_service, "set_audio_device"):
                        self._audio_service.set_audio_device(device_id)
                        app_logger.log_audio_event(
                            "Audio device reloaded", {"device_id": device_id}
                        )

            # 4. 处理 Whisper GPU 配置变更（需要重新加载模型）
            if "whisper" in new_config:
                whisper_config = new_config["whisper"]

                # 检查 use_gpu 配置是否变更
                if "use_gpu" in whisper_config:
                    new_use_gpu = whisper_config["use_gpu"]

                    # 安全地获取当前 GPU 设置，通过新API访问
                    current_use_gpu = None
                    if self._speech_service and hasattr(
                        self._speech_service, "model_manager"
                    ):
                        try:
                            # 通过model_manager获取whisper_engine
                            whisper_engine = (
                                self._speech_service.model_manager.get_whisper_engine()
                            )
                            # 只在 whisper_engine 不为 None 时才尝试访问 use_gpu
                            if whisper_engine is not None:
                                current_use_gpu = getattr(
                                    whisper_engine, "use_gpu", None
                                )
                        except (AttributeError, RuntimeError) as e:
                            app_logger.log_audio_event(
                                "Warning: Could not retrieve current GPU setting",
                                {
                                    "error": str(e),
                                    "action": "proceeding with config change",
                                },
                            )

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

            app_logger.log_audio_event("Config hot reload completed", {})

        except Exception as e:
            app_logger.log_error(e, "_on_config_changed")

    def _reload_model_with_gpu_setting(self, use_gpu: bool) -> None:
        """使用新的 GPU 设置重新加载模型

        Args:
            use_gpu: 是否使用 GPU
        """
        if self._speech_service and hasattr(self._speech_service, "reload_model"):

            def on_success(success: bool, error: str):
                # 安全地获取重加载后的设备信息，通过新API访问
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
                self.events.emit(Events.MODEL_LOADING_COMPLETED, model_info)

            def on_error(error_msg: str):
                app_logger.log_error(Exception(error_msg), "reload_model_with_gpu")

            self._speech_service.reload_model(
                use_gpu=use_gpu, callback=on_success, error_callback=on_error
            )
        else:
            app_logger.log_audio_event("Speech service does not support hot reload", {})

    def get_status(self) -> dict:
        """获取应用状态"""
        return {
            "is_initialized": self.is_initialized,
            "is_recording": self.state.is_recording(),
            "is_processing": self.state.is_processing(),
            "model_loaded": (
                self._speech_service.model_manager.is_model_loaded()
                if self._speech_service
                and hasattr(self._speech_service, "model_manager")
                else False
            ),
            "hotkey_active": self._hotkey_service.is_listening
            if self._hotkey_service
            else False,
        }

    def shutdown(self) -> None:
        """关闭应用"""
        try:
            app_logger.log_audio_event("Shutting down voice input app", {})

            # 停止录音
            if self._recording_controller and self._recording_controller.is_recording():
                self._recording_controller.stop_recording()

            # 停止快捷键监听
            if self._hotkey_service:
                self._hotkey_service.stop_listening()
                self._hotkey_service.unregister_all_hotkeys()

            # 卸载模型
            if self._speech_service:
                self._speech_service.unload_model()

            # 清理容器
            self.container.cleanup()

            app_logger.log_shutdown()

        except Exception as e:
            app_logger.log_error(e, "shutdown")
