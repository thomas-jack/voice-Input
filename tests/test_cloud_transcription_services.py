"""云转录服务测试

测试目标：
1. 验证 Groq 云转录服务的基本功能
2. 验证 SpeechServiceFactory 工厂模式
3. 验证配置驱动的服务创建
4. 验证错误处理和回退机制
5. 验证与本地服务的接口兼容性
"""

import pytest
import numpy as np
from unittest.mock import MagicMock, patch
from sonicinput.core.interfaces import ISpeechService
from sonicinput.speech.groq_speech_service import GroqSpeechService
from sonicinput.speech.speech_service_factory import SpeechServiceFactory
from sonicinput.core.services.config_service import ConfigService


# ============= Fixtures =============

@pytest.fixture
def mock_config():
    """Mock配置服务"""
    config = MagicMock(spec=ConfigService)

    # 默认本地配置
    config.get_setting.side_effect = lambda key, default=None: {
        # 转录配置
        "transcription.provider": "local",
        "transcription.local.model": "large-v3-turbo",
        "transcription.local.use_gpu": True,
        "transcription.local.language": "auto",

        # 兼容性配置
        "whisper.model": "large-v3-turbo",
        "whisper.use_gpu": True,
        "whisper.language": "auto",

        # Groq配置
        "transcription.groq.api_key": "test_api_key",
        "transcription.groq.model": "whisper-large-v3-turbo",

        # AI配置
        "ai.enabled": False,

    }.get(key, default)

    return config


@pytest.fixture
def mock_config_groq():
    """Mock Groq 配置"""
    config = MagicMock(spec=ConfigService)

    config.get_setting.side_effect = lambda key, default=None: {
        "transcription.provider": "groq",
        "transcription.local.model": "large-v3-turbo",
        "transcription.local.use_gpu": True,
        "transcription.groq.api_key": "test_api_key",
        "transcription.groq.model": "whisper-large-v3-turbo",
        "ai.enabled": False,
    }.get(key, default)

    return config


@pytest.fixture
def mock_config_no_api_key():
    """Mock 无API密钥的 Groq 配置"""
    config = MagicMock(spec=ConfigService)

    config.get_setting.side_effect = lambda key, default=None: {
        "transcription.provider": "groq",
        "transcription.groq.api_key": "",  # 空API密钥
        "transcription.groq.model": "whisper-large-v3-turbo",
        "transcription.local.model": "large-v3-turbo",
        "transcription.local.use_gpu": True,
        "ai.enabled": False,
    }.get(key, default)

    return config


@pytest.fixture
def sample_audio_data():
    """生成示例音频数据"""
    # 生成2秒的16kHz单通道音频数据
    sample_rate = 16000
    duration = 2.0  # 秒
    samples = int(sample_rate * duration)

    # 生成随机音频数据（int16格式）
    audio_data = np.random.randint(-32768, 32767, samples, dtype=np.int16)

    return audio_data


# ============= SpeechServiceFactory 测试 =============

def test_factory_create_local_service():
    """测试工厂创建本地服务"""
    service = SpeechServiceFactory.create_service(
        provider="local",
        model="large-v3-turbo",
        use_gpu=True
    )

    assert service is not None
    assert isinstance(service, ISpeechService)
    assert service.model_name == "large-v3-turbo"
    assert service.use_gpu == True


@patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
def test_factory_create_groq_service(mock_import):
    """测试工厂创建Groq服务"""
    # Mock Groq import
    mock_groq = MagicMock()
    mock_import.return_value = mock_groq

    service = SpeechServiceFactory.create_service(
        provider="groq",
        api_key="test_key",
        model="whisper-large-v3-turbo"
    )

    assert service is not None
    assert isinstance(service, GroqSpeechService)
    assert service.api_key == "test_key"
    assert service.model == "whisper-large-v3-turbo"
    assert service.device == "cloud"


def test_factory_groq_requires_api_key():
    """测试Groq服务需要API密钥"""
    with pytest.raises(ValueError, match="Groq provider requires API key"):
        SpeechServiceFactory.create_service(provider="groq", api_key="")


def test_factory_unsupported_provider():
    """测试不支持的provider"""
    with pytest.raises(ValueError, match="Unsupported speech provider"):
        SpeechServiceFactory.create_service(provider="unsupported")


def test_factory_from_config_local(mock_config):
    """测试从配置创建本地服务"""
    service = SpeechServiceFactory.create_from_config(mock_config)

    assert service is not None
    assert isinstance(service, ISpeechService)
    # 应该是本地服务（不是GroqSpeechService）
    assert not isinstance(service, GroqSpeechService)


@patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
def test_factory_from_config_groq(mock_import, mock_config_groq):
    """测试从配置创建Groq服务"""
    # Mock Groq import
    mock_groq = MagicMock()
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_import.return_value = mock_groq

    service = SpeechServiceFactory.create_from_config(mock_config_groq)

    assert service is not None
    assert isinstance(service, GroqSpeechService)
    assert service.api_key == "test_api_key"


def test_factory_from_config_no_api_key_fallback(mock_config_no_api_key):
    """测试无API密钥时回退到本地服务"""
    service = SpeechServiceFactory.create_from_config(mock_config_no_api_key)

    assert service is not None
    assert isinstance(service, ISpeechService)
    # 应该回退到本地服务
    assert not isinstance(service, GroqSpeechService)


def test_factory_local_fallback(mock_config_no_api_key):
    """测试本地回退功能"""
    service = SpeechServiceFactory.create_from_config_local_fallback(mock_config_no_api_key)

    assert service is not None
    assert isinstance(service, ISpeechService)
    assert not isinstance(service, GroqSpeechService)


# ============= GroqSpeechService 测试 =============

@pytest.fixture
@patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
def groq_service(mock_import):
    """创建Groq服务实例"""
    # Mock Groq import
    mock_groq = MagicMock()
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_import.return_value = mock_groq

    service = GroqSpeechService(api_key="test_key", model="whisper-large-v3-turbo")
    service._client = mock_client
    service._model_loaded = True

    return service, mock_client


def test_groq_service_initialization():
    """测试Groq服务初始化"""
    service = GroqSpeechService(api_key="test_key", model="whisper-large-v3")

    assert service.api_key == "test_key"
    assert service.model == "whisper-large-v3"
    assert service.model_name == "whisper-large-v3"  # 别名
    assert service.device == "cloud"
    assert service.use_gpu == False
    assert not service._model_loaded


def test_groq_available_models():
    """测试获取可用模型列表"""
    service = GroqSpeechService(api_key="test_key")
    models = service.get_available_models()

    assert "whisper-large-v3-turbo" in models
    assert "whisper-large-v3" in models
    assert len(models) == 2


def test_groq_load_model_success():
    """测试成功加载模型"""
    with patch('sonicinput.speech.groq_speech_service._ensure_groq_imported') as mock_import:
        mock_groq = MagicMock()
        mock_import.return_value = mock_groq

        service = GroqSpeechService(api_key="test_key")
        success = service.load_model()

        assert success == True
        assert service._model_loaded == True
        assert service._client is not None


def test_groq_load_model_no_api_key():
    """测试无API密钥时加载模型失败"""
    service = GroqSpeechService(api_key="")
    success = service.load_model()

    assert success == False
    assert service._model_loaded == False
    assert service._client is None


def test_groq_load_model_invalid_model():
    """测试加载无效模型"""
    service = GroqSpeechService(api_key="test_key", model="invalid-model")
    success = service.load_model("invalid-model")

    assert success == False


@patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
def test_groq_transcribe_success(mock_import, groq_service, sample_audio_data):
    """测试成功的转录"""
    service, mock_client = groq_service

    # Mock API响应
    mock_transcription = MagicMock()
    mock_transcription.text = "这是一个测试转录"
    mock_transcription.language = "zh"
    mock_transcription.segments = [
        {"start": 0.0, "end": 2.0, "text": "这是一个测试转录", "avg_logprob": -0.1, "no_speech_prob": 0.01}
    ]

    mock_client.audio.transcriptions.create.return_value = mock_transcription

    result = service.transcribe(sample_audio_data, language="zh")

    assert result["text"] == "这是一个测试转录"
    assert result["language"] == "zh"
    assert result["duration"] == len(sample_audio_data) / 16000.0
    assert result["processing_time"] > 0
    assert result["rtf"] >= 0
    assert len(result["segments"]) == 1

    # 验证API调用参数
    mock_client.audio.transcriptions.create.assert_called_once()
    call_args = mock_client.audio.transcriptions.create.call_args
    assert call_args[1]["model"] == "whisper-large-v3-turbo"
    assert call_args[1]["language"] == "zh"


@patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
def test_groq_transcribe_auto_language(mock_import, groq_service, sample_audio_data):
    """测试自动语言检测转录"""
    service, mock_client = groq_service

    # Mock API响应
    mock_transcription = MagicMock()
    mock_transcription.text = "Hello world"
    mock_transcription.language = "en"
    mock_transcription.segments = []

    mock_client.audio.transcriptions.create.return_value = mock_transcription

    # 不指定语言（auto-detect）
    result = service.transcribe(sample_audio_data, language=None)

    assert result["text"] == "Hello world"
    assert result["language"] == "en"

    # 验证API调用时language参数为None
    call_args = mock_client.audio.transcriptions.create.call_args
    assert call_args[1]["language"] is None


@patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
def test_groq_transcribe_api_error(mock_import, groq_service, sample_audio_data):
    """测试API错误处理"""
    service, mock_client = groq_service

    # Mock API错误
    mock_client.audio.transcriptions.create.side_effect = Exception("API Error")

    result = service.transcribe(sample_audio_data)

    assert result["text"] == ""
    assert result["error"] == "API Error"
    assert result["success"] == False
    assert result["rtf"] == 0.0


def test_groq_transcribe_model_not_loaded(sample_audio_data):
    """测试模型未加载时的转录"""
    service = GroqSpeechService(api_key="invalid_key")  # 使用无效API密钥
    # 不调用load_model()

    result = service.transcribe(sample_audio_data)

    assert result["text"] == ""
    assert "error" in result
    assert result["rtf"] == 0.0
    assert result["success"] == False


def test_groq_numpy_to_wav_conversion():
    """测试numpy数组到WAV转换"""
    service = GroqSpeechService(api_key="test_key")

    # 创建测试音频数据（int16）
    audio_data = np.array([1000, -1000, 2000, -2000], dtype=np.int16)

    wav_bytes = service._numpy_to_wav(audio_data)

    assert isinstance(wav_bytes, bytes)
    assert len(wav_bytes) > 0

    # 验证WAV格式基本结构（RIFF header）
    assert wav_bytes.startswith(b'RIFF')
    assert b'WAVE' in wav_bytes


def test_groq_numpy_to_wav_float_conversion():
    """测试float音频数据的转换"""
    service = GroqSpeechService(api_key="test_key")

    # 创建float音频数据
    audio_data = np.array([0.1, -0.1, 0.2, -0.2], dtype=np.float32)

    wav_bytes = service._numpy_to_wav(audio_data)

    assert isinstance(wav_bytes, bytes)
    assert len(wav_bytes) > 0


def test_groq_convert_segments_dict_format():
    """测试段格式转换（字典格式）"""
    service = GroqSpeechService(api_key="test_key")

    # Mock Groq响应（字典格式）
    mock_transcription = MagicMock()
    mock_transcription.segments = [
        {"start": 0.0, "end": 1.0, "text": "Hello", "avg_logprob": -0.1, "no_speech_prob": 0.01},
        {"start": 1.0, "end": 2.0, "text": "world", "avg_logprob": -0.2, "no_speech_prob": 0.02}
    ]

    segments = service._convert_segments(mock_transcription)

    assert len(segments) == 2
    assert segments[0]["text"] == "Hello"
    assert segments[1]["text"] == "world"
    assert segments[0]["start"] == 0.0
    assert segments[1]["end"] == 2.0


def test_groq_convert_segments_object_format():
    """测试段格式转换（对象格式）"""
    service = GroqSpeechService(api_key="test_key")

    # Mock Groq响应（对象格式）
    mock_seg1 = MagicMock()
    mock_seg1.start = 0.0
    mock_seg1.end = 1.0
    mock_seg1.text = "Hello"
    mock_seg1.avg_logprob = -0.1
    mock_seg1.no_speech_prob = 0.01

    mock_seg2 = MagicMock()
    mock_seg2.start = 1.0
    mock_seg2.end = 2.0
    mock_seg2.text = "world"
    mock_seg2.avg_logprob = -0.2
    mock_seg2.no_speech_prob = 0.02

    mock_transcription = MagicMock()
    mock_transcription.segments = [mock_seg1, mock_seg2]

    segments = service._convert_segments(mock_transcription)

    assert len(segments) == 2
    assert segments[0]["text"] == "Hello"
    assert segments[1]["text"] == "world"


def test_groq_convert_segments_no_segments():
    """测试无段时的转换"""
    service = GroqSpeechService(api_key="test_key")

    mock_transcription = MagicMock()
    mock_transcription.segments = None

    segments = service._convert_segments(mock_transcription)

    assert segments == []


def test_groq_unload_model():
    """测试卸载模型"""
    service = GroqSpeechService(api_key="test_key")
    service._client = MagicMock()
    service._model_loaded = True

    service.unload_model()

    assert service._client is None
    assert service._model_loaded == False


def test_groq_is_model_loaded_property():
    """测试is_model_loaded属性"""
    service = GroqSpeechService(api_key="test_key")

    # 云服务总是返回True（始终就绪）
    assert service.is_model_loaded == True


@patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
def test_groq_on_demand_initialization(mock_import, sample_audio_data):
    """测试按需初始化行为"""
    # Mock Groq import
    mock_groq = MagicMock()
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_import.return_value = mock_groq

    # Mock API响应
    mock_transcription = MagicMock()
    mock_transcription.text = "按需初始化测试"
    mock_transcription.language = "zh"
    mock_transcription.segments = []

    mock_client.audio.transcriptions.create.return_value = mock_transcription

    service = GroqSpeechService(api_key="test_key")

    # 初始状态客户端为空
    assert service._client is None
    assert service.is_model_loaded == True  # 云服务始终就绪

    # 转录时自动初始化客户端
    result = service.transcribe(sample_audio_data)

    # 验证客户端已初始化
    assert service._client is not None
    assert result["text"] == "按需初始化测试"

    # 验证API只调用一次
    mock_import.assert_called_once()
    mock_groq.assert_called_once_with(api_key="test_key")


@patch('sonicinput.speech.groq_speech_service._ensure_groq_imported')
def test_groq_pre_initialization_vs_on_demand(mock_import, sample_audio_data):
    """测试预初始化vs按需初始化的一致性"""
    mock_groq = MagicMock()
    mock_client = MagicMock()
    mock_groq.return_value = mock_client
    mock_import.return_value = mock_groq

    # Mock API响应
    mock_transcription = MagicMock()
    mock_transcription.text = "测试文本"
    mock_transcription.language = "zh"
    mock_transcription.segments = []

    mock_client.audio.transcriptions.create.return_value = mock_transcription

    # 测试1: 按需初始化
    service1 = GroqSpeechService(api_key="test_key")
    result1 = service1.transcribe(sample_audio_data)

    # 记录按需初始化的调用次数
    on_demand_calls = mock_import.call_count

    # 重置API转录mock（但保留import状态）
    mock_client.audio.transcriptions.create.reset_mock()

    # 测试2: 预初始化
    service2 = GroqSpeechService(api_key="test_key")
    service2.load_model()  # 预初始化
    assert service2._client is not None
    result2 = service2.transcribe(sample_audio_data)

    # 两种方式结果应该一致
    assert result1["text"] == result2["text"]
    assert result1["language"] == result2["language"]

    # 预初始化会额外调用一次import（在load_model时）
    assert mock_import.call_count == on_demand_calls + 1


def test_groq_is_model_loaded_property():
    """测试is_model_loaded属性"""
    service = GroqSpeechService(api_key="test_key")

    # 云服务总是返回True（始终就绪）
    assert service.is_model_loaded == True