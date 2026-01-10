"""示例插件

这是一个演示插件系统的简单插件，展示了如何创建和实现自定义插件。
"""

from typing import Dict, Any, Optional, List
from sonicinput.core.interfaces import BasePlugin, PluginType, IPluginContext
from sonicinput.core.services.events import Events


class ExamplePlugin(BasePlugin):
    """示例插件

    演示插件系统的基本用法。
    """

    @property
    def name(self) -> str:
        """插件名称"""
        return "example_plugin"

    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"

    @property
    def description(self) -> str:
        """插件描述"""
        return "演示插件系统的示例插件"

    @property
    def author(self) -> str:
        """插件作者"""
        return "SonicInput Team"

    @property
    def plugin_type(self) -> PluginType:
        """插件类型"""
        return PluginType.EXTENSION

    @property
    def dependencies(self) -> List[str]:
        """插件依赖列表"""
        return []  # 这个示例插件没有依赖

    def initialize(self, context: IPluginContext) -> bool:
        """初始化插件"""
        super().initialize(context)
        self.log("ExamplePlugin initialized")
        return True

    def activate(self) -> bool:
        """激活插件"""
        if not super().activate():
            return False

        # 注册事件处理器
        self.register_event_handler(Events.APP_STARTED, self._on_application_started)
        self.register_event_handler(Events.RECORDING_STARTED, self._on_recording_started)

        self.log("ExamplePlugin activated and ready to use")
        return True

    def deactivate(self) -> bool:
        """停用插件"""
        if not super().deactivate():
            return False

        self.log("ExamplePlugin deactivated")
        return True

    def cleanup(self) -> None:
        """清理插件资源"""
        self.log("ExamplePlugin cleanup completed")
        super().cleanup()

    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        info = super().get_info()
        info.update(
            {
                "features": ["事件监听", "日志记录", "示例功能"],
                "supported_events": [
                    Events.APP_STARTED,
                    Events.RECORDING_STARTED,
                    Events.RECORDING_STOPPED,
                ],
            }
        )
        return info

    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """获取插件配置模式"""
        return {
            "type": "object",
            "properties": {
                "enable_logging": {
                    "type": "boolean",
                    "default": True,
                    "description": "是否启用插件日志",
                },
                "message_prefix": {
                    "type": "string",
                    "default": "[Example]",
                    "description": "日志消息前缀",
                },
            },
        }

    def set_config(self, config: Dict[str, Any]) -> bool:
        """设置插件配置"""
        if not super().set_config(config):
            return False

        # 应用配置
        self._enable_logging = config.get("enable_logging", True)
        self._message_prefix = config.get("message_prefix", "[Example]")
        return True

    def get_config(self) -> Optional[Dict[str, Any]]:
        """获取插件配置"""
        config = super().get_config()
        if config:
            return config

        # 返回默认配置
        return {"enable_logging": True, "message_prefix": "[Example]"}

    def _on_application_started(self, data: Any = None) -> None:
        """应用启动事件处理器"""
        if self._enable_logging:
            self.log("Application started!")

    def _on_recording_started(self, data: Any = None) -> None:
        """录音开始事件处理器"""
        if self._enable_logging:
            self.log("Recording started!")

    def log(self, message: str) -> None:
        """记录日志"""
        if self._enable_logging:
            full_message = f"{self._message_prefix} {message}"
            super().log(full_message)

    def perform_custom_action(self, action_name: str, data: Any = None) -> bool:
        """执行自定义操作"""
        if self._enable_logging:
            self.log(f"Performing custom action: {action_name}")

        # 在这里实现插件的具体功能
        if action_name == "example":
            self.log("This is an example action!")
            return True

        return False
