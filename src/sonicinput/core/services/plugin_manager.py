"""插件管理器实现

提供完整的插件生命周期管理功能，包括加载、激活、停用、卸载等。
"""

import os
import importlib
import importlib.util
import inspect
from typing import Dict, List, Optional, Type, Any
from pathlib import Path
from ..interfaces import IPlugin, PluginType, PluginStatus, BasePlugin
from ...utils import app_logger


class PluginContext:
    """插件上下文实现

    为插件提供运行时环境和服务访问。
    """

    def __init__(self, service_container, event_service, config_service):
        self._service_container = service_container
        self._event_service = event_service
        self._config_service = config_service

    def get_service(self, service_interface: Type) -> Any:
        """获取服务实例"""
        try:
            return self._service_container.get(service_interface)
        except Exception as e:
            app_logger.log_error(
                e, f"PluginContext.get_service for {service_interface.__name__}"
            )
            return None

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        try:
            return self._config_service.get_setting(key, default)
        except Exception as e:
            app_logger.log_error(e, f"PluginContext.get_config for {key}")
            return default

    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        try:
            self._config_service.set_setting(key, value)
        except Exception as e:
            app_logger.log_error(e, f"PluginContext.set_config for {key}")

    def log(self, message: str, level: str = "INFO") -> None:
        """记录日志"""
        try:
            if hasattr(app_logger, f"log_{level.lower()}"):
                getattr(app_logger, f"log_{level.lower()}")(
                    f"[PluginContext] {message}"
                )
            else:
                app_logger.log_audio_event(
                    f"[PluginContext] {message}", {"level": level}
                )
        except Exception as e:
            print(f"[PluginContext Error] {message}: {e}")

    def emit_event(self, event_name: str, data: Any = None) -> None:
        """发送事件"""
        try:
            if self._event_service:
                self._event_service.emit(event_name, data)
        except Exception as e:
            app_logger.log_error(e, f"PluginContext.emit_event for {event_name}")

    def register_event_handler(self, event_name: str, handler) -> None:
        """注册事件处理器"""
        try:
            if self._event_service:
                self._event_service.on(event_name, handler)
        except Exception as e:
            app_logger.log_error(
                e, f"PluginContext.register_event_handler for {event_name}"
            )


class PluginRegistry:
    """插件注册表实现"""

    def __init__(self):
        self._plugins: Dict[str, IPlugin] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._event_handlers: Dict[str, List[Any]] = {}

    def register_plugin(self, plugin: IPlugin) -> bool:
        """注册插件"""
        try:
            plugin_name = plugin.name
            if plugin_name in self._plugins:
                app_logger.log_audio_event(
                    "Plugin already registered", {"plugin_name": plugin_name}
                )
                return False

            self._plugins[plugin_name] = plugin
            self._metadata[plugin_name] = plugin.get_info()
            app_logger.log_audio_event(
                "Plugin registered",
                {
                    "plugin_name": plugin_name,
                    "plugin_type": plugin.plugin_type.value,
                    "version": plugin.version,
                },
            )
            return True
        except Exception as e:
            app_logger.log_error(e, "PluginRegistry.register_plugin")
            return False

    def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件"""
        try:
            if plugin_name not in self._plugins:
                return False

            plugin = self._plugins[plugin_name]
            plugin.cleanup()
            del self._plugins[plugin_name]
            del self._metadata[plugin_name]

            if plugin_name in self._event_handlers:
                del self._event_handlers[plugin_name]

            app_logger.log_audio_event(
                "Plugin unregistered", {"plugin_name": plugin_name}
            )
            return True
        except Exception as e:
            app_logger.log_error(e, "PluginRegistry.unregister_plugin")
            return False

    def is_plugin_registered(self, plugin_name: str) -> bool:
        """检查插件是否已注册"""
        return plugin_name in self._plugins

    def get_plugin_metadata(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件元数据"""
        return self._metadata.get(plugin_name)

    def list_registered_plugins(self) -> List[str]:
        """列出已注册的插件"""
        return list(self._plugins.keys())

    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """获取插件实例"""
        return self._plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, IPlugin]:
        """获取所有插件"""
        return self._plugins.copy()


class PluginLoader:
    """插件加载器实现"""

    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
        self._plugin_classes: Dict[str, Type[IPlugin]] = {}

    def load_from_file(self, file_path: str) -> Optional[IPlugin]:
        """从文件加载插件"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                app_logger.log_error(
                    Exception(f"Plugin file not found: {file_path}"),
                    "PluginLoader.load_from_file",
                )
                return None

            # 动态加载模块
            spec = importlib.util.spec_from_file_location(
                f"plugin_{file_path.stem}", file_path
            )
            if spec is None or spec.loader is None:
                app_logger.log_error(
                    Exception(f"Could not create spec for {file_path}"),
                    "PluginLoader.load_from_file",
                )
                return None

            module = importlib.util.module_from_spec(spec)
            if spec.loader:
                spec.loader.exec_module(module)

            self._loaded_modules[file_path.stem] = module

            # 查找插件类
            plugin_class = self._find_plugin_class(module)
            if plugin_class:
                plugin_instance = plugin_class()
                self._plugin_classes[plugin_instance.name] = plugin_class
                return plugin_instance
            else:
                app_logger.log_error(
                    Exception(f"No valid plugin class found in {file_path}"),
                    "PluginLoader.load_from_file",
                )
                return None

        except Exception as e:
            app_logger.log_error(e, f"PluginLoader.load_from_file for {file_path}")
            return None

    def load_from_module(self, module_path: str) -> Optional[IPlugin]:
        """从模块加载插件"""
        try:
            module = importlib.import_module(module_path)
            self._loaded_modules[module_path] = module

            plugin_class = self._find_plugin_class(module)
            if plugin_class:
                plugin_instance = plugin_class()
                self._plugin_classes[plugin_instance.name] = plugin_class
                return plugin_instance
            else:
                app_logger.log_error(
                    Exception(f"No valid plugin class found in module {module_path}"),
                    "PluginLoader.load_from_module",
                )
                return None

        except Exception as e:
            app_logger.log_error(e, f"PluginLoader.load_from_module for {module_path}")
            return None

    def load_from_package(self, package_path: str) -> Optional[IPlugin]:
        """从包加载插件"""
        try:
            module = importlib.import_module(package_path)
            self._loaded_modules[package_path] = module

            plugin_class = self._find_plugin_class(module)
            if plugin_class:
                plugin_instance = plugin_class()
                self._plugin_classes[plugin_instance.name] = plugin_class
                return plugin_instance
            else:
                app_logger.log_error(
                    Exception(f"No valid plugin class found in package {package_path}"),
                    "PluginLoader.load_from_package",
                )
                return None

        except Exception as e:
            app_logger.log_error(
                e, f"PluginLoader.load_from_package for {package_path}"
            )
            return None

    def _find_plugin_class(self, module) -> Optional[Type[IPlugin]]:
        """在模块中查找插件类"""
        try:
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, (IPlugin, BasePlugin))
                    and obj != IPlugin
                    and obj != BasePlugin
                ):
                    return obj
            return None
        except Exception as e:
            app_logger.log_error(e, "PluginLoader._find_plugin_class")
            return None

    def validate_plugin(self, plugin: IPlugin) -> bool:
        """验证插件"""
        try:
            # 检查必需的属性和方法
            required_attrs = [
                "name",
                "version",
                "description",
                "author",
                "plugin_type",
                "dependencies",
            ]
            for attr in required_attrs:
                if not hasattr(plugin, attr):
                    return False

            # 检查必需的方法
            required_methods = [
                "initialize",
                "activate",
                "deactivate",
                "cleanup",
                "get_info",
            ]
            for method in required_methods:
                if not hasattr(plugin, method) or not callable(getattr(plugin, method)):
                    return False

            # 检查插件类型
            if not isinstance(plugin.plugin_type, PluginType):
                return False

            return True
        except Exception as e:
            app_logger.log_error(e, "PluginLoader.validate_plugin")
            return False

    def get_plugin_class(self, plugin_name: str) -> Optional[Type[IPlugin]]:
        """获取插件类"""
        return self._plugin_classes.get(plugin_name)


class PluginManager:
    """插件管理器实现"""

    def __init__(self, service_container=None, event_service=None, config_service=None):
        self._registry = PluginRegistry()
        self._loader = PluginLoader()
        self._context = PluginContext(service_container, event_service, config_service)
        self._auto_load_enabled = True
        self._plugin_directories: List[str] = []
        self._plugin_status: Dict[str, PluginStatus] = {}

        app_logger.log_audio_event("PluginManager initialized", {})

    def load_plugin(self, plugin_path: str) -> bool:
        """加载插件"""
        try:
            plugin = self._loader.load_from_file(plugin_path)
            if not plugin:
                return False

            if not self._loader.validate_plugin(plugin):
                app_logger.log_audio_event(
                    "Plugin validation failed",
                    {"plugin_name": plugin.name, "plugin_path": plugin_path},
                )
                return False

            if self._registry.register_plugin(plugin):
                plugin.set_context(self._context)
                plugin.initialize(self._context)
                self._plugin_status[plugin.name] = PluginStatus.LOADED
                app_logger.log_audio_event(
                    "Plugin loaded successfully",
                    {"plugin_name": plugin.name, "plugin_path": plugin_path},
                )
                return True
            else:
                return False

        except Exception as e:
            app_logger.log_error(e, f"PluginManager.load_plugin for {plugin_path}")
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        try:
            plugin = self._registry.get_plugin(plugin_name)
            if not plugin:
                return False

            # 停用插件
            if plugin.status == PluginStatus.ACTIVE:
                self.deactivate_plugin(plugin_name)

            # 卸载插件
            plugin.cleanup()
            success = self._registry.unregister_plugin(plugin_name)
            if success:
                self._plugin_status[plugin_name] = PluginStatus.UNKNOWN
                app_logger.log_audio_event(
                    "Plugin unloaded", {"plugin_name": plugin_name}
                )
            return success

        except Exception as e:
            app_logger.log_error(e, f"PluginManager.unload_plugin for {plugin_name}")
            return False

    def activate_plugin(self, plugin_name: str) -> bool:
        """激活插件"""
        try:
            plugin = self._registry.get_plugin(plugin_name)
            if not plugin:
                return False

            # 检查依赖
            if not self._check_dependencies(plugin):
                return False

            success = plugin.activate()
            if success:
                self._plugin_status[plugin_name] = PluginStatus.ACTIVE
                app_logger.log_audio_event(
                    "Plugin activated", {"plugin_name": plugin_name}
                )
            return success

        except Exception as e:
            app_logger.log_error(e, f"PluginManager.activate_plugin for {plugin_name}")
            return False

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """停用插件"""
        try:
            plugin = self._registry.get_plugin(plugin_name)
            if not plugin:
                return False

            success = plugin.deactivate()
            if success:
                self._plugin_status[plugin_name] = PluginStatus.INACTIVE
                app_logger.log_audio_event(
                    "Plugin deactivated", {"plugin_name": plugin_name}
                )
            return success

        except Exception as e:
            app_logger.log_error(
                e, f"PluginManager.deactivate_plugin for {plugin_name}"
            )
            return False

    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """获取插件实例"""
        return self._registry.get_plugin(plugin_name)

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[IPlugin]:
        """根据类型获取插件列表"""
        all_plugins = self._registry.get_all_plugins()
        return [
            plugin
            for plugin in all_plugins.values()
            if plugin.plugin_type == plugin_type
        ]

    def get_all_plugins(self) -> Dict[str, IPlugin]:
        """获取所有插件"""
        return self._registry.get_all_plugins()

    def get_plugin_status(self, plugin_name: str) -> PluginStatus:
        """获取插件状态"""
        return self._plugin_status.get(plugin_name, PluginStatus.UNKNOWN)

    def scan_plugins_directory(self, directory: str) -> int:
        """扫描插件目录"""
        try:
            if not os.path.exists(directory):
                app_logger.log_audio_event(
                    "Plugin directory does not exist", {"directory": directory}
                )
                return 0

            discovered_plugins = 0
            directory_path = Path(directory)

            # 扫描.py文件
            for file_path in directory_path.glob("*.py"):
                if file_path.name.startswith("__"):
                    continue

                if self.load_plugin(str(file_path)):
                    discovered_plugins += 1

            app_logger.log_audio_event(
                "Plugin directory scanned",
                {"directory": directory, "plugins_found": discovered_plugins},
            )
            return discovered_plugins

        except Exception as e:
            app_logger.log_error(
                e, f"PluginManager.scan_plugins_directory for {directory}"
            )
            return 0

    def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件"""
        try:
            # 卸载插件
            if self._registry.is_plugin_registered(plugin_name):
                self.unload_plugin(plugin_name)

            # 重新扫描并加载
            for plugin_dir in self._plugin_directories:
                discovered = self.scan_plugins_directory(plugin_dir)
                if discovered > 0:
                    break

            # 检查是否重新加载成功
            return self._registry.is_plugin_registered(plugin_name)

        except Exception as e:
            app_logger.log_error(e, f"PluginManager.reload_plugin for {plugin_name}")
            return False

    def enable_plugin_auto_load(self, enabled: bool) -> None:
        """启用/禁用插件自动加载"""
        self._auto_load_enabled = enabled
        app_logger.log_audio_event(
            "Plugin auto load setting changed", {"enabled": enabled}
        )

    def add_plugin_directory(self, directory: str) -> None:
        """添加插件目录"""
        if directory not in self._plugin_directories:
            self._plugin_directories.append(directory)
            if self._auto_load_enabled:
                self.scan_plugins_directory(directory)

    def get_plugin_dependencies(self, plugin_name: str) -> List[str]:
        """获取插件依赖"""
        plugin = self._registry.get_plugin(plugin_name)
        if plugin:
            return plugin.dependencies
        return []

    def resolve_dependency_order(self, plugin_names: List[str]) -> List[str]:
        """解析插件依赖顺序"""
        try:
            visited = set()
            result = []

            def visit(plugin_name: str):
                if plugin_name in visited:
                    return
                visited.add(plugin_name)

                plugin = self._registry.get_plugin(plugin_name)
                if plugin:
                    for dep in plugin.dependencies:
                        visit(dep)

                result.append(plugin_name)

            for plugin_name in plugin_names:
                if plugin_name not in visited:
                    visit(plugin_name)

            return result

        except Exception as e:
            app_logger.log_error(e, "PluginManager.resolve_dependency_order")
            return plugin_names
