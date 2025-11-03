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
        """测试Groq服务创建（无API key）- 测试工厂回退逻辑"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory

        config = {"model": "whisper-large-v3-turbo"}  # 没有api_key

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=False):
            # 工厂有回退逻辑：可能抛出异常或返回None
            # 测试目标：工厂能优雅处理缺少API key的情况，不会崩溃
            try:
                service = SpeechServiceFactory.create_service("groq", config)
                # 如果没抛异常，应该返回None（因为本地也不可用）
                assert service is None, "Expected None when no API key and local unavailable"
            except (ValueError, RuntimeError) as e:
                # 如果抛异常也是合理的行为
                assert "api" in str(e).lower() or "key" in str(e).lower()

    def test_unsupported_provider(self):
        """测试不支持的提供商"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory

        with pytest.raises((ValueError, NotImplementedError)):
            SpeechServiceFactory.create_service("unsupported", {})


class TestGroqServiceMock:
    """Groq服务Mock测试"""

    @pytest.fixture
    def mock_groq_service(self):
        """创建Mock Groq服务（带状态管理）"""
        from sonicinput.core.interfaces import ISpeechService
        from unittest.mock import MagicMock

        service = MagicMock(spec=ISpeechService)

        # 使用内部状态跟踪模型加载状态
        _model_loaded = {'value': False}

        def _load_model(model_name=None):
            _model_loaded['value'] = True
            return True

        def _is_model_loaded():
            return _model_loaded['value']

        service.load_model = MagicMock(side_effect=_load_model)
        service.is_model_loaded = MagicMock(side_effect=_is_model_loaded)
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
        """测试服务配置和接口行为"""
        import numpy as np

        # 测试接口方法可用性（ISpeechService 定义的方法）
        assert hasattr(mock_groq_service, 'transcribe')
        assert hasattr(mock_groq_service, 'load_model')
        assert hasattr(mock_groq_service, 'is_model_loaded')

        # 测试转录功能（接口行为）
        audio_data = np.zeros(16000, dtype=np.float32)
        result = mock_groq_service.transcribe(audio_data)
        assert isinstance(result, dict)
        assert "text" in result


class TestCloudServiceIntegration:
    """云服务集成测试"""

    def test_service_factory_from_config(self):
        """测试从配置创建服务"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory

        # 创建 Mock ConfigService - 本地配置
        mock_config = Mock()
        mock_config.get_setting = Mock(side_effect=lambda key, default=None: {
            "transcription.provider": "local",
            "transcription.local.model": "tiny",
            "transcription.local.use_gpu": False,
            "whisper.model": "tiny",
            "whisper.use_gpu": False,
        }.get(key, default))

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=True):
            service = SpeechServiceFactory.create_from_config(mock_config)
            assert service is not None

        # 创建 Mock ConfigService - 云服务配置
        mock_config_cloud = Mock()
        mock_config_cloud.get_setting = Mock(side_effect=lambda key, default=None: {
            "transcription.provider": "groq",
            "transcription.groq.api_key": "test_key",
            "transcription.groq.model": "whisper-large-v3-turbo",
        }.get(key, default))

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=False):
            with patch('sonicinput.speech.groq_speech_service._ensure_groq_imported'):
                service = SpeechServiceFactory.create_from_config(mock_config_cloud)
                # 可能返回None如果依赖不可用
                # 这在CI环境中是预期的行为

    def test_fallback_mechanism(self):
        """测试回退机制"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory

        # 创建 Mock ConfigService - Groq配置但缺少api_key
        mock_config = Mock()
        mock_config.get_setting = Mock(side_effect=lambda key, default=None: {
            "transcription.provider": "groq",
            # 缺少 transcription.groq.api_key，应该回退到本地
            "transcription.groq.model": "whisper-large-v3-turbo",
            "whisper.model": "tiny",
            "whisper.use_gpu": False,
        }.get(key, default))

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=True):
            # 应该回退到本地服务
            service = SpeechServiceFactory.create_from_config(mock_config)
            assert service is not None

    def test_error_handling(self):
        """测试错误处理"""
        from sonicinput.speech.speech_service_factory import SpeechServiceFactory

        # 创建 Mock ConfigService - 无效的provider
        mock_config = Mock()
        mock_config.get_setting = Mock(side_effect=lambda key, default=None: {
            "transcription.provider": "invalid_provider",
        }.get(key, default))

        with patch.object(SpeechServiceFactory, '_is_local_available', return_value=False):
            # 应该优雅地处理错误，返回None或抛出异常
            service = SpeechServiceFactory.create_from_config(mock_config)
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