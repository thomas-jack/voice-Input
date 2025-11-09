"""Whisper speech recognition engine - faster-whisper implementation"""

import numpy as np
import time
import threading
from typing import Optional, Dict, Any
from .gpu_manager import GPUManager
from ..utils import WhisperLoadError, app_logger
from ..core.interfaces import ISpeechService

# Lazy import faster_whisper to avoid DLL loading issues on module import
faster_whisper = None
_whisper_import_lock = threading.RLock()
_whisper_loaded_in_thread = {}


def _ensure_whisper_imported():
    """Ensure faster-whisper is imported when needed - thread-safe version"""
    global faster_whisper

    current_thread_id = threading.get_ident()

    with _whisper_import_lock:
        if faster_whisper is None:
            try:
                app_logger.log_model_loading_step(
                    "Starting faster-whisper module import",
                    {
                        "thread_id": current_thread_id,
                        "thread_name": threading.current_thread().name,
                    },
                )

                # Import faster-whisper
                from faster_whisper import WhisperModel

                faster_whisper = WhisperModel

                _whisper_loaded_in_thread[current_thread_id] = True

                app_logger.log_model_loading_step(
                    "faster-whisper module imported successfully",
                    {
                        "thread_id": current_thread_id,
                        "thread_name": threading.current_thread().name,
                    },
                )

            except ImportError as e:
                error_msg = f"Failed to import faster-whisper: {e}"
                suggestions = [
                    "Install faster-whisper: pip install faster-whisper",
                    "Check Python environment and dependencies",
                    "Verify CTranslate2 installation",
                    "Try reinstalling with: pip uninstall faster-whisper && pip install faster-whisper",
                ]
                app_logger.log_error(e, "faster_whisper_import")
                app_logger.log_audio_event(
                    "faster-whisper import failed - suggestions",
                    {"error": str(e), "suggestions": suggestions},
                )
                raise WhisperLoadError(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error importing faster-whisper: {e}"
                suggestions = [
                    "Check Python version compatibility",
                    "Verify all dependencies are installed",
                    "Try creating a fresh virtual environment",
                    "Check for conflicting packages",
                ]
                app_logger.log_error(e, "faster_whisper_import_general")
                app_logger.log_audio_event(
                    "faster-whisper import error - suggestions",
                    {"error": str(e), "suggestions": suggestions},
                )
                raise WhisperLoadError(error_msg)

    return faster_whisper


def preload_whisper_module():
    """Preload the faster-whisper module to avoid DLL issues."""
    _ensure_whisper_imported()


class WhisperEngine(ISpeechService):
    """Whisper model management and inference engine - faster-whisper version"""

    # Provider metadata
    provider_id = "local"
    display_name = "Local Whisper"
    description = "Local Whisper model with GPU acceleration"

    def __init__(
        self, model_name: str = "large-v3-turbo", use_gpu: Optional[bool] = None
    ):
        self.model_name = model_name
        self.model = None
        self.gpu_manager = GPUManager()

        # 添加线程安全的状态检查
        self._device_lock = threading.RLock()

        # Determine device - 线程安全检测
        with self._device_lock:
            # use_gpu: None (auto-detect), True (force GPU), False (force CPU)
            if use_gpu is None:
                # 自动检测：根据硬件可用性决定
                self.use_gpu = self.gpu_manager.is_gpu_available()
            else:
                # 用户明确指定：尊重用户选择，但添加警告日志
                if use_gpu and not self.gpu_manager.is_gpu_available():
                    app_logger.log_audio_event(
                        "Warning: GPU requested but hardware not available",
                        {
                            "requested_gpu": True,
                            "hardware_available": False,
                            "action": "forcing GPU mode (may fail at runtime)",
                        },
                    )
                self.use_gpu = use_gpu

            self.device = "cuda" if self.use_gpu else "cpu"
            self.compute_type = "float16" if self.use_gpu else "int8"

        # Model status
        self._is_model_loaded = False
        self._load_time = None

        # Model configuration
        self.model_config = {
            "device": self.device,
            "compute_type": self.compute_type,
            "num_workers": 4,  # Parallel processing threads
            "cpu_threads": 0,  # 0 = auto
            "download_root": None,  # Use default cache directory
        }

        app_logger.log_audio_event(
            "Whisper engine initialized (faster-whisper)",
            {
                "model_name": model_name,
                "device": self.device,
                "compute_type": self.compute_type,
            },
        )

    def set_model_name(self, model_name: str) -> None:
        """Set the model name to load"""
        if model_name != self.model_name:
            if self.model is not None:
                app_logger.log_audio_event(
                    "Unloading model due to name change",
                    {"old_model": self.model_name, "new_model": model_name},
                )
                self.unload_model()

            self.model_name = model_name
            app_logger.log_audio_event("Model name updated", {"new_model": model_name})

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """Load Whisper model - 符合 ISpeechService 接口定义

        Args:
            model_name: 模型名称，None 表示使用当前模型

        Returns:
            是否加载成功

        Raises:
            WhisperLoadError: 加载失败时抛出

        Note: Should be called in TranscriptionService worker thread, not main thread
        """
        # 如果提供了新模型名称，先更新
        if model_name is not None:
            self.set_model_name(model_name)

        if self._is_model_loaded and self.model is not None:
            app_logger.log_audio_event(
                "Model already loaded", {"model_name": self.model_name}
            )
            return True

        try:
            app_logger.log_audio_event(
                "Loading model directly",
                {
                    "model_name": self.model_name,
                    "device": self.device,
                    "thread_id": threading.get_ident(),
                    "thread_name": threading.current_thread().name,
                },
            )

            timeout_seconds = 300  # 固定超时时间
            self._load_model_internal(timeout_seconds)
            self._is_model_loaded = True

            app_logger.log_audio_event(
                "Model loaded successfully",
                {
                    "model_name": self.model_name,
                    "device": self.device,
                    "load_time": self._load_time,
                },
            )

            return True

        except Exception as e:
            # Reset model loaded flag on failure
            self._is_model_loaded = False
            self.model = None
            error_msg = f"Failed to load model: {e}"
            app_logger.log_error(e, "load_model")
            raise WhisperLoadError(error_msg)

    def _load_model_internal(self, timeout_seconds: int = 300) -> None:
        """Internal method - direct model loading"""
        if self.model is not None:
            app_logger.log_audio_event(
                "Model already loaded", {"model_name": self.model_name}
            )
            return

        current_thread_id = threading.get_ident()
        thread_name = threading.current_thread().name

        try:
            app_logger.log_model_loading_step(
                "Starting model loading process",
                {
                    "model_name": self.model_name,
                    "device": self.device,
                    "timeout": timeout_seconds,
                    "thread_id": current_thread_id,
                    "thread_name": thread_name,
                },
            )

            start_time = time.time()

            # Step 1: Import faster-whisper module
            app_logger.log_model_loading_step("Importing faster-whisper module")
            WhisperModel = _ensure_whisper_imported()
            app_logger.log_model_loading_step(
                "faster-whisper module imported successfully"
            )

            # Step 2: Prepare GPU (if available)
            if self.use_gpu:
                app_logger.log_model_loading_step("Preparing GPU for model loading")
                try:
                    self.gpu_manager.prepare_for_model_loading()
                    app_logger.log_model_loading_step("GPU preparation completed")
                except Exception as gpu_error:
                    app_logger.log_model_loading_step(
                        "GPU preparation failed, proceeding anyway",
                        {"error": str(gpu_error), "thread_id": current_thread_id},
                    )

            # Step 3: Load model (with fallback strategy)
            app_logger.log_model_loading_step(
                "Loading faster-whisper model",
                {
                    "model_name": self.model_name,
                    "device": self.device,
                    "compute_type": self.compute_type,
                    "thread_id": current_thread_id,
                },
            )

            # Try local-first approach to avoid unnecessary network requests
            model = None
            try:
                # First attempt: Try loading from local cache only
                app_logger.log_model_loading_step(
                    "Attempting to load from local cache",
                    {"model_name": self.model_name},
                )
                model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                    num_workers=self.model_config["num_workers"],
                    cpu_threads=self.model_config["cpu_threads"],
                    download_root=self.model_config["download_root"],
                    local_files_only=True,  # Priority: use local cache first
                )
                app_logger.log_model_loading_step(
                    "Model loaded from local cache", {"model_name": self.model_name}
                )
            except (OSError, ValueError) as local_error:
                # Local cache not available, try downloading
                app_logger.log_model_loading_step(
                    "Local cache not found, downloading model",
                    {"model_name": self.model_name, "local_error": str(local_error)},
                )
                model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                    num_workers=self.model_config["num_workers"],
                    cpu_threads=self.model_config["cpu_threads"],
                    download_root=self.model_config["download_root"],
                    local_files_only=False,  # Allow network download
                )
                app_logger.log_model_loading_step(
                    "Model downloaded successfully", {"model_name": self.model_name}
                )

            load_time = time.time() - start_time
            self._load_time = load_time

            # Step 4: Validate model loading
            app_logger.log_model_loading_step("Validating loaded model")
            if model is None:
                raise WhisperLoadError("Model loaded but returned None")

            # Record loading info
            memory_info = self.gpu_manager.get_memory_usage() if self.use_gpu else {}

            app_logger.log_model_loading_step(
                "Model loaded successfully",
                {
                    "model_name": self.model_name,
                    "load_time": f"{load_time:.2f}s",
                    "device": self.device,
                    "memory_usage": memory_info,
                    "thread_id": current_thread_id,
                    "thread_name": thread_name,
                },
            )

            # Success
            self.model = model

        except Exception as e:
            error_msg = f"Failed to load Whisper model '{self.model_name}': {e}"

            # Provide detailed diagnostics based on error type
            suggestions = []
            error_str = str(e).lower()

            if (
                "could not find" in error_str
                or "dll" in error_str
                or "shared" in error_str
            ):
                suggestions = [
                    "Install Microsoft Visual C++ Redistributables",
                    "Check CUDA installation: nvidia-smi",
                    "Reinstall faster-whisper: pip uninstall faster-whisper && pip install faster-whisper",
                    "Run as administrator",
                    "Try CPU mode: set device to 'cpu' in settings",
                ]
            elif "memory" in error_str or "cuda" in error_str:
                suggestions = [
                    "Try a smaller model (base or small instead of large)",
                    "Close other GPU applications",
                    "Restart the application",
                    "Switch to CPU mode if GPU memory is insufficient",
                ]
            elif "network" in error_str or "download" in error_str:
                suggestions = [
                    "Check internet connection",
                    "Try downloading the model manually",
                    "Use a different network or VPN",
                    "Check firewall settings",
                ]
            else:
                suggestions = [
                    "Check Python environment and dependencies",
                    "Try reinstalling faster-whisper: pip uninstall faster-whisper && pip install faster-whisper",
                    "Create a fresh virtual environment",
                    "Check system compatibility",
                ]

            app_logger.log_error(e, f"faster_whisper_model_load_{self.model_name}")
            app_logger.log_audio_event(
                "Model load failed - suggestions",
                {"model": self.model_name, "error": str(e), "suggestions": suggestions},
            )
            raise WhisperLoadError(error_msg)

    def transcribe(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """Transcribe audio"""
        start_time = time.time()

        # 模型状态检查
        if self.model is None:
            raise WhisperLoadError("Model not loaded. Call load_model() first.")

        # 音频数据有效性检查
        if audio_data is None or len(audio_data) == 0:
            return {"text": "", "language": "unknown", "confidence": 0.0}

        try:
            transcription_start = time.time()

            # Prepare audio data
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Ensure audio is in correct range
            max_abs = np.max(np.abs(audio_data))
            if max_abs > 1.0:
                audio_data = audio_data / max_abs

            # Execute transcription
            try:
                segments, info = self.model.transcribe(
                    audio_data,
                    language=language if language != "auto" else None,
                    task="transcribe",
                    beam_size=1,
                    best_of=1,
                    patience=1.0,
                    length_penalty=1.0,
                    temperature=temperature,
                    compression_ratio_threshold=2.4,
                    log_prob_threshold=-1.0,
                    no_speech_threshold=0.6,
                    condition_on_previous_text=False,
                    initial_prompt=None,
                    vad_filter=False,
                )
            except Exception as transcribe_error:
                # 直接抛出错误，保留完整堆栈信息
                raise transcribe_error

            # Collect all segments
            segment_list = []
            text_parts = []

            for segment in segments:
                segment_dict = {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "avg_logprob": segment.avg_logprob,
                    "no_speech_prob": segment.no_speech_prob,
                }
                segment_list.append(segment_dict)
                text_parts.append(segment.text)

            text = " ".join(text_parts).strip()

            transcription_time = time.time() - transcription_start

            # Extract info
            detected_language = (
                info.language if hasattr(info, "language") else "unknown"
            )
            language_probability = (
                info.language_probability
                if hasattr(info, "language_probability")
                else 0.5
            )

            # Calculate average confidence from segments
            if segment_list:
                avg_logprob = np.mean([seg["avg_logprob"] for seg in segment_list])
                confidence = max(0.0, min(1.0, (avg_logprob + 1.0) / 2.0))
            else:
                confidence = 0.5

            # Clean up GPU cache (温和清理)
            if self.use_gpu:
                try:
                    self.gpu_manager.cleanup_after_inference()
                except Exception:
                    pass  # 清理失败不影响转录结果

            # Log transcription result
            app_logger.log_transcription(
                audio_length=len(audio_data) / 16000, text=text, confidence=confidence
            )

            app_logger.log_audio_event(
                "Transcription completed",
                {
                    "transcription_time": transcription_time,
                    "audio_duration": len(audio_data) / 16000,
                    "text_length": len(text),
                    "detected_language": detected_language,
                    "language_probability": language_probability,
                    "confidence": confidence,
                    "segments_count": len(segment_list),
                },
            )

            return {
                "text": text,
                "language": detected_language,
                "confidence": confidence,
                "segments": segment_list,
                "transcription_time": transcription_time,
            }

        except WhisperLoadError:
            raise

        except Exception as e:
            error_msg = f"Transcription failed: {e}"
            app_logger.log_error(WhisperLoadError(error_msg), "whisper_transcribe")
            raise WhisperLoadError(error_msg)

    def transcribe_with_timestamps(
        self, audio_data: np.ndarray, language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe with word-level timestamps"""
        if self.model is None:
            raise WhisperLoadError("Model not loaded. Call load_model() first.")

        try:
            # Enable word-level timestamps
            segments, info = self.model.transcribe(
                audio_data,
                language=language if language != "auto" else None,
                task="transcribe",
                word_timestamps=True,
            )

            # Collect all segments with word timestamps
            segment_list = []
            for segment in segments:
                segment_dict = {
                    "id": segment.id,
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "words": [],
                }

                # Add word-level timestamps if available
                if hasattr(segment, "words") and segment.words:
                    for word in segment.words:
                        segment_dict["words"].append(
                            {
                                "word": word.word,
                                "start": word.start,
                                "end": word.end,
                                "probability": word.probability,
                            }
                        )

                segment_list.append(segment_dict)

            return {
                "text": " ".join([seg["text"] for seg in segment_list]).strip(),
                "language": info.language if hasattr(info, "language") else "unknown",
                "segments": segment_list,
            }

        except Exception as e:
            error_msg = f"Transcription with timestamps failed: {e}"
            app_logger.log_error(
                WhisperLoadError(error_msg), "transcribe_with_timestamps"
            )
            raise WhisperLoadError(error_msg)

    def detect_language(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Detect audio language"""
        if self.model is None:
            raise WhisperLoadError("Model not loaded. Call load_model() first.")

        try:
            # Use faster-whisper's language detection
            # Transcribe with language detection enabled
            segments, info = self.model.transcribe(
                audio_data[: int(16000 * 30)],  # Use first 30 seconds for detection
                task="transcribe",
                beam_size=1,
            )

            # Consume segments iterator (required)
            _ = list(segments)

            detected_language = info.language if hasattr(info, "language") else "en"
            confidence = (
                info.language_probability
                if hasattr(info, "language_probability")
                else 0.5
            )

            app_logger.log_audio_event(
                "Language detected",
                {"language": detected_language, "confidence": confidence},
            )

            return {
                "language": detected_language,
                "confidence": confidence,
                "all_probabilities": {},  # faster-whisper doesn't provide all probabilities
            }

        except Exception as e:
            error_msg = f"Language detection failed: {e}"
            app_logger.log_error(WhisperLoadError(error_msg), "detect_language")
            return {"language": "en", "confidence": 0.5, "all_probabilities": {}}

    def unload_model(self) -> None:
        """Unload model and release memory - enhanced GPU memory cleanup"""
        if self.model is not None:
            try:
                # 确保模型引用被清理
                model_ref = self.model
                self.model = None
                del model_ref

                # 强制Python垃圾回收
                import gc

                gc.collect()

                # Clean GPU cache with enhanced cleanup
                if self.use_gpu:
                    self.gpu_manager.clear_cache()

                self._is_model_loaded = False
                self._load_time = None

                app_logger.log_audio_event(
                    "Whisper model unloaded successfully",
                    {"model_name": self.model_name, "was_gpu": self.use_gpu},
                )

            except Exception as e:
                app_logger.log_error(e, "unload_model")
                # 即使清理失败，也要重置状态
                self.model = None
                self._is_model_loaded = False
                self._load_time = None

    @property
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._is_model_loaded and self.model is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        info = {
            "model_name": self.model_name,
            "is_loaded": self.is_model_loaded,
            "device": self.device,
            "gpu_available": self.use_gpu,
            "model_config": self.model_config.copy(),
        }

        if self.use_gpu:
            info["gpu_info"] = self.gpu_manager.get_device_info()
            info["memory_usage"] = self.gpu_manager.get_memory_usage()

        return info

    def set_language(self, language: Optional[str]) -> None:
        """Set default language"""
        self.model_config["language"] = language
        app_logger.log_audio_event("Default language set", {"language": language})

    def set_task(self, task: str) -> None:
        """Set task type (transcribe or translate)"""
        if task not in ["transcribe", "translate"]:
            raise ValueError(
                f"Invalid task: {task}. Must be 'transcribe' or 'translate'"
            )

        self.model_config["task"] = task
        app_logger.log_audio_event("Task set", {"task": task})

    def get_available_models(self) -> list:
        """Get list of available models"""
        # Standard Whisper models supported by faster-whisper (multilingual only)
        return ["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo"]

    def benchmark_performance(self, test_duration: float = 10.0) -> Dict[str, float]:
        """Performance benchmark test"""
        if self.model is None:
            raise WhisperLoadError("Model not loaded. Call load_model() first.")

        # Generate test audio (silence)
        sample_rate = 16000
        test_audio = np.zeros(int(test_duration * sample_rate), dtype=np.float32)

        start_time = time.time()
        self.transcribe(test_audio)
        end_time = time.time()

        processing_time = end_time - start_time
        real_time_factor = processing_time / test_duration

        benchmark_results = {
            "test_duration": test_duration,
            "processing_time": processing_time,
            "real_time_factor": real_time_factor,
            "performance_rating": "excellent"
            if real_time_factor < 0.1
            else "good"
            if real_time_factor < 0.3
            else "fair"
            if real_time_factor < 0.8
            else "poor",
        }

        app_logger.log_audio_event("Performance benchmark completed", benchmark_results)

        return benchmark_results

    def _validate_cuda_context(self) -> bool:
        """验证CUDA上下文是否有效"""
        if not self.use_gpu:
            return True

        try:
            import torch

            if not torch.cuda.is_available():
                return False

            # 检查模型是否已经在这个线程中成功初始化
            if self.model is not None and self._is_model_loaded:
                # 如果模型已经加载且可使用，说明CUDA上下文在这个线程中是有效的
                app_logger.debug(
                    "CUDA context validation: model already loaded and valid"
                )
                return True

            # 尝试设置当前设备的CUDA上下文
            device = torch.cuda.current_device()

            # 如果没有CUDA上下文，尝试初始化一个
            if not torch.cuda.current_stream().device():
                torch.cuda.set_device(device)
                app_logger.debug(f"Set CUDA device to {device}")

            # 尝试一个简单的CUDA操作来验证上下文
            test_tensor = torch.zeros(1, device=device)
            result = test_tensor + 1
            del test_tensor, result

            app_logger.debug("CUDA context validation successful")
            return True

        except RuntimeError as cuda_error:
            # 特殊处理CUDA相关的运行时错误
            error_str = str(cuda_error).lower()
            if "cuda" in error_str and (
                "context" in error_str or "device" in error_str
            ):
                app_logger.debug(f"CUDA context issue detected: {cuda_error}")
                return False
            else:
                # 其他CUDA错误，重新抛出
                raise cuda_error
        except Exception as e:
            app_logger.debug(f"CUDA context validation failed: {e}")
            return False

    # Simple test connection method
    def test_connection(self) -> Dict[str, Any]:
        """Test model loading and basic functionality

        Returns:
            Connection test result
        """
        try:
            # Check if model is loaded
            if not self.is_model_loaded:
                return {
                    "success": False,
                    "message": "Model not loaded",
                    "provider": self.provider_id,
                }

            # Generate 0.1 second test audio
            test_audio = np.zeros(1600, dtype=np.float32)  # 0.1s @ 16kHz

            # Try transcription
            result = self.transcribe(test_audio, language=None, temperature=0.0)

            # Check result
            if "error" in result:
                return {
                    "success": False,
                    "message": f"Transcription test failed: {result['error']}",
                    "provider": self.provider_id,
                }

            return {
                "success": True,
                "message": "Model loaded and ready",
                "provider": self.provider_id,
                "details": {
                    "model": self.model_name,
                    "device": self.device,
                    "gpu_available": self.use_gpu,
                },
            }

        except Exception as e:
            app_logger.log_error(e, "whisper_test_connection")
            return {
                "success": False,
                "message": f"Connection test error: {str(e)}",
                "provider": self.provider_id,
            }
