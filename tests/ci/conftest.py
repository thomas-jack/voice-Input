"""
CI测试专用配置

这个模块提供了CI环境的pytest配置，包括：
1. 自定义标记定义
2. Mock fixtures
3. CI环境检测和配置
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, Mock
from pathlib import Path

# 添加src到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))


def pytest_configure(config):
    """配置pytest自定义标记"""
    config.addinivalue_line(
        "markers", "ci: 标记适合CI环境的测试"
    )
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试（使用Mock）"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试，在CI中可能跳过"
    )


@pytest.fixture(scope="session")
def ci_config():
    """CI环境配置fixture"""
    return {
        "mock_services": True,
        "skip_gpu": True,
        "skip_gui": True,
        "skip_network": True,
        "timeout": 30  # CI环境中较短的超时时间
    }


@pytest.fixture
def mock_config_service():
    """通用Mock配置服务"""
    mock_config = MagicMock()
    mock_config.get_setting.side_effect = lambda key, default=None: {
        "transcription.provider": "local",
        "transcription.local.model": "tiny",  # CI中使用最小模型
        "transcription.local.use_gpu": False,  # CI中禁用GPU
        "transcription.local.language": "en",
        "whisper.model": "tiny",
        "whisper.use_gpu": False,
        "whisper.language": "en",
        "ai.enabled": False,  # CI中禁用AI优化
        "logging.level": "WARNING",  # 减少CI日志输出
        "logging.console_output": False,
        "hotkeys": ["f9"],  # 简化热键配置
    }.get(key, default)

    mock_config.set_setting.return_value = True
    mock_config.save_config.return_value = True
    return mock_config


@pytest.fixture
def mock_audio_service():
    """Mock音频服务"""
    mock_audio = MagicMock()
    mock_audio.start_recording.return_value = True
    mock_audio.stop_recording.return_value = None
    mock_audio.get_audio_level.return_value = 0.5
    mock_audio.is_recording.return_value = False
    return mock_audio


@pytest.fixture
def mock_speech_service():
    """Mock语音转录服务"""
    mock_speech = MagicMock()
    mock_speech.transcribe.return_value = {
        "text": "CI test transcription",
        "language": "en",
        "duration": 1.0
    }
    mock_speech.is_model_loaded.return_value = True
    mock_speech.load_model.return_value = True
    mock_speech.reload_model.return_value = True
    return mock_speech


@pytest.fixture
def mock_input_service():
    """Mock输入服务"""
    mock_input = MagicMock()
    mock_input.input_text.return_value = True
    return mock_input


@pytest.fixture
def mock_event_service():
    """Mock事件服务"""
    mock_events = MagicMock()
    mock_events.subscribe.return_value = True
    mock_events.unsubscribe.return_value = True
    mock_events.publish.return_value = True
    return mock_events


# CI环境检查
def is_ci_environment():
    """检查是否在CI环境中运行"""
    return any([
        os.getenv("CI"),
        os.getenv("GITHUB_ACTIONS"),
        os.getenv("GITLAB_CI"),
        os.getenv("TRAVIS"),
        os.getenv("APPVEYOR"),
        os.getenv("JENKINS_URL"),
    ])


# 自动跳过不适合CI的测试
def pytest_collection_modifyitems(config, items):
    """根据环境自动修改测试收集"""

    # 在CI环境中，自动跳过一些标记的测试
    skip_ci = pytest.mark.skip(reason="Test not suitable for CI environment")
    skip_gpu = pytest.mark.skip(reason="GPU test skipped in CI")
    skip_gui = pytest.mark.skip(reason="GUI test skipped in CI")
    skip_slow = pytest.mark.skip(reason="Slow test skipped in CI")

    # 自动标记定义
    unit_marker = pytest.mark.unit
    integration_marker = pytest.mark.integration

    for item in items:
        # 根据文件路径自动添加标记
        if "unit/" in str(item.fspath):
            item.add_marker(unit_marker)
        elif "integration/" in str(item.fspath):
            item.add_marker(integration_marker)

        if is_ci_environment():
            # 在CI中跳过有PySide6依赖的测试文件
            if "test_event_listener_regression.py" in str(item.fspath):
                item.add_marker(skip_gui)
            if "test_refactoring_completeness.py" in str(item.fspath):
                item.add_marker(skip_gui)

            # 跳过需要完整DI容器的测试（需要PyAudio等Windows依赖）
            # 这些测试会尝试实例化所有服务，包括音频服务
            if item.name in [
                "test_di_container",
                "test_container_creation",
                "test_container_basic_functionality"
            ]:
                item.add_marker(pytest.mark.skip(
                    reason="DI container tests require Windows-specific dependencies (PyAudio, etc.)"
                ))

            # 跳过GPU测试
            if "gpu" in item.keywords:
                item.add_marker(skip_gpu)

            # 跳过GUI测试
            if "gui" in item.keywords:
                item.add_marker(skip_gui)

            # 跳过慢速测试
            if "slow" in item.keywords:
                item.add_marker(skip_slow)