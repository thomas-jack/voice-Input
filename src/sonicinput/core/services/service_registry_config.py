"""服务注册配置实现

负责：
- 服务配置管理
- 依赖关系解析
- 注册顺序计算
- 配置文件加载和保存
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...utils import app_logger
from ..interfaces.service_registry_config import IServiceRegistryConfig


class ServiceRegistryConfig(IServiceRegistryConfig):
    """服务注册配置实现

    职责：
    - 管理服务注册配置
    - 解析服务依赖关系
    - 计算服务注册顺序
    - 提供配置文件持久化
    """

    def __init__(self, config_path: Optional[str] = None):
        """初始化服务注册配置

        Args:
            config_path: 配置文件路径，可选
        """
        self.config_path = config_path
        self._service_configs: Dict[str, Dict[str, Any]] = {}
        self._dependency_graph: Dict[str, List[str]] = {}
        self._registration_order: Optional[List[str]] = None
        self._is_dirty = False

        # 初始化默认配置
        self._initialize_default_configs()

        if config_path and Path(config_path).exists():
            self.load_config_from_file(config_path)

        app_logger.log_audio_event(
            "ServiceRegistryConfig initialized",
            {"services_count": len(self._service_configs)},
        )

    def _initialize_default_configs(self) -> None:
        """初始化默认服务配置"""
        default_configs = {
            "event_service": {
                "interface": "IEventService",
                "implementation": "DynamicEventSystem",
                "lifetime": "singleton",
                "dependencies": [],
                "factory": None,
                "description": "事件总线服务，负责组件间通信",
                "priority": 1,
            },
            "config_service": {
                "interface": "IConfigService",
                "implementation": "ConfigService",
                "lifetime": "singleton",
                "dependencies": ["event_service"],
                "factory": None,
                "description": "配置管理服务，负责应用配置管理",
                "priority": 2,
            },
            "state_manager": {
                "interface": "IStateManager",
                "implementation": "StateManager",
                "lifetime": "singleton",
                "dependencies": ["event_service"],
                "factory": None,
                "description": "状态管理器，负责应用状态管理",
                "priority": 3,
            },
            "history_service": {
                "interface": "IHistoryStorageService",
                "implementation": "HistoryStorageService",
                "lifetime": "singleton",
                "dependencies": ["config_service"],
                "factory": "create_history_service",
                "description": "历史记录存储服务，负责录音历史持久化",
                "priority": 4,
            },
            "audio_service": {
                "interface": "IAudioService",
                "implementation": "AudioRecorder",
                "lifetime": "transient",
                "dependencies": ["config_service"],
                "factory": "create_audio_service",
                "description": "音频录制服务，负责音频数据采集",
                "priority": 5,
            },
            "speech_service": {
                "interface": "ISpeechService",
                "implementation": "TranscriptionService",
                "lifetime": "singleton",
                "dependencies": ["config_service", "event_service"],
                "factory": "create_speech_service",
                "description": "语音识别服务，负责语音转文字",
                "priority": 6,
            },
            "ai_service": {
                "interface": "IAIService",
                "implementation": None,  # 工厂创建
                "lifetime": "transient",
                "dependencies": ["config_service"],
                "factory": "create_ai_service",
                "description": "AI处理服务，负责文本优化和处理",
                "priority": 7,
            },
            "input_service": {
                "interface": "IInputService",
                "implementation": "SmartTextInput",
                "lifetime": "transient",
                "dependencies": ["config_service"],
                "factory": "create_input_service",
                "description": "智能输入服务，负责文本输入模拟",
                "priority": 8,
            },
            "hotkey_service": {
                "interface": "IHotkeyService",
                "implementation": "HotkeyManager",
                "lifetime": "transient",
                "dependencies": [],
                "factory": "create_hotkey_service",
                "description": "快捷键服务，负责全局快捷键管理",
                "priority": 10,
            },
            "application_orchestrator": {
                "interface": "IApplicationOrchestrator",
                "implementation": "ApplicationOrchestrator",
                "lifetime": "singleton",
                "dependencies": [
                    "config_service",
                    "event_service",
                    "state_manager",
                ],
                "factory": "create_application_orchestrator",
                "description": "应用编排器，负责应用启动流程管理",
                "priority": 9,
            },
            "ui_event_bridge": {
                "interface": "IUIEventBridge",
                "implementation": "UIEventBridge",
                "lifetime": "singleton",
                "dependencies": ["event_service"],
                "factory": "create_ui_event_bridge",
                "description": "UI事件桥接器，负责UI层事件通信",
                "priority": 11,
            },
        }

        for service_name, config in default_configs.items():
            self._service_configs[service_name] = config

        # 构建依赖图
        self._build_dependency_graph()

    def _build_dependency_graph(self) -> None:
        """构建服务依赖图"""
        self._dependency_graph.clear()
        for service_name, config in self._service_configs.items():
            dependencies = config.get("dependencies", [])
            self._dependency_graph[service_name] = dependencies

        # 标记需要重新计算注册顺序
        self._registration_order = None
        self._is_dirty = True

    def get_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取特定服务的配置"""
        return self._service_configs.get(service_name)

    def get_all_service_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务配置"""
        return self._service_configs.copy()

    def register_service_config(
        self, service_name: str, config: Dict[str, Any]
    ) -> None:
        """注册服务配置"""
        # 验证配置格式
        required_fields = ["interface", "lifetime"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Service config missing required field: {field}")

        self._service_configs[service_name] = config
        self._build_dependency_graph()
        self._is_dirty = True

        app_logger.log_audio_event(
            "Service config registered",
            {
                "service_name": service_name,
                "implementation": config.get("implementation"),
                "lifetime": config.get("lifetime"),
            },
        )

    def get_service_dependencies(self, service_name: str) -> List[str]:
        """获取服务依赖列表"""
        return self._dependency_graph.get(service_name, []).copy()

    def load_config_from_file(self, config_path: str) -> None:
        """从文件加载服务配置"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            if "services" in config_data:
                for service_name, config in config_data["services"].items():
                    self._service_configs[service_name] = config

            self._build_dependency_graph()
            self.config_path = config_path
            self._is_dirty = False

            app_logger.log_audio_event(
                "Service configs loaded from file",
                {
                    "config_path": config_path,
                    "services_count": len(self._service_configs),
                },
            )

        except Exception as e:
            app_logger.log_error(e, "load_config_from_file")
            raise

    def save_config_to_file(self, config_path: Optional[str] = None) -> None:
        """保存服务配置到文件"""
        if config_path is None:
            config_path = self.config_path

        if config_path is None:
            raise ValueError("No config path specified")

        try:
            config_data = {
                "version": "1.0",
                "description": "SonicInput Service Registry Configuration",
                "services": self._service_configs,
            }

            # 确保目录存在
            Path(config_path).parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            self.config_path = config_path
            self._is_dirty = False

            app_logger.log_audio_event(
                "Service configs saved to file",
                {
                    "config_path": config_path,
                    "services_count": len(self._service_configs),
                },
            )

        except Exception as e:
            app_logger.log_error(e, "save_config_to_file")
            raise

    def validate_config(self) -> List[str]:
        """验证配置完整性，返回错误列表"""
        errors = []

        # 检查循环依赖
        if self._has_circular_dependencies():
            errors.append("Circular dependencies detected in service configuration")

        # 检查依赖服务是否存在
        for service_name, dependencies in self._dependency_graph.items():
            for dep in dependencies:
                if dep not in self._service_configs:
                    errors.append(
                        f"Service '{service_name}' depends on non-existent service '{dep}'"
                    )

        # 检查接口和实现的有效性
        for service_name, config in self._service_configs.items():
            interface = config.get("interface")
            implementation = config.get("implementation")
            factory = config.get("factory")

            if not factory and not implementation:
                errors.append(
                    f"Service '{service_name}' must have either implementation or factory"
                )

            lifetime = config.get("lifetime")
            if lifetime and lifetime not in ["singleton", "transient", "scoped"]:
                errors.append(
                    f"Service '{service_name}' has invalid lifetime: {lifetime}"
                )

        return errors

    def get_registration_order(self) -> List[str]:
        """获取服务注册顺序（根据依赖关系）"""
        if self._registration_order is None:
            self._registration_order = self._calculate_registration_order()

        return self._registration_order.copy()

    def _calculate_registration_order(self) -> List[str]:
        """计算服务注册顺序（拓扑排序）"""
        # 拓扑排序算法
        in_degree = {service: 0 for service in self._service_configs}

        # 计算入度
        for service in self._service_configs:
            for dep in self._dependency_graph.get(service, []):
                if dep in in_degree:
                    in_degree[service] += 1

        # 使用优先队列，按priority排序
        from heapq import heappop, heappush

        queue = []
        for service, degree in in_degree.items():
            if degree == 0:
                priority = self._service_configs[service].get("priority", 999)
                heappush(queue, (priority, service))

        order = []
        while queue:
            priority, service = heappop(queue)
            order.append(service)

            # 更新依赖此服务的其他服务的入度
            for other_service in self._service_configs:
                if service in self._dependency_graph.get(other_service, []):
                    in_degree[other_service] -= 1
                    if in_degree[other_service] == 0:
                        other_priority = self._service_configs[other_service].get(
                            "priority", 999
                        )
                        heappush(queue, (other_priority, other_service))

        # 检查是否所有服务都被处理（没有循环依赖）
        if len(order) != len(self._service_configs):
            raise ValueError("Circular dependencies detected in service configuration")

        return order

    def _has_circular_dependencies(self) -> bool:
        """检查是否存在循环依赖"""
        try:
            self._calculate_registration_order()
            return False
        except ValueError:
            return True

    @property
    def is_dirty(self) -> bool:
        """检查配置是否已修改但未保存"""
        return self._is_dirty

    def reload_from_file(self) -> None:
        """从配置文件重新加载配置"""
        if self.config_path and Path(self.config_path).exists():
            self.load_config_from_file(self.config_path)
        else:
            app_logger.log_audio_event("No config file available for reload", {})
