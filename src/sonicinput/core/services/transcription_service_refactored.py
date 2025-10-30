"""重构后的转录服务 - 协调器模式

将原来的单一大类拆分为多个专职类的协调器。
职责单一，专注于组件协调而非具体实现。
"""

import time
import threading
from typing import Optional, Dict, Any, Callable, List
import numpy as np

from .transcription_core import TranscriptionCore
from .model_manager import ModelManager, ModelState
from .streaming_coordinator import StreamingCoordinator
from .task_queue_manager import TaskQueueManager, Task, TaskPriority, TaskStatus
from .error_recovery_service import ErrorRecoveryService

from ...utils import app_logger, WhisperLoadError
from ...core.interfaces.speech import ISpeechService


class RefactoredTranscriptionService(ISpeechService):
    """重构后的转录服务

    采用协调器模式，将原来的复杂功能拆分为多个专职组件：
    - TranscriptionCore: 纯转录功能
    - ModelManager: 模型生命周期管理
    - StreamingCoordinator: 流式转录协调
    - TaskQueueManager: 任务队列管理
    - ErrorRecoveryService: 错误恢复服务

    这个类主要负责组件间的协调和对外提供统一的API接口。
    """

    def __init__(self, whisper_engine_factory, event_service=None):
        """初始化重构后的转录服务

        Args:
            whisper_engine_factory: Whisper引擎工厂函数
            event_service: 事件服务（可选）
        """
        self.event_service = event_service

        # 创建专职组件
        self.model_manager = ModelManager(whisper_engine_factory, event_service)
        self.transcription_core = None  # 将在model加载后创建
        self.streaming_coordinator = StreamingCoordinator(event_service)
        self.task_queue_manager = TaskQueueManager(worker_count=1, event_service=event_service)
        self.error_recovery_service = ErrorRecoveryService(event_service)

        # 状态管理
        self._service_lock = threading.RLock()
        self._is_started = False

        # 注册任务处理器
        self._register_task_handlers()

        app_logger.audio("RefactoredTranscriptionService initialized", {})

    def start(self) -> None:
        """启动转录服务"""
        with self._service_lock:
            if self._is_started:
                return

            try:
                # 启动各个组件
                self.model_manager.start()
                self.task_queue_manager.start()

                # 加载模型（如果未加载）
                if not self.model_manager.is_model_loaded():
                    app_logger.audio("Loading model on service startup", {})
                    self.model_manager.load_model()

                # 创建转录核心（需要模型管理器启动并加载模型）
                whisper_engine = self.model_manager.get_whisper_engine()
                if whisper_engine:
                    try:
                        self.transcription_core = TranscriptionCore(whisper_engine)
                        app_logger.audio("Transcription core created successfully", {})
                    except Exception as e:
                        app_logger.error("Transcription core creation failed", e, context={"error_type": "transcription_core_creation_failed"})
                        self.transcription_core = None

                # 验证转录核心是否可用
                if not self.transcription_core:
                    app_logger.warning("Transcription core not available after startup",
                        context={"whisper_engine_available": whisper_engine is not None,
                               "model_loaded": self.model_manager.is_model_loaded()})

                self._is_started = True

                app_logger.audio("RefactoredTranscriptionService started",
                    {"transcription_core_available": self.transcription_core is not None})

                # 发送服务启动事件
                if self.event_service:
                    self.event_service.emit("transcription_service_started", {
                        "transcription_core_available": self.transcription_core is not None
                    })

            except Exception as e:
                app_logger.error("Transcription service start failed", e, context={"error_type": "transcription_service_start_failed"})
                self.stop()
                raise

    def stop(self) -> None:
        """停止转录服务"""
        with self._service_lock:
            if not self._is_started:
                return

            try:
                # 停止流式转录
                self.streaming_coordinator.cleanup()

                # 停止任务队列
                self.task_queue_manager.stop()

                # 停止模型管理器
                self.model_manager.stop()

                # 清理转录核心
                self.transcription_core = None

                self._is_started = False

                app_logger.audio("RefactoredTranscriptionService stopped", {})

                # 发送服务停止事件
                if self.event_service:
                    self.event_service.emit("transcription_service_stopped", {})

            except Exception as e:
                app_logger.error("Transcription service stop failed", e, context={"error_type": "transcription_service_stop_failed"})

    def transcribe(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """转录音频（同步）- ISpeechService 接口实现

        Args:
            audio_data: 音频数据
            language: 指定语言（可选）
            temperature: 温度参数

        Returns:
            转录结果字典
        """
        return self.transcribe_sync(audio_data, language, temperature)

    def transcribe_async(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0,
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None
    ) -> str:
        """转录音频（异步）- 保持向后兼容

        Args:
            audio_data: 音频数据
            language: 指定语言（可选）
            temperature: 温度参数
            callback: 成功回调函数
            error_callback: 错误回调函数

        Returns:
            任务ID
        """
        if not self._is_started:
            raise RuntimeError("Transcription service is not started")

        # 准备任务数据
        task_data = {
            "audio_data": audio_data,
            "language": language,
            "temperature": temperature
        }

        # 提交任务
        task_id = self.task_queue_manager.submit_task(
            task_type="transcribe",
            data=task_data,
            priority=TaskPriority.NORMAL,
            callback=callback,
            error_callback=error_callback,
            timeout=120.0,  # 2分钟超时
            max_retries=2
        )

        return task_id

    def transcribe_sync(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0
    ) -> Dict[str, Any]:
        """转录音频（同步）

        Args:
            audio_data: 音频数据
            language: 指定语言（可选）
            temperature: 温度参数

        Returns:
            转录结果
        """
        if not self._is_started:
            raise RuntimeError("Transcription service is not started")

        if not self.transcription_core:
            raise WhisperLoadError("Transcription core not available")

        try:
            # 使用转录核心进行同步转录
            result = self.transcription_core.transcribe_audio(
                audio_data, language, temperature
            )

            # 发送转录完成事件
            if self.event_service:
                self.event_service.emit("transcription_completed", {
                    "result": result
                })

            return result

        except Exception as e:
            # 使用错误恢复服务处理错误
            error_result = self.error_recovery_service.handle_error(e, {
                "operation": "transcribe_sync",
                "audio_length": len(audio_data),
                "language": language,
                "temperature": temperature
            })

            # 转换为标准错误格式
            return {
                "success": False,
                "text": "",
                "error": str(e),
                "error_result": error_result
            }

    def start_streaming(self) -> None:
        """开始流式转录模式"""
        if not self._is_started:
            raise RuntimeError("Transcription service is not started")

        self.streaming_coordinator.start_streaming()

        app_logger.audio("Streaming transcription started", {})

    def stop_streaming(self) -> Dict[str, Any]:
        """停止流式转录模式并处理所有待处理的块

        Returns:
            流式转录统计信息
        """
        # 获取所有待处理的块
        pending_chunks = self.streaming_coordinator.get_pending_chunks()

        app_logger.audio("Processing pending chunks before stopping", {
            "pending_count": len(pending_chunks)
        })

        # 为每个待处理的块提交转录任务,并保存块的引用
        pending_chunk_refs = []
        for chunk in pending_chunks:
            task_data = {
                "chunk_id": chunk.chunk_id,
                "audio_data": chunk.audio_data
            }

            # 提交到任务队列进行转录
            self.task_queue_manager.submit_task(
                task_type="process_streaming_chunk",
                data=task_data,
                priority=TaskPriority.HIGH
            )

            # 保存块的完整引用(包括result_event和result_container)
            pending_chunk_refs.append(chunk)

            app_logger.audio("Submitted pending chunk for transcription", {
                "chunk_id": chunk.chunk_id,
                "audio_length": len(chunk.audio_data)
            })

        # 等待所有块完成转录(最多等待30秒)
        timeout = 30.0
        start_time = time.time()

        for chunk in pending_chunk_refs:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time <= 0:
                app_logger.audio("Timeout waiting for chunk completion", {
                    "chunk_id": chunk.chunk_id
                })
                break

            if not chunk.result_event.wait(timeout=remaining_time):
                app_logger.audio("Chunk processing timeout", {
                    "chunk_id": chunk.chunk_id,
                    "timeout": remaining_time
                })

        # 从保存的块引用中提取转录文本
        text_parts = []
        completed_count = 0

        for chunk in pending_chunk_refs:
            result = chunk.result_container
            if result.get("success"):
                completed_count += 1
                # 转录结果直接存储在顶层的 "text" 字段中
                text = result.get("text", "")
                if text:
                    text_parts.append(text)

        transcribed_text = " ".join(text_parts).strip()

        app_logger.audio("Extracted transcription text from chunks", {
            "total_chunks": len(pending_chunk_refs),
            "completed_chunks": completed_count,
            "text_length": len(transcribed_text)
        })

        # 停止流式模式
        stats = self.streaming_coordinator.stop_streaming()

        app_logger.audio("Streaming transcription stopped", stats)

        # 返回包含文本和统计信息的结果
        return {
            "text": transcribed_text,
            "stats": stats
        }

    def add_streaming_chunk(self, audio_data: np.ndarray) -> int:
        """添加流式转录块

        Args:
            audio_data: 音频数据

        Returns:
            块ID
        """
        if not self._is_started:
            raise RuntimeError("Transcription service is not started")

        return self.streaming_coordinator.add_streaming_chunk(audio_data)

    def load_model(
        self,
        model_name: Optional[str] = None,
        timeout: int = 300,
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None
    ) -> str:
        """加载模型（异步）

        Args:
            model_name: 模型名称（可选）
            timeout: 超时时间
            callback: 成功回调
            error_callback: 错误回调

        Returns:
            任务ID
        """
        # 提交模型加载任务
        task_id = self.task_queue_manager.submit_task(
            task_type="load_model",
            data={
                "model_name": model_name,
                "timeout": timeout
            },
            priority=TaskPriority.HIGH,
            callback=callback,
            error_callback=error_callback,
            timeout=float(timeout + 60),  # 额外60秒缓冲
            max_retries=1
        )

        return task_id

    def load_model_async(
        self,
        model_name: Optional[str] = None,
        callback: Optional[Callable[[bool, str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """加载模型（异步，兼容旧API）

        Args:
            model_name: 模型名称（可选）
            callback: 成功回调，签名：callback(success: bool, error: str)
            error_callback: 错误回调，签名：error_callback(error_msg: str)
        """
        def adapted_callback(task_result: Dict[str, Any]) -> None:
            """适配任务队列结果到旧API回调格式"""
            success = task_result.get("success", False)
            error = task_result.get("error", "")

            if callback:
                callback(success, error)

        def adapted_error_callback(error_msg: str) -> None:
            """适配错误回调到旧API格式"""
            if error_callback:
                error_callback(error_msg)

        # 直接使用model_manager加载模型
        success = self.model_manager.load_model(model_name)

        # 立即调用回调（同步模拟异步）
        if adapted_callback:
            adapted_callback({"success": success, "error": "" if success else "Failed to load model"})

    def load_model_sync(self, model_name: Optional[str] = None, timeout: int = 300) -> bool:
        """加载模型（同步）

        Args:
            model_name: 模型名称（可选）
            timeout: 超时时间

        Returns:
            True如果加载成功
        """
        if not self._is_started:
            raise RuntimeError("Transcription service is not started")

        success = self.model_manager.load_model(model_name, timeout)

        if success:
            # 更新转录核心
            whisper_engine = self.model_manager.get_whisper_engine()
            if whisper_engine:
                self.transcription_core = TranscriptionCore(whisper_engine)

        return success

    def unload_model(self) -> None:
        """卸载模型"""
        if not self._is_started:
            raise RuntimeError("Transcription service is not started")

        self.model_manager.unload_model()
        self.transcription_core = None

        app_logger.audio("Model unloaded", {})

    def reload_model(
        self,
        model_name: Optional[str] = None,
        use_gpu: Optional[bool] = None,
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None
    ) -> str:
        """重新加载模型（异步）

        Args:
            model_name: 新模型名称（可选）
            use_gpu: 是否使用GPU（可选）
            callback: 成功回调
            error_callback: 错误回调

        Returns:
            任务ID
        """
        # 提交模型重载任务
        task_id = self.task_queue_manager.submit_task(
            task_type="reload_model",
            data={
                "model_name": model_name,
                "use_gpu": use_gpu
            },
            priority=TaskPriority.HIGH,
            callback=callback,
            error_callback=error_callback,
            timeout=600.0,  # 10分钟超时
            max_retries=1
        )

        return task_id

    def reload_model_sync(
        self,
        model_name: Optional[str] = None,
        use_gpu: Optional[bool] = None
    ) -> bool:
        """重新加载模型（同步）

        Args:
            model_name: 新模型名称（可选）
            use_gpu: 是否使用GPU（可选）

        Returns:
            True如果重载成功
        """
        if not self._is_started:
            raise RuntimeError("Transcription service is not started")

        success = self.model_manager.reload_model(model_name, use_gpu)

        if success:
            # 更新转录核心
            whisper_engine = self.model_manager.get_whisper_engine()
            if whisper_engine:
                self.transcription_core = TranscriptionCore(whisper_engine)

        return success

    def is_model_loaded(self) -> bool:
        """检查模型是否已加载

        Returns:
            True如果模型已加载
        """
        return self.model_manager.is_model_loaded()

    def is_ready(self) -> bool:
        """检查服务是否就绪

        Returns:
            True如果服务已启动且模型已加载
        """
        return (self._is_started and
                self.model_manager.is_model_loaded() and
                self.transcription_core is not None)

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态

        Returns:
            服务状态信息
        """
        status = {
            "service_started": self._is_started,
            "model_status": self.model_manager.get_model_info(),
            "streaming_status": self.streaming_coordinator.get_stats(),
            "task_queue_status": self.task_queue_manager.get_stats(),
            "error_recovery_status": self.error_recovery_service.get_error_stats()
        }

        return status

    def get_available_models(self) -> list:
        """获取可用模型列表

        Returns:
            模型名称列表
        """
        return self.model_manager.get_available_models()

    def _register_task_handlers(self) -> None:
        """注册任务处理器"""
        self.task_queue_manager.register_task_handler(
            "transcribe",
            self._handle_transcribe_task
        )

        self.task_queue_manager.register_task_handler(
            "load_model",
            self._handle_load_model_task
        )

        self.task_queue_manager.register_task_handler(
            "reload_model",
            self._handle_reload_model_task
        )

        # 流式转录处理器
        self.task_queue_manager.register_task_handler(
            "process_streaming_chunk",
            self._handle_streaming_chunk_task
        )

    def ensure_transcription_core(self) -> bool:
        """确保转录核心可用

        Returns:
            True如果转录核心可用
        """
        if not self.transcription_core:
            try:
                whisper_engine = self.model_manager.get_whisper_engine()
                if whisper_engine:
                    self.transcription_core = TranscriptionCore(whisper_engine)
                    app_logger.audio("Transcription core recreated successfully", {})
                    return True
            except Exception as e:
                app_logger.error("Transcription core recreation failed", e, context={"error_type": "transcription_core_recreation_failed"})
                return False

        return self.transcription_core is not None

    def _handle_transcribe_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理转录任务

        Args:
            task_data: 任务数据

        Returns:
            转录结果
        """
        audio_data = task_data["audio_data"]
        language = task_data.get("language")
        temperature = task_data.get("temperature", 0.0)

        # 尝试确保转录核心可用
        if not self.ensure_transcription_core():
            # 提供详细的错误信息帮助诊断
            error_info = {
                "service_started": self._is_started,
                "model_loaded": self.model_manager.is_model_loaded() if self.model_manager else False,
                "whisper_engine_available": self.model_manager.get_whisper_engine() is not None if self.model_manager else False
            }
            app_logger.error("Transcription core not available", Exception("Transcription core not available"), context=error_info, category="transcribe_task_failed")
            raise WhisperLoadError("Transcription core not available")

        try:
            return self.transcription_core.transcribe_audio(
                audio_data, language, temperature
            )
        except Exception as e:
            app_logger.error("Transcription core transcription failed", e, context={
                "audio_length": len(audio_data),
                "language": language,
                "temperature": temperature
            })
            raise

    def _handle_load_model_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理模型加载任务

        Args:
            task_data: 任务数据

        Returns:
            加载结果
        """
        model_name = task_data.get("model_name")
        timeout = task_data.get("timeout", 300)

        success = self.model_manager.load_model(model_name, timeout)

        if success:
            # 更新转录核心
            whisper_engine = self.model_manager.get_whisper_engine()
            if whisper_engine:
                self.transcription_core = TranscriptionCore(whisper_engine)

        return {
            "success": success,
            "model_name": model_name,
            "model_info": self.model_manager.get_model_info()
        }

    def _handle_reload_model_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理模型重载任务

        Args:
            task_data: 任务数据

        Returns:
            重载结果
        """
        model_name = task_data.get("model_name")
        use_gpu = task_data.get("use_gpu")

        success = self.model_manager.reload_model(model_name, use_gpu)

        if success:
            # 更新转录核心
            whisper_engine = self.model_manager.get_whisper_engine()
            if whisper_engine:
                self.transcription_core = TranscriptionCore(whisper_engine)

        return {
            "success": success,
            "model_name": model_name,
            "use_gpu": use_gpu,
            "model_info": self.model_manager.get_model_info()
        }

    def _handle_streaming_chunk_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理流式转录块任务

        Args:
            task_data: 任务数据

        Returns:
            处理结果
        """
        chunk_id = task_data["chunk_id"]
        audio_data = task_data["audio_data"]

        if not self.transcription_core:
            # 提供详细的错误信息帮助诊断
            error_info = {
                "service_started": self._is_started,
                "model_loaded": self.model_manager.is_model_loaded() if self.model_manager else False,
                "whisper_engine_available": self.model_manager.get_whisper_engine() is not None if self.model_manager else False,
                "chunk_id": chunk_id
            }
            app_logger.error("Transcription core not available for streaming chunk", Exception("Transcription core not available for streaming chunk"), context=error_info, category="streaming_chunk_failed")

            error_result = {
                "success": False,
                "error": "Transcription core not available"
            }
            self.streaming_coordinator.complete_chunk(chunk_id, error_result)
            return error_result

        try:
            # 转录音频块
            result = self.transcription_core.transcribe_audio(audio_data)

            # 完成流式块
            self.streaming_coordinator.complete_chunk(chunk_id, result)

            return result

        except Exception as e:
            # 标记块为失败
            error_result = {
                "success": False,
                "error": str(e)
            }
            self.streaming_coordinator.complete_chunk(chunk_id, error_result)

            app_logger.error("Streaming chunk transcription failed", e, context={
                "chunk_id": chunk_id,
                "audio_length": len(audio_data)
            })

            raise

    def start_streaming_processing(self) -> None:
        """开始处理流式转录块"""
        # 提交一个持续处理流式块的任务
        self.task_queue_manager.submit_task(
            task_type="streaming_processor",
            data={},
            priority=TaskPriority.LOW,
            max_retries=0
        )

    def cleanup(self) -> None:
        """清理资源"""
        self.stop()

        # 清理各个组件
        self.streaming_coordinator.cleanup()
        self.error_recovery_service.cleanup()

        app_logger.audio("RefactoredTranscriptionService cleaned up", {})

    # ISpeechService interface implementation
    def load_model(self, model_name: Optional[str] = None) -> bool:
        """加载语音识别模型 - ISpeechService 接口实现"""
        return self.model_manager.load_model(model_name)

    def unload_model(self) -> None:
        """卸载当前模型 - ISpeechService 接口实现"""
        self.model_manager.unload_model()

    def get_available_models(self) -> List[str]:
        """获取可用的模型列表 - ISpeechService 接口实现"""
        return self.model_manager.get_available_models()

    def is_model_loaded(self) -> bool:
        """模型是否已加载 - ISpeechService 接口实现（使用方法而非属性以避免装饰器冲突）"""
        return self.model_manager.is_model_loaded

    # Backward compatibility properties - 这些属性用于UI显示
    @property
    def model_name(self) -> str:
        """获取当前模型名称 - 向后兼容性"""
        if self.model_manager and hasattr(self.model_manager, '_current_model_name'):
            return self.model_manager._current_model_name or "Unknown"
        return "Unknown"

    @property
    def device(self) -> str:
        """获取当前设备 - 向后兼容性"""
        if self.model_manager:
            whisper_engine = self.model_manager.get_whisper_engine()
            if whisper_engine and hasattr(whisper_engine, 'device'):
                return getattr(whisper_engine, 'device', 'Unknown')
        return "Unknown"

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息 - 向后兼容性"""
        if self.model_manager:
            return self.model_manager.get_model_info()
        return {
            "model_name": self.model_name,
            "device": self.device,
            "is_loaded": False,
            "use_gpu": False
        }