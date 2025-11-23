"""Qwen ASR Engine - Alibaba Cloud Speech Recognition

Cloud-based speech recognition service powered by Alibaba's Qwen large model.
Supports emotion detection and language identification.
"""

import base64
import time
from typing import Any, Dict, Optional

import numpy as np

from ..utils import app_logger
from .cloud_base import CloudTranscriptionBase


class QwenEngine(CloudTranscriptionBase):
    """Qwen ASR engine for Alibaba Cloud speech recognition

    Features:
    - High accuracy powered by Qwen large model (qwen3-asr-flash)
    - Emotion detection (neutral, positive, negative, etc.)
    - Automatic language identification
    - JSON-based API (not multipart form data)
    - Base64 audio encoding
    - Zero GPU dependency: Pure cloud service
    """

    # Provider metadata
    provider_id = "qwen"
    display_name = "Qwen ASR"
    description = "Alibaba Cloud Qwen ASR with emotion and language detection"
    api_endpoint = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"

    # Available models
    AVAILABLE_MODELS = ["qwen3-asr-flash"]

    def __init__(
        self,
        api_key: str = "",
        model: str = "qwen3-asr-flash",
        base_url: Optional[str] = None,
        enable_itn: bool = True,
        config_service=None,
    ):
        """Initialize Qwen ASR Engine

        Args:
            api_key: DashScope API key (default: empty, must be set via initialize)
            model: ASR model to use (default: qwen3-asr-flash)
            base_url: Optional custom base URL for API
            enable_itn: Enable Inverse Text Normalization (convert "一千" to "1000")
            config_service: Optional config service for streaming chunk duration
        """
        # Note: Don't call super().__init__() - need custom session setup
        self.api_key = api_key
        self.model = model
        self.model_name = model
        self.base_url = base_url if base_url else "https://dashscope.aliyuncs.com"
        self.enable_itn = enable_itn
        self._is_model_loaded = False
        self.device = "cloud"
        self.use_gpu = False
        self._config_service = config_service

        # HTTP session with connection pooling
        self._session = None
        self._session_lock = __import__("threading").RLock()

        # Performance tracking
        self._request_count = 0
        self._total_request_time = 0.0
        self._error_count = 0

        # Cloud chunk accumulator for streaming mode
        self._chunk_accumulator = None

    def _get_session(self):  # type: ignore
        """Get or create HTTP session"""
        import requests

        with self._session_lock:
            if self._session is None:
                self._session = requests.Session()
                self._session.headers.update(
                    {
                        "User-Agent": "SonicInput/1.4",
                        "Content-Type": "application/json",
                        **self.get_auth_headers(),
                    }
                )
            return self._session

    def prepare_request_data(self, **kwargs) -> Dict[str, Any]:
        """Prepare Qwen-specific request data (JSON format)

        Note: This only prepares the non-audio parts of the request.
        Audio data is added in transcribe() method.

        Args:
            **kwargs: Transcription parameters (language, etc.)

        Returns:
            Qwen API request body structure (without audio data)
        """
        request_data = {
            "model": self.model,
            "input": {
                "messages": [
                    {"role": "system", "content": [{"text": ""}]},
                    {
                        "role": "user",
                        "content": [],  # Audio will be added here
                    },
                ]
            },
            "parameters": {"asr_options": {"enable_itn": self.enable_itn}},
        }

        return request_data

    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Qwen API response into standard format

        Args:
            response_data: Raw Qwen API response

        Returns:
            Standard transcription result format with emotion and language
        """
        try:
            # Extract choices array
            choices = response_data.get("output", {}).get("choices", [])
            if not choices:
                app_logger.log_audio_event(
                    "Qwen response has no choices",
                    {"response": str(response_data)[:200]},
                )
                return {
                    "text": "",
                    "language": "unknown",
                    "confidence": 0.0,
                    "emotion": "unknown",
                    "segments": [],
                }

            # Extract message
            message = choices[0].get("message", {})
            content = message.get("content", [])

            if not content:
                return {
                    "text": "",
                    "language": "unknown",
                    "confidence": 0.0,
                    "emotion": "unknown",
                    "segments": [],
                }

            # Extract text
            text = content[0].get("text", "").strip()

            # Extract annotations (language, emotion)
            annotations = message.get("annotations", [])
            language = "unknown"
            emotion = "neutral"

            if annotations:
                first_annotation = annotations[0]
                language = first_annotation.get("language", "unknown")
                emotion = first_annotation.get("emotion", "neutral")

            # Qwen doesn't provide confidence scores, use high default
            confidence = 0.9 if text else 0.0

            return {
                "text": text,
                "language": language,
                "confidence": confidence,
                "emotion": emotion,  # Extra metadata
                "segments": [],  # Qwen doesn't provide segments
            }

        except Exception as e:
            app_logger.log_error(e, "qwen_parse_response")
            return {
                "text": "",
                "language": "unknown",
                "confidence": 0.0,
                "emotion": "unknown",
                "segments": [],
                "error": f"Parse error: {str(e)}",
            }

    def get_auth_headers(self) -> Dict[str, str]:
        """Get Qwen-specific authentication headers

        Returns:
            Authentication headers dictionary
        """
        return {"Authorization": f"Bearer {self.api_key}"}

    def transcribe(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs,
    ) -> Dict[str, Any]:
        """Transcribe audio data using Qwen ASR API

        Note: Overrides base class method because Qwen uses JSON body
        instead of multipart form data.

        Args:
            audio_data: Audio data as numpy array (16kHz, mono)
            language: Language code (not used by Qwen - auto-detects)
            temperature: Sampling temperature (not used by Qwen)
            max_retries: Maximum retry attempts
            retry_delay: Initial retry delay in seconds
            **kwargs: Additional parameters

        Returns:
            Transcription result with text, language, emotion, confidence, etc.
        """
        start_time = time.time()

        # Validate input
        if audio_data is None or len(audio_data) == 0:
            return {
                "text": "",
                "error": "Empty audio data",
                "provider": self.provider_id,
            }

        try:
            # Convert audio to WAV bytes
            wav_bytes = self._numpy_to_wav_bytes(audio_data)

            # Base64 encode audio
            audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")

            # Prepare request body
            request_body = self.prepare_request_data(**kwargs)

            # Add audio to request (with data URI format)
            request_body["input"]["messages"][1]["content"] = [
                {"audio": f"data:audio/wav;base64,{audio_base64}"}
            ]

            # Make request with retry logic
            result = self._make_json_request_with_retry(
                json_body=request_body,
                max_retries=max_retries,
                retry_delay=retry_delay,
            )

            # Calculate timing
            processing_time = time.time() - start_time
            audio_duration = len(audio_data) / 16000.0

            # Update statistics
            self._total_request_time += processing_time

            # Parse and format response
            if "error" not in result:
                try:
                    parsed_result = self.parse_response(result)
                    parsed_result.update(
                        {
                            "processing_time": processing_time,
                            "duration": audio_duration,
                            "real_time_factor": processing_time / audio_duration
                            if audio_duration > 0
                            else 0,
                            "provider": self.provider_id,
                        }
                    )

                    app_logger.log_transcription(
                        audio_length=audio_duration,
                        text=parsed_result.get("text", ""),
                        confidence=parsed_result.get("confidence", 0.0),
                    )

                    return parsed_result

                except Exception as e:
                    app_logger.log_error(e, f"{self.provider_id}_parse_response")
                    return {
                        "text": "",
                        "error": f"Response parsing failed: {str(e)}",
                        "processing_time": processing_time,
                        "duration": audio_duration,
                        "provider": self.provider_id,
                    }
            else:
                # Error occurred during request
                result.update(
                    {
                        "processing_time": processing_time,
                        "duration": audio_duration,
                        "real_time_factor": processing_time / audio_duration
                        if audio_duration > 0
                        else 0,
                    }
                )
                return result

        except Exception as e:
            app_logger.log_error(e, "qwen_transcribe")
            processing_time = time.time() - start_time
            return {
                "text": "",
                "error": f"Transcription failed: {str(e)}",
                "processing_time": processing_time,
                "duration": len(audio_data) / 16000.0 if audio_data is not None else 0,
                "provider": self.provider_id,
            }

    def _make_json_request_with_retry(
        self,
        json_body: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Make JSON request with exponential backoff retry

        Similar to base class _make_request_with_retry but for JSON body.

        Args:
            json_body: JSON request body
            max_retries: Maximum number of retries
            retry_delay: Initial retry delay in seconds
            timeout: Request timeout in seconds

        Returns:
            Parsed response data or error information
        """
        import requests

        session = self._get_session()
        last_error = None
        retry_count = 0

        while retry_count <= max_retries:
            try:
                app_logger.log_audio_event(
                    "Sending Qwen ASR request",
                    {
                        "provider": self.provider_id,
                        "url": self.api_endpoint,
                        "retry_count": retry_count,
                        "timeout": timeout,
                    },
                )

                response = session.post(
                    self.api_endpoint,
                    json=json_body,  # Key difference: json= not files=
                    timeout=timeout,
                )

                # Update statistics
                self._request_count += 1

                # Handle successful response
                if response.status_code == 200:
                    app_logger.log_audio_event(
                        "Qwen ASR transcription successful",
                        {
                            "provider": self.provider_id,
                            "status_code": response.status_code,
                            "retry_count": retry_count,
                        },
                    )
                    return response.json()

                # Handle error response
                self._error_count += 1
                error_data = self._handle_api_error(response)

                # Check if we should retry
                if self._should_retry(response.status_code, retry_count, max_retries):
                    retry_count += 1
                    wait_time = retry_delay * (2 ** (retry_count - 1))

                    app_logger.log_audio_event(
                        "Retrying Qwen ASR request",
                        {
                            "provider": self.provider_id,
                            "status_code": response.status_code,
                            "retry_count": retry_count,
                            "max_retries": max_retries,
                            "wait_time": wait_time,
                            "error": last_error,
                        },
                    )

                    time.sleep(wait_time)
                    continue
                else:
                    return error_data

            except requests.exceptions.Timeout as e:
                last_error = f"Request timeout ({timeout}s): {str(e)}"
                self._error_count += 1

                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = retry_delay * (2 ** (retry_count - 1))
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        "error": last_error,
                        "error_code": "TIMEOUT",
                        "provider": self.provider_id,
                        "retry_count": retry_count,
                    }

            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {str(e)}"
                self._error_count += 1

                if retry_count < max_retries:
                    retry_count += 1
                    wait_time = retry_delay * (2 ** (retry_count - 1))
                    time.sleep(wait_time)
                    continue
                else:
                    return {
                        "error": last_error,
                        "error_code": "CONNECTION_ERROR",
                        "provider": self.provider_id,
                        "retry_count": retry_count,
                    }

            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                app_logger.log_error(e, f"{self.provider_id}_json_request")
                break

        # All retries failed
        return {
            "error": last_error or "Unknown error",
            "error_code": "MAX_RETRIES_EXCEEDED",
            "provider": self.provider_id,
            "retry_count": retry_count,
        }

    def _handle_api_error(self, response) -> Dict[str, Any]:  # type: ignore
        """Handle Qwen API error response

        Args:
            response: HTTP response object

        Returns:
            Error result dictionary
        """
        try:
            error_data = response.json()
            # Qwen error format may vary, try to extract message
            error_message = error_data.get("message", "Unknown error")
            if "error" in error_data:
                error_message = error_data["error"].get("message", error_message)
        except Exception:
            error_message = f"HTTP {response.status_code}: {response.text[:200]}"

        app_logger.log_audio_event(
            "Qwen API error",
            {
                "status_code": response.status_code,
                "error": error_message,
                "provider": self.provider_id,
            },
        )

        return {
            "error": error_message,
            "error_code": response.status_code,
            "provider": self.provider_id,
        }

    def get_available_models(self) -> list:
        """Get list of available Qwen models

        Returns:
            List of model names
        """
        return self.AVAILABLE_MODELS.copy()

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """Load model (for Qwen, just validate configuration)

        Args:
            model_name: Model name to use

        Returns:
            True if successful
        """
        if model_name:
            if model_name not in self.AVAILABLE_MODELS:
                app_logger.log_audio_event(
                    "Invalid Qwen model requested",
                    {"requested": model_name, "available": self.AVAILABLE_MODELS},
                )
                return False
            self.model = model_name
            self.model_name = model_name

        # For cloud service, just mark as loaded
        self._is_model_loaded = True
        app_logger.log_audio_event(
            "Qwen ASR service marked as loaded",
            {"model": self.model, "endpoint": self.api_endpoint},
        )
        return True

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize Qwen service with configuration

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: Invalid configuration
            RuntimeError: Initialization failed
        """
        # Extract configuration
        self.api_key = config.get("api_key", "")
        model = config.get("model", "qwen3-asr-flash")
        self.base_url = config.get("base_url", "https://dashscope.aliyuncs.com")
        self.enable_itn = config.get("enable_itn", True)

        # Validate API key
        if not self.api_key or self.api_key.strip() == "":
            raise ValueError("Qwen API key (DashScope) is required")

        # Validate model
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model '{model}'. Available: {self.AVAILABLE_MODELS}"
            )

        self.model = model
        self.model_name = model

        # Update API endpoint based on base_url
        if self.base_url != "https://dashscope.aliyuncs.com":
            self.api_endpoint = (
                f"{self.base_url}/api/v1/services/aigc/multimodal-generation/generation"
            )

        # Mark as loaded
        self._is_model_loaded = True

        app_logger.log_model_loading_step(
            "Qwen ASR provider initialized",
            {
                "model": self.model,
                "base_url": self.base_url,
                "enable_itn": self.enable_itn,
            },
        )

    def test_connection(self) -> Dict[str, Any]:
        """Test Qwen API connection

        Returns:
            Connection test result
        """
        result = super().test_connection()
        result.update(
            {
                "details": {
                    "model": self.model,
                    "base_url": self.base_url,
                    "endpoint": self.api_endpoint,
                    "enable_itn": self.enable_itn,
                }
            }
        )
        return result
