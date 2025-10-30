"""流式转录协调器 - 负责流式转录的协调和管理"""

import threading
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import numpy as np

from ...utils import app_logger


@dataclass
class StreamingChunk:
    """流式转录块"""
    chunk_id: int
    audio_data: np.ndarray
    timestamp: float
    result_event: threading.Event
    result_container: Dict[str, Any]


class StreamingCoordinator:
    """流式转录协调器

    负责管理流式转录的分块处理和结果协调。
    与具体的转录逻辑和模型管理解耦。
    """

    def __init__(self, event_service=None):
        """初始化流式协调器

        Args:
            event_service: 事件服务（可选）
        """
        self.event_service = event_service

        # 流式转录状态管理
        self._streaming_mode = False
        self._streaming_lock = threading.RLock()

        # 流式块管理
        with self._streaming_lock:
            self._streaming_chunks: List[StreamingChunk] = []
            self._next_chunk_id = 0

        # 流式统计
        self._streaming_stats = {
            "total_chunks": 0,
            "completed_chunks": 0,
            "failed_chunks": 0,
            "total_audio_duration": 0.0,
            "average_chunk_time": 0.0
        }

        app_logger.log_audio_event("StreamingCoordinator initialized", {})

    def start_streaming(self) -> None:
        """开始流式转录模式"""
        with self._streaming_lock:
            if self._streaming_mode:
                return

            self._streaming_mode = True
            self._reset_stats()

            app_logger.log_audio_event("Streaming mode started", {})

            # 发送流式开始事件
            self._emit_streaming_event("streaming_started", {})

    def stop_streaming(self) -> Dict[str, Any]:
        """停止流式转录模式

        Returns:
            流式转录统计信息
        """
        with self._streaming_lock:
            if not self._streaming_mode:
                return self._get_stats()

            self._streaming_mode = False

            # 处理剩余的块
            pending_chunks = len(self._streaming_chunks)
            if pending_chunks > 0:
                app_logger.log_audio_event("Cleaning up pending chunks", {
                    "pending_count": pending_chunks
                })

                # 标记剩余块为失败
                for chunk in self._streaming_chunks:
                    chunk.result_container.update({
                        "success": False,
                        "error": "Streaming stopped before processing",
                        "error_type": "streaming_stopped"
                    })
                    chunk.result_event.set()

                self._streaming_chunks.clear()

            stats = self._get_stats()

            app_logger.log_audio_event("Streaming mode stopped", stats)

            # 发送流式结束事件
            self._emit_streaming_event("streaming_stopped", stats)

            return stats

    def add_streaming_chunk(self, audio_data: np.ndarray) -> int:
        """添加流式转录块

        Args:
            audio_data: 音频数据

        Returns:
            块ID
        """
        with self._streaming_lock:
            if not self._streaming_mode:
                return -1

            chunk_id = self._next_chunk_id
            self._next_chunk_id += 1

            # 创建结果容器和事件
            result_container = {
                "success": False,
                "text": "",
                "error": None,
                "error_type": None,
                "processing_time": 0.0,
                "timestamp": time.time()
            }

            result_event = threading.Event()

            # 创建流式块
            chunk = StreamingChunk(
                chunk_id=chunk_id,
                audio_data=audio_data.copy(),  # 复制数据避免引用问题
                timestamp=time.time(),
                result_event=result_event,
                result_container=result_container
            )

            self._streaming_chunks.append(chunk)
            self._streaming_stats["total_chunks"] += 1
            self._streaming_stats["total_audio_duration"] += len(audio_data) / 16000  # 假设16kHz

            app_logger.log_audio_event("Streaming chunk added", {
                "chunk_id": chunk_id,
                "audio_length": len(audio_data),
                "queue_size": len(self._streaming_chunks)
            })

            return chunk_id

    def get_pending_chunks(self) -> List[StreamingChunk]:
        """获取所有待处理的流式块

        Returns:
            待处理的流式块列表
        """
        with self._streaming_lock:
            # 返回所有待处理块的副本
            return list(self._streaming_chunks)

    def get_next_chunk(self, timeout: Optional[float] = None) -> Optional[StreamingChunk]:
        """获取下一个待处理的流式块

        Args:
            timeout: 超时时间（秒）

        Returns:
            流式块对象，如果没有块则返回None
        """
        start_time = time.time()

        while True:
            with self._streaming_lock:
                if self._streaming_chunks:
                    chunk = self._streaming_chunks.pop(0)
                    return chunk

                # 检查超时
                if timeout and (time.time() - start_time) > timeout:
                    return None

                # 检查是否仍在流式模式
                if not self._streaming_mode:
                    return None

            # 短暂等待
            time.sleep(0.01)

    def complete_chunk(self, chunk_id: int, result: Dict[str, Any]) -> None:
        """标记流式块处理完成

        Args:
            chunk_id: 块ID
            result: 处理结果
        """
        with self._streaming_lock:
            # 查找对应的块
            chunk = None
            for c in self._streaming_chunks:
                if c.chunk_id == chunk_id:
                    chunk = c
                    break

            if chunk:
                # 更新结果容器
                chunk.result_container.update(result)
                chunk.result_container["chunk_id"] = chunk_id
                chunk.result_container["completed_at"] = time.time()

                # 计算处理时间
                processing_time = time.time() - chunk.timestamp
                chunk.result_container["processing_time"] = processing_time

                # 更新统计
                self._update_stats(processing_time, result.get("success", False))

                # 设置事件标志
                chunk.result_event.set()

                # 从队列中移除
                self._streaming_chunks.remove(chunk)

                app_logger.log_audio_event("Streaming chunk completed", {
                    "chunk_id": chunk_id,
                    "success": result.get("success", False),
                    "processing_time": processing_time,
                    "text_length": len(result.get("text", "")),
                    "queue_size": len(self._streaming_chunks)
                })

                # 发送块完成事件
                self._emit_streaming_event("streaming_chunk_completed", {
                    "chunk_id": chunk_id,
                    "result": result
                })

    def get_chunk_result(self, chunk_id: int, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """获取流式块的处理结果

        Args:
            chunk_id: 块ID
            timeout: 超时时间（秒）

        Returns:
            处理结果，如果超时则返回None
        """
        with self._streaming_lock:
            # 查找对应的块
            chunk = None
            for c in self._streaming_chunks:
                if c.chunk_id == chunk_id:
                    chunk = c
                    break

        if not chunk:
            return None

        # 等待结果
        if chunk.result_event.wait(timeout=timeout):
            return chunk.result_container.copy()
        else:
            return None

    def get_pending_chunk_count(self) -> int:
        """获取待处理的块数量

        Returns:
            待处理块数量
        """
        with self._streaming_lock:
            return len(self._streaming_chunks)

    def is_streaming(self) -> bool:
        """检查是否在流式模式

        Returns:
            True如果在流式模式
        """
        return self._streaming_mode

    def get_stats(self) -> Dict[str, Any]:
        """获取流式转录统计信息

        Returns:
            统计信息字典
        """
        with self._streaming_lock:
            return self._get_stats().copy()

    def get_completed_chunks(self) -> List[StreamingChunk]:
        """获取所有已完成的转录块

        Returns:
            已完成的转录块列表
        """
        with self._streaming_lock:
            completed_chunks = []

            # 遍历所有块，找到已完成的
            for chunk in self._streaming_chunks:
                if chunk.result_event.is_set():
                    completed_chunks.append(chunk)

            return completed_chunks

    def _get_stats(self) -> Dict[str, Any]:
        """获取统计信息（内部方法，需要持有锁）"""
        stats = self._streaming_stats.copy()
        stats.update({
            "is_streaming": self._streaming_mode,
            "pending_chunks": len(self._streaming_chunks),
            "next_chunk_id": self._next_chunk_id,
            "success_rate": (
                stats["completed_chunks"] / max(stats["total_chunks"], 1) * 100
            ) if stats["total_chunks"] > 0 else 0.0
        })
        return stats

    def _reset_stats(self) -> None:
        """重置统计信息"""
        self._streaming_stats = {
            "total_chunks": 0,
            "completed_chunks": 0,
            "failed_chunks": 0,
            "total_audio_duration": 0.0,
            "average_chunk_time": 0.0
        }
        self._next_chunk_id = 0

    def _update_stats(self, processing_time: float, success: bool) -> None:
        """更新统计信息

        Args:
            processing_time: 处理时间
            success: 是否成功
        """
        if success:
            self._streaming_stats["completed_chunks"] += 1
        else:
            self._streaming_stats["failed_chunks"] += 1

        # 更新平均处理时间
        completed = self._streaming_stats["completed_chunks"]
        if completed > 0:
            current_avg = self._streaming_stats["average_chunk_time"]
            self._streaming_stats["average_chunk_time"] = (
                (current_avg * (completed - 1) + processing_time) / completed
            )

    def _emit_streaming_event(self, event_name: str, data: Dict[str, Any]) -> None:
        """发送流式转录事件

        Args:
            event_name: 事件名称
            data: 事件数据
        """
        if self.event_service:
            try:
                self.event_service.emit(event_name, data)
            except Exception as e:
                app_logger.log_error(e, "emit_streaming_event")

    def cleanup(self) -> None:
        """清理资源"""
        self.stop_streaming()

        with self._streaming_lock:
            self._streaming_chunks.clear()

        app_logger.log_audio_event("StreamingCoordinator cleaned up", {})