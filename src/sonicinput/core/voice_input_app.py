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
    IConfigReloadService,
    IApplicationOrchestrator,
    IUIEventBridge,
    IHistoryStorageService,
)
from .services.event_bus import Events
from ..utils import app_logger, logger, VoiceInputError


class VoiceInputApp:
    """应用协调器

    架构改进：
    - 使用控制器模式拆分职责
    - 通过事件总线解耦组件
    - 使用 StateManager 统一状态管理
    - 使用 ApplicationOrchestrator 编排启动流程
    - 使用 UIEventBridge 解耦UI层通信
    - UI 层通过事件通信
    """

    def __init__(self, container: Optional[DIContainer] = None):
        # 依赖注入容器
        self.container = container or DIContainer()

        # 核心服务
        self.config: IConfigService = self.container.get(IConfigService)
        self.events: IEventService = self.container.get(IEventService)
        self.state: IStateManager = self.container.get(IStateManager)
        self.config_reload: IConfigReloadService = self.container.get(IConfigReloadService)

        # 新增服务 - 应用编排和UI事件桥接
        self.orchestrator: IApplicationOrchestrator = self.container.get(IApplicationOrchestrator)
        self.ui_bridge: IUIEventBridge = self.container.get(IUIEventBridge)

        # 业务服务（延迟初始化）
        self._audio_service: Optional[IAudioService] = None
        self._speech_service: Optional[ISpeechService] = None
        self._input_service: Optional[IInputService] = None
        self._hotkey_service: Optional[IHotkeyService] = None
        self._history_service: Optional[IHistoryStorageService] = None

        # 控制器（延迟初始化）
        self._recording_controller: Optional[RecordingController] = None
        self._transcription_controller: Optional[TranscriptionController] = None
        self._ai_controller: Optional[AIProcessingController] = None
        self._input_controller: Optional[InputController] = None

        # 应用状态
        self.is_initialized = False

        # UI 组件（向后兼容）
        self.recording_overlay = None

        app_logger.log_audio_event("VoiceInputApp initialized with orchestrator and UI bridge", {})

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

            app_logger.log_audio_event("Initializing voice input app with orchestrator", {})

            # 初始化核心服务
            self._audio_service = self.container.get(IAudioService)
            self._speech_service = self.container.get(ISpeechService)
            self._input_service = self.container.get(IInputService)
            self._history_service = self.container.get(IHistoryStorageService)

            # 初始化快捷键服务（支持win32和pynput后端）
            from .hotkey_manager import create_hotkey_manager
            from .hotkey_config_helper import get_hotkeys_from_config

            # 读取配置确定后端
            _, backend = get_hotkeys_from_config(self.config)

            self._hotkey_service = create_hotkey_manager(
                self._on_hotkey_triggered,
                backend=backend,
                config=self.config
            )
            app_logger.log_audio_event(
                "Hotkey service created with backend",
                {"backend": backend}
            )

            # 初始化控制器
            self._init_controllers()

            # 设置编排器依赖
            self.orchestrator.set_services(
                audio_service=self._audio_service,
                speech_service=self._speech_service,
                input_service=self._input_service,
                hotkey_service=self._hotkey_service,
            )
            self.orchestrator.set_controllers(
                recording=self._recording_controller,
                transcription=self._transcription_controller,
                ai=self._ai_controller,
                input=self._input_controller,
            )

            # 注册关闭回调
            self.orchestrator.register_shutdown_callback(self._cleanup_resources)

            # 使用编排器执行启动流程
            self.orchestrator.orchestrate_startup()

            self.is_initialized = True
            self.events.emit(Events.APP_STARTED)

            app_logger.log_audio_event("Voice input app initialized successfully", {})

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
            history_service=self._history_service,
        )

        # 转录控制器
        self._transcription_controller = TranscriptionController(
            speech_service=self._speech_service,
            config_service=self.config,
            event_service=self.events,
            state_manager=self.state,
            history_service=self._history_service,
        )

        # AI处理控制器
        self._ai_controller = AIProcessingController(
            config_service=self.config,
            event_service=self.events,
            state_manager=self.state,
            history_service=self._history_service,
        )

        # 输入控制器
        self._input_controller = InputController(
            input_service=self._input_service,
            config_service=self.config,
            event_service=self.events,
            state_manager=self.state,
        )

        app_logger.log_audio_event("All controllers initialized", {})

    
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

        注意: 现在使用 UIEventBridge 处理UI事件通信
        """
        self.recording_overlay = recording_overlay

        # 使用UI事件桥接器设置事件监听
        self.ui_bridge.setup_overlay_events(recording_overlay)

    def reload_hotkeys(self) -> bool:
        """重新加载快捷键配置（支持多快捷键）"""
        try:
            if self._hotkey_service:
                # 注销所有旧快捷键
                self._hotkey_service.unregister_all_hotkeys()

                # 从配置读取新快捷键列表（支持新旧格式）
                from .hotkey_config_helper import get_hotkeys_from_config
                from .hotkey_manager_win32 import HotkeyConflictError
                from ..utils import HotkeyRegistrationError

                hotkeys, backend = get_hotkeys_from_config(self.config)

                # 注册所有新快捷键，处理冲突
                registered_count = 0
                failed_hotkeys = []

                for hotkey in hotkeys:
                    if hotkey and hotkey.strip():
                        try:
                            self._hotkey_service.register_hotkey(
                                hotkey.strip(), "toggle_recording"
                            )
                            registered_count += 1
                        except HotkeyConflictError as e:
                            # 记录冲突但继续处理其他快捷键
                            failed_hotkeys.append(hotkey.strip())
                            app_logger.log_audio_event(
                                "Hotkey conflict during reload",
                                {"hotkey": hotkey.strip(), "suggestions": e.suggestions}
                            )
                            # 发送事件通知UI
                            self.events.emit("HOTKEY_CONFLICT", {
                                "hotkey": e.hotkey,
                                "suggestions": e.suggestions,
                                "error_code": e.error_code,
                            })
                        except HotkeyRegistrationError as e:
                            failed_hotkeys.append(hotkey.strip())
                            app_logger.log_error(e, f"hotkey_registration_{hotkey}")
                            self.events.emit("HOTKEY_REGISTRATION_ERROR", {
                                "hotkey": hotkey.strip(),
                                "error": str(e),
                            })
                        except Exception as e:
                            failed_hotkeys.append(hotkey.strip())
                            app_logger.log_error(e, f"hotkey_unexpected_error_{hotkey}")

                app_logger.log_audio_event(
                    "Hotkeys reloaded",
                    {
                        "hotkeys": hotkeys,
                        "registered": registered_count,
                        "failed": len(failed_hotkeys),
                        "failed_hotkeys": failed_hotkeys,
                        "backend": backend,
                    }
                )
                return registered_count > 0
            return False

        except Exception as e:
            app_logger.log_error(e, "reload_hotkeys")
            return False

    
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

    def _cleanup_resources(self) -> None:
        """清理应用资源（供编排器调用）"""
        try:
            app_logger.log_audio_event("Cleaning up application resources", {})

            # 移除UI事件桥接
            self.ui_bridge.remove_overlay_events()

            # 清理容器
            self.container.cleanup()

            app_logger.log_audio_event("Application resources cleaned up", {})

        except Exception as e:
            app_logger.log_error(e, "_cleanup_resources")

    def shutdown(self) -> None:
        """关闭应用"""
        try:
            app_logger.log_audio_event("Shutting down voice input app", {})

            # 使用编排器执行关闭流程
            if hasattr(self.orchestrator, 'orchestrate_shutdown'):
                self.orchestrator.orchestrate_shutdown()
            else:
                # 回退到直接清理
                self._cleanup_resources()

            app_logger.log_shutdown()

        except Exception as e:
            app_logger.log_error(e, "shutdown")

    def get_initialization_phase(self) -> str:
        """获取当前初始化阶段（委托给编排器）"""
        return self.orchestrator.get_initialization_phase()

    def is_startup_complete(self) -> bool:
        """检查启动是否完成（委托给编排器）"""
        return self.orchestrator.is_startup_complete()
