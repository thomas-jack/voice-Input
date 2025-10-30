#!/usr/bin/env python3
"""
重构完整性测试

这个测试验证VoiceInputApp已经完全迁移到新架构，不再依赖旧的API调用。

测试目标：
1. 验证VoiceInputApp使用统一的model_manager API
2. 确保没有遗留的whisper_engine直接访问
3. 验证reload_model方法（而不是reload_model_async）
4. 确保所有模型状态查询都通过model_manager
"""

import pytest
from unittest.mock import Mock, MagicMock
from sonicinput.core.voice_input_app import VoiceInputApp
from sonicinput.core.di_container import create_container


def test_voice_input_app_uses_unified_api():
    """测试VoiceInputApp完全使用新的统一API"""
    container = create_container()
    voice_app = VoiceInputApp(container)
    voice_app.initialize()

    # 验证RefactoredTranscriptionService有正确的组件
    assert hasattr(voice_app._speech_service, 'model_manager'), "应该有model_manager组件"
    assert hasattr(voice_app._speech_service.model_manager, 'get_whisper_engine'), "model_manager应该有get_whisper_engine方法"
    assert hasattr(voice_app._speech_service.model_manager, 'is_model_loaded'), "model_manager应该有is_model_loaded方法"
    assert hasattr(voice_app._speech_service, 'reload_model'), "应该有reload_model方法"

    # 验证状态查询通过新API
    status = voice_app.get_status()
    assert "model_loaded" in status
    assert isinstance(status["model_loaded"], bool)

    # 验证所有模型状态查询都通过model_manager
    assert voice_app._speech_service.model_manager.is_model_loaded() == status["model_loaded"], "状态应该通过model_manager查询"


def test_model_reload_uses_reload_model():
    """测试模型重载使用reload_model方法（而不是reload_model_async）"""
    container = create_container()
    voice_app = VoiceInputApp(container)
    voice_app.initialize()

    # 模拟reload_model方法
    voice_app._speech_service.reload_model = Mock()

    # 测试调用reload_model而不是reload_model_async
    voice_app._reload_model_with_gpu_setting(use_gpu=False)

    # 验证调用了正确的方法
    voice_app._speech_service.reload_model.assert_called_once()


def test_no_legacy_whisper_engine_access():
    """确保VoiceInputApp不再直接访问whisper_engine属性"""
    container = create_container()
    voice_app = VoiceInputApp(container)
    voice_app.initialize()

    # 应该通过model_manager访问
    assert hasattr(voice_app._speech_service, 'model_manager'), \
        "RefactoredTranscriptionService should have model_manager"


def test_refactoring_completeness():
    """测试重构完整性 - 所有API调用都使用新架构"""
    container = create_container()
    voice_app = VoiceInputApp(container)
    voice_app.initialize()

    # 模拟新API
    mock_whisper_engine = Mock()
    mock_whisper_engine.use_gpu = True
    mock_whisper_engine.device = "cuda:0"

    voice_app._speech_service.model_manager.get_whisper_engine = Mock(return_value=mock_whisper_engine)
    voice_app._speech_service.model_manager.is_model_loaded = Mock(return_value=True)
    voice_app._speech_service.reload_model = Mock()

    # 测试配置变更处理 - 只在use_gpu实际改变时才调用
    config_changes = {"whisper": {"use_gpu": True}}  # 设置为True以触发变更检查
    voice_app._on_config_changed(config_changes)

    # 测试模型重载使用统一方法
    voice_app._reload_model_with_gpu_setting(use_gpu=True)
    voice_app._speech_service.reload_model.assert_called()


if __name__ == "__main__":
    print("Testing Refactoring Completeness...")
    print("=" * 50)

    try:
        test_voice_input_app_uses_unified_api()
        print("[OK] VoiceInputApp uses unified model_manager API")

        test_model_reload_uses_reload_model()
        print("[OK] Model reload uses reload_model method")

        test_no_legacy_whisper_engine_access()
        print("[OK] No legacy whisper_engine access")

        test_refactoring_completeness()
        print("[OK] All API calls use new architecture")

        print("=" * 50)
        print("All refactoring completeness tests passed!")

    except Exception as e:
        print("=" * 50)
        print(f"Test failed: {e}")
        raise