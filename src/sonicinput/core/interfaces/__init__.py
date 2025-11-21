"""核心接口定义模块

统一的接口定义，用于实现高内聚、低耦合的架构设计。
所有服务和组件都应该依赖接口而不是具体实现。
"""

from .config import IConfigService
from .audio import IAudioService
from .speech import ISpeechService
from .ai import IAIService
from .input import IInputService
from .hotkey import IHotkeyService
from .event import IEventService, EventPriority
from .ui import IUIComponent, IOverlayComponent, ITrayComponent
from .storage import IStorageService, ICacheService
from .lifecycle import ILifecycleManaged, ILifecycleManager
from .state import IStateManager, AppState, RecordingState
from .lifecycle import ComponentState
from .controller import (
    IRecordingController,
    ITranscriptionController,
    IAIProcessingController,
    IInputController,
)
from .ui_main_service import (
    IUIMainService,
    IUISettingsService,
    IUIModelService,
    IUIAudioService,
    IUIGPUService,
)

# Interfaces added after Phase 1.2 cleanup (missing definitions)
from typing import Protocol, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class HistoryRecord:
    """历史记录数据类

    完整记录包含：
    - 基础信息（id, timestamp, duration）
    - 音频文件路径
    - 转录结果（text, provider, status, error）
    - AI优化结果（optimized_text, provider, status, error）
    - 最终文本（final_text）
    """

    id: str
    timestamp: datetime
    audio_file_path: str
    duration: float
    transcription_text: str
    transcription_provider: str
    transcription_status: str
    transcription_error: Optional[str] = None
    ai_optimized_text: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_status: str = "pending"
    ai_error: Optional[str] = None
    final_text: str = ""


class IHistoryStorageService(Protocol):
    """历史存储服务接口"""

    def save_record(self, record: HistoryRecord) -> bool: ...

    def get_records(self, limit: int = 100) -> List[HistoryRecord]: ...


class IApplicationOrchestrator(Protocol):
    """应用编排器接口"""

    pass


class IUIEventBridge(Protocol):
    """UI事件桥接接口"""

    pass


__all__ = [
    # 核心服务接口
    "IConfigService",
    "IAudioService",
    "ISpeechService",
    "IAIService",
    "IInputService",
    "IHotkeyService",
    "IEventService",
    "EventPriority",
    # UI组件接口
    "IUIComponent",
    "IOverlayComponent",
    "ITrayComponent",
    # 数据存储接口
    "IStorageService",
    "ICacheService",
    # 生命周期管理接口
    "ILifecycleManaged",
    "ILifecycleManager",
    # 状态管理接口
    "IStateManager",
    "AppState",
    "RecordingState",
    "ComponentState",
    # 控制器接口
    "IRecordingController",
    "ITranscriptionController",
    "IAIProcessingController",
    "IInputController",
    # 新增接口
    "IHistoryStorageService",
    "HistoryRecord",
    "IApplicationOrchestrator",
    "IUIEventBridge",
    # UI服务接口
    "IUIMainService",
    "IUISettingsService",
    "IUIModelService",
    "IUIAudioService",
    "IUIGPUService",
]
