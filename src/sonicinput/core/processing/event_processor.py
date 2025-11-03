"""事件处理管道 - 责任链模式实现

提供可扩展的事件处理机制，支持多个处理器按顺序处理事件。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import threading
import time
from dataclasses import dataclass

from ..interfaces.event import IEventService, EventPriority
from ..interfaces.ui import IUIEventProcessor


@dataclass
class EventContext:
    """事件上下文"""

    event_name: str
    data: Any
    priority: EventPriority
    timestamp: float
    metadata: Dict[str, Any]
    halted: bool = False
    result: Any = None


class EventHandler(ABC):
    """事件处理器抽象基类"""

    def __init__(self, name: str, priority: int = 0):
        self.name = name
        self.priority = priority
        self.next_handler: Optional["EventHandler"] = None
        self.event_service: Optional[IEventService] = None

    def set_next(self, handler: "EventHandler") -> "EventHandler":
        """设置下一个处理器"""
        self.next_handler = handler
        return handler

    def set_event_service(self, event_service: IEventService):
        """设置事件服务"""
        self.event_service = event_service
        if self.next_handler:
            self.next_handler.set_event_service(event_service)

    @abstractmethod
    def can_handle(self, event_name: str, context: EventContext) -> bool:
        """判断是否能处理该事件"""
        pass

    @abstractmethod
    def process(self, context: EventContext) -> Any:
        """处理事件"""
        pass

    def handle(self, event_name: str, context: EventContext) -> Any:
        """处理事件的入口方法"""
        if not self.can_handle(event_name, context):
            if self.next_handler:
                return self.next_handler.handle(event_name, context)
            return None

        try:
            # 处理事件
            result = self.process(context)

            # 如果处理器设置了结果，保存到上下文
            if result is not None:
                context.result = result

            # 传递给下一个处理器
            if self.next_handler and not context.halted:
                return self.next_handler.handle(event_name, context)

            return context.result

        except Exception as e:
            # 记录错误并继续处理
            if self.event_service:
                self.event_service.emit(
                    "event_handler_error",
                    {
                        "handler_name": self.name,
                        "event_name": event_name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )

            if self.next_handler:
                return self.next_handler.handle(event_name, context)
            return None


class ValidationHandler(EventHandler):
    """验证处理器"""

    def __init__(self):
        super().__init__("validation", priority=10)

    def can_handle(self, event_name: str, context: EventContext) -> bool:
        return True  # 所有事件都需要验证

    def process(self, context: EventContext) -> Any:
        # 验证事件数据
        if context.data is None:
            context.metadata["validation_error"] = "Event data is None"
            context.halted = True
            return None

        # 检查事件数据类型
        if hasattr(context.data, "__dict__"):
            # 如果是对象，检查必要属性
            required_attrs = getattr(context.data, "_required_attrs", [])
            missing_attrs = [
                attr for attr in required_attrs if not hasattr(context.data, attr)
            ]

            if missing_attrs:
                context.metadata["validation_error"] = (
                    f"Missing required attributes: {missing_attrs}"
                )
                context.halted = True
                return None

        return context.data


class LoggingHandler(EventHandler):
    """日志处理器"""

    def __init__(self, log_all_events: bool = False):
        super().__init__("logging", priority=5)
        self.log_all_events = log_all_events

    def can_handle(self, event_name: str, context: EventContext) -> bool:
        # 只记录重要事件或配置记录所有事件
        important_events = {
            "recording_started",
            "recording_stopped",
            "transcription_completed",
            "ai_processing_started",
            "ai_processing_completed",
            "text_input_started",
        }

        return self.log_all_events or event_name in important_events

    def process(self, context: EventContext) -> Any:
        # 记录事件
        if self.event_service:
            self.event_service.emit(
                "event_logged",
                {
                    "event_name": context.event_name,
                    "priority": context.priority.name,
                    "timestamp": context.timestamp,
                    "has_data": context.data is not None,
                    "metadata": context.metadata,
                },
            )

        return context.data


class TransformationHandler(EventHandler):
    """数据转换处理器"""

    def __init__(self):
        super().__init__("transformation", priority=8)

    def can_handle(self, event_name: str, context: EventContext) -> bool:
        # 只处理需要数据转换的事件
        return event_name in ["audio_level_update", "text_refined"]

    def process(self, context: EventContext) -> Any:
        # 数据转换逻辑
        if context.event_name == "audio_level_update" and isinstance(
            context.data, (int, float)
        ):
            # 音频级别标准化
            normalized_value = min(1.0, max(0.0, float(context.data) / 100.0))
            context.metadata["normalized_value"] = normalized_value
            return normalized_value

        elif context.event_name == "text_refined" and isinstance(context.data, str):
            # 文本处理
            processed_text = context.data.strip()
            context.metadata["text_length"] = len(processed_text)
            return processed_text

        return context.data


class EventProcessorPipeline:
    """事件处理管道"""

    def __init__(self, event_service: IEventService):
        self.event_service = event_service
        self.handlers: List[EventHandler] = []
        self._lock = threading.RLock()
        self.pipeline_initialized = False

    def add_handler(self, handler: EventHandler) -> "EventProcessorPipeline":
        """添加处理器"""
        with self._lock:
            self.handlers.append(handler)
            self.handlers.sort(key=lambda h: h.priority, reverse=True)

            # 设置事件服务
            handler.set_event_service(self.event_service)

            # 连接处理器
            for i in range(len(self.handlers) - 1):
                self.handlers[i].set_next(self.handlers[i + 1])

            self.pipeline_initialized = True

        return self

    def process_event(
        self,
        event_name: str,
        data: Any = None,
        priority: EventPriority = EventPriority.NORMAL,
    ) -> Any:
        """处理事件"""
        if not self.pipeline_initialized:
            return data

        with self._lock:
            # 创建事件上下文
            context = EventContext(
                event_name=event_name,
                data=data,
                priority=priority,
                timestamp=time.time(),
                metadata={},
            )

            # 从第一个处理器开始处理
            if self.handlers:
                return self.handlers[0].handle(event_name, context)

            return data

    def clear_handlers(self):
        """清空所有处理器"""
        with self._lock:
            self.handlers.clear()
            self.pipeline_initialized = False

    def get_handler_names(self) -> List[str]:
        """获取处理器名称列表"""
        return [handler.name for handler in self.handlers]


# UI 事件处理器接口实现
class UIEventProcessor(IUIEventProcessor):
    """UI 事件处理器"""

    def __init__(self, event_service: IEventService):
        self.event_service = event_service
        self.pipeline = EventProcessorPipeline(event_service)
        self._setup_default_handlers()

    def _setup_default_handlers(self):
        """设置默认处理器"""
        validation_handler = ValidationHandler()
        logging_handler = LoggingHandler(log_all_events=True)
        transformation_handler = TransformationHandler()

        self.pipeline.add_handler(validation_handler)
        self.pipeline.add_handler(logging_handler)
        self.pipeline.add_handler(transformation_handler)

    def process_ui_event(self, event_name: str, data: Any = None) -> Any:
        """处理 UI 事件"""
        return self.pipeline.process_event(event_name, data, EventPriority.HIGH)

    def add_ui_handler(self, handler: EventHandler):
        """添加 UI 特定处理器"""
        self.pipeline.add_handler(handler)

    def get_processing_stats(self) -> Dict[str, Any]:
        """获取处理统计"""
        return {
            "handler_count": len(self.pipeline.handlers),
            "handler_names": self.pipeline.get_handler_names(),
            "pipeline_initialized": self.pipeline.pipeline_initialized,
        }


# 注册事件处理管道到 DI 容器
def register_event_processor(container) -> None:
    """注册事件处理管道到 DI 容器"""
    event_service = container.get(IEventService)
    processor = UIEventProcessor(event_service)
    container.register_singleton(IUIEventProcessor, processor)
