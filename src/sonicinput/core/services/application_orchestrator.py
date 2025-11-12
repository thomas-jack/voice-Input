"""应用编排器实现

负责：
- 应用启动流程编排
- 服务依赖协调
- 生命周期阶段管理
- 错误处理和回滚
"""

from typing import Dict, List, Callable, Any, Optional
from enum import Enum
from ..interfaces import (
    IApplicationOrchestrator,
    IConfigService,
    IEventService,
    IStateManager,
    IAudioService,
    ISpeechService,
    IInputService,
    IHotkeyService,
    IConfigReloadService,
)
from ...utils import app_logger, VoiceInputError


class InitializationPhase(Enum):
    """初始化阶段枚举"""
    NOT_STARTED = "not_started"
    CORE_SERVICES = "core_services"
    CONTROLLERS = "controllers"
    HOTKEY_SETUP = "hotkey_setup"
    CONFIG_RELOAD = "config_reload"
    MODEL_LOADING = "model_loading"
    COMPLETED = "completed"


class ApplicationOrchestrator(IApplicationOrchestrator):
    """应用编排器实现

    职责：
    - 管理应用启动的各个阶段
    - 协调服务之间的依赖关系
    - 提供阶段化的初始化流程
    - 处理启动过程中的错误和回滚
    """

    def __init__(
        self,
        config_service: IConfigService,
        event_service: IEventService,
        state_manager: IStateManager,
        config_reload_service: IConfigReloadService,
    ):
        """初始化应用编排器

        Args:
            config_service: 配置服务
            event_service: 事件服务
            state_manager: 状态管理器
            config_reload_service: 配置重载服务
        """
        self.config = config_service
        self.events = event_service
        self.state = state_manager
        self.config_reload = config_reload_service

        # 初始化状态
        self._current_phase = InitializationPhase.NOT_STARTED
        self._startup_complete = False
        self._initialization_error: Optional[Exception] = None

        # 回调管理
        self._startup_callbacks: Dict[str, List[Callable]] = {}
        self._shutdown_callbacks: List[Callable] = []

        # 服务引用（运行时设置）
        self._audio_service: Optional[IAudioService] = None
        self._speech_service: Optional[ISpeechService] = None
        self._input_service: Optional[IInputService] = None
        self._hotkey_service: Optional[IHotkeyService] = None

        # 控制器引用（运行时设置）
        self._controllers: Dict[str, Any] = {}

        app_logger.log_audio_event("ApplicationOrchestrator initialized", {})

    def set_services(
        self,
        audio_service: IAudioService,
        speech_service: ISpeechService,
        input_service: IInputService,
        hotkey_service: IHotkeyService,
    ) -> None:
        """设置服务引用"""
        self._audio_service = audio_service
        self._speech_service = speech_service
        self._input_service = input_service
        self._hotkey_service = hotkey_service

    def set_controllers(self, **controllers) -> None:
        """设置控制器引用"""
        self._controllers.update(controllers)

    def orchestrate_startup(self) -> None:
        """编排应用启动流程"""
        if self._startup_complete:
            return

        try:
            app_logger.log_audio_event("Application startup orchestrated", {})

            # 按阶段初始化
            self._execute_phase(InitializationPhase.CORE_SERVICES, self._init_core_services)
            self._execute_phase(InitializationPhase.CONTROLLERS, self._init_controllers)
            self._execute_phase(InitializationPhase.HOTKEY_SETUP, self._init_hotkeys)
            self._execute_phase(InitializationPhase.CONFIG_RELOAD, self._init_config_reload)
            self._execute_phase(InitializationPhase.MODEL_LOADING, self._init_model_loading)

            # 标记启动完成
            self._current_phase = InitializationPhase.COMPLETED
            self._startup_complete = True

            # 触发启动完成事件
            self.events.emit("APP_STARTUP_COMPLETED")
            app_logger.log_audio_event("Application startup completed successfully", {})

        except Exception as e:
            self._initialization_error = e
            app_logger.log_error(e, "orchestrate_startup")

            # 尝试回滚
            self._rollback_initialization()
            raise VoiceInputError(f"Application startup failed: {e}")

    def orchestrate_shutdown(self) -> None:
        """编排应用关闭流程"""
        try:
            app_logger.log_audio_event("Application shutdown orchestrated", {})

            # 执行关闭回调
            for callback in self._shutdown_callbacks:
                try:
                    callback()
                except Exception as e:
                    app_logger.log_error(e, "shutdown_callback")

            # 停止录音
            recording_controller = self._controllers.get("recording")
            if recording_controller and hasattr(recording_controller, "is_recording") and recording_controller.is_recording():
                recording_controller.stop_recording()

            # 停止快捷键监听
            if self._hotkey_service:
                self._hotkey_service.stop_listening()
                self._hotkey_service.unregister_all_hotkeys()

            # 卸载模型
            if self._speech_service:
                self._speech_service.unload_model()

            # 清理音频服务 (修复PyAudio资源泄漏)
            if self._audio_service and hasattr(self._audio_service, "cleanup"):
                try:
                    self._audio_service.cleanup()
                    app_logger.log_audio_event("Audio service cleaned up", {})
                except Exception as e:
                    app_logger.log_error(e, "audio_service_cleanup")

            # 停止配置重载监控
            if self.config_reload and hasattr(self.config_reload, "stop_monitoring"):
                try:
                    self.config_reload.stop_monitoring()
                    app_logger.log_audio_event("Config reload monitoring stopped", {})
                except Exception as e:
                    app_logger.log_error(e, "config_reload_stop")

            self._current_phase = InitializationPhase.NOT_STARTED
            self._startup_complete = False

            app_logger.log_audio_event("Application shutdown completed", {})

        except Exception as e:
            app_logger.log_error(e, "orchestrate_shutdown")

    def get_initialization_phase(self) -> str:
        """获取当前初始化阶段"""
        return self._current_phase.value

    def is_startup_complete(self) -> bool:
        """检查启动是否完成"""
        return self._startup_complete

    def register_startup_callback(self, phase: str, callback: Callable) -> None:
        """注册启动阶段回调"""
        if phase not in self._startup_callbacks:
            self._startup_callbacks[phase] = []
        self._startup_callbacks[phase].append(callback)
        app_logger.log_audio_event(
            "Startup callback registered",
            {"phase": phase, "callback_count": len(self._startup_callbacks[phase])}
        )

    def register_shutdown_callback(self, callback: Callable) -> None:
        """注册关闭回调"""
        self._shutdown_callbacks.append(callback)
        app_logger.log_audio_event(
            "Shutdown callback registered",
            {"callback_count": len(self._shutdown_callbacks)}
        )

    def _execute_phase(self, phase: InitializationPhase, phase_handler: Callable) -> None:
        """执行初始化阶段"""
        self._current_phase = phase
        app_logger.log_audio_event(f"Starting initialization phase: {phase.value}", {})

        # 执行阶段处理器
        phase_handler()

        # 执行注册的回调
        callbacks = self._startup_callbacks.get(phase.value, [])
        for callback in callbacks:
            try:
                callback()
            except Exception as e:
                app_logger.log_error(e, f"phase_callback_{phase.value}")

        app_logger.log_audio_event(f"Completed initialization phase: {phase.value}", {})

    def _init_core_services(self) -> None:
        """初始化核心服务阶段"""
        # 配置日志系统
        from ...utils import logger
        logger.set_config_service(self.config)

        # 核心服务已在DI容器中初始化，这里只需验证
        if not all([
            self._audio_service,
            self._speech_service,
            self._input_service,
        ]):
            raise VoiceInputError("Core services not properly initialized")

    def _init_controllers(self) -> None:
        """初始化控制器阶段"""
        required_controllers = ["recording", "transcription", "ai", "input"]
        for controller_name in required_controllers:
            if controller_name not in self._controllers:
                raise VoiceInputError(f"Controller '{controller_name}' not initialized")

    def _init_hotkeys(self) -> None:
        """初始化快捷键阶段"""
        if not self._hotkey_service:
            raise VoiceInputError("Hotkey service not available")

        # 支持多快捷键配置（新旧格式兼容）
        from ..hotkey_config_helper import get_hotkeys_from_config
        from ..hotkey_manager_win32 import HotkeyConflictError
        from ...utils import HotkeyRegistrationError

        hotkeys, backend = get_hotkeys_from_config(self.config)

        # 注册所有快捷键，处理冲突
        registered_count = 0
        failed_hotkeys = []

        for hotkey in hotkeys:
            if hotkey and hotkey.strip():
                try:
                    self._hotkey_service.register_hotkey(hotkey.strip(), "toggle_recording")
                    registered_count += 1
                    app_logger.log_audio_event(
                        "Hotkey registered successfully",
                        {"hotkey": hotkey.strip()}
                    )
                except HotkeyConflictError as e:
                    # 记录冲突但不中断启动
                    failed_hotkeys.append(hotkey.strip())
                    app_logger.log_audio_event(
                        "Hotkey conflict detected",
                        {"hotkey": hotkey.strip(), "suggestions": e.suggestions}
                    )
                    # 发送事件通知UI
                    self.events.emit("HOTKEY_CONFLICT", {
                        "hotkey": e.hotkey,
                        "suggestions": e.suggestions,
                        "error_code": e.error_code,
                    })
                except HotkeyRegistrationError as e:
                    # 记录注册错误但不中断启动
                    failed_hotkeys.append(hotkey.strip())
                    app_logger.log_error(e, f"hotkey_registration_{hotkey}")
                    self.events.emit("HOTKEY_REGISTRATION_ERROR", {
                        "hotkey": hotkey.strip(),
                        "error": str(e),
                    })
                except Exception as e:
                    # 记录其他异常
                    failed_hotkeys.append(hotkey.strip())
                    app_logger.log_error(e, f"hotkey_unexpected_error_{hotkey}")

        # 至少注册了一个快捷键才启动监听
        if registered_count > 0:
            self._hotkey_service.start_listening()
            app_logger.log_audio_event(
                "Hotkeys initialized",
                {
                    "hotkeys": hotkeys,
                    "registered": registered_count,
                    "failed": len(failed_hotkeys),
                    "failed_hotkeys": failed_hotkeys,
                }
            )
        else:
            # 所有快捷键都注册失败
            app_logger.log_audio_event(
                "Warning: No hotkeys registered successfully",
                {"attempted": hotkeys, "failed": failed_hotkeys}
            )
            # 应用仍然可以启动，只是没有快捷键

    def _init_config_reload(self) -> None:
        """初始化配置重载阶段"""
        if not self.config_reload:
            raise VoiceInputError("Config reload service not available")

        # 设置服务依赖
        self.config_reload.set_speech_service(self._speech_service)
        self.config_reload.set_audio_service(self._audio_service)
        self.config_reload.set_hotkey_service(self._hotkey_service)

        # 启动监控
        self.config_reload.start_monitoring()
        app_logger.log_audio_event("Config reload monitoring enabled", {})

    def _init_model_loading(self) -> None:
        """初始化模型加载阶段"""
        if self._should_enable_auto_load():
            model_name = self.config.get_setting("whisper.model", "large-v3-turbo")
            app_logger.log_audio_event(
                "Auto-loading model on startup", {"model_name": model_name}
            )
            self._load_model_async(model_name)

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

    def _load_model_async(self, model_name: str) -> None:
        """异步加载语音模型"""
        from .event_bus import Events

        self.events.emit(Events.MODEL_LOADING_STARTED)

        def on_success(result: Dict[str, Any]):
            """成功回调

            Args:
                result: 包含以下键的字典:
                    - success: bool
                    - model_name: str
                    - model_info: Dict[str, Any]
            """
            success = result.get("success", False)
            result_model_name = result.get("model_name", model_name)
            model_info = result.get("model_info", {})

            app_logger.log_audio_event(
                "Model loaded successfully", {"model": result_model_name}
            )

            # 如果结果中没有model_info，尝试获取
            if not model_info:
                if hasattr(self._speech_service, "get_model_info"):
                    model_info = self._speech_service.get_model_info()
                else:
                    model_info = {
                        "model_name": result_model_name,
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

    def _rollback_initialization(self) -> None:
        """回滚初始化（错误处理）"""
        try:
            app_logger.log_audio_event("Rolling back initialization", {})

            # 停止快捷键监听
            if self._hotkey_service:
                self._hotkey_service.stop_listening()
                self._hotkey_service.unregister_all_hotkeys()

            # 重置状态
            self._current_phase = InitializationPhase.NOT_STARTED
            self._startup_complete = False

            app_logger.log_audio_event("Initialization rollback completed", {})

        except Exception as e:
            app_logger.log_error(e, "rollback_initialization")