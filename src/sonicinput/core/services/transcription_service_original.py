"""持久化转录服务 - 维护单个工作线程复用模型"""

import queue
import threading
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np

from ...utils import app_logger, WhisperLoadError


class TranscriptionTaskType(Enum):
    """转录任务类型"""
    TRANSCRIBE = "transcribe"
    LOAD_MODEL = "load_model"
    UNLOAD_MODEL = "unload_model"
    RELOAD_MODEL = "reload_model"  # 新增：重新加载模型
    SHUTDOWN = "shutdown"


@dataclass
class TranscriptionTask:
    """转录任务"""
    task_type: TranscriptionTaskType
    audio_data: Optional[np.ndarray] = None
    language: Optional[str] = None
    temperature: float = 0.0
    callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None
    model_name: Optional[str] = None

    # 任务标识
    task_id: Optional[str] = None


@dataclass
class TranscriptionResult:
    """转录结果"""
    success: bool
    text: str = ""
    language: Optional[str] = None
    confidence: float = 0.0
    segments: list = None
    transcription_time: float = 0.0
    error: Optional[str] = None
    recovery_suggestions: Optional[list] = None

    def __post_init__(self):
        if self.segments is None:
            self.segments = []
        if self.recovery_suggestions is None:
            self.recovery_suggestions = []


class TranscriptionService:
    """持久化转录服务

    维护一个持久的工作线程,加载模型一次后复用于所有转录请求。
    避免了每次转录都重新创建线程和加载模型的开销。
    """

    def __init__(self, whisper_engine, event_service=None):
        """初始化转录服务

        Args:
            whisper_engine: WhisperEngine 实例
            event_service: 事件服务（可选，用于广播模型加载事件）
        """
        self.whisper_engine = whisper_engine
        self._event_service = event_service

        # 任务队列（限制最大大小，防止内存泄漏）
        self._task_queue = queue.Queue(maxsize=50)

        # 工作线程
        self._worker_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._shutdown_event = threading.Event()

        # 状态跟踪
        self._is_model_loaded = False
        self._current_task_id = None
        self._lock = threading.Lock()

        # 流式转录状态 - 线程安全初始化
        self._streaming_mode = False
        self._streaming_lock = threading.Lock()
        with self._streaming_lock:
            self._streaming_chunks = []  # 存储 {chunk_id, result_event, result_container}
            self._streaming_chunk_id = 0

        app_logger.log_audio_event("TranscriptionService initialized", {
            "model_name": whisper_engine.model_name
        })

    def start(self) -> None:
        """启动转录服务"""
        if self._is_running:
            app_logger.log_audio_event("TranscriptionService already running", {})
            return

        self._is_running = True
        self._shutdown_event.clear()

        # 创建并启动持久工作线程
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            name="TranscriptionWorker",
            daemon=True
        )
        self._worker_thread.start()

        app_logger.log_audio_event("TranscriptionService started", {
            "thread_id": self._worker_thread.ident,
            "thread_name": self._worker_thread.name
        })

    def stop(self, timeout: float = 5.0) -> None:
        """停止转录服务

        Args:
            timeout: 等待线程结束的超时时间(秒)
        """
        if not self._is_running:
            return

        app_logger.log_audio_event("Stopping TranscriptionService", {})

        # 发送关闭任务
        shutdown_task = TranscriptionTask(
            task_type=TranscriptionTaskType.SHUTDOWN
        )
        self._task_queue.put(shutdown_task)

        # 设置关闭事件
        self._shutdown_event.set()

        # 等待线程结束
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=timeout)

            if self._worker_thread.is_alive():
                app_logger.log_audio_event("TranscriptionService worker thread did not stop in time", {
                    "timeout": timeout
                })

        self._is_running = False
        app_logger.log_audio_event("TranscriptionService stopped", {})

    def cleanup(self) -> None:
        """清理资源 - 停止工作线程"""
        self.stop()

    def load_model_async(self, model_name: Optional[str] = None,
                        callback: Optional[Callable] = None,
                        error_callback: Optional[Callable] = None) -> None:
        """异步加载模型

        Args:
            model_name: 模型名称,None表示使用默认模型
            callback: 加载成功回调
            error_callback: 加载失败回调
        """
        if not self._is_running:
            if error_callback:
                error_callback("TranscriptionService is not running")
            return

        task = TranscriptionTask(
            task_type=TranscriptionTaskType.LOAD_MODEL,
            model_name=model_name,
            callback=callback,
            error_callback=error_callback
        )

        self._task_queue.put(task)
        app_logger.log_audio_event("Model load task queued", {
            "model_name": model_name or self.whisper_engine.model_name
        })

    def transcribe_async(self, audio_data: np.ndarray,
                        language: Optional[str] = None,
                        temperature: float = 0.0,
                        callback: Optional[Callable] = None,
                        error_callback: Optional[Callable] = None) -> str:
        """异步转录音频

        Args:
            audio_data: 音频数据
            language: 语言代码
            temperature: 温度参数
            callback: 转录成功回调,接收TranscriptionResult
            error_callback: 转录失败回调,接收错误消息

        Returns:
            任务ID
        """
        if not self._is_running:
            if error_callback:
                error_callback("TranscriptionService is not running")
            return ""

        # 生成任务ID
        task_id = f"transcribe_{int(time.time() * 1000)}"

        task = TranscriptionTask(
            task_type=TranscriptionTaskType.TRANSCRIBE,
            audio_data=audio_data,
            language=language,
            temperature=temperature,
            callback=callback,
            error_callback=error_callback,
            task_id=task_id
        )

        self._task_queue.put(task)

        app_logger.log_audio_event("Transcription task queued", {
            "task_id": task_id,
            "audio_length": len(audio_data) / 16000,
            "queue_size": self._task_queue.qsize()
        })

        return task_id

    def unload_model_async(self, callback: Optional[Callable] = None) -> None:
        """异步卸载模型

        Args:
            callback: 卸载完成回调
        """
        if not self._is_running:
            return

        task = TranscriptionTask(
            task_type=TranscriptionTaskType.UNLOAD_MODEL,
            callback=callback
        )

        self._task_queue.put(task)
        app_logger.log_audio_event("Model unload task queued", {})

    def reload_model_async(self, use_gpu: Optional[bool] = None,
                          model_name: Optional[str] = None,
                          callback: Optional[Callable] = None,
                          error_callback: Optional[Callable] = None) -> None:
        """异步重新加载模型（用于切换 GPU/CPU 模式）

        Args:
            use_gpu: GPU 模式，None = 自动检测
            model_name: 模型名称，None = 使用当前模型
            callback: 重载成功回调
            error_callback: 重载失败回调
        """
        if not self._is_running:
            if error_callback:
                error_callback("TranscriptionService is not running")
            return

        task = TranscriptionTask(
            task_type=TranscriptionTaskType.RELOAD_MODEL,
            model_name=model_name,
            callback=callback,
            error_callback=error_callback
        )

        # 使用 task 的 temperature 字段临时存储 use_gpu（hack，但避免修改数据类）
        # 实际上我们应该扩展 TranscriptionTask，但为了最小化改动
        if use_gpu is not None:
            # 存储到 audio_data（作为标记）
            task.audio_data = np.array([1.0 if use_gpu else 0.0], dtype=np.float32)

        self._task_queue.put(task)
        app_logger.log_audio_event("Model reload task queued", {
            "use_gpu": use_gpu,
            "model_name": model_name or self.whisper_engine.model_name
        })

    # ===================================================================
    # 流式转录方法
    # ===================================================================

    def start_streaming_mode(self) -> None:
        """启动流式转录模式"""
        with self._streaming_lock:
            self._streaming_mode = True
            self._streaming_chunks = []
            self._streaming_chunk_id = 0

        app_logger.log_audio_event("Streaming transcription mode started", {})

    def transcribe_chunk_async(self, audio_data: np.ndarray) -> None:
        """提交音频块进行异步转录

        Args:
            audio_data: 音频数据块
        """
        if not self._streaming_mode:
            app_logger.log_audio_event("Warning: transcribe_chunk_async called outside streaming mode", {})
            return

        with self._streaming_lock:
            chunk_id = self._streaming_chunk_id
            self._streaming_chunk_id += 1

        # 创建结果容器
        result_event = threading.Event()
        result_container = {"chunk_id": chunk_id, "text": "", "success": False}

        # 定义回调
        def on_success(result: TranscriptionResult):
            result_container["text"] = result.text
            result_container["success"] = True
            result_event.set()

        def on_error(error_msg: str):
            result_container["success"] = False
            result_container["error"] = error_msg
            result_event.set()

        # 提交转录任务
        task_id = self.transcribe_async(
            audio_data,
            callback=on_success,
            error_callback=on_error
        )

        # 保存到流式块列表
        with self._streaming_lock:
            self._streaming_chunks.append({
                "chunk_id": chunk_id,
                "task_id": task_id,
                "result_event": result_event,
                "result_container": result_container
            })

        app_logger.log_audio_event("Streaming chunk submitted", {
            "chunk_id": chunk_id,
            "task_id": task_id,
            "audio_duration": len(audio_data) / 16000
        })

    def finalize_streaming_transcription(self, timeout: float = 30.0) -> str:
        """完成流式转录，等待所有块并拼接结果

        Args:
            timeout: 每个块的等待超时时间（秒）

        Returns:
            拼接后的完整文本
        """
        if not self._streaming_mode:
            app_logger.log_audio_event("Warning: finalize_streaming_transcription called outside streaming mode", {})
            return ""

        with self._streaming_lock:
            chunks_to_process = self._streaming_chunks.copy()

        app_logger.log_audio_event("Finalizing streaming transcription", {
            "total_chunks": len(chunks_to_process)
        })

        results = []
        failed_chunks = []
        timeout_chunks = []

        for chunk_info in chunks_to_process:
            chunk_id = chunk_info["chunk_id"]
            result_event = chunk_info["result_event"]
            result_container = chunk_info["result_container"]

            # 等待该块完成
            if result_event.wait(timeout=timeout):
                if result_container.get("success"):
                    results.append({
                        "chunk_id": chunk_id,
                        "text": result_container.get("text", "")
                    })
                    app_logger.log_audio_event("Chunk completed", {
                        "chunk_id": chunk_id,
                        "text_length": len(result_container.get("text", ""))
                    })
                else:
                    error_msg = result_container.get("error", "unknown")
                    failed_chunks.append((chunk_id, error_msg))
                    app_logger.log_audio_event("Chunk failed", {
                        "chunk_id": chunk_id,
                        "error": error_msg
                    })
                    # 添加占位符，避免静默跳过
                    results.append({
                        "chunk_id": chunk_id,
                        "text": f" [转录失败: chunk {chunk_id}] "
                    })
            else:
                timeout_chunks.append(chunk_id)
                app_logger.log_audio_event("Chunk timed out", {
                    "chunk_id": chunk_id,
                    "timeout": timeout
                })
                # 添加占位符
                results.append({
                    "chunk_id": chunk_id,
                    "text": f" [超时: chunk {chunk_id}] "
                })

        # 按 chunk_id 排序
        results.sort(key=lambda x: x["chunk_id"])

        # 拼接文本
        full_text = "".join([r["text"] for r in results])

        # 清理流式状态
        with self._streaming_lock:
            self._streaming_mode = False
            self._streaming_chunks = []
            self._streaming_chunk_id = 0

        app_logger.log_audio_event("Streaming transcription finalized", {
            "chunks_processed": len(results),
            "chunks_failed": len(failed_chunks),
            "chunks_timeout": len(timeout_chunks),
            "total_text_length": len(full_text)
        })

        # 如果有失败或超时块，在日志中记录警告
        if failed_chunks or timeout_chunks:
            app_logger.warning(f"Streaming transcription completed with issues: "
                             f"{len(failed_chunks)} failed, {len(timeout_chunks)} timed out")

        return full_text.strip()

    @property
    def is_model_loaded(self) -> bool:
        """检查模型是否已加载"""
        with self._lock:
            return self._is_model_loaded

    @property
    def is_busy(self) -> bool:
        """检查服务是否正在处理任务"""
        return not self._task_queue.empty() or self._current_task_id is not None

    @property
    def model_name(self) -> str:
        """代理到底层 WhisperEngine 的 model_name"""
        return self.whisper_engine.model_name

    @property
    def device(self) -> str:
        """代理到底层 WhisperEngine 的 device"""
        return self.whisper_engine.device

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息 - 代理到底层 WhisperEngine"""
        with self._lock:
            if hasattr(self.whisper_engine, 'get_model_info'):
                return self.whisper_engine.get_model_info()
            else:
                # Fallback: 返回基本信息
                return {
                    "model_name": getattr(self.whisper_engine, 'model_name', 'Unknown'),
                    "is_loaded": self._is_model_loaded,
                    "device": getattr(self.whisper_engine, 'device', 'unknown'),
                }

    def _worker_loop(self) -> None:
        """工作线程主循环 - 持久运行"""
        app_logger.log_audio_event("TranscriptionService worker loop started", {
            "thread_id": threading.get_ident()
        })

        try:
            while self._is_running and not self._shutdown_event.is_set():
                try:
                    # 获取任务 (带超时,以便能响应shutdown)
                    task = self._task_queue.get(timeout=1.0)

                    # 处理任务
                    self._process_task(task)

                    # 标记任务完成
                    self._task_queue.task_done()

                except queue.Empty:
                    # 超时,继续循环检查shutdown
                    continue
                except Exception as e:
                    app_logger.log_error(e, "transcription_worker_loop")

        finally:
            app_logger.log_audio_event("TranscriptionService worker loop exiting", {})

    def _process_task(self, task: TranscriptionTask) -> None:
        """处理单个任务

        Args:
            task: 转录任务
        """
        try:
            if task.task_type == TranscriptionTaskType.SHUTDOWN:
                self._handle_shutdown()

            elif task.task_type == TranscriptionTaskType.LOAD_MODEL:
                self._handle_load_model(task)

            elif task.task_type == TranscriptionTaskType.UNLOAD_MODEL:
                self._handle_unload_model(task)

            elif task.task_type == TranscriptionTaskType.RELOAD_MODEL:
                self._handle_reload_model(task)

            elif task.task_type == TranscriptionTaskType.TRANSCRIBE:
                self._handle_transcribe(task)

        except Exception as e:
            app_logger.log_error(e, f"process_task_{task.task_type.value}")
            if task.error_callback:
                task.error_callback(str(e))

    def _handle_shutdown(self) -> None:
        """处理关闭任务"""
        app_logger.log_audio_event("Handling shutdown task", {})

        # 卸载模型
        if self._is_model_loaded:
            try:
                self.whisper_engine.unload_model()
                with self._lock:
                    self._is_model_loaded = False
            except Exception as e:
                app_logger.log_error(e, "shutdown_unload_model")

        # 停止循环
        self._is_running = False

    def _handle_load_model(self, task: TranscriptionTask) -> None:
        """处理加载模型任务

        Args:
            task: 加载模型任务
        """
        start_time = time.time()

        try:
            # 如果指定了新模型名称,更新engine
            if task.model_name:
                self.whisper_engine.set_model_name(task.model_name)

            app_logger.log_audio_event("Loading model in persistent thread", {
                "model_name": self.whisper_engine.model_name
            })

            # 调用简化的加载方法 (不再创建临时线程)
            self.whisper_engine.load_model()

            with self._lock:
                self._is_model_loaded = True

            load_time = time.time() - start_time

            # 获取GPU信息（如果可用）
            gpu_info = {}
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_info = {
                        "device": "cuda",
                        "allocated_gb": torch.cuda.memory_allocated() / (1024**3),
                        "reserved_gb": torch.cuda.memory_reserved() / (1024**3),
                        "total_gb": torch.cuda.get_device_properties(0).total_memory / (1024**3)
                    }
            except Exception:
                pass

            app_logger.log_audio_event("Model loaded successfully", {
                "model_name": self.whisper_engine.model_name,
                "load_time": f"{load_time:.2f}s"
            })

            # 发送模型加载完成事件
            if self._event_service:
                try:
                    from ...utils.constants import Events
                    self._event_service.emit(Events.MODEL_LOADING_COMPLETED, {
                        "model_name": self.whisper_engine.model_name,
                        "load_time": load_time,
                        "device": self.whisper_engine.device,
                        **gpu_info
                    })
                except Exception as e:
                    app_logger.log_error(e, "emit_model_loaded_event")

            if task.callback:
                task.callback(True, "")

        except Exception as e:
            error_msg = f"Failed to load model: {e}"
            app_logger.log_error(e, "load_model_task")

            with self._lock:
                self._is_model_loaded = False

            if task.error_callback:
                task.error_callback(error_msg)

    def _handle_unload_model(self, task: TranscriptionTask) -> None:
        """处理卸载模型任务

        Args:
            task: 卸载模型任务
        """
        try:
            self.whisper_engine.unload_model()

            with self._lock:
                self._is_model_loaded = False

            app_logger.log_audio_event("Model unloaded", {})

            if task.callback:
                task.callback()

        except Exception as e:
            app_logger.log_error(e, "unload_model_task")

    def _handle_reload_model(self, task: TranscriptionTask) -> None:
        """处理重新加载模型任务（用于切换 GPU/CPU）

        Args:
            task: 重载模型任务
        """
        start_time = time.time()

        try:
            # 提取 use_gpu 参数（从 audio_data hack 中恢复）
            use_gpu = None
            if task.audio_data is not None and len(task.audio_data) > 0:
                use_gpu = bool(task.audio_data[0] > 0.5)

            app_logger.log_audio_event("Reloading model with new settings", {
                "use_gpu": use_gpu,
                "model_name": task.model_name or self.whisper_engine.model_name
            })

            # 1. 卸载旧模型
            if self._is_model_loaded:
                self.whisper_engine.unload_model()
                with self._lock:
                    self._is_model_loaded = False

            # 2. 创建新的 WhisperEngine 实例（使用新配置）
            from ...speech import WhisperEngine
            old_model_name = self.whisper_engine.model_name
            new_model_name = task.model_name or old_model_name

            self.whisper_engine = WhisperEngine(new_model_name, use_gpu=use_gpu)

            # 3. 加载新模型
            self.whisper_engine.load_model()

            with self._lock:
                self._is_model_loaded = True

            load_time = time.time() - start_time

            app_logger.log_audio_event("Model reloaded successfully", {
                "model_name": self.whisper_engine.model_name,
                "device": self.whisper_engine.device,
                "use_gpu": self.whisper_engine.use_gpu,
                "reload_time": f"{load_time:.2f}s"
            })

            if task.callback:
                task.callback(True, "")

        except Exception as e:
            error_msg = f"Failed to reload model: {e}"
            app_logger.log_error(e, "reload_model_task")

            with self._lock:
                self._is_model_loaded = False

            if task.error_callback:
                task.error_callback(error_msg)

    def _handle_transcribe(self, task: TranscriptionTask) -> None:
        """处理转录任务

        Args:
            task: 转录任务
        """
        import traceback
        start_time = time.time()

        self._current_task_id = task.task_id

        try:
            # 模型状态检查
            if not self._is_model_loaded:
                if self._auto_load_model():
                    app_logger.log_audio_event("Auto-loaded model during transcription", {})
                else:
                    error_msg = (
                        "Model not ready. Please wait for model loading or check configuration.\n"
                        "Suggestions:\n"
                        "1. Wait a few moments for model to finish loading\n"
                        "2. Check if GPU memory is sufficient\n"
                        "3. Verify model files are not corrupted\n"
                        "4. Try restarting the application"
                    )
                    raise WhisperLoadError(error_msg)

            # 音频数据有效性检查
            if task.audio_data is None or len(task.audio_data) == 0:
                if task.error_callback:
                    task.error_callback("Audio data is empty")
                return

            # 执行转录
            transcription_start = time.time()
            transcription_dict = self.whisper_engine.transcribe(
                task.audio_data,
                language=task.language,
                temperature=task.temperature
            )
            transcription_time = time.time() - transcription_start

            # 构建结果对象
            result = TranscriptionResult(
                success=True,
                text=transcription_dict.get("text", ""),
                language=transcription_dict.get("language"),
                confidence=transcription_dict.get("confidence", 0.0),
                segments=transcription_dict.get("segments", []),
                transcription_time=transcription_time
            )

            app_logger.log_audio_event("Transcription completed", {
                "task_id": task.task_id,
                "text_length": len(result.text),
                "transcription_time": f"{transcription_time:.2f}s"
            })

            if task.callback:
                task.callback(result)

        except WhisperLoadError as whisper_error:
            error_msg = f"Transcription failed: {whisper_error}"
            app_logger.log_error(whisper_error, f"transcribe_task_{task.task_id}_whisper_error")

            result = TranscriptionResult(
                success=False,
                error=error_msg,
                recovery_suggestions=self._get_error_recovery_suggestions(whisper_error)
            )

            if task.error_callback:
                task.error_callback(error_msg)
            elif task.callback:
                task.callback(result)

        except Exception as e:
            error_msg = f"Transcription failed: {e}"
            app_logger.log_error(e, f"transcribe_task_{task.task_id}_unexpected_error")

            result = TranscriptionResult(
                success=False,
                error=error_msg,
                recovery_suggestions=self._get_error_recovery_suggestions(e)
            )

            if task.error_callback:
                task.error_callback(error_msg)
            elif task.callback:
                task.callback(result)

    # ===================================================================
    # ISpeechService 接口实现 - 同步方法包装
    # ===================================================================

    def transcribe(self, audio_data: np.ndarray, language: Optional[str] = None) -> Dict[str, Any]:
        """同步转录接口 - 阻塞等待结果

        Args:
            audio_data: 音频数据
            language: 语言代码

        Returns:
            转录结果字典
        """
        result_event = threading.Event()
        result_container = {"result": None, "error": None}

        def on_success(result: TranscriptionResult):
            result_container["result"] = {
                "text": result.text,
                "language": result.language,
                "confidence": result.confidence,
                "segments": result.segments
            }
            result_event.set()

        def on_error(error_msg: str):
            result_container["error"] = error_msg
            result_event.set()

        self.transcribe_async(
            audio_data,
            language=language,
            callback=on_success,
            error_callback=on_error
        )

        # 等待结果
        if not result_event.wait(timeout=60.0):
            raise WhisperLoadError("Transcription timed out after 60 seconds")

        if result_container["error"]:
            raise WhisperLoadError(result_container["error"])

        return result_container["result"] or {"text": "", "language": None}

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """同步加载模型接口 - 阻塞等待加载完成

        Args:
            model_name: 模型名称

        Returns:
            是否加载成功
        """
        result_event = threading.Event()
        result_container = {"success": False, "error": None}

        def on_success(success: bool, error: str):
            result_container["success"] = success
            result_container["error"] = error
            result_event.set()

        def on_error(error_msg: str):
            result_container["error"] = error_msg
            result_event.set()

        self.load_model_async(
            model_name=model_name,
            callback=on_success,
            error_callback=on_error
        )

        # 阻塞等待结果
        result_event.wait(timeout=300.0)  # 5分钟超时

        if result_container["error"]:
            app_logger.log_audio_event("Sync load_model failed", {
                "error": result_container["error"]
            })
            return False

        return result_container["success"]

    def unload_model(self) -> None:
        """同步卸载模型接口"""
        result_event = threading.Event()

        def on_complete():
            result_event.set()

        self.unload_model_async(callback=on_complete)
        result_event.wait(timeout=10.0)

    def get_available_models(self) -> list:
        """获取可用模型列表"""
        return self.whisper_engine.get_available_models()

    def _auto_load_model(self) -> bool:
        """尝试自动加载模型"""
        try:
            # 使用默认配置加载模型
            success = self.whisper_engine.load_model(timeout=60)  # 给60秒时间
            if success:
                self._is_model_loaded = True
                app_logger.log_audio_event("Model auto-loaded successfully", {})
            return success
        except Exception as e:
            app_logger.log_warning(f"Auto-load model failed: {e}", {})
            return False

    def _get_error_recovery_suggestions(self, error: Exception) -> list:
        """根据错误类型提供恢复建议"""
        suggestions = []
        error_str = str(error).lower()
        error_type = type(error).__name__

        # CUDA/GPU 相关错误
        if any(keyword in error_str for keyword in ["cuda", "gpu", "cudnn", "cublas", "out of memory", "memory error"]):
            suggestions.extend([
                "Check GPU drivers: nvidia-smi in command prompt",
                "Verify CUDA installation: Verify with 'nvcc --version'",
                "Try switching to CPU mode in application settings",
                "Restart application to reset GPU state",
                "Close other GPU-intensive applications",
            ])
            if "out of memory" in error_str:
                suggestions.extend([
                    "Use smaller model (base/small instead of large)",
                    "Reduce batch size in settings",
                ])

        # 模型加载相关错误
        elif any(keyword in error_str for keyword in ["model", "load", "import", "dll", "shared", "could not find"]):
            suggestions.extend([
                "Wait for model to finish loading (check status)",
                "Try downloading model again manually",
                "Check disk space (minimum 5GB free)",
                "Verify internet connection stability",
            ])
            if "dll" in error_str or "shared" in error_str:
                suggestions.extend([
                    "Install Microsoft Visual C++ Redistributables",
                    "Run application as administrator",
                ])

        # 内存相关错误
        elif any(keyword in error_str for keyword in ["memory", "ram", "allocation"]):
            suggestions.extend([
                "Close other applications to free system memory",
                "Try smaller model or reduced audio quality",
                "Restart application to clear memory",
            ])

        # 音频相关错误
        elif any(keyword in error_str for keyword in ["audio", "microphone", "device", "recording"]):
            suggestions.extend([
                "Check microphone connection and volume",
                "Verify audio device permissions in Windows",
                "Try different audio input device",
            ])

        # 网络相关错误
        elif any(keyword in error_str for keyword in ["network", "download", "connection", "timeout"]):
            suggestions.extend([
                "Check internet connection",
                "Try different network environment",
                "Check firewall/antivirus blocking",
            ])

        # Whisper 特定错误
        elif "faster_whisper" in error_str or "whisper" in error_str:
            suggestions.extend([
                "Reinstall faster-whisper",
                "Check Python version compatibility (Python 3.8+ recommended)",
                "Verify CTranslate2 installation",
            ])

        # 未知错误类型
        else:
            suggestions.extend([
                "Restart the application",
                "Check system resources (CPU, RAM, GPU)",
                "Update to latest application version",
            ])

        return sorted(list(set(suggestions)))  # 去重并排序

    def log_diagnostics(self) -> Dict[str, Any]:
        """记录转录系统诊断信息"""
        import sys
        import os
        import platform

        diagnostics = {
            "timestamp": time.time(),
            "system_info": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "machine": platform.machine()
            },
            "transcription_service": {
                "is_running": self._is_running,
                "is_model_loaded": self._is_model_loaded,
                "current_task_id": self._current_task_id,
                "is_busy": self.is_busy,
                "queue_size": self._task_queue.qsize(),
                "thread_info": {
                    "worker_thread_alive": self._worker_thread.is_alive() if self._worker_thread else False,
                    "worker_thread_name": self._worker_thread.name if self._worker_thread else None,
                    "worker_thread_id": self._worker_thread.ident if self._worker_thread else None
                },
                "streaming_mode": self._streaming_mode,
                "streaming_chunks_count": len(self._streaming_chunks) if hasattr(self, '_streaming_chunks') else 0
            },
            "whisper_engine": {
                "model_name": self.whisper_engine.model_name,
                "device": self.whisper_engine.device,
                "use_gpu": self.whisper_engine.use_gpu,
                "is_model_loaded": self.whisper_engine.is_model_loaded,
                "compute_type": self.whisper_engine.compute_type
            },
            "event_bus": {
                "available": self._event_service is not None,
                "event_names": self._event_service.get_event_names() if self._event_service else []
            },
            "memory_usage": {},
            "gpu_info": {}
        }

        # 内存使用情况
        try:
            import psutil
            process = psutil.Process(os.getpid())
            diagnostics["memory_usage"] = {
                "process_memory_mb": process.memory_info().rss / 1024 / 1024,
                "system_memory_percent": process.memory_percent()
            }
        except ImportError:
            pass

        # GPU 信息
        if self.whisper_engine.use_gpu:
            try:
                import torch
                if torch.cuda.is_available():
                    diagnostics["gpu_info"] = {
                        "cuda_available": True,
                        "device_count": torch.cuda.device_count(),
                        "current_device": torch.cuda.current_device(),
                        "device_name": torch.cuda.get_device_name(0),
                        "memory_allocated_gb": torch.cuda.memory_allocated() / 1024**3,
                        "memory_reserved_gb": torch.cuda.memory_reserved() / 1024**3,
                        "memory_total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3
                    }
            except Exception:
                pass

        # 记录诊断信息
        app_logger.log_audio_event("Transcription system diagnostics", diagnostics)

        return diagnostics

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要信息"""
        try:
            # 检查关键状态
            issues = []

            if not self._is_running:
                issues.append("TranscriptionService is not running")

            if not self._is_model_loaded:
                issues.append("Model is not loaded")

            if self._current_task_id and self.is_busy:
                issues.append(f"Processing task: {self._current_task_id}")

            if self._task_queue.qsize() > 10:
                issues.append(f"Queue backlog: {self._task_queue.qsize()} tasks")

            # GPU 状态检查
            gpu_issues = []
            if self.whisper_engine.use_gpu:
                try:
                    import torch
                    if not torch.cuda.is_available():
                        gpu_issues.append("CUDA not available")
                    else:
                        memory_allocated = torch.cuda.memory_allocated()
                        memory_total = torch.cuda.get_device_properties(0).total_memory
                        memory_percent = (memory_allocated / memory_total) * 100

                        if memory_percent > 80:
                            gpu_issues.append(f"High GPU memory usage: {memory_percent:.1f}%")
                except Exception:
                    gpu_issues.append("GPU status check failed")

            issues.extend(gpu_issues)

            return {
                "timestamp": time.time(),
                "issues_count": len(issues),
                "issues": issues,
                "service_status": "healthy" if not issues else "has_issues",
                "whisper_status": "loaded" if self.whisper_engine.is_model_loaded else "not_loaded",
                "queue_status": f"{self._task_queue.qsize()} tasks"
            }

        except Exception as e:
            return {
                "timestamp": time.time(),
                "error": str(e),
                "status": "error",
                "message": "Failed to generate error summary"
            }
