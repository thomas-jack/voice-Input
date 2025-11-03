"""配置命令模式实现

提供可撤销的配置操作，支持命令历史和批量操作。
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict
import uuid
from dataclasses import dataclass

from ..interfaces.config import IConfigService
from ..interfaces.event import IEventService, EventPriority
from ..interfaces.ui import IUICommand


@dataclass
class CommandHistory:
    """命令历史记录"""

    command_id: str
    command_name: str
    executed_at: float
    previous_state: Dict[str, Any]
    current_state: Dict[str, Any]


class Command(ABC):
    """命令抽象基类"""

    @abstractmethod
    def execute(self) -> Any:
        """执行命令"""
        pass

    @abstractmethod
    def undo(self) -> None:
        """撤销命令"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """获取命令名称"""
        pass


class ConfigChangeCommand(Command):
    """配置变更命令"""

    def __init__(
        self,
        config_service: IConfigService,
        event_service: IEventService,
        key: str,
        value: Any,
        group: str = "default",
    ):
        self.config_service = config_service
        self.event_service = event_service
        self.key = key
        self.value = value
        self.group = group
        self.previous_value = None
        self.command_id = str(uuid.uuid4())

    def execute(self) -> Any:
        """执行配置变更"""
        # 保存之前的状态用于撤销
        self.previous_value = self.config_service.get_setting(self.key)

        # 执行变更
        self.config_service.set_setting(self.key, self.value)

        # 发送事件
        self.event_service.emit(
            "config_changed",
            {
                "key": self.key,
                "old_value": self.previous_value,
                "new_value": self.value,
                "group": self.group,
                "command_id": self.command_id,
            },
            EventPriority.HIGH,
        )

        return self.previous_value

    def undo(self) -> None:
        """撤销配置变更"""
        if self.previous_value is not None:
            self.config_service.set_setting(self.key, self.previous_value)

            self.event_service.emit(
                "config_undone",
                {
                    "key": self.key,
                    "old_value": self.value,
                    "new_value": self.previous_value,
                    "group": self.group,
                    "command_id": self.command_id,
                },
                EventPriority.HIGH,
            )

    def get_name(self) -> str:
        return f"ConfigChange({self.key}={self.value})"


class BulkConfigCommand(Command):
    """批量配置命令"""

    def __init__(self, config_service: IConfigService, event_service: IEventService):
        self.config_service = config_service
        self.event_service = event_service
        self.commands: List[Command] = []
        self.history: List[CommandHistory] = []
        self.command_id = str(uuid.uuid4())

    def add_command(self, command: Command) -> "BulkConfigCommand":
        """添加子命令"""
        self.commands.append(command)
        return self

    def execute(self) -> List[Any]:
        """执行所有命令"""
        results = []

        # 保存批量操作开始状态
        initial_state = self._capture_current_state()

        for command in self.commands:
            result = command.execute()
            results.append(result)

            # 记录单个命令历史
            self.history.append(
                CommandHistory(
                    command_id=command.command_id,
                    command_name=command.get_name(),
                    executed_at=0,  # 将在事件中设置
                    previous_state=command.previous_value,
                    current_state=command.value,
                )
            )

        # 发送批量配置变更事件
        self.event_service.emit(
            "bulk_config_changed",
            {
                "command_count": len(self.commands),
                "command_id": self.command_id,
                "individual_commands": [
                    {
                        "command_id": cmd.command_id,
                        "name": cmd.get_name(),
                        "key": cmd.key if hasattr(cmd, "key") else "bulk",
                        "old_value": cmd.previous_value
                        if hasattr(cmd, "previous_value")
                        else None,
                        "new_value": cmd.value if hasattr(cmd, "value") else None,
                    }
                    for cmd in self.commands
                ],
            },
            EventPriority.HIGH,
        )

        return results

    def undo(self) -> None:
        """撤销所有命令（逆序）"""
        for command in reversed(self.commands):
            command.undo()

        self.event_service.emit(
            "bulk_config_undone",
            {"command_count": len(self.commands), "command_id": self.command_id},
            EventPriority.HIGH,
        )

    def get_name(self) -> str:
        return f"BulkConfig({len(self.commands)} commands)"

    def _capture_current_state(self) -> Dict[str, Any]:
        """捕获当前配置状态"""
        # 简化实现，实际可能需要更完整的状态捕获
        state = {}
        for cmd in self.commands:
            if hasattr(cmd, "key"):
                state[cmd.key] = cmd.previous_value
        return state


class UndoRedoManager:
    """撤销重做管理器"""

    def __init__(self, event_service: IEventService):
        self.event_service = event_service
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_history = 50

    def execute_command(self, command: Command) -> Any:
        """执行命令"""
        result = command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()  # 新操作清空重做栈

        # 限制历史记录数量
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

        return result

    def undo(self) -> bool:
        """撤销操作"""
        if not self.undo_stack:
            return False

        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)

        return True

    def redo(self) -> bool:
        """重做操作"""
        if not self.redo_stack:
            return False

        command = self.redo_stack.pop()
        command.execute()
        self.undo_stack.append(command)

        return True

    def clear_history(self) -> None:
        """清空历史"""
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_history_info(self) -> Dict[str, int]:
        """获取历史信息"""
        return {
            "undo_count": len(self.undo_stack),
            "redo_count": len(self.redo_stack),
            "max_history": self.max_history,
        }


# UI 命令接口实现
class UIConfigChangeCommand(IUICommand):
    """UI 配置变更命令"""

    def __init__(
        self,
        config_service: IConfigService,
        event_service: IEventService,
        key: str,
        value: Any,
        display_name: str,
    ):
        self.config_command = ConfigChangeCommand(
            config_service, event_service, key, value
        )
        self.display_name = display_name
        self.undo_manager = UndoRedoManager(event_service)

    def execute(self) -> bool:
        """执行命令"""
        try:
            self.undo_manager.execute_command(self.config_command)
            return True
        except Exception as e:
            self.event_service.emit(
                "ui_command_error", {"command_name": self.display_name, "error": str(e)}
            )
            return False

    def undo(self) -> bool:
        """撤销命令"""
        return self.undo_manager.undo()

    def redo(self) -> bool:
        """重做命令"""
        return self.undo_manager.redo()

    def get_display_name(self) -> str:
        return self.display_name

    def get_description(self) -> str:
        return f"Change {self.display_name}"
