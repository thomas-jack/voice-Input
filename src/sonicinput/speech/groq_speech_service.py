"""Groq Cloud Speech Service - Simplified implementation"""

from typing import Optional, Dict, Any, List
from ..utils import app_logger
from .cloud_base import CloudTranscriptionBase

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


class GroqSpeechService(CloudTranscriptionBase):
    """Groq Cloud Whisper API implementation - simplified version"""

    # Provider metadata
    provider_id = "groq"
    display_name = "Groq Cloud"
    description = "Fast cloud-based transcription with Whisper models"
    api_endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"

    # Available models
    AVAILABLE_MODELS = ["whisper-large-v3-turbo", "whisper-large-v3"]

    def __init__(
        self,
        api_key: str = "",
        model: str = "whisper-large-v3-turbo",
        base_url: Optional[str] = None,
    ):
        """Initialize Groq Speech Service

        Args:
            api_key: Groq API key (default: empty, must be set via initialize)
            model: Whisper model to use
            base_url: Optional custom base URL for Groq API
        """
        super().__init__(api_key)
        self.model = model
        self.model_name = model  # Alias for compatibility
        self.base_url = base_url

        # Validate model
        if model not in self.AVAILABLE_MODELS:
            app_logger.log_audio_event(
                "Invalid Groq model, using default",
                {"requested": model, "default": self.AVAILABLE_MODELS[0]},
            )
            self.model = self.AVAILABLE_MODELS[0]
            self.model_name = self.model

    def prepare_request_data(self, **kwargs) -> Dict[str, Any]:
        """Prepare Groq-specific request data

        Args:
            **kwargs: Transcription parameters

        Returns:
            Groq API request parameters
        """
        request_data = {
            "model": self.model,
            "response_format": "verbose_json",
            "temperature": kwargs.get("temperature", 0.0),
        }

        # Add language if specified (not "auto")
        language = kwargs.get("language")
        if language and language != "auto":
            request_data["language"] = language

        return request_data

    def parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Groq API response into standard format

        Args:
            response_data: Raw Groq API response

        Returns:
            Standard transcription result format
        """
        text = response_data.get("text", "").strip()
        language = response_data.get("language", "unknown")

        # Convert segments to standard format
        segments = []
        if "segments" in response_data and response_data["segments"]:
            for seg in response_data["segments"]:
                # Handle both dict and object formats
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

        # Calculate confidence from segments
        confidence = 0.5  # Default confidence
        if segments:
            avg_logprob = sum(seg.get("avg_logprob", 0.0) for seg in segments) / len(
                segments
            )
            confidence = max(0.0, min(1.0, (avg_logprob + 1.0) / 2.0))

        return {
            "text": text,
            "language": language,
            "confidence": confidence,
            "segments": segments,
        }

    def get_auth_headers(self) -> Dict[str, str]:
        """Get Groq-specific authentication headers

        Returns:
            Authentication headers dictionary
        """
        return {"Authorization": f"Bearer {self.api_key}"}

    def load_model(self, model_name: Optional[str] = None) -> bool:
        """Load model (for Groq, just validate configuration)

        Args:
            model_name: Model name to use

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
            self.model_name = model_name

        # For cloud service, just mark as loaded
        self._is_model_loaded = True
        app_logger.log_audio_event(
            "Groq service marked as loaded",
            {"model": self.model, "endpoint": self.api_endpoint},
        )
        return True

    def get_available_models(self) -> List[str]:
        """Get list of available Groq models

        Returns:
            List of model names
        """
        return self.AVAILABLE_MODELS.copy()

    def test_connection(self) -> Dict[str, Any]:
        """Test Groq API connection

        Returns:
            Connection test result
        """
        result = super().test_connection()
        result.update(
            {
                "details": {
                    "model": self.model,
                    "base_url": self.base_url or "default",
                    "endpoint": self.api_endpoint,
                }
            }
        )
        return result

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize Groq service with configuration

        Args:
            config: Configuration dictionary

        Raises:
            ValueError: Invalid configuration
            RuntimeError: Initialization failed
        """
        # Extract configuration
        self.api_key = config.get("api_key", "")
        model = config.get("model", "whisper-large-v3-turbo")
        self.base_url = config.get("base_url", None)

        # Validate API key
        if not self.api_key or self.api_key.strip() == "":
            raise ValueError("Groq API key is required")

        # Validate model
        if model not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model '{model}'. Available: {self.AVAILABLE_MODELS}"
            )

        self.model = model
        self.model_name = model

        # Mark as loaded
        self._is_model_loaded = True

        app_logger.log_model_loading_step(
            "Groq provider initialized",
            {
                "model": self.model,
                "base_url": self.base_url or "default",
            },
        )
