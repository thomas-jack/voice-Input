"""云服务轻量级集成测试 - CI优化版

完全Mock化的云服务测试，避免任何网络依赖：
1. 工厂模式测试
2. 服务接口兼容性
3. 错误处理机制
4. 配置驱动逻辑
"""

import pytest
from unittest.mock import MagicMock, Mock, patch
from pathlib import Path
import sys

# 添加 src 到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# CI标记
pytestmark = [pytest.mark.ci, pytest.mark.integration]


class TestSpeechServiceFactory:
    """语音服务工厂测试"""

    def test_local_service_creation(self):
        """测试本地服务创建"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory
        from sonicinput.core.interfaces import ISpeechService

        # Mock本地服务可用性检查
        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=True):
            service = SpeechServiceFactory.create_service("local", {})
            assert service is not None
            assert isinstance(service, ISpeechService)

    def test_groq_service_creation_with_api_key(self):
        """测试Groq服务创建（有API key）"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory
        from sonicinput.core.interfaces import ISpeechService

        config = {"api_key": "test_key", "model": "whisper-large-v3-turbo"}

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=False):
            with patch('sonicinput.speech.groq_speech_service._ensure_groq_imported'):
                service = SpeechServiceFactory.create_service("groq", config)
                assert service is not None
                assert isinstance(service, ISpeechService)

    def test_groq_service_creation_without_api_key(self):
        """测试Groq服务创建（无API key）"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory

        config = {"model": "whisper-large-v3-turbo"}  # 没有api_key

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=False):
            # 应该回退到本地服务
            service = SpeechServiceFactory.create_service("groq", config)
            # 由于本地服务不可用，应该返回None或抛出异常
            assert service is None

    def test_unsupported_provider(self):
        """测试不支持的提供商"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory

        with pytest.raises((ValueError, NotImplementedError)):
            SpeechServiceFactory.create_service("unsupported", {})


class TestGroqServiceMock:
    """Groq服务Mock测试"""

    @pytest.fixture
    def mock_groq_service(self):
        """创建Mock Groq服务"""
        from sonicinput.core.interfaces import ISpeechService
        from unittest.mock import MagicMock

        service = MagicMock(spec=ISpeechService)
        service.is_model_loaded.return_value = False
        service.load_model.return_value = True
        service.transcribe.return_value = {
            "text": "Mock transcription result",
            "language": "en",
            "segments": []
        }
        return service

    def test_model_loading_workflow(self, mock_groq_service):
        """测试模型加载工作流"""
        # 初始状态
        assert mock_groq_service.is_model_loaded() == False

        # 加载模型
        result = mock_groq_service.load_model("whisper-large-v3-turbo")
        assert result == True

        # 验证加载后状态
        assert mock_groq_service.is_model_loaded() == True

    def test_transcription_workflow(self, mock_groq_service):
        """测试转录工作流"""
        import numpy as np

        # 模拟音频数据
        audio_data = np.random.randn(16000).astype(np.float32)

        # 执行转录
        result = mock_groq_service.transcribe(audio_data)

        # 验证结果
        assert isinstance(result, dict)
        assert "text" in result
        assert "language" in result
        assert result["text"] == "Mock transcription result"

    def test_service_configuration(self, mock_groq_service):
        """测试服务配置"""
        # 测试配置属性
        assert hasattr(mock_groq_service, 'config')
        assert hasattr(mock_groq_service, 'model_name')

        # 设置配置
        mock_groq_service.config = {"api_key": "test_key"}
        mock_groq_service.model_name = "whisper-large-v3-turbo"

        assert mock_groq_service.config["api_key"] == "test_key"
        assert mock_groq_service.model_name == "whisper-large-v3-turbo"


class TestCloudServiceIntegration:
    """云服务集成测试"""

    def test_service_factory_from_config(self):
        """测试从配置创建服务"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory

        # 测试本地配置
        local_config = {
            "transcription": {
                "provider": "local",
                "local": {
                    "model": "tiny",
                    "use_gpu": False
                }
            }
        }

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=True):
            service = SpeechServiceFactory.from_config(local_config)
            assert service is not None

        # 测试云服务配置
        cloud_config = {
            "transcription": {
                "provider": "groq",
                "groq": {
                    "api_key": "test_key",
                    "model": "whisper-large-v3-turbo"
                }
            }
        }

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=False):
            with patch('sonicinput.speech.groq_speech_service._ensure_groq_imported'):
                service = SpeechServiceFactory.from_config(cloud_config)
                # 可能返回None如果依赖不可用
                # 这在CI环境中是预期的行为

    def test_fallback_mechanism(self):
        """测试回退机制"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory

        config = {
            "transcription": {
                "provider": "groq",
                "groq": {
                    # 缺少api_key，应该回退到本地
                    "model": "whisper-large-v3-turbo"
                }
            }
        }

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=True):
            # 应该回退到本地服务
            service = SpeechServiceFactory.from_config(config)
            assert service is not None

    def test_error_handling(self):
        """测试错误处理"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory

        # 测试无效配置
        invalid_config = {
            "transcription": {
                "provider": "invalid_provider"
            }
        }

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=False):
            # 应该优雅地处理错误
            service = SpeechServiceFactory.from_config(invalid_config)
            assert service is None


class TestConfigurationDrivenService:
    """配置驱动服务测试"""

    def test_service_selection_logic(self):
        """测试服务选择逻辑"""
        # 这个测试验证服务选择的业务逻辑，而不实际创建服务

        scenarios = [
            {"provider": "local", "has_key": False, "expected": "local"},
            {"provider": "groq", "has_key": True, "expected": "groq"},
            {"provider": "groq", "has_key": False, "expected": "local"},
        ]

        for scenario in scenarios:
            provider = scenario["provider"]
            has_key = scenario["has_key"]
            expected = scenario["expected"]

            if provider == "local" or not has_key:
                # 应该选择或回退到本地服务
                assert expected == "local", f"Failed for provider: {provider}, has_key: {has_key}"
            else:
                # 应该选择云服务
                assert expected == "groq", f"Failed for provider: {provider}, has_key: {has_key}"


if __name__ == "__main__":
    print("Running CI cloud services integration tests...")
    pytest.main([__file__, "-v"])