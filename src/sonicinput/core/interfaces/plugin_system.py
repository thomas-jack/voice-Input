"""插件系统接口

定义插件化的核心接口，支持功能的动态扩展。
插件可以添加新的语音识别引擎、AI服务、输入方法、UI组件等。
"""

from typing import Protocol, Dict, Any, List, Optional, Type
from abc import ABC
from enum import Enum


class PluginType(Enum):
    """插件类型枚举"""

    SPEECH_ENGINE = "speech_engine"  # 语音识别引擎
    AI_SERVICE = "ai_service"  # AI处理服务
    INPUT_METHOD = "input_method"  # 输入方法
    AUDIO_PROCESSOR = "audio_processor"  # 音频处理器
    UI_COMPONENT = "ui_component"  # UI组件
    EVENT_HANDLER = "event_handler"  # 事件处理器
    EXTENSION = "extension"  # 通用扩展


class PluginStatus(Enum):
    """插件状态枚举"""

    UNKNOWN = "unknown"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"


class IPlugin(Protocol):
    """插件基础接口

    所有插件都必须实现此接口。
    """

    @property
    def name(self) -> str:
        """插件名称"""
        ...

    @property
    def version(self) -> str:
        """插件版本"""
        ...

    @property
    def description(self) -> str:
        """插件描述"""
        ...

    @property
    def author(self) -> str:
        """插件作者"""
        ...

    @property
    def plugin_type(self) -> PluginType:
        """插件类型"""
        ...

    @property
    def dependencies(self) -> List[str]:
        """插件依赖列表"""
        ...

    def initialize(self, context: "IPluginContext") -> bool:
        """初始化插件

        Args:
            context: 插件上下文

        Returns:
            bool: 初始化是否成功
        """
        ...

    def activate(self) -> bool:
        """激活插件

        Returns:
            bool: 激活是否成功
        """
        ...

    def deactivate(self) -> bool:
        """停用插件

        Returns:
            bool: 停用是否成功
        """
        ...

    def cleanup(self) -> None:
        """清理插件资源"""
        ...

    def get_info(self) -> Dict[str, Any]:
        """获取插件信息

        Returns:
            Dict[str, Any]: 插件信息字典
        """
        ...

    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """获取插件配置模式

        Returns:
            Optional[Dict[str, Any]]: JSON Schema格式的配置模式，如果没有配置需求则返回None
        """
        ...

    def set_config(self, config: Dict[str, Any]) -> bool:
        """设置插件配置

        Args:
            config: 配置字典

        Returns:
            bool: 设置是否成功
        """
        ...

    def get_config(self) -> Optional[Dict[str, Any]]:
        """获取插件配置

        Returns:
            Optional[Dict[str, Any]]: 当前配置，如果没有配置则返回None
        """
        ...


class IPluginContext(Protocol):
    """插件上下文接口

    提供插件运行所需的服务和资源访问。
    """

    def get_service(self, service_interface: Type) -> Any:
        """获取服务实例

        Args:
            service_interface: 服务接口类型

        Returns:
            Any: 服务实例，如果服务不存在则返回None
        """
        ...

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            Any: 配置值
        """
        ...

    def set_config(self, key: str, value: Any) -> None:
        """设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        ...

    def log(self, message: str, level: str = "INFO") -> None:
        """记录日志

        Args:
            message: 日志消息
            level: 日志级别
        """
        ...

    def emit_event(self, event_name: str, data: Any = None) -> None:
        """发送事件

        Args:
            event_name: 事件名称
            data: 事件数据
        """
        ...

    def register_event_handler(self, event_name: str, handler) -> None:
        """注册事件处理器

        Args:
            event_name: 事件名称
            handler: 事件处理器函数
        """
        ...


class IPluginManager(Protocol):
    """插件管理器接口

    负责插件的加载、激活、停用和生命周期管理。
    """

    def load_plugin(self, plugin_path: str) -> bool:
        """加载插件

        Args:
            plugin_path: 插件文件路径

        Returns:
            bool: 加载是否成功
        """
        ...

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 卸载是否成功
        """
        ...

    def activate_plugin(self, plugin_name: str) -> bool:
        """激活插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 激活是否成功
        """
        ...

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """停用插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 停用是否成功
        """
        ...

    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """获取插件实例

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[IPlugin]: 插件实例，如果不存在则返回None
        """
        ...

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[IPlugin]:
        """根据类型获取插件列表

        Args:
            plugin_type: 插件类型

        Returns:
            List[IPlugin]: 插件列表
        """
        ...

    def get_all_plugins(self) -> Dict[str, IPlugin]:
        """获取所有插件

        Returns:
            Dict[str, IPlugin]: 插件字典 {plugin_name: plugin_instance}
        """
        ...

    def get_plugin_status(self, plugin_name: str) -> PluginStatus:
        """获取插件状态

        Args:
            plugin_name: 插件名称

        Returns:
            PluginStatus: 插件状态
        """
        ...

    def scan_plugins_directory(self, directory: str) -> int:
        """扫描插件目录

        Args:
            directory: 插件目录路径

        Returns:
            int: 发现的插件数量
        """
        ...

    def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 重新加载是否成功
        """
        ...

    def enable_plugin_auto_load(self, enabled: bool) -> None:
        """启用/禁用插件自动加载

        Args:
            enabled: 是否启用自动加载
        """
        ...

    def get_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """获取插件依赖

        Args:
            plugin_name: 插件名称

        Returns:
            List[str]: 依赖的插件名称列表
        """
        ...

    def resolve_dependency_order(self, plugin_names: List[str]) -> List[str]:
        """解析插件依赖顺序

        Args:
            plugin_names: 插件名称列表

        Returns:
            List[str]: 按依赖顺序排序的插件名称列表
        """
        ...


class IPluginRegistry(Protocol):
    """插件注册表接口

    管理插件的注册信息和元数据。
    """

    def register_plugin(self, plugin: IPlugin) -> bool:
        """注册插件

        Args:
            plugin: 插件实例

        Returns:
            bool: 注册是否成功
        """
        ...

    def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 注销是否成功
        """
        ...

    def is_plugin_registered(self, plugin_name: str) -> bool:
        """检查插件是否已注册

        Args:
            plugin_name: 插件名称

        Returns:
            bool: 是否已注册
        """
        ...

    def get_plugin_metadata(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件元数据

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[Dict[str, Any]]: 元数据字典，如果不存在则返回None
        """
        ...

    def list_registered_plugins(self) -> List[str]:
        """列出已注册的插件

        Returns:
            List[str]: 插件名称列表
        """
        ...


class IPluginLoader(Protocol):
    """插件加载器接口

    负责从不同来源加载插件。
    """

    def load_from_file(self, file_path: str) -> Optional[IPlugin]:
        """从文件加载插件

        Args:
            file_path: 插件文件路径

        Returns:
            Optional[IPlugin]: 插件实例，加载失败则返回None
        """
        ...

    def load_from_module(self, module_path: str) -> Optional[IPlugin]:
        """从模块加载插件

        Args:
            module_path: 模块路径

        Returns:
            Optional[IPlugin]: 插件实例，加载失败则返回None
        """
        ...

    def load_from_package(self, package_path: str) -> Optional[IPlugin]:
        """从包加载插件

        Args:
            package_path: 包路径

        Returns:
            Optional[IPlugin]: 插件实例，加载失败则返回None
        """
        ...

    def validate_plugin(self, plugin: IPlugin) -> bool:
        """验证插件

        Args:
            plugin: 插件实例

        Returns:
            bool: 验证是否通过
        """
        ...

    def get_plugin_class(self, plugin_name: str) -> Optional[Type[IPlugin]]:
        """获取插件类

        Args:
            plugin_name: 插件名称

        Returns:
            Optional[Type[IPlugin]]: 插件类，如果不存在则返回None
        """
        ...


class BasePlugin(ABC):
    """插件基类

    提供插件的基础实现，插件可以继承此类来简化开发。
    """

    def __init__(self):
        self._context: Optional[IPluginContext] = None
        self._config: Optional[Dict[str, Any]] = None
        self._status = PluginStatus.UNKNOWN

    @property
    def context(self) -> Optional[IPluginContext]:
        """获取插件上下文"""
        return self._context

    @property
    def status(self) -> PluginStatus:
        """获取插件状态"""
        return self._status

    def set_context(self, context: IPluginContext) -> None:
        """设置插件上下文"""
        self._context = context

    def initialize(self, context: IPluginContext) -> bool:
        """初始化插件"""
        self._context = context
        self._status = PluginStatus.LOADED
        return True

    def activate(self) -> bool:
        """激活插件"""
        if self._status != PluginStatus.LOADED:
            return False
        self._status = PluginStatus.ACTIVE
        return True

    def deactivate(self) -> bool:
        """停用插件"""
        if self._status == PluginStatus.ACTIVE:
            self._status = PluginStatus.INACTIVE
        return True

    def cleanup(self) -> None:
        """清理插件资源"""
        self._context = None
        self._config = None
        self._status = PluginStatus.UNKNOWN

    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "type": self.plugin_type.value,
            "status": self._status.value,
            "dependencies": self.dependencies,
        }

    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """获取插件配置模式"""
        return None

    def set_config(self, config: Dict[str, Any]) -> bool:
        """设置插件配置"""
        self._config = config
        return True

    def get_config(self) -> Optional[Dict[str, Any]]:
        """获取插件配置"""
        return self._config

    def log(self, message: str, level: str = "INFO") -> None:
        """记录日志"""
        if self._context:
            self._context.log(f"[{self.name}] {message}", level)

    def emit_event(self, event_name: str, data: Any = None) -> None:
        """发送事件"""
        if self._context:
            self._context.emit_event(event_name, data)

    def register_event_handler(self, event_name: str, handler) -> None:
        """注册事件处理器"""
        if self._context:
            self._context.register_event_handler(event_name, handler)
