"""依赖注入容器"""

import threading
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
        config = self.get(IConfigService)
        model_name = config.get_setting("whisper.model", "large-v3-turbo")
        use_gpu = config.get_setting("whisper.use_gpu", None)  # None = auto-detect

        # 创建WhisperEngine，传递 use_gpu 配置
        whisper_engine = WhisperEngine(model_name, use_gpu=use_gpu)

        # 获取事件服务
        event_service = self.get(IEventService)

        # 使用TranscriptionService包装,提供线程隔离
        transcription_service = TranscriptionService(whisper_engine, event_service)
        transcription_service.start()  # 启动持久化工作线程

        return transcription_service
    
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
        with self._get_lock:
            # 检查单例
            if interface in self._singletons:
                return self._singletons[interface]

            # 检查工厂
            if interface in self._factories:
                factory = self._factories[interface]
                if factory is None:  # Handle None factory (like hotkey service)
                    raise ValueError(f"Factory for {interface} returns None - service not properly configured")

                instance = factory()
                if instance is None:
                    raise ValueError(f"Factory for {interface} returned None instance")

                # 配置、事件和状态管理器作为单例
                if interface in (IConfigService, IEventService, IStateManager):
                    self._singletons[interface] = instance

                return instance

            raise ValueError(f"No registration found for {interface}")
    
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