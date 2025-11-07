"""历史记录相关接口定义"""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Optional, List
from pathlib import Path


@dataclass
class HistoryRecord:
    """历史记录数据类

    存储单次录音的完整信息，包括音频文件、转录结果和AI优化结果
    """

    id: str  # UUID
    timestamp: datetime  # 录音时间
    audio_file_path: str  # WAV文件路径
    duration: float  # 录音时长（秒）

    # 转录阶段
    transcription_text: str  # 转录文本
    transcription_provider: str  # 转录提供商（local/groq/siliconflow等）
    transcription_status: str  # 转录状态："success" | "failed"
    transcription_error: Optional[str]  # 转录错误信息（如果有）

    # AI优化阶段
    ai_optimized_text: Optional[str]  # AI优化后的文本
    ai_provider: Optional[str]  # AI提供商（groq/nvidia/openrouter等）
    ai_status: str  # AI状态："success" | "failed" | "skipped"
    ai_error: Optional[str]  # AI错误信息（如果有）

    # 最终结果
    final_text: str  # 最终输入的文本（AI成功则是优化文本，否则是转录文本）

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "audio_file_path": self.audio_file_path,
            "duration": self.duration,
            "transcription_text": self.transcription_text,
            "transcription_provider": self.transcription_provider,
            "transcription_status": self.transcription_status,
            "transcription_error": self.transcription_error,
            "ai_optimized_text": self.ai_optimized_text,
            "ai_provider": self.ai_provider,
            "ai_status": self.ai_status,
            "ai_error": self.ai_error,
            "final_text": self.final_text,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryRecord":
        """从字典创建记录"""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            audio_file_path=data["audio_file_path"],
            duration=data["duration"],
            transcription_text=data["transcription_text"],
            transcription_provider=data["transcription_provider"],
            transcription_status=data["transcription_status"],
            transcription_error=data.get("transcription_error"),
            ai_optimized_text=data.get("ai_optimized_text"),
            ai_provider=data.get("ai_provider"),
            ai_status=data["ai_status"],
            ai_error=data.get("ai_error"),
            final_text=data["final_text"],
        )


class IHistoryStorageService(Protocol):
    """历史记录存储服务接口

    负责管理录音历史记录的持久化存储和检索
    """

    def save_record(self, record: HistoryRecord) -> bool:
        """保存历史记录（插入新记录）

        Args:
            record: 历史记录对象

        Returns:
            保存是否成功
        """
        ...

    def update_record(self, record: HistoryRecord) -> bool:
        """更新现有历史记录（只更新AI相关字段）

        Args:
            record: 历史记录对象（必须包含有效的id）

        Returns:
            更新是否成功
        """
        ...

    def get_record_by_id(self, record_id: str) -> Optional[HistoryRecord]:
        """根据ID获取单条记录

        Args:
            record_id: 记录ID

        Returns:
            历史记录对象，如果不存在则返回None
        """
        ...

    def get_records(
        self, limit: int = 50, offset: int = 0, order_by: str = "timestamp DESC"
    ) -> List[HistoryRecord]:
        """分页获取记录列表

        Args:
            limit: 返回记录数量限制
            offset: 偏移量（用于分页）
            order_by: 排序字段和方向，默认按时间倒序

        Returns:
            历史记录列表
        """
        ...

    def search_records(
        self,
        query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transcription_status: Optional[str] = None,
        ai_status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[HistoryRecord]:
        """搜索记录

        Args:
            query: 文本搜索关键词（搜索转录文本和AI优化文本）
            start_date: 开始日期
            end_date: 结束日期
            transcription_status: 转录状态筛选
            ai_status: AI状态筛选
            limit: 返回记录数量限制
            offset: 偏移量（用于分页）

        Returns:
            匹配的历史记录列表
        """
        ...

    def delete_record(self, record_id: str) -> bool:
        """删除记录（包括音频文件）

        Args:
            record_id: 记录ID

        Returns:
            删除是否成功
        """
        ...

    def delete_records(self, record_ids: List[str]) -> int:
        """批量删除记录

        Args:
            record_ids: 记录ID列表

        Returns:
            成功删除的记录数量
        """
        ...

    def get_total_count(
        self,
        query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transcription_status: Optional[str] = None,
        ai_status: Optional[str] = None,
    ) -> int:
        """获取记录总数（用于分页）

        Args:
            query: 文本搜索关键词
            start_date: 开始日期
            end_date: 结束日期
            transcription_status: 转录状态筛选
            ai_status: AI状态筛选

        Returns:
            符合条件的记录总数
        """
        ...

    def get_storage_path(self) -> Path:
        """获取存储路径

        Returns:
            历史记录和音频文件的存储路径
        """
        ...

    def cleanup_orphaned_files(self) -> int:
        """清理孤立的音频文件（数据库中没有对应记录的文件）

        Returns:
            清理的文件数量
        """
        ...
