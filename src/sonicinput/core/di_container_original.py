"""依赖注入容器"""

import threading
import time
from typing import Dict, Type, Any, TypeVar, Callable, Optional

# 显式导入接口（避免import *）
from .interfaces.ai import IAIService
from .interfaces.audio import IAudioService
from .interfaces.config import IConfigService
from .interfaces.event import IEventService
from .interfaces.hotkey import IHotkeyService
from .interfaces.input import IInputService
from .interfaces.speech import ISpeechService
from .interfaces.state import IStateManager

# 服务实现
from .services.config_service import ConfigService
from .services.event_bus import EventBus
from .services.state_manager import StateManager
from .services.transcription_service import TranscriptionService
from .hotkey_manager import HotkeyManager
from ..audio import AudioRecorder
from ..speech import WhisperEngine
from ..ai import AIClientFactory
from ..input import SmartTextInput


T = TypeVar('T')


class DIContainer:
    """依赖注入容器"""

    def __init__(self):
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
        self._get_lock = threading.RLock()  # 线程安全锁

        # 注册核心服务工厂
        self._register_factories()
    
    def _register_factories(self) -> None:
        """注册服务工厂方法"""

        # 事件服务 - 单例（最先创建，因为其他服务依赖它）
        self._factories[IEventService] = lambda: EventBus()

        # 配置服务 - 单例（需要 EventService）
        def create_config():
            event_service = self.get(IEventService)
            return ConfigService(event_service=event_service)
        self._factories[IConfigService] = create_config

        # 状态管理器 - 单例（需要 EventService）
        def create_state_manager():
            event_service = self.get(IEventService)
            return StateManager(event_service=event_service)
        self._factories[IStateManager] = create_state_manager

        # 音频服务
        self._factories[IAudioService] = self._create_audio_service

        # 语音服务
        self._factories[ISpeechService] = self._create_speech_service

        # AI服务
        self._factories[IAIService] = self._create_ai_service

        # 输入服务
        self._factories[IInputService] = self._create_input_service

        # 快捷键服务
        self._factories[IHotkeyService] = self._create_hotkey_service
    
    def _create_audio_service(self) -> IAudioService:
        """创建音频服务"""
        config = self.get(IConfigService)
        sample_rate = config.get_setting("audio.sample_rate", 16000)
        channels = config.get_setting("audio.channels", 1)
        chunk_size = config.get_setting("audio.chunk_size", 1024)

        return AudioRecorder(
            sample_rate=sample_rate,
            channels=channels,
            chunk_size=chunk_size,
            config_service=config
        )
    
    def _create_speech_service(self) -> ISpeechService:
        """创建语音服务 - 使用TranscriptionService包装WhisperEngine"""
        # === DEBUG: 语音服务创建开始 ===
        import traceback
        start_time = time.time()
        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name

        # 获取logger（避免循环导入）
        try:
            from ...utils import app_logger
        except ImportError:
            app_logger = None

        if app_logger:
            app_logger.debug("=== DI CREATE SPEECH SERVICE DEBUG START ===")
            app_logger.debug(f"Thread: {thread_name} (ID: {thread_id})")

        try:
            # === DEBUG: 获取配置服务 ===
            if app_logger:
                app_logger.debug("Getting IConfigService...")

            config = self.get(IConfigService)

            if app_logger:
                app_logger.debug("Config service obtained successfully")
                app_logger.debug(f"Config service type: {type(config).__name__}")

            # === DEBUG: 获取模型配置 ===
            model_name = config.get_setting("whisper.model", "large-v3-turbo")
            use_gpu = config.get_setting("whisper.use_gpu", None)  # None = auto-detect

            if app_logger:
                app_logger.debug(f"Model configuration:")
                app_logger.debug(f"  - model_name: {model_name}")
                app_logger.debug(f"  - use_gpu: {use_gpu}")

            # === DEBUG: 创建WhisperEngine ===
            if app_logger:
                app_logger.debug("Creating WhisperEngine...")

            # 创建WhisperEngine，传递 use_gpu 配置
            whisper_engine = WhisperEngine(model_name, use_gpu=use_gpu)

            if app_logger:
                app_logger.debug("WhisperEngine created successfully")
                app_logger.debug(f"WhisperEngine type: {type(whisper_engine).__name__}")
                app_logger.debug(f"WhisperEngine model_name: {whisper_engine.model_name}")
                app_logger.debug(f"WhisperEngine device: {whisper_engine.device}")
                app_logger.debug(f"WhisperEngine use_gpu: {whisper_engine.use_gpu}")

            # === DEBUG: 获取事件服务 ===
            if app_logger:
                app_logger.debug("Getting IEventService...")

            event_service = self.get(IEventService)

            if app_logger:
                app_logger.debug("Event service obtained successfully")
                app_logger.debug(f"Event service type: {type(event_service).__name__}")

            # === DEBUG: 创建TranscriptionService ===
            if app_logger:
                app_logger.debug("Creating TranscriptionService...")

            # 使用TranscriptionService包装,提供线程隔离
            transcription_service = TranscriptionService(whisper_engine, event_service)

            if app_logger:
                app_logger.debug("TranscriptionService created successfully")
                app_logger.debug(f"TranscriptionService type: {type(transcription_service).__name__}")

            # === DEBUG: 启动TranscriptionService ===
            if app_logger:
                app_logger.debug("Starting TranscriptionService...")

            transcription_service.start()  # 启动持久化工作线程

            if app_logger:
                app_logger.debug("TranscriptionService started successfully")
                app_logger.debug(f"TranscriptionService is_model_loaded: {transcription_service.is_model_loaded}")
                app_logger.debug(f"TranscriptionService is_busy: {transcription_service.is_busy}")

            creation_time = time.time() - start_time

            if app_logger:
                app_logger.debug(f"Speech service creation completed in {creation_time:.3f}s")
                app_logger.debug("=== DI CREATE SPEECH SERVICE DEBUG END (SUCCESS) ===")

            return transcription_service

        except Exception as e:
            creation_time = time.time() - start_time

            if app_logger:
                app_logger.debug(f"Speech service creation failed after {creation_time:.3f}s")
                app_logger.debug(f"Error type: {type(e).__name__}")
                app_logger.debug(f"Error: {e}")
                app_logger.debug(f"Stack trace: {traceback.format_exc()}")
                app_logger.debug("=== DI CREATE SPEECH SERVICE DEBUG END (ERROR) ===")

            # 重新抛出异常，但提供更多上下文
            error_msg = f"Failed to create speech service: {e}"
            raise ValueError(error_msg) from e
    
    def _create_ai_service(self) -> IAIService:
        """创建AI服务 - 使用 AIClientFactory 统一创建"""
        config = self.get(IConfigService)

        # 使用工厂从配置创建客户端
        client = AIClientFactory.create_from_config(config)

        # 如果工厂返回 None，创建默认的 OpenRouter 客户端
        if client is None:
            from ..ai import OpenRouterClient
            api_key = config.get_setting("ai.openrouter.api_key", "")
            return OpenRouterClient(api_key)

        return client
    
    def _create_input_service(self) -> IInputService:
        """创建输入服务"""
        config_service = self.get(IConfigService)
        return SmartTextInput(config_service)
    
    def _create_hotkey_service(self) -> IHotkeyService:
        """创建快捷键服务"""
        # 创建一个空的回调函数，在VoiceInputApp中会被替换
        def dummy_callback(action: str):
            pass
        return HotkeyManager(dummy_callback)
    
    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """注册单例服务"""
        self._singletons[interface] = instance
    
    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """注册工厂方法"""
        self._factories[interface] = factory
    
    def get(self, interface: Type[T]) -> T:
        """获取服务实例（线程安全）"""
        # === DEBUG: DI容器获取服务开始 ===
        import traceback
        start_time = time.time()
        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name

        # 获取logger（避免循环导入）
        try:
            from ...utils import app_logger
        except ImportError:
            app_logger = None

        if app_logger:
            app_logger.debug("=== DI GET SERVICE DEBUG START ===")
            app_logger.debug(f"Thread: {thread_name} (ID: {thread_id})")
            app_logger.debug(f"Interface: {interface}")

        try:
            with self._get_lock:
                # === DEBUG: 检查单例 ===
                if app_logger:
                    app_logger.debug("Checking singleton cache...")

                if interface in self._singletons:
                    instance = self._singletons[interface]
                    if app_logger:
                        app_logger.debug(f"Found singleton instance of {interface}")
                        app_logger.debug(f"Singleton type: {type(instance).__name__}")
                    return instance

                # === DEBUG: 检查工厂 ===
                if app_logger:
                    app_logger.debug("Checking factories...")

                if interface in self._factories:
                    factory = self._factories[interface]

                    if factory is None:  # Handle None factory (like hotkey service)
                        if app_logger:
                            app_logger.debug(f"Factory for {interface} is None")
                        raise ValueError(f"Factory for {interface} returns None - service not properly configured")

                    if app_logger:
                        app_logger.debug(f"Found factory for {interface}")
                        app_logger.debug(f"Factory type: {type(factory).__name__}")

                    try:
                        # === DEBUG: 实例化服务 ===
                        if app_logger:
                            app_logger.debug("Creating service instance...")

                        instance = factory()
                        creation_time = time.time() - start_time

                        if instance is None:
                            if app_logger:
                                app_logger.debug(f"Factory returned None instance for {interface}")
                            raise ValueError(f"Factory for {interface} returned None instance")

                        if app_logger:
                            app_logger.debug(f"Service instance created successfully")
                            app_logger.debug(f"Instance type: {type(instance).__name__}")
                            app_logger.debug(f"Creation time: {creation_time:.3f}s")

                        # 配置、事件和状态管理器作为单例
                        if interface in (IConfigService, IEventService, IStateManager):
                            if app_logger:
                                app_logger.debug(f"Adding {interface} to singleton cache")
                            self._singletons[interface] = instance

                        return instance

                    except Exception as factory_error:
                        if app_logger:
                            app_logger.debug(f"Factory failed for {interface}: {factory_error}")
                            app_logger.debug(f"Factory error stack trace: {traceback.format_exc()}")
                        raise factory_error

                # === DEBUG: ��找到注册 ===
                if app_logger:
                    app_logger.debug(f"No registration found for {interface}")
                    app_logger.debug(f"Available interfaces: {list(self._factories.keys())}")
                    app_logger.debug(f"Available singletons: {list(self._singletons.keys())}")

                raise ValueError(f"No registration found for {interface}")

        except Exception as e:
            if app_logger:
                total_time = time.time() - start_time
                app_logger.debug(f"DI get service failed after {total_time:.3f}s")
                app_logger.debug(f"Error type: {type(e).__name__}")
                app_logger.debug(f"Error: {e}")
                app_logger.debug(f"Stack trace: {traceback.format_exc()}")
                app_logger.debug("=== DI GET SERVICE DEBUG END (ERROR) ===")

            # 重新抛出异常，但添加更多上下文
            error_msg = f"Failed to get service {interface}: {e}"
            raise ValueError(error_msg) from e

        finally:
            if app_logger:
                total_time = time.time() - start_time
                if not hasattr(self, '_error_occurred') or not self._error_occurred:
                    app_logger.debug(f"=== DI GET SERVICE DEBUG END (SUCCESS) - Total time: {total_time:.3f}s ===")
    
    def get_optional(self, interface: Type[T]) -> Optional[T]:
        """获取可选服务实例，如果不存在返回None"""
        try:
            return self.get(interface)
        except ValueError:
            return None
    
    def cleanup(self) -> None:
        """清理资源"""
        for service in self._singletons.values():
            if hasattr(service, 'cleanup'):
                try:
                    service.cleanup()
                except Exception:
                    pass  # 忽略清理错误
        
        self._singletons.clear()