"""Doubao (ByteDance) Speech Recognition Engine

Cloud-based speech recognition service powered by ByteDance's Doubao large model.
Uses async task submission and polling for audio transcription.
"""

import numpy as np
import time
import threading
import requests
import wave
import io
import uuid
import base64
from typing import Optional, Dict, Any, List
from ..utils import app_logger
from ..core.interfaces import ISpeechService


class DoubaoEngine(ISpeechService):
    """Doubao large model audio transcription engine

    Features:
    - High accuracy powered by Doubao large model
    - Async task-based transcription
    - Intelligent text normalization
    - Punctuation restoration
    - Zero GPU dependency: Pure cloud service
    """

    # Doubao API endpoints
    BASE_URL = "https://openspeech.bytedance.com"
    SUBMIT_ENDPOINT = "/api/v3/auc/bigmodel/submit"
    QUERY_ENDPOINT = "/api/v3/auc/bigmodel/query"

    # Resource ID for bigmodel ASR
    RESOURCE_ID = "volc.bigasr.auc"

    def __init__(
        self,
        api_key: str,
        app_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize Doubao engine

        Args:
            api_key: Doubao API key (x-api-key header)
            app_id: Optional app ID for tracking
            base_url: Optional custom API endpoint (for proxies or compatible services)
        """
        self.api_key = api_key
        self.app_id = app_id or "sonicinput"
        self.base_url = base_url if base_url else self.BASE_URL
        self._is_model_loaded = False
        self.device = "cloud"  # Cloud service

        # Request session for connection reuse
        self._session = None
        self._session_lock = threading.RLock()

        # Performance statistics
        self._request_count = 0
        self._total_request_time = 0.0
        self._error_count = 0

        app_logger.log_audio_event(
            "Doubao engine initialized",
            {
                "api_endpoint": f"{self.base_url}{self.QUERY_ENDPOINT}",
                "custom_base_url": base_url is not None,
                "app_id": self.app_id,
            },
        )

    def _get_session(self) -> requests.Session:
        """Get or create HTTP session"""
        with self._session_lock:
            if self._session is None:
                self._session = requests.Session()
                self._session.headers.update(
                    {
                        "x-api-key": self.api_key,
                        "User-Agent": "SonicInput/1.4",
                    }
                )
            return self._session

    def _numpy_to_base64_wav(
        self, audio_data: np.ndarray, sample_rate: int = 16000
    ) -> str:
        """Convert numpy audio data to base64-encoded WAV

        Args:
            audio_data: Audio data (numpy array)
            sample_rate: Sample rate, default 16000Hz

        Returns:
            Base64-encoded WAV data
        """
        # Ensure audio is float32 format
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Convert to 16-bit integer
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # Create WAV file in memory
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())

            wav_bytes = wav_buffer.getvalue()
            return base64.b64encode(wav_bytes).decode('utf-8')

    def _submit_task(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
    ) -> Optional[str]:
        """Submit transcription task and get task ID

        Args:
            audio_data: Audio data (numpy array)
            language: Language code (zh-CN, en-US, etc.)

        Returns:
            Task ID if successful, None otherwise
        """
        try:
            # Convert audio to base64 WAV
            audio_base64 = self._numpy_to_base64_wav(audio_data)

            # Generate request ID
            request_id = str(uuid.uuid4())

            # Prepare request
            session = self._get_session()
            url = f"{self.base_url}{self.SUBMIT_ENDPOINT}"

            headers = {
                "Content-Type": "application/json",
                "X-Api-Resource-Id": self.RESOURCE_ID,
                "X-Api-Request-Id": request_id,
            }

            payload = {
                "audio": audio_base64,
                "format": "wav",
                "rate": 16000,
                "bits": 16,
                "channel": 1,
                "language": language or "zh-CN",
                "enable_itn": True,  # Intelligent text normalization
                "enable_punc": True,  # Punctuation
            }

            app_logger.log_audio_event(
                "Submitting transcription task",
                {
                    "audio_length": len(audio_data),
                    "language": language or "zh-CN",
                    "request_id": request_id,
                },
            )

            response = session.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id") or result.get("id")

                if task_id:
                    app_logger.log_audio_event(
                        "Task submitted successfully",
                        {"task_id": task_id, "request_id": request_id},
                    )
                    return task_id
                else:
                    app_logger.log_audio_event(
                        "Task submission failed: no task_id in response",
                        {"response": result},
                    )
                    return None
            else:
                app_logger.log_audio_event(
                    "Task submission failed",
                    {
                        "status_code": response.status_code,
                        "response": response.text,
                    },
                )
                return None

        except Exception as e:
            app_logger.log_error(e, "doubao_submit_task")
            return None

    def _query_result(
        self,
        task_id: str,
        max_polls: int = 30,
        poll_interval: float = 1.0,
    ) -> Optional[Dict[str, Any]]:
        """Query transcription result by task ID

        Args:
            task_id: Task ID from submit
            max_polls: Maximum number of polling attempts
            poll_interval: Interval between polls (seconds)

        Returns:
            Transcription result dict if successful, None otherwise
        """
        try:
            session = self._get_session()
            url = f"{self.base_url}{self.QUERY_ENDPOINT}"

            for poll_count in range(max_polls):
                # Generate unique request ID for each query
                request_id = str(uuid.uuid4())

                headers = {
                    "Content-Type": "application/json",
                    "X-Api-Resource-Id": self.RESOURCE_ID,
                    "X-Api-Request-Id": request_id,
                }

                payload = {
                    "task_id": task_id,
                }

                response = session.post(url, json=payload, headers=headers, timeout=10)

                if response.status_code == 200:
                    result = response.json()

                    # Check task status
                    status = result.get("status") or result.get("task_status")

                    if status == "success" or status == "completed":
                        # Task completed successfully
                        return result
                    elif status == "failed" or status == "error":
                        # Task failed
                        app_logger.log_audio_event(
                            "Task failed",
                            {"task_id": task_id, "result": result},
                        )
                        return None
                    elif status == "processing" or status == "running":
                        # Still processing, continue polling
                        app_logger.log_audio_event(
                            "Task still processing",
                            {
                                "task_id": task_id,
                                "poll_count": poll_count + 1,
                                "max_polls": max_polls,
                            },
                        )
                        time.sleep(poll_interval)
                        continue
                    else:
                        # Unknown status
                        app_logger.log_audio_event(
                            "Unknown task status",
                            {"task_id": task_id, "status": status, "result": result},
                        )
                        time.sleep(poll_interval)
                        continue
                else:
                    app_logger.log_audio_event(
                        "Query failed",
                        {
                            "task_id": task_id,
                            "status_code": response.status_code,
                            "response": response.text,
                        },
                    )
                    return None

            # Max polls exceeded
            app_logger.log_audio_event(
                "Query timeout: max polls exceeded",
                {"task_id": task_id, "max_polls": max_polls},
            )
            return None

        except Exception as e:
            app_logger.log_error(e, "doubao_query_result")
            return None

    def transcribe(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """Transcribe audio data using async task mechanism

        Args:
            audio_data: Audio data (numpy array)
            language: Language code (zh-CN, en-US, etc.)
            temperature: Not used for cloud API (for interface compatibility)
            max_retries: Maximum number of retries
            retry_delay: Retry delay (seconds)

        Returns:
            Transcription result dict with text, language, etc.
        """
        start_time = time.time()

        # Validate data
        if audio_data is None or len(audio_data) == 0:
            app_logger.log_audio_event("Empty audio data provided")
            return {
                "text": "",
                "language": "unknown",
                "confidence": 0.0,
                "provider": "doubao",
                "error": "Empty audio data",
            }

        last_error = None
        retry_count = 0

        while retry_count <= max_retries:
            try:
                # Submit task
                task_id = self._submit_task(audio_data, language)

                if not task_id:
                    last_error = "Failed to submit task"
                    if retry_count < max_retries:
                        retry_count += 1
                        app_logger.log_audio_event(
                            "Retrying task submission",
                            {"retry_count": retry_count, "max_retries": max_retries},
                        )
                        time.sleep(retry_delay * (2 ** (retry_count - 1)))
                        continue
                    else:
                        break

                # Query result
                result = self._query_result(task_id, max_polls=30, poll_interval=1.0)

                if result:
                    # Extract transcription text
                    text = result.get("text") or result.get("result", {}).get("text", "")

                    # Calculate performance metrics
                    request_time = time.time() - start_time
                    audio_duration = len(audio_data) / 16000  # Assuming 16kHz
                    real_time_factor = (
                        request_time / audio_duration if audio_duration > 0 else 0
                    )

                    # Update statistics
                    self._request_count += 1
                    self._total_request_time += request_time

                    app_logger.log_transcription(
                        audio_length=audio_duration,
                        text=text,
                        confidence=0.95,  # Doubao doesn't provide confidence, use default
                    )

                    app_logger.log_audio_event(
                        "Transcription completed",
                        {
                            "provider": "doubao",
                            "request_time": request_time,
                            "audio_duration": audio_duration,
                            "real_time_factor": real_time_factor,
                            "text_length": len(text),
                            "retry_count": retry_count,
                        },
                    )

                    return {
                        "text": text.strip(),
                        "language": language or "zh-CN",
                        "confidence": 0.95,
                        "transcription_time": request_time,
                        "real_time_factor": real_time_factor,
                        "provider": "doubao",
                        "retry_count": retry_count,
                    }
                else:
                    last_error = "Failed to query result"
                    if retry_count < max_retries:
                        retry_count += 1
                        app_logger.log_audio_event(
                            "Retrying transcription",
                            {"retry_count": retry_count, "max_retries": max_retries},
                        )
                        time.sleep(retry_delay * (2 ** (retry_count - 1)))
                        continue
                    else:
                        break

            except Exception as e:
                last_error = f"Unexpected error: {e}"
                app_logger.log_error(e, "doubao_transcribe")

                if retry_count < max_retries:
                    retry_count += 1
                    time.sleep(retry_delay * (2 ** (retry_count - 1)))
                    continue
                else:
                    break

        # All retries failed
        self._error_count += 1
        return {
            "text": "",
            "error": last_error or "Unknown error",
            "error_code": "MAX_RETRIES_EXCEEDED",
            "provider": "doubao",
            "retry_count": retry_count,
        }

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """Load model (cloud service, just mark as loaded)

        Args:
            model_name: Not used for Doubao (for interface compatibility)

        Returns:
            True if successful
        """
        # Cloud service doesn't need preloading
        self._is_model_loaded = True
        app_logger.log_audio_event(
            "Model marked as loaded (cloud service)",
            {
                "provider": "doubao",
                "note": "API will be validated on first transcription request"
            },
        )
        return True

    def unload_model(self) -> None:
        """Unload model (cloud service doesn't need unloading)"""
        self._is_model_loaded = False

        # Clean up session
        with self._session_lock:
            if self._session:
                self._session.close()
                self._session = None

        app_logger.log_audio_event(
            "Model unloaded", {"provider": "doubao"}
        )

    def get_available_models(self) -> List[str]:
        """Get list of available models

        Returns:
            List of model names
        """
        return ["bigmodel"]  # Doubao only has one large model

    @property
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._is_model_loaded

    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics

        Returns:
            Statistics dict
        """
        avg_request_time = (
            self._total_request_time / self._request_count
            if self._request_count > 0
            else 0
        )

        return {
            "request_count": self._request_count,
            "error_count": self._error_count,
            "average_request_time": avg_request_time,
            "total_request_time": self._total_request_time,
            "success_rate": (self._request_count - self._error_count)
            / self._request_count
            if self._request_count > 0
            else 0,
            "provider": "doubao",
        }

    def test_connection(self) -> bool:
        """Test API connection (using real transcription request)

        Returns:
            True if connection successful
        """
        try:
            # Generate 0.1 second of silence for testing
            test_audio = np.zeros(1600, dtype=np.float32)  # 0.1s @ 16kHz

            app_logger.log_audio_event(
                "Testing connection with real transcription",
                {"provider": "doubao"},
            )

            # Execute real transcription request (shorter timeout)
            result = self.transcribe(
                test_audio,
                language="zh-CN",
                temperature=0.0,
                max_retries=1,
                retry_delay=1.0
            )

            # Check if successful
            success = "error" not in result or not result["error"]

            app_logger.log_audio_event(
                "Connection test",
                {
                    "success": success,
                    "provider": "doubao",
                    "error": result.get("error") if not success else None,
                },
            )

            return success
        except Exception as e:
            app_logger.log_error(e, "doubao_connection_test")
            return False

    def __del__(self):
        """Destructor, clean up resources"""
        try:
            self.unload_model()
        except Exception:
            pass  # Ignore errors during cleanup
