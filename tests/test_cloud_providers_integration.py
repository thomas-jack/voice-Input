"""Tests for cloud transcription providers integration (Groq, SiliconFlow)

Tests cover:
- Base URL customization
- Retry mechanism with exponential backoff
- Configuration loading and saving
- Factory pattern with custom parameters
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from sonicinput.speech.speech_service_factory import SpeechServiceFactory
from sonicinput.speech.groq_speech_service import GroqSpeechService
from sonicinput.speech.siliconflow_engine import SiliconFlowEngine


class TestGroqBaseURL:
    """Test Groq service with custom base URL"""

    def test_groq_default_base_url(self):
        """Test Groq service uses default base URL when None is provided"""
        service = GroqSpeechService(api_key="test_key", model="whisper-large-v3-turbo", base_url=None)
        assert service.base_url is None
        assert service.api_key == "test_key"

    def test_groq_custom_base_url(self):
        """Test Groq service accepts custom base URL"""
        custom_url = "https://custom-proxy.example.com/v1"
        service = GroqSpeechService(api_key="test_key", model="whisper-large-v3-turbo", base_url=custom_url)
        assert service.base_url == custom_url

    @patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
    def test_groq_client_initialization_with_custom_url(self, mock_import):
        """Test Groq client is initialized with custom base URL"""
        mock_groq_class = Mock()
        mock_import.return_value = mock_groq_class

        custom_url = "https://custom-proxy.example.com/v1"
        service = GroqSpeechService(api_key="test_key", base_url=custom_url)

        # Initialize client
        service._initialize_client()

        # Verify client was created with custom base_url
        mock_groq_class.assert_called_once_with(api_key="test_key", base_url=custom_url)


class TestSiliconFlowBaseURL:
    """Test SiliconFlow service with custom base URL"""

    def test_siliconflow_default_base_url(self):
        """Test SiliconFlow service uses default base URL when None is provided"""
        service = SiliconFlowEngine(api_key="test_key", model_name="FunAudioLLM/SenseVoiceSmall", base_url=None)
        assert service.base_url == "https://api.siliconflow.cn/v1"

    def test_siliconflow_custom_base_url(self):
        """Test SiliconFlow service accepts custom base URL"""
        custom_url = "https://custom-api.example.com/v1"
        service = SiliconFlowEngine(api_key="test_key", model_name="FunAudioLLM/SenseVoiceSmall", base_url=custom_url)
        assert service.base_url == custom_url

    def test_siliconflow_api_endpoint_uses_custom_url(self):
        """Test SiliconFlow uses custom base URL for API calls"""
        custom_url = "https://custom-api.example.com/v1"
        service = SiliconFlowEngine(api_key="test_key", base_url=custom_url)

        # Verify the base_url is used correctly
        assert service.base_url == custom_url
        expected_endpoint = f"{custom_url}/audio/transcriptions"
        assert expected_endpoint == f"{service.base_url}{service.TRANSCRIBE_ENDPOINT}"


class TestRetryMechanism:
    """Test retry mechanism with exponential backoff"""

    @patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_groq_retry_on_failure(self, mock_sleep, mock_import):
        """Test Groq service retries on API failure"""
        mock_groq_class = Mock()
        mock_client = Mock()
        mock_import.return_value = mock_groq_class
        mock_groq_class.return_value = mock_client

        # Simulate API failure then success
        mock_client.audio.transcriptions.create.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            Mock(text="Test transcription", language="en", segments=[])
        ]

        service = GroqSpeechService(api_key="test_key")
        service._client = mock_client

        audio_data = np.random.randn(16000).astype(np.float32)
        result = service.transcribe(audio_data, max_retries=3, retry_delay=0.1)

        # Should succeed after 2 retries
        assert result["text"] == "Test transcription"
        assert result["retry_count"] == 2
        assert mock_client.audio.transcriptions.create.call_count == 3

    @patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
    @patch('time.sleep')
    def test_groq_max_retries_exceeded(self, mock_sleep, mock_import):
        """Test Groq service stops after max retries"""
        mock_groq_class = Mock()
        mock_client = Mock()
        mock_import.return_value = mock_groq_class
        mock_groq_class.return_value = mock_client

        # Always fail
        mock_client.audio.transcriptions.create.side_effect = Exception("Network error")

        service = GroqSpeechService(api_key="test_key")
        service._client = mock_client

        audio_data = np.random.randn(16000).astype(np.float32)
        result = service.transcribe(audio_data, max_retries=2, retry_delay=0.1)

        # Should fail after 3 attempts (initial + 2 retries)
        assert result["text"] == ""
        assert result["error_code"] == "MAX_RETRIES_EXCEEDED"
        assert result["retry_count"] == 2
        assert mock_client.audio.transcriptions.create.call_count == 3

    def test_siliconflow_retry_parameters(self):
        """Test SiliconFlow service accepts retry parameters"""
        service = SiliconFlowEngine(api_key="test_key")

        # Verify transcribe method accepts retry parameters
        audio_data = np.random.randn(16000).astype(np.float32)

        # This will fail because no API key is valid, but we're testing that the parameters are accepted
        result = service.transcribe(audio_data, max_retries=2, retry_delay=0.05)

        # Should have error but retry parameters were accepted
        assert "error" in result or "text" in result
        # The method should have completed without raising exceptions about unknown parameters


class TestFactoryWithBaseURL:
    """Test factory pattern with base URL support"""

    def test_factory_create_groq_with_base_url(self):
        """Test factory creates Groq service with custom base URL"""
        custom_url = "https://custom.example.com/v1"
        service = SpeechServiceFactory.create_service(
            provider="groq",
            api_key="test_key",
            model="whisper-large-v3-turbo",
            base_url=custom_url
        )

        assert isinstance(service, GroqSpeechService)
        assert service.base_url == custom_url

    def test_factory_create_siliconflow_with_base_url(self):
        """Test factory creates SiliconFlow service with custom base URL"""
        custom_url = "https://custom.example.com/v1"
        service = SpeechServiceFactory.create_service(
            provider="siliconflow",
            api_key="test_key",
            model="FunAudioLLM/SenseVoiceSmall",
            base_url=custom_url
        )

        assert isinstance(service, SiliconFlowEngine)
        assert service.base_url == custom_url

    @patch('sonicinput.speech.speech_service_factory.SpeechServiceFactory._is_local_available')
    def test_factory_from_config_with_custom_groq_url(self, mock_local_available):
        """Test factory loads custom Groq base URL from config"""
        mock_local_available.return_value = False

        mock_config = Mock()
        mock_config.get_setting.side_effect = lambda key, default=None: {
            "transcription.provider": "groq",
            "transcription.groq.api_key": "test_key",
            "transcription.groq.model": "whisper-large-v3-turbo",
            "transcription.groq.base_url": "https://custom.example.com/v1"
        }.get(key, default)

        service = SpeechServiceFactory.create_from_config(mock_config)

        assert isinstance(service, GroqSpeechService)
        assert service.base_url == "https://custom.example.com/v1"

    @patch('sonicinput.speech.speech_service_factory.SpeechServiceFactory._is_local_available')
    def test_factory_from_config_default_url_uses_none(self, mock_local_available):
        """Test factory passes None for default base URL"""
        mock_local_available.return_value = False

        mock_config = Mock()
        mock_config.get_setting.side_effect = lambda key, default=None: {
            "transcription.provider": "groq",
            "transcription.groq.api_key": "test_key",
            "transcription.groq.model": "whisper-large-v3-turbo",
            "transcription.groq.base_url": "https://api.groq.com/openai/v1"  # Default URL
        }.get(key, default)

        service = SpeechServiceFactory.create_from_config(mock_config)

        assert isinstance(service, GroqSpeechService)
        # Should be None to use SDK default
        assert service.base_url is None


class TestConfigurationDefaults:
    """Test configuration defaults include new parameters"""

    def test_groq_config_has_base_url(self):
        """Test Groq configuration includes base_url"""
        from sonicinput.core.services.config.config_defaults import get_default_config

        config = get_default_config()
        groq_config = config["transcription"]["groq"]

        assert "base_url" in groq_config
        assert groq_config["base_url"] == "https://api.groq.com/openai/v1"
        assert "timeout" in groq_config
        assert "max_retries" in groq_config

    def test_siliconflow_config_has_base_url(self):
        """Test SiliconFlow configuration includes base_url"""
        from sonicinput.core.services.config.config_defaults import get_default_config

        config = get_default_config()
        siliconflow_config = config["transcription"]["siliconflow"]

        assert "base_url" in siliconflow_config
        assert siliconflow_config["base_url"] == "https://api.siliconflow.cn/v1"
        assert "timeout" in siliconflow_config
        assert "max_retries" in siliconflow_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
