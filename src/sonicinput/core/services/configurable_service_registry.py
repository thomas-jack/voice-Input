"""可配置服务注册器

负责：
- 根据配置动态注册服务
- 支持多种服务生命周期
- 提供服务工厂实现
- 自动依赖解析
"""

import importlib
from typing import Dict, List, Type, Callable
from ..interfaces.service_registry_config import IServiceRegistryConfig
from ...utils import app_logger
from ..di_container_enhanced import EnhancedDIContainer, ServiceLifetime


class ConfigurableServiceRegistry:
    """可配置服务注册器

    职责：
    - 根据配置自动注册服务
    - 解析服务依赖关系
    - 创建服务工厂函数
    - 管理服务生命周期
    """

    def __init__(self, container: EnhancedDIContainer, config: IServiceRegistryConfig):
        """初始化可配置服务注册器

        Args:
            container: DI容器实例
            config: 服务注册配置
        """
        self.container = container
        self.config = config
        self._service_factories: Dict[str, Callable] = {}

        # 注册默认工厂函数
        self._register_default_factories()

        app_logger.log_audio_event("ConfigurableServiceRegistry initialized", {})

    def register_all_services(self) -> None:
        """根据配置注册所有服务"""
        try:
            # 验证配置
            errors = self.config.validate_config()
            if errors:
                raise ValueError(f"Service configuration validation failed: {errors}")

            # 获取注册顺序
            registration_order = self.config.get_registration_order()

            app_logger.log_audio_event("Registering services from config", {
                "services_count": len(registration_order)
            })

            # 按顺序注册服务
            for service_name in registration_order:
                self._register_service(service_name)

            app_logger.log_audio_event("All services registered from config", {
                "services_count": len(registration_order)
            })

        except Exception as e:
            app_logger.log_error(e, "register_all_services")
            raise

    def _register_service(self, service_name: str) -> None:
        """注册单个服务"""
        service_config = self.config.get_service_config(service_name)
        if not service_config:
            raise ValueError(f"Service configuration not found: {service_name}")

        try:
            # 解析接口和实现类
            interface_class = self._resolve_interface(service_config["interface"])
            lifetime = self._resolve_lifetime(service_config["lifetime"])

            # 检查是否使用工厂函数
            factory_name = service_config.get("factory")
            if factory_name:
                self._register_service_with_factory(service_name, interface_class, factory_name, lifetime)
            else:
                implementation_class = self._resolve_implementation(service_config["implementation"])
                self._register_service_with_class(service_name, interface_class, implementation_class, lifetime)

            app_logger.log_audio_event("Service registered from config", {
                "service_name": service_name,
                "interface": service_config["interface"],
                "lifetime": service_config["lifetime"]
            })

        except Exception as e:
            app_logger.log_error(e, f"register_service_{service_name}")
            raise

    def _register_service_with_class(
        self,
        service_name: str,
        interface_class: Type,
        implementation_class: Type,
        lifetime: ServiceLifetime
    ) -> None:
        """使用类注册服务"""
        if lifetime == ServiceLifetime.SINGLETON:
            self.container.register_singleton(interface_class, implementation_class)
        elif lifetime == ServiceLifetime.TRANSIENT:
            self.container.register_transient(interface_class, implementation_class)
        elif lifetime == ServiceLifetime.SCOPED:
            self.container.register_scoped(interface_class, implementation_class)

    def _register_service_with_factory(
        self,
        service_name: str,
        interface_class: Type,
        factory_name: str,
        lifetime: ServiceLifetime
    ) -> None:
        """使用工厂函数注册服务"""
        factory_func = self._service_factories.get(factory_name)
        if not factory_func:
            raise ValueError(f"Factory function not found: {factory_name}")

        self.container.register_factory(interface_class, factory_func, lifetime)

    def _resolve_interface(self, interface_name: str) -> Type:
        """解析接口类"""
        try:
            # 从core.interfaces模块导入
            module = importlib.import_module("..interfaces", package=__name__)
            interface_class = getattr(module, interface_name)
            return interface_class
        except (ImportError, AttributeError):
            raise ValueError(f"Interface not found: {interface_name}")

    def _resolve_implementation(self, implementation_name: str) -> Type:
        """解析实现类"""
        try:
            # 尝试从不同的模块导入
            implementation_mappings = {
                "DynamicEventSystem": ("..services.dynamic_event_system", "DynamicEventSystem"),
                "ConfigService": ("..services.config_service", "ConfigService"),
                "StateManager": ("..services.state_manager", "StateManager"),
                "ConfigReloadService": ("..services.config_reload_service", "ConfigReloadService"),
                "ApplicationOrchestrator": ("..services.application_orchestrator", "ApplicationOrchestrator"),
                "UIEventBridge": ("..services.ui_event_bridge", "UIEventBridge"),
                "UIMainServiceAdapter": ("..services.ui_service_adapter", "UIMainServiceAdapter"),
                "UISettingsServiceAdapter": ("..services.ui_service_adapter", "UISettingsServiceAdapter"),
                "UIModelServiceAdapter": ("..services.ui_service_adapter", "UIModelServiceAdapter"),
                "UIAudioServiceAdapter": ("..services.ui_service_adapter", "UIAudioServiceAdapter"),
                # UIGPUServiceAdapter removed - sherpa-onnx is CPU-only
                "AudioRecorder": ("..audio.recorder", "AudioRecorder"),
                "SherpaEngine": ("..speech.sherpa_engine", "SherpaEngine"),
                "SmartTextInput": ("..input.smart_input", "SmartTextInput"),
                "HotkeyManager": ("..hotkey_manager", "HotkeyManager"),
            }

            if implementation_name in implementation_mappings:
                module_name, class_name = implementation_mappings[implementation_name]
                module = importlib.import_module(module_name, package=__name__)
                implementation_class = getattr(module, class_name)
                return implementation_class
            else:
                # 尝试从core.services模块导入
                module = importlib.import_module("..services", package=__name__)
                implementation_class = getattr(module, implementation_name)
                return implementation_class

        except (ImportError, AttributeError):
            raise ValueError(f"Implementation not found: {implementation_name}")

    def _resolve_lifetime(self, lifetime_str: str) -> ServiceLifetime:
        """解析服务生命周期"""
        lifetime_map = {
            "singleton": ServiceLifetime.SINGLETON,
            "transient": ServiceLifetime.TRANSIENT,
            "scoped": ServiceLifetime.SCOPED,
        }

        lifetime = lifetime_map.get(lifetime_str.lower())
        if not lifetime:
            raise ValueError(f"Invalid lifetime: {lifetime_str}")

        return lifetime

    def _register_default_factories(self) -> None:
        """注册默认工厂函数"""
        self._service_factories.update({
            "create_config_reload_service": self._create_config_reload_service,
            "create_audio_service": self._create_audio_service,
            "create_speech_service": self._create_speech_service,
            "create_ai_service": self._create_ai_service,
            "create_input_service": self._create_input_service,
            "create_hotkey_service": self._create_hotkey_service,
            "create_application_orchestrator": self._create_application_orchestrator,
            "create_ui_event_bridge": self._create_ui_event_bridge,
            "create_ui_main_service": self._create_ui_main_service,
            "create_ui_settings_service": self._create_ui_settings_service,
            "create_ui_model_service": self._create_ui_model_service,
            "create_ui_audio_service": self._create_ui_audio_service,
            "create_ui_gpu_service": self._create_ui_gpu_service,
        })

    def _create_config_reload_service(self, container):
        """创建配置重载服务工厂"""
        from ..interfaces import IConfigService, IEventService, IStateManager
        from ..services.config_reload_service import ConfigReloadService

        config = container.get(IConfigService)
        events = container.get(IEventService)
        state = container.get(IStateManager)

        return ConfigReloadService(config=config, events=events, state=state)

    def _create_audio_service(self, container):
        """创建音频服务工厂"""
        from ..interfaces import IConfigService
        from ..audio.recorder import AudioRecorder

        config = container.get(IConfigService)
        sample_rate = config.get_setting("audio.sample_rate", 16000)
        channels = config.get_setting("audio.channels", 1)
        chunk_size = config.get_setting("audio.chunk_size", 1024)

        return AudioRecorder(
            sample_rate=sample_rate,
            channels=channels,
            chunk_size=chunk_size,
            config_service=config,
        )

    def _create_speech_service(self, container):
        """创建语音服务工厂"""
        from ..interfaces import IConfigService, IEventService
        from ..services.transcription_service import TranscriptionService

        config = container.get(IConfigService)
        event_service = container.get(IEventService)

        # 使用 SpeechServiceFactory 从配置创建服务
        from ..speech import SpeechServiceFactory

        def speech_service_factory():
            service = SpeechServiceFactory.create_from_config(config)
            if service is None:
                from ..speech.sherpa_engine import SherpaEngine
                return SherpaEngine("paraformer", language="zh")
            return service

        # 使用TranscriptionService包装（传递 config_service 用于流式模式配置）
        transcription_service = TranscriptionService(
            speech_service_factory, event_service, config_service=config
        )
        transcription_service.start()

        return transcription_service

    def _create_ai_service(self, container):
        """创建AI服务工厂"""
        from ..interfaces import IConfigService
        from ..ai import AIClientFactory

        config = container.get(IConfigService)
        client = AIClientFactory.create_from_config(config)

        if client is None:
            from ..ai.openrouter_client import OpenRouterClient
            api_key = config.get_setting("ai.openrouter.api_key", "")
            return OpenRouterClient(api_key)

        return client

    def _create_input_service(self, container):
        """创建输入服务工厂"""
        from ..interfaces import IConfigService
        from ..input.smart_input import SmartTextInput

        config_service = container.get(IConfigService)
        return SmartTextInput(config_service)

    def _create_hotkey_service(self, container):
        """创建快捷键服务工厂"""
        from ..hotkey_manager import HotkeyManager

        def dummy_callback(action: str):
            pass

        return HotkeyManager(dummy_callback)

    def _create_application_orchestrator(self, container):
        """创建应用编排器工厂"""
        from ..interfaces import (
            IConfigService, IEventService, IStateManager, IConfigReloadService
        )
        from ..services.application_orchestrator import ApplicationOrchestrator

        config = container.get(IConfigService)
        events = container.get(IEventService)
        state = container.get(IStateManager)
        config_reload = container.get(IConfigReloadService)

        return ApplicationOrchestrator(
            config_service=config,
            event_service=events,
            state_manager=state,
            config_reload_service=config_reload,
        )

    def _create_ui_event_bridge(self, container):
        """创建UI事件桥接器工厂"""
        from ..interfaces import IEventService
        from ..services.ui_event_bridge import UIEventBridge

        events = container.get(IEventService)
        return UIEventBridge(event_service=events)

    def _create_ui_main_service(self, container):
        """创建UI主服务工厂"""
        from ..services.ui_service_adapter import UIMainServiceAdapter

        # 这里需要获取VoiceInputApp实例，暂时从容器中获取
        # 在实际使用中，这个工厂需要适配不同的应用初始化方式
        try:
            # 尝试获取VoiceInputApp实例
            voice_app = container.get(None)  # 如果VoiceInputApp还没有注册，需要特殊处理
            if hasattr(voice_app, 'voice_input_app'):
                voice_app = voice_app.voice_input_app
            return UIMainServiceAdapter(voice_app)
        except:
            # 如果无法获取VoiceInputApp，返回None或抛出异常
            # 在实际集成时需要正确处理这种情况
            app_logger.log_audio_event("Warning: Could not create UI main service - VoiceInputApp not available", {})
            return None

    def _create_ui_settings_service(self, container):
        """创建UI设置服务工厂"""
        from ..interfaces import IConfigService, IEventService, IHistoryStorageService
        from ..services.ui_service_adapter import UISettingsServiceAdapter

        config = container.get(IConfigService)
        events = container.get(IEventService)
        history = container.get(IHistoryStorageService)

        # 获取转录服务和AI处理控制器（从VoiceInputApp实例获取）
        transcription_service = None
        ai_processing_controller = None

        try:
            # 尝试从容器获取VoiceInputApp实例
            voice_app = container.get(None)
            app_logger.log_audio_event(
                "DEBUG: Got voice_app from container",
                {"has_voice_input_app_attr": hasattr(voice_app, 'voice_input_app') if voice_app else False}
            )

            if hasattr(voice_app, 'voice_input_app'):
                voice_app = voice_app.voice_input_app
                app_logger.log_audio_event("DEBUG: Unwrapped voice_input_app", {})

            # 从ApplicationOrchestrator获取服务
            if hasattr(voice_app, 'orchestrator'):
                orchestrator = voice_app.orchestrator
                app_logger.log_audio_event(
                    "DEBUG: Got orchestrator",
                    {
                        "has_speech_service": hasattr(orchestrator, '_speech_service'),
                        "has_controllers": hasattr(orchestrator, '_controllers')
                    }
                )

                # 获取转录服务 - 使用正确的属性名 _speech_service
                if hasattr(orchestrator, '_speech_service'):
                    transcription_service = orchestrator._speech_service
                    app_logger.log_audio_event(
                        "Got transcription service from orchestrator for UI settings",
                        {"service_type": type(transcription_service).__name__ if transcription_service else "None"}
                    )
                else:
                    app_logger.log_audio_event("DEBUG: orchestrator has no _speech_service attr", {})

                # 获取AI处理控制器 - 从 _controllers 字典获取
                if hasattr(orchestrator, '_controllers'):
                    ai_processing_controller = orchestrator._controllers.get('ai')
                    if ai_processing_controller:
                        app_logger.log_audio_event(
                            "Got AI processing controller from orchestrator for UI settings",
                            {"controller_type": type(ai_processing_controller).__name__}
                        )
                    else:
                        app_logger.log_audio_event("DEBUG: orchestrator._controllers['ai'] is None", {})
                else:
                    app_logger.log_audio_event("DEBUG: orchestrator has no _controllers attr", {})
            else:
                app_logger.log_audio_event("DEBUG: voice_app has no orchestrator attr", {})
        except Exception as e:
            app_logger.log_audio_event(
                "Warning: Could not get services from orchestrator for UI settings",
                {"error": str(e)}
            )

        return UISettingsServiceAdapter(
            config,
            events,
            history,
            transcription_service=transcription_service,
            ai_processing_controller=ai_processing_controller,
        )

    def _create_ui_model_service(self, container):
        """创建UI模型服务工厂"""
        from ..services.ui_service_adapter import UIModelServiceAdapter

        # 类似于UI主服务，需要VoiceInputApp实例
        try:
            voice_app = container.get(None)
            if hasattr(voice_app, 'voice_input_app'):
                voice_app = voice_app.voice_input_app
            return UIModelServiceAdapter(voice_app)
        except:
            app_logger.log_audio_event("Warning: Could not create UI model service - VoiceInputApp not available", {})
            return None

    def _create_ui_audio_service(self, container):
        """创建UI音频服务工厂"""
        from ..services.ui_service_adapter import UIAudioServiceAdapter

        try:
            voice_app = container.get(None)
            if hasattr(voice_app, 'voice_input_app'):
                voice_app = voice_app.voice_input_app
            return UIAudioServiceAdapter(voice_app)
        except:
            app_logger.log_audio_event("Warning: Could not create UI audio service - VoiceInputApp not available", {})
            return None

    def _create_ui_gpu_service(self, container):
        """创建UI GPU服务工厂"""
        from ..services.ui_service_adapter import UIGPUServiceAdapter
        return UIGPUServiceAdapter()

    def register_custom_factory(self, factory_name: str, factory_func: Callable) -> None:
        """注册自定义工厂函数"""
        self._service_factories[factory_name] = factory_func
        app_logger.log_audio_event("Custom factory registered", {
            "factory_name": factory_name
        })

    def get_registered_factories(self) -> List[str]:
        """获取已注册的工厂函数列表"""
        return list(self._service_factories.keys())