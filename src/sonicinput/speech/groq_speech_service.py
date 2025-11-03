"""Groq Cloud Speech Service - Whisper API implementation"""

import numpy as np
import io
import wave
import time
from typing import Optional, Dict, Any, List
from ..core.interfaces import ISpeechService
from ..utils import app_logger

# Lazy import groq to avoid dependency issues
groq = None


def _ensure_groq_imported():
    """Ensure groq is imported when needed"""
    global groq
    if groq is None:
        try:
            from groq import Groq

            groq = Groq
            app_logger.log_model_loading_step("Groq module imported successfully", {})
        except ImportError as e:
            error_msg = f"Failed to import groq: {e}. Install with: pip install groq"
            app_logger.log_error(e, "groq_import")
            raise ImportError(error_msg)
    return groq


class GroqSpeechService(ISpeechService):
    """Groq Cloud Whisper API implementation"""

    # Available Groq Whisper models
    AVAILABLE_MODELS = ["whisper-large-v3-turbo", "whisper-large-v3"]

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-large-v3-turbo",
        base_url: Optional[str] = None,
    ):
        """Initialize Groq Speech Service

        Args:
            api_key: Groq API key
            model: Whisper model to use
            base_url: Optional custom base URL for Groq API (e.g., for proxies or compatible services)
        """
        self.api_key = api_key
        self.model = model
        self.model_name = model  # Alias for compatibility with WhisperEngine
        self.base_url = base_url  # None means use default Groq endpoint
        self.device = "cloud"  # For compatibility with WhisperEngine
        self.use_gpu = False  # Cloud service, not using local GPU
        self._client = None
        self._model_loaded = False

    def transcribe(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """Transcribe audio data using Groq Whisper API with automatic retry

        Args:
            audio_data: Audio data as numpy array (16kHz, mono)
            language: Language code (ISO-639-1), None for auto-detection
            temperature: Temperature for sampling (0.0-1.0), default 0.0 for deterministic output
            max_retries: Maximum number of retries on failure
            retry_delay: Initial retry delay in seconds (exponential backoff)

        Returns:
            Transcription result with text, segments, etc.
        """
        # For cloud service, initialize client on-demand (no "model loading" required)
        if self._client is None:
            success = self._initialize_client()
            if not success:
                # Return error result if client initialization failed
                return {
                    "text": "",
                    "language": language or "unknown",
                    "segments": [],
                    "duration": len(audio_data) / 16000.0,
                    "processing_time": 0.0,
                    "rtf": 0.0,
                    "error": "Failed to initialize Groq client. Check API key and network connection.",
                    "provider": "groq",
                }

        start_time = time.time()
        last_error = None
        retry_count = 0

        while retry_count <= max_retries:
            try:
                # Convert numpy array to WAV bytes
                audio_bytes = self._numpy_to_wav(audio_data)

                # Create transcription request
                app_logger.log_audio_event(
                    "Sending audio to Groq API",
                    {
                        "model": self.model,
                        "language": language or "auto",
                        "audio_size_bytes": len(audio_bytes),
                        "retry_count": retry_count,
                    },
                )

                # Call Groq API
                transcription = self._client.audio.transcriptions.create(
                    file=("audio.wav", audio_bytes),
                    model=self.model,
                    language=language if language and language != "auto" else None,
                    response_format="verbose_json",
                    temperature=temperature,
                )

                elapsed_time = time.time() - start_time
                audio_duration = len(audio_data) / 16000.0  # Assuming 16kHz
                rtf = elapsed_time / audio_duration if audio_duration > 0 else 0

                # Convert Groq response to our standard format
                result = {
                    "text": transcription.text,
                    "language": getattr(
                        transcription, "language", language or "unknown"
                    ),
                    "segments": self._convert_segments(transcription),
                    "duration": audio_duration,
                    "processing_time": elapsed_time,
                    "rtf": rtf,
                    "provider": "groq",
                    "retry_count": retry_count,
                }

                app_logger.log_audio_event(
                    "Groq transcription completed",
                    {
                        "text_length": len(result["text"]),
                        "duration": audio_duration,
                        "processing_time": elapsed_time,
                        "rtf": rtf,
                        "model": self.model,
                        "retry_count": retry_count,
                    },
                )

                return result

            except Exception as e:
                last_error = str(e)
                app_logger.log_error(e, "GroqSpeechService.transcribe")

                # Check if we should retry
                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = retry_delay * (
                        2 ** (retry_count - 1)
                    )  # Exponential backoff
                    app_logger.log_audio_event(
                        "Retrying Groq transcription",
                        {
                            "retry_count": retry_count,
                            "max_retries": max_retries,
                            "delay": wait_time,
                            "error": last_error,
                        },
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    # All retries exhausted
                    break

        # All retries failed
        elapsed_time = time.time() - start_time
        audio_duration = len(audio_data) / 16000.0

        return {
            "text": "",
            "language": language or "unknown",
            "segments": [],
            "duration": audio_duration,
            "processing_time": elapsed_time,
            "rtf": 0.0,
            "error": last_error or "Unknown error",
            "error_code": "MAX_RETRIES_EXCEEDED",
            "provider": "groq",
            "retry_count": retry_count,
            "success": False,
        }

    def _numpy_to_wav(self, audio_data: np.ndarray, sample_rate: int = 16000) -> bytes:
        """Convert numpy array to WAV bytes

        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate in Hz

        Returns:
            WAV file as bytes
        """
        # Ensure audio is in int16 format
        if audio_data.dtype != np.int16:
            # Convert float to int16
            if audio_data.dtype in [np.float32, np.float64]:
                audio_data = (audio_data * 32767).astype(np.int16)
            else:
                audio_data = audio_data.astype(np.int16)

        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        wav_buffer.seek(0)
        return wav_buffer.read()

    def _convert_segments(self, transcription) -> List[Dict[str, Any]]:
        """Convert Groq segments to our standard format

        Args:
            transcription: Groq transcription response

        Returns:
            List of segment dictionaries
        """
        if not hasattr(transcription, "segments") or not transcription.segments:
            return []

        segments = []
        for seg in transcription.segments:
            # Handle both dict and object attribute access
            if isinstance(seg, dict):
                segments.append(
                    {
                        "start": seg.get("start", 0.0),
                        "end": seg.get("end", 0.0),
                        "text": seg.get("text", ""),
                        "avg_logprob": seg.get("avg_logprob", 0.0),
                        "no_speech_prob": seg.get("no_speech_prob", 0.0),
                    }
                )
            else:
                # Object attribute access
                segments.append(
                    {
                        "start": getattr(seg, "start", 0.0),
                        "end": getattr(seg, "end", 0.0),
                        "text": getattr(seg, "text", ""),
                        "avg_logprob": getattr(seg, "avg_logprob", 0.0),
                        "no_speech_prob": getattr(seg, "no_speech_prob", 0.0),
                    }
                )

        return segments

    def _initialize_client(self) -> bool:
        """Initialize Groq client on-demand

        Returns:
            True if successful
        """
        # Check API key
        if not self.api_key or self.api_key.strip() == "":
            app_logger.log_audio_event(
                "Groq API key not configured", {"error": "API key is empty or missing"}
            )
            return False

        try:
            Groq = _ensure_groq_imported()

            # Initialize client with optional base_url
            if self.base_url:
                self._client = Groq(api_key=self.api_key, base_url=self.base_url)
            else:
                self._client = Groq(api_key=self.api_key)

            app_logger.log_model_loading_step(
                "Groq client initialized on-demand",
                {
                    "model": self.model,
                    "api_key_present": True,
                    "base_url": self.base_url or "default",
                },
            )

            return True

        except Exception as e:
            app_logger.log_error(e, "GroqSpeechService._initialize_client")
            return False

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """Pre-initialize Groq client (for compatibility with local service interface)

        Args:
            model_name: Model name to use (optional)

        Returns:
            True if successful
        """
        if model_name:
            if model_name not in self.AVAILABLE_MODELS:
                app_logger.log_audio_event(
                    "Invalid Groq model requested",
                    {"requested": model_name, "available": self.AVAILABLE_MODELS},
                )
                return False
            self.model = model_name
            self.model_name = model_name  # Keep in sync

        # For cloud service, just pre-initialize the client
        success = self._initialize_client()
        self._model_loaded = success  # Keep for compatibility
        return success

    def unload_model(self) -> None:
        """Unload Groq client (cleanup)"""
        self._client = None
        self._model_loaded = False
        app_logger.log_audio_event("Groq client unloaded", {})

    def get_available_models(self) -> List[str]:
        """Get list of available Groq Whisper models

        Returns:
            List of model names
        """
        return self.AVAILABLE_MODELS.copy()

    @property
    def is_model_loaded(self) -> bool:
        """Check if model/client is ready

        Returns:
            True if client is initialized or can be initialized on-demand
        """
        # For cloud services, the service is always "ready"
        # Client will be initialized on-demand during transcription
        return True
