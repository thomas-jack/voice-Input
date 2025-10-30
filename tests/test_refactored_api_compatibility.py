#!/usr/bin/env python3
"""
重构后API兼容性测试

这个测试验证VoiceInputApp正确使用了RefactoredTranscriptionService的新API，
而不是依赖旧的直接属性访问。

测试目标：
1. 验证VoiceInputApp使用新的model_manager API
2. 确保没有访问直接whisper_engine属性
3. 验证reload_model方法正常工作
4. 确保is_model_loaded通过model_manager访问
"""

import pytest
from unittest.mock import Mock, MagicMock
from sonicinput.core.voice_input_app import VoiceInputApp
from sonicinput.core.di_container import create_container


def test_voice_input_app_uses_new_api():
    """测试VoiceInputApp使用重构后的新API"""
    container = create_container()
    voice_app = VoiceInputApp(container)
    voice_app.initialize()

    # 验证RefactoredTranscriptionService有正确的组件
    assert hasattr(voice_app._speech_service, 'model_manager'), "应该有model_manager组件"
    assert hasattr(voice_app._speech_service.model_manager, 'get_whisper_engine'), "model_manager应该有get_whisper_engine方法"
    assert hasattr(voice_app._speech_service.model_manager, 'is_model_loaded'), "model_manager应该有is_model_loaded方法"
    assert hasattr(voice_app._speech_service, 'reload_model'), "应该有reload_model方法"

    # 验证状态查询使用新API
    status = voice_app.get_status()
    assert "model_loaded" in status
    assert isinstance(status["model_loaded"], bool)

    # 验证没有直接的whisper_engine属性
    assert not hasattr(voice_app._speech_service, 'whisper_engine'), "不应该有直接的whisper_engine属性"


def test_model_reload_uses_new_api():
    """测试模型重载使用新的reload_model方法"""
    container = create_container()
    voice_app = VoiceInputApp(container)
    voice_app.initialize()

    # 模拟新的reload_model方法
    voice_app._speech_service.reload_model = Mock()

    # 测试调用reload_model而不是reload_model_async
    voice_app._reload_model_with_gpu_setting(use_gpu=False)

    # 验证调用了正确的方法
    voice_app._speech_service.reload_model.assert_called_once()


def test_no_direct_whisper_engine_access():
    """确保没有直接访问whisper_engine属性"""
    container = create_container()
    voice_app = VoiceInputApp(container)
    voice_app.initialize()

    # RefactoredTranscriptionService不应该有whisper_engine属性
    assert not hasattr(voice_app._speech_service, 'whisper_engine'), \
        "RefactoredTranscriptionService should not expose whisper_engine directly"

    # 应该通过model_manager访问
    assert hasattr(voice_app._speech_service, 'model_manager'), \
        "RefactoredTranscriptionService should have model_manager"


def test_api_consistency():
    """测试API调用的一致性"""
    container = create_container()
    voice_app = VoiceInputApp(container)
    voice_app.initialize()

    # 模拟所有新API
    mock_whisper_engine = Mock()
    mock_whisper_engine.use_gpu = True
    mock_whisper_engine.device = "cuda:0"

    voice_app._speech_service.model_manager.get_whisper_engine = Mock(return_value=mock_whisper_engine)
    voice_app._speech_service.model_manager.is_model_loaded = Mock(return_value=True)
    voice_app._speech_service.reload_model = Mock()

    # 测试配置变更
    config_changes = {"whisper": {"use_gpu": False, "model": "base"}}
    voice_app._on_config_changed(config_changes)

    # 验证所有调用都使用新API
    voice_app._speech_service.model_manager.get_whisper_engine.assert_called()

    # 测试模型重载
    voice_app._reload_model_with_gpu(use_gpu=True)
    voice_app._speech_service.reload_model.assert_called()


if __name__ == "__main__":
    print("Testing Refactored API Compatibility...")
    print("=" * 50)

    try:
        test_voice_input_app_uses_new_api()
        print("[OK] VoiceInputApp uses new model_manager API")

        test_model_reload_uses_new_api()
        print("[OK] Model reload uses reload_model method")

        test_no_direct_whisper_engine_access()
        print("[OK] No direct whisper_engine access")

        test_api_consistency()
        print("[OK] API calls are consistent")

        print("=" * 50)
        print("All API compatibility tests passed!")

    except Exception as e:
        print("=" * 50)
        print(f"Test failed: {e}")
        raise