"""UI服务实现

真正的UI服务实现，直接依赖核心服务，不依赖VoiceInputApp。
采用纯依赖注入模式，符合SOLID原则。
"""

from typing import Dict, Any, Optional
from ..interfaces import (
    IUIMainService, IUISettingsService, IUIModelService,
    IUIAudioService, IUIGPUService, IEventService, IConfigService,
    IStateManager, ISpeechService, IHistoryStorageService
)
from ...utils import app_logger


class UIMainService:
    """UI主窗口服务实现

    直接依赖核心服务，通过事件驱动实现功能。
    """

    def __init__(
        self,
        config_service: IConfigService,
        event_service: IEventService,
        state_manager: IStateManager
    ):
        """初始化UI主服务

        Args:
            config_service: 配置服务
            event_service: 事件服务
            state_manager: 状态管理器
        """
        self.config = config_service
        self.events = event_service
        self.state = state_manager
        app_logger.log_audio_event("UIMainService initialized", {})

    def is_recording(self) -> bool:
        """检查是否正在录音"""
        return self.state.is_recording

    def start_recording(self) -> None:
        """开始录音

        通过事件驱动，不直接调用控制器
        """
        from ...utils.constants import Events
        self.events.emit(Events.RECORDING_STARTED)

    def stop_recording(self) -> None:
        """停止录音

        通过事件驱动，不直接调用控制器
        """
        from ...utils.constants import Events
        self.events.emit(Events.RECORDING_STOPPED)

    def get_current_status(self) -> str:
        """获取当前状态文本"""
        if self.is_recording():
            return "Recording..."
        return "Ready"

    def get_event_service(self) -> IEventService:
        """获取事件服务"""
        return self.events

    def show_settings(self) -> None:
        """显示设置窗口

        这个方法在MainWindow中实现，这里不需要实现
        """
        pass

    def reload_hotkeys(self) -> None:
        """重新加载快捷键配置

        通过配置重载服务实现
        """
        from ...utils.constants import Events
        self.events.emit(Events.CONFIG_CHANGED, {"section": "hotkeys"})

    def get_whisper_engine(self) -> Optional[Any]:
        """获取Whisper引擎

        注意：这个方法在新架构中应该通过 IUIModelService 访问，
        这里保留是为了向后兼容。
        """
        # 通过容器获取 speech service
        # 但这里我们没有容器的引用...
        # 这个方法应该被废弃，UI应该使用 IUIModelService
        app_logger.log_audio_event(
            "UIMainService.get_whisper_engine() called - deprecated",
            {"message": "Use IUIModelService instead"}
        )
        return None

    def cleanup(self) -> None:
        """清理资源"""
        app_logger.log_audio_event("UIMainService cleanup", {})


class UISettingsService:
    """UI设置服务实现

    封装配置服务，提供UI友好的接口。
    """

    def __init__(self, config_service: IConfigService, event_service: IEventService, history_service: IHistoryStorageService):
        """初始化UI设置服务

        Args:
            config_service: 配置服务
            event_service: 事件服务
            history_service: 历史记录存储服务
        """
        self.config_service = config_service
        self.event_service = event_service
        self.history_service = history_service
        app_logger.log_audio_event("UISettingsService initialized", {})

    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有设置"""
        return self.config_service.get_all_settings()

    def set_setting(self, key: str, value: Any) -> None:
        """设置单个配置项"""
        self.config_service.set_setting(key, value)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取单个配置项"""
        return self.config_service.get_setting(key, default)

    def save_settings(self) -> None:
        """保存设置到文件"""
        if hasattr(self.config_service, 'save_config'):
            self.config_service.save_config()

    def export_config(self, file_path: str) -> None:
        """导出配置到文件"""
        if hasattr(self.config_service, 'export_config'):
            self.config_service.export_config(file_path)

    def import_config(self, file_path: str) -> None:
        """从文件导入配置"""
        if hasattr(self.config_service, 'import_config'):
            self.config_service.import_config(file_path)

    def reset_to_defaults(self) -> None:
        """重置为默认配置"""
        if hasattr(self.config_service, 'reset_to_defaults'):
            self.config_service.reset_to_defaults()

    def get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        if hasattr(self.config_service, '_default_config'):
            return self.config_service._default_config
        return {}

    def get_event_service(self) -> IEventService:
        """获取事件服务"""
        return self.event_service

    def get_history_service(self) -> IHistoryStorageService:
        """获取历史记录存储服务"""
        return self.history_service


class UIModelService:
    """UI模型管理服务实现

    直接依赖语音服务，提供模型管理功能。
    """

    def __init__(self, speech_service: ISpeechService):
        """初始化UI模型服务

        Args:
            speech_service: 语音识别服务
        """
        self.speech_service = speech_service
        app_logger.log_audio_event("UIModelService initialized", {})

    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        if self.speech_service and hasattr(self.speech_service, 'is_model_loaded'):
            return self.speech_service.is_model_loaded
        return False

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        # TranscriptionService 包装了实际的 WhisperEngine
        # 需要通过 whisper_engine 属性访问
        engine = None
        if hasattr(self.speech_service, 'whisper_engine'):
            engine = self.speech_service.whisper_engine
        elif hasattr(self.speech_service, '_engine'):
            engine = self.speech_service._engine

        if engine and hasattr(engine, 'get_model_info'):
            return engine.get_model_info()

        # Fallback: 构建基本信息
        if engine:
            return {
                "is_loaded": getattr(engine, 'is_model_loaded', False),
                "model_name": getattr(engine, 'model_name', 'Unknown'),
                "device": getattr(engine, 'device', 'Unknown')
            }

        return {"is_loaded": False, "model_name": "Unknown", "device": "Unknown"}

    def load_model(self, model_name: str) -> None:
        """加载模型"""
        engine = self._get_engine()
        if engine and hasattr(engine, 'load_model'):
            engine.load_model(model_name)

    def unload_model(self) -> None:
        """卸载模型"""
        engine = self._get_engine()
        if engine and hasattr(engine, 'unload_model'):
            engine.unload_model()

    def test_model(self) -> Dict[str, Any]:
        """测试模型"""
        engine = self._get_engine()
        if not engine:
            return {"success": False, "error": "No engine available"}

        if not self.is_model_loaded():
            return {"success": False, "error": "Model not loaded"}

        return {
            "success": True,
            "model_name": getattr(engine, 'model_name', 'Unknown'),
            "device": getattr(engine, 'device', 'Unknown')
        }

    def _get_engine(self) -> Optional[Any]:
        """获取底层引擎（内部方法）"""
        if hasattr(self.speech_service, 'whisper_engine'):
            return self.speech_service.whisper_engine
        elif hasattr(self.speech_service, '_engine'):
            return self.speech_service._engine
        return None


class UIAudioService:
    """UI音频服务实现

    提供音频设备管理功能。
    """

    def __init__(self):
        """初始化UI音频服务"""
        app_logger.log_audio_event("UIAudioService initialized", {})

    def get_audio_devices(self) -> list:
        """获取可用音频设备列表"""
        try:
            from ...audio.recorder import AudioRecorder
            temp_recorder = AudioRecorder()
            devices = temp_recorder.get_audio_devices()
            temp_recorder.cleanup()
            return devices
        except Exception as e:
            app_logger.log_error(e, "get_audio_devices")
            return []

    def refresh_audio_devices(self) -> None:
        """刷新音频设备列表

        主要用于UI刷新，具体实现可能需要重新初始化录音器
        """
        pass


class UIGPUService:
    """UI GPU服务实现

    提供GPU信息查询功能。
    """

    def __init__(self):
        """初始化UI GPU服务"""
        app_logger.log_audio_event("UIGPUService initialized", {})

    def get_gpu_info(self) -> Dict[str, Any]:
        """获取GPU信息"""
        try:
            from ...speech.gpu_manager import GPUManager
            temp_gpu_manager = GPUManager()
            gpu_info = temp_gpu_manager.get_device_info()
            return gpu_info
        except Exception as e:
            app_logger.log_error(e, "get_gpu_info")
            return {"error": str(e), "cuda_available": False}

    def check_gpu_availability(self) -> bool:
        """检查GPU是否可用"""
        gpu_info = self.get_gpu_info()
        return gpu_info.get("cuda_available", False)
