"""重构后的转录服务 - 协调器模式

将原来的单一大类拆分为多个专职类的协调器。
职责单一，专注于组件协调而非具体实现。
"""

import time
import threading
from typing import Optional, Dict, Any, Callable, List, Tuple
import numpy as np

from .transcription_core import TranscriptionCore
from .model_manager import ModelManager
from .streaming_coordinator import StreamingCoordinator
from .task_queue_manager import TaskQueueManager, TaskPriority
from .error_recovery_service import ErrorRecoveryService

from ...utils import app_logger, WhisperLoadError
from ...core.interfaces.speech import ISpeechService
from ...core.base.lifecycle_component import LifecycleComponent
from ..interfaces.config_reload import (
    IConfigReloadable,
    ConfigDiff,
    ReloadResult,
    ReloadStrategy,
)
from .config import ConfigKeys


class RefactoredTranscriptionService(
    LifecycleComponent, ISpeechService, IConfigReloadable
):
    """重构后的转录服务（支持配置热重载）

    采用协调器模式，将原来的复杂功能拆分为多个专职组件：
    - TranscriptionCore: 纯转录功能
    - ModelManager: 模型生命周期管理
    - StreamingCoordinator: 流式转录协调
    - TaskQueueManager: 任务队列管理
    - ErrorRecoveryService: 错误恢复服务

    这个类主要负责组件间的协调和对外提供统一的API接口。
    """

    def __init__(self, whisper_engine_factory, event_service=None, config_service=None):
        """初始化重构后的转录服务

        Args:
            whisper_engine_factory: Whisper引擎工厂函数
            event_service: 事件服务（可选）
            config_service: 配置服务（可选）
        """
        super().__init__("TranscriptionService")
        self.event_service = event_service
        self.config_service = config_service

        app_logger.audio(
            "TranscriptionService __init__ called",
            {
                "has_config_service": config_service is not None,
                "config_service_type": type(config_service).__name__
                if config_service
                else "None",
            },
        )

        # 从配置读取流式模式
        streaming_mode = "chunked"  # 默认值
        if config_service:
            streaming_mode = config_service.get_setting(
                ConfigKeys.TRANSCRIPTION_LOCAL_STREAMING_MODE, "chunked"
            )
            app_logger.audio(
                "Reading streaming_mode from config",
                {
                    "streaming_mode": streaming_mode,
                    "config_key": ConfigKeys.TRANSCRIPTION_LOCAL_STREAMING_MODE,
                },
            )
        else:
            app_logger.audio(
                "No config_service provided, using default streaming_mode",
                {"streaming_mode": streaming_mode},
            )

        # 创建专职组件
        self.model_manager = ModelManager(whisper_engine_factory, event_service)
        self.transcription_core = None  # 将在model加载后创建
        self.streaming_coordinator = StreamingCoordinator(event_service, streaming_mode)
        self.task_queue_manager = TaskQueueManager(
            worker_count=1, event_service=event_service
        )
        self.error_recovery_service = ErrorRecoveryService(event_service)

        # 状态管理（LifecycleComponent 提供 _state，不需要 _is_started）
        self._service_lock = threading.RLock()

        # 注册任务处理器
        self._register_task_handlers()

        app_logger.audio(
            "RefactoredTranscriptionService initialized",
            {"streaming_mode": streaming_mode},
        )

    def _do_start(self) -> bool:
        """启动转录服务 - LifecycleComponent 实现

        Returns:
            True if start successful
        """
        with self._service_lock:
            try:
                # 启动各个组件
                self.model_manager.start()
                self.task_queue_manager.start()

                # 不再自动加载模型，由ApplicationOrchestrator根据配置决定是否加载
                # 这避免了冗余的模型加载

                # 创建转录核心（需要模型管理器启动并加载模型）
                whisper_engine = self.model_manager.get_whisper_engine()
                if whisper_engine:
                    try:
                        self.transcription_core = TranscriptionCore(whisper_engine)
                        app_logger.audio("Transcription core created successfully", {})
                    except Exception as e:
                        app_logger.error(
                            "Transcription core creation failed",
                            e,
                            context={
                                "error_type": "transcription_core_creation_failed"
                            },
                        )
                        self.transcription_core = None

                # 验证转录核心是否可用
                if not self.transcription_core:
                    app_logger.warning(
                        "Transcription core not available after startup",
                        context={
                            "whisper_engine_available": whisper_engine is not None,
                            "model_loaded": self.model_manager.is_model_loaded(),
                        },
                    )

                app_logger.audio(
                    "RefactoredTranscriptionService started",
                    {
                        "transcription_core_available": self.transcription_core
                        is not None
                    },
                )

                # 发送服务启动事件
                if self.event_service:
                    self.event_service.emit(
                        "transcription_service_started",
                        {
                            "transcription_core_available": self.transcription_core
                            is not None
                        },
                    )

                return True

            except Exception as e:
                app_logger.error(
                    "Transcription service start failed",
                    e,
                    context={"error_type": "transcription_service_start_failed"},
                )
                # LifecycleComponent will handle setting state to ERROR
                return False

    def _do_stop(self) -> bool:
        """停止转录服务 - LifecycleComponent 实现

        Returns:
            True if stop successful
        """
        with self._service_lock:
            try:
                # 停止流式转录
                self.streaming_coordinator.cleanup()

                # 停止任务队列
                self.task_queue_manager.stop()

                # 停止模型管理器
                self.model_manager.stop()

                # 清理转录核心
                self.transcription_core = None

                # 清理错误恢复服务（合并 cleanup() 逻辑）
                self.error_recovery_service.cleanup()

                app_logger.audio("RefactoredTranscriptionService stopped", {})

                # 发送服务停止事件
                if self.event_service:
                    self.event_service.emit("transcription_service_stopped", {})

                return True

            except Exception as e:
                app_logger.error(
                    "Transcription service stop failed",
                    e,
                    context={"error_type": "transcription_service_stop_failed"},
                )
                return False

    def transcribe(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0,
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
        error_callback: Optional[Callable] = None,
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
        if not self.is_running:
            raise RuntimeError("Transcription service is not started")

        # 准备任务数据
        task_data = {
            "audio_data": audio_data,
            "language": language,
            "temperature": temperature,
        }

        # 提交任务
        task_id = self.task_queue_manager.submit_task(
            task_type="transcribe",
            data=task_data,
            priority=TaskPriority.NORMAL,
            callback=callback,
            error_callback=error_callback,
            timeout=120.0,  # 2分钟超时
            max_retries=2,
        )

        return task_id

    def transcribe_sync(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0,
        emit_event: bool = False,
    ) -> Dict[str, Any]:
        """转录音频（同步）

        Args:
            audio_data: 音频数据
            language: 指定语言（可选）
            temperature: 温度参数
            emit_event: 是否发送transcription_completed事件（默认False，避免触发AI处理流程）

        Returns:
            转录结果
        """
        if not self.is_running:
            raise RuntimeError("Transcription service is not started")

        if not self.transcription_core:
            raise WhisperLoadError("Transcription core not available")

        try:
            # 使用转录核心进行同步转录
            result = self.transcription_core.transcribe_audio(
                audio_data, language, temperature
            )

            # 仅在明确要求时发送转录完成事件
            # 注意：retry等手动转录不应触发事件，避免与正常录音流程冲突
            if emit_event and self.event_service:
                self.event_service.emit(
                    "transcription_completed",
                    {
                        "result": result,
                        "text": result.get("text", ""),
                        "streaming_mode": "chunked",
                    },
                )

            return result

        except Exception as e:
            # 使用错误恢复服务处理错误
            error_result = self.error_recovery_service.handle_error(
                e,
                {
                    "operation": "transcribe_sync",
                    "audio_length": len(audio_data),
                    "language": language,
                    "temperature": temperature,
                },
            )

            # 转换为标准错误格式
            return {
                "success": False,
                "text": "",
                "error": str(e),
                "error_result": error_result,
            }

    def start_streaming(self) -> None:
        """开始流式转录模式"""
        if not self.is_running:
            raise RuntimeError("Transcription service is not started")

        self.streaming_coordinator.start_streaming()

        app_logger.audio("Streaming transcription started", {})

    def stop_streaming(self) -> Dict[str, Any]:
        """停止流式转录模式并处理所有待处理的块

        Returns:
            流式转录统计信息（包含text和stats字段）
        """
        streaming_mode = self.streaming_coordinator.get_streaming_mode()

        if streaming_mode == "realtime":
            # Realtime 模式：直接获取最终文本
            final_text = self.streaming_coordinator.get_realtime_text()

            app_logger.audio(
                "Getting realtime transcription text", {"text_length": len(final_text)}
            )

            # 停止流式模式
            stats = self.streaming_coordinator.stop_streaming()

            app_logger.audio("Realtime streaming stopped", stats)

            return {"text": final_text, "stats": stats}

        else:
            # Chunked 模式：处理待处理的块
            # 获取所有待处理的块
            pending_chunks = self.streaming_coordinator.get_pending_chunks()

            app_logger.audio(
                "Processing pending chunks before stopping",
                {"pending_count": len(pending_chunks)},
            )

            # 为每个待处理的块提交转录任务,并保存块的引用
            pending_chunk_refs = []
            for chunk in pending_chunks:
                task_data = {"chunk_id": chunk.chunk_id, "audio_data": chunk.audio_data}

                # 提交到任务队列进行转录
                self.task_queue_manager.submit_task(
                    task_type="process_streaming_chunk",
                    data=task_data,
                    priority=TaskPriority.HIGH,
                )

                # 保存块的完整引用(包括result_event和result_container)
                pending_chunk_refs.append(chunk)

                app_logger.audio(
                    "Submitted pending chunk for transcription",
                    {"chunk_id": chunk.chunk_id, "audio_length": len(chunk.audio_data)},
                )

            # 等待所有块完成转录(最多等待30秒)
            timeout = 30.0
            start_time = time.time()

            for chunk in pending_chunk_refs:
                remaining_time = timeout - (time.time() - start_time)
                if remaining_time <= 0:
                    app_logger.audio(
                        "Timeout waiting for chunk completion",
                        {"chunk_id": chunk.chunk_id},
                    )
                    break

                if not chunk.result_event.wait(timeout=remaining_time):
                    app_logger.audio(
                        "Chunk processing timeout",
                        {"chunk_id": chunk.chunk_id, "timeout": remaining_time},
                    )

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

            app_logger.audio(
                "Extracted transcription text from chunks",
                {
                    "total_chunks": len(pending_chunk_refs),
                    "completed_chunks": completed_count,
                    "text_length": len(transcribed_text),
                },
            )

            # 停止流式模式
            stats = self.streaming_coordinator.stop_streaming()

            app_logger.audio("Streaming transcription stopped", stats)

            # 返回包含文本和统计信息的结果
            return {"text": transcribed_text, "stats": stats}

    def add_streaming_chunk(self, audio_data: np.ndarray) -> int:
        """添加流式转录块

        Args:
            audio_data: 音频数据

        Returns:
            块ID
        """
        if not self.is_running:
            raise RuntimeError("Transcription service is not started")

        return self.streaming_coordinator.add_streaming_chunk(audio_data)

    def load_model_async(
        self,
        model_name: Optional[str] = None,
        timeout: int = 300,
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
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
            data={"model_name": model_name, "timeout": timeout},
            priority=TaskPriority.HIGH,
            callback=callback,
            error_callback=error_callback,
            timeout=float(timeout + 60),  # 额外60秒缓冲
            max_retries=1,
        )

        return task_id

    def unload_model_async(self) -> None:
        """卸载模型（异步）"""
        if not self.is_running:
            raise RuntimeError("Transcription service is not started")

        self.model_manager.unload_model()
        self.transcription_core = None

        app_logger.audio("Model unloaded", {})

    def reload_model(
        self,
        model_name: Optional[str] = None,
        use_gpu: Optional[bool] = None,
        callback: Optional[Callable] = None,
        error_callback: Optional[Callable] = None,
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
            data={"model_name": model_name, "use_gpu": use_gpu},
            priority=TaskPriority.HIGH,
            callback=callback,
            error_callback=error_callback,
            timeout=600.0,  # 10分钟超时
            max_retries=1,
        )

        return task_id

    def reload_model_sync(
        self, model_name: Optional[str] = None, use_gpu: Optional[bool] = None
    ) -> bool:
        """重新加载模型（同步）

        Args:
            model_name: 新模型名称（可选）
            use_gpu: 是否使用GPU（可选）

        Returns:
            True如果重载成功
        """
        if not self.is_running:
            raise RuntimeError("Transcription service is not started")

        success = self.model_manager.reload_model(model_name, use_gpu)

        if success:
            # 更新转录核心
            whisper_engine = self.model_manager.get_whisper_engine()
            if whisper_engine:
                self.transcription_core = TranscriptionCore(whisper_engine)

        return success

    def is_ready(self) -> bool:
        """检查服务是否就绪

        Returns:
            True如果服务已启动且模型已加载
        """
        return (
            self.is_running
            and self.model_manager.is_model_loaded()
            and self.transcription_core is not None
        )

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态

        Returns:
            服务状态信息
        """
        status = {
            "service_started": self.is_running,
            "model_status": self.model_manager.get_model_info(),
            "streaming_status": self.streaming_coordinator.get_stats(),
            "task_queue_status": self.task_queue_manager.get_stats(),
            "error_recovery_status": self.error_recovery_service.get_error_stats(),
        }

        return status

    def get_available_models_async(self) -> list:
        """获取可用模型列表（异步）

        Returns:
            模型名称列表
        """
        return self.model_manager.get_available_models()

    def _register_task_handlers(self) -> None:
        """注册任务处理器"""
        self.task_queue_manager.register_task_handler(
            "transcribe", self._handle_transcribe_task
        )

        self.task_queue_manager.register_task_handler(
            "load_model", self._handle_load_model_task
        )

        self.task_queue_manager.register_task_handler(
            "reload_model", self._handle_reload_model_task
        )

        # 流式转录处理器
        self.task_queue_manager.register_task_handler(
            "process_streaming_chunk", self._handle_streaming_chunk_task
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
                app_logger.error(
                    "Transcription core recreation failed",
                    e,
                    context={"error_type": "transcription_core_recreation_failed"},
                )
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
                "service_started": self.is_running,
                "model_loaded": self.model_manager.is_model_loaded()
                if self.model_manager
                else False,
                "whisper_engine_available": self.model_manager.get_whisper_engine()
                is not None
                if self.model_manager
                else False,
            }
            app_logger.error(
                "Transcription core not available",
                Exception("Transcription core not available"),
                context=error_info,
                category="transcribe_task_failed",
            )
            raise WhisperLoadError("Transcription core not available")

        try:
            return self.transcription_core.transcribe_audio(
                audio_data, language, temperature
            )
        except Exception as e:
            app_logger.error(
                "Transcription core transcription failed",
                e,
                context={
                    "audio_length": len(audio_data),
                    "language": language,
                    "temperature": temperature,
                },
            )
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
            "model_info": self.model_manager.get_model_info(),
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
            "model_info": self.model_manager.get_model_info(),
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
                "service_started": self.is_running,
                "model_loaded": self.model_manager.is_model_loaded()
                if self.model_manager
                else False,
                "whisper_engine_available": self.model_manager.get_whisper_engine()
                is not None
                if self.model_manager
                else False,
                "chunk_id": chunk_id,
            }
            app_logger.error(
                "Transcription core not available for streaming chunk",
                Exception("Transcription core not available for streaming chunk"),
                context=error_info,
                category="streaming_chunk_failed",
            )

            error_result = {
                "success": False,
                "error": "Transcription core not available",
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
            error_result = {"success": False, "error": str(e)}
            self.streaming_coordinator.complete_chunk(chunk_id, error_result)

            app_logger.error(
                "Streaming chunk transcription failed",
                e,
                context={"chunk_id": chunk_id, "audio_length": len(audio_data)},
            )

            raise

    def start_streaming_processing(self) -> None:
        """开始处理流式转录块"""
        # 提交一个持续处理流式块的任务
        self.task_queue_manager.submit_task(
            task_type="streaming_processor",
            data={},
            priority=TaskPriority.LOW,
            max_retries=0,
        )

    def reload_streaming_mode(self) -> None:
        """重新加载流式模式配置"""
        if not self.config_service:
            return

        new_mode = self.config_service.get_setting(
            ConfigKeys.TRANSCRIPTION_LOCAL_STREAMING_MODE, "chunked"
        )

        # 只有在非活动状态下才能更改
        if self.streaming_coordinator.set_streaming_mode(new_mode):
            app_logger.audio(
                "Streaming mode reloaded from config", {"new_mode": new_mode}
            )
        else:
            app_logger.audio(
                "Cannot reload streaming mode while active",
                {"current_mode": self.streaming_coordinator.get_streaming_mode()},
            )

    def cleanup(self) -> None:
        """清理资源 - 向后兼容方法，内部调用 stop()"""
        self.stop()

    # Backward compatibility properties - 这些属性用于UI显示
    @property
    def model_name(self) -> str:
        """获取当前模型名称 - 向后兼容性"""
        if self.model_manager and hasattr(self.model_manager, "_current_model_name"):
            return self.model_manager._current_model_name or "Unknown"
        return "Unknown"

    @property
    def device(self) -> str:
        """获取当前设备 - 向后兼容性"""
        if self.model_manager:
            whisper_engine = self.model_manager.get_whisper_engine()
            if whisper_engine and hasattr(whisper_engine, "device"):
                return getattr(whisper_engine, "device", "Unknown")
        return "Unknown"

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息 - 向后兼容性"""
        if self.model_manager:
            return self.model_manager.get_model_info()
        return {
            "model_name": self.model_name,
            "device": self.device,
            "is_loaded": False,
            "use_gpu": False,
        }

    # ISpeechService interface implementation (同步版本)
    # 这些方法符合 ISpeechService 接口要求，用于兼容性
    # 推荐使用带 _async 后缀的异步版本以获得更好的性能

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """加载模型（同步阻塞）- ISpeechService 接口实现

        注意：这是同步阻塞调用，推荐使用 load_model_async() 异步版本

        Args:
            model_name: 模型名称，None 表示使用当前配置的模型

        Returns:
            是否加载成功
        """
        if not self.is_running:
            raise RuntimeError("Transcription service is not started")

        return self.model_manager.load_model(model_name)

    def unload_model(self) -> None:
        """卸载模型（同步）- ISpeechService 接口实现"""
        if self.model_manager:
            self.model_manager.unload_model()
            self.transcription_core = None

    def get_available_models(self) -> List[str]:
        """获取可用模型列表 - ISpeechService 接口实现

        Returns:
            模型名称列表
        """
        if self.model_manager:
            return self.model_manager.get_available_models()
        return []

    @property
    def is_model_loaded(self) -> bool:
        """模型是否已加载 - ISpeechService 接口的属性实现

        Returns:
            True 如果模型已加载
        """
        if self.model_manager:
            return self.model_manager.is_model_loaded()
        return False

    # ==================== IConfigReloadable 接口实现 ====================

    def get_config_dependencies(self) -> List[str]:
        """声明此服务依赖的配置键

        Returns:
            配置键列表
        """
        return [
            "transcription.provider",
            "transcription.local.model",
            "transcription.local.language",
            "transcription.local.auto_load",
            "transcription.local.streaming_mode",
            "transcription.groq.api_key",
            "transcription.groq.model",
            "transcription.groq.base_url",
            "transcription.siliconflow.api_key",
            "transcription.siliconflow.model",
            "transcription.siliconflow.base_url",
            "transcription.qwen.api_key",
            "transcription.qwen.model",
            "transcription.qwen.base_url",
            "transcription.qwen.enable_itn",
        ]

    def get_service_dependencies(self) -> List[str]:
        """声明此服务依赖的其他服务

        Returns:
            服务名称列表
        """
        return ["config_service"]
        # 注意：虽然也使用 audio_service，但音频服务不需要先重载
        # 因为转录服务的配置变更不影响音频采集

    def get_reload_strategy(self, diff: ConfigDiff) -> ReloadStrategy:
        """根据配置变更决定重载策略

        Args:
            diff: 配置变更差异

        Returns:
            重载策略
        """
        # 检查是否切换提供商
        if "transcription.provider" in diff.changed_keys:
            return ReloadStrategy.RECREATE

        # 检查是否变更需要重新初始化的配置
        reinit_keys = {
            "transcription.local.model",
            "transcription.local.language",
            "transcription.groq.api_key",
            "transcription.groq.model",
            "transcription.siliconflow.api_key",
            "transcription.siliconflow.model",
            "transcription.qwen.api_key",
            "transcription.qwen.model",
        }
        if diff.changed_keys & reinit_keys:
            return ReloadStrategy.REINITIALIZE

        # 其他变更仅需参数更新
        return ReloadStrategy.PARAMETER_UPDATE

    def can_reload_now(self) -> Tuple[bool, str]:
        """检查当前是否可以执行重载

        Returns:
            (是否可以重载, 原因说明)
        """
        # 检查是否正在流式转录
        if self.streaming_coordinator and self.streaming_coordinator.get_stats().get(
            "is_streaming", False
        ):
            return False, "流式转录进行中，无法重载转录服务"

        # 检查任务队列是否有正在处理的任务
        if self.task_queue_manager:
            stats = self.task_queue_manager.get_stats()
            active_tasks = stats.get("active_tasks", 0)
            if active_tasks > 0:
                return False, "转录任务进行中，请稍后重试"

        return True, ""

    def prepare_reload(self, diff: ConfigDiff) -> ReloadResult:
        """准备重载：验证新配置，保存回滚数据

        Args:
            diff: 配置变更差异

        Returns:
            重载结果
        """
        try:
            # 获取新配置
            new_config = diff.new_config
            new_provider = new_config.get("transcription", {}).get("provider", "local")

            # 验证新配置的有效性
            if new_provider == "groq":
                api_key = (
                    new_config.get("transcription", {}).get("groq", {}).get("api_key")
                )
                if not api_key:
                    return ReloadResult(
                        success=False, message="Groq provider requires API key"
                    )

            elif new_provider == "siliconflow":
                api_key = (
                    new_config.get("transcription", {})
                    .get("siliconflow", {})
                    .get("api_key")
                )
                if not api_key:
                    return ReloadResult(
                        success=False, message="SiliconFlow provider requires API key"
                    )

            elif new_provider == "qwen":
                api_key = (
                    new_config.get("transcription", {}).get("qwen", {}).get("api_key")
                )
                if not api_key:
                    return ReloadResult(
                        success=False, message="Qwen provider requires API key"
                    )

            # 保存回滚数据
            rollback_data = {
                "whisper_engine": self.model_manager.get_whisper_engine()
                if self.model_manager
                else None,
                "transcription_core": self.transcription_core,
                "streaming_mode": self.streaming_coordinator.get_streaming_mode()
                if self.streaming_coordinator
                else "chunked",
                "model_info": self.model_manager.get_model_info()
                if self.model_manager
                else {},
            }

            app_logger.audio(
                "TranscriptionService prepare_reload success",
                {
                    "old_provider": rollback_data["model_info"].get(
                        "model_name", "unknown"
                    ),
                    "new_provider": new_provider,
                    "strategy": self.get_reload_strategy(diff).value,
                },
            )

            return ReloadResult(
                success=True,
                message="Preparation successful",
                rollback_data=rollback_data,
            )

        except Exception as e:
            app_logger.error(
                "TranscriptionService.prepare_reload failed",
                e,
                context={"error_type": "prepare_reload_failed"},
            )
            return ReloadResult(success=False, message=f"Preparation failed: {str(e)}")

    def commit_reload(self, diff: ConfigDiff) -> ReloadResult:
        """提交重载：应用配置变更

        Args:
            diff: 配置变更差异

        Returns:
            重载结果
        """
        try:
            strategy = self.get_reload_strategy(diff)

            if strategy == ReloadStrategy.PARAMETER_UPDATE:
                # 仅更新参数（如 streaming_mode）
                new_config = diff.new_config
                streaming_mode = (
                    new_config.get("transcription", {})
                    .get("local", {})
                    .get("streaming_mode", "chunked")
                )

                if (
                    self.streaming_coordinator
                    and streaming_mode
                    != self.streaming_coordinator.get_streaming_mode()
                ):
                    old_mode = self.streaming_coordinator.get_streaming_mode()
                    if self.streaming_coordinator.set_streaming_mode(streaming_mode):
                        app_logger.audio(
                            "Streaming mode updated",
                            {"old": old_mode, "new": streaming_mode},
                        )
                    else:
                        return ReloadResult(
                            success=False,
                            message="Cannot update streaming mode while active",
                        )

                return ReloadResult(success=True, message="Parameter updated")

            elif strategy == ReloadStrategy.REINITIALIZE:
                # 重新初始化（如更换模型、API key）
                app_logger.audio("Reinitializing transcription service", {})

                # 对于本地模型，需要重新加载
                new_config = diff.new_config
                provider = new_config.get("transcription", {}).get("provider", "local")

                if provider == "local":
                    # 获取新模型配置
                    model_name = (
                        new_config.get("transcription", {})
                        .get("local", {})
                        .get("model", "paraformer")
                    )

                    # 卸载旧模型
                    if self.model_manager:
                        try:
                            self.model_manager.unload_model()
                            app_logger.audio("Old model unloaded", {})
                        except Exception as e:
                            app_logger.error(
                                "Failed to unload old model",
                                e,
                                context={"error_type": "unload_model_failed"},
                            )

                    # 加载新模型
                    if self.model_manager:
                        try:
                            success = self.model_manager.load_model(model_name)
                            if not success:
                                return ReloadResult(
                                    success=False, message="Failed to load new model"
                                )

                            # 重新创建转录核心
                            whisper_engine = self.model_manager.get_whisper_engine()
                            if whisper_engine:
                                self.transcription_core = TranscriptionCore(
                                    whisper_engine
                                )
                                app_logger.audio(
                                    "Transcription core reinitialized",
                                    {"model": model_name},
                                )
                            else:
                                return ReloadResult(
                                    success=False,
                                    message="Failed to get whisper engine",
                                )

                        except Exception as e:
                            app_logger.error(
                                "Failed to load new model",
                                e,
                                context={"error_type": "load_model_failed"},
                            )
                            return ReloadResult(
                                success=False, message=f"Failed to load model: {str(e)}"
                            )

                app_logger.audio("Service reinitialized", {"provider": provider})
                return ReloadResult(success=True, message="Service reinitialized")

            elif strategy == ReloadStrategy.RECREATE:
                # RECREATE 策略由 Coordinator 处理，这里不应该被调用
                # 但为了完整性，也实现一下
                app_logger.audio(
                    "RECREATE strategy should be handled by Coordinator", {}
                )
                return ReloadResult(
                    success=True, message="RECREATE handled by Coordinator"
                )

            else:
                return ReloadResult(
                    success=False, message=f"Unknown strategy: {strategy}"
                )

        except Exception as e:
            app_logger.error(
                "TranscriptionService.commit_reload failed",
                e,
                context={"error_type": "commit_reload_failed"},
            )
            return ReloadResult(success=False, message=f"Commit failed: {str(e)}")

    def rollback_reload(self, rollback_data: Dict[str, Any]) -> bool:
        """回滚到之前的配置状态

        Args:
            rollback_data: prepare_reload 返回的回滚数据

        Returns:
            是否回滚成功
        """
        try:
            # 恢复转录核心
            if "transcription_core" in rollback_data:
                self.transcription_core = rollback_data["transcription_core"]

            # 恢复 whisper 引擎
            if "whisper_engine" in rollback_data and self.model_manager:
                # 注意：这里需要谨慎处理，因为 whisper_engine 可能已经被卸载
                # 实际上回滚可能需要重新加载旧模型
                old_model_info = rollback_data.get("model_info", {})
                old_model_name = old_model_info.get("model_name")

                if old_model_name:
                    try:
                        self.model_manager.load_model(old_model_name)
                        app_logger.audio(
                            "Rolled back to old model", {"model": old_model_name}
                        )
                    except Exception as e:
                        app_logger.error(
                            "Failed to rollback model",
                            e,
                            context={"error_type": "rollback_model_failed"},
                        )

            # 恢复流式模式
            if "streaming_mode" in rollback_data and self.streaming_coordinator:
                old_mode = rollback_data["streaming_mode"]
                self.streaming_coordinator.set_streaming_mode(old_mode)
                app_logger.audio(
                    "Rolled back streaming mode", {"streaming_mode": old_mode}
                )

            app_logger.audio("TranscriptionService rollback successful", {})
            return True

        except Exception as e:
            app_logger.error(
                "TranscriptionService.rollback_reload failed",
                e,
                context={"error_type": "rollback_reload_failed"},
            )
            return False
