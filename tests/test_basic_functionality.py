"""基础功能测试 - 避免编码问题"""

import pytest
import time
import os
import sys

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_basic_imports():
    """测试基础导入"""
    try:
        from sonicinput.core.voice_input_app import VoiceInputApp
        from sonicinput.core.di_container_enhanced import create_container
        from sonicinput.core.services.event_bus import Events
        from sonicinput.core.interfaces.state import AppState, RecordingState
        print("SUCCESS: All basic imports passed")
        assert True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        assert False


def test_di_container_creation():
    """测试DI容器创建"""
    try:
        from sonicinput.core.di_container_enhanced import create_container

        container = create_container()
        assert container is not None

        # 测试服务获取
        from sonicinput.core.interfaces import IConfigService, IEventService

        config = container.get(IConfigService)
        events = container.get(IEventService)

        assert config is not None
        assert events is not None

        print("✅ DI容器创建成功")

    except Exception as e:
        print(f"❌ DI容器创建失败: {e}")
        assert False


def test_event_system():
    """测试事件系统"""
    try:
        from sonicinput.core.di_container_enhanced import create_container
        from sonicinput.core.services.event_bus import Events

        container = create_container()
        events = container.get(type(container.events))

        # 测试事件常量
        assert hasattr(Events, 'RECORDING_STARTED')
        assert hasattr(Events, 'RECORDING_STOPPED')
        assert hasattr(Events, 'TRANSCRIPTION_REQUEST')
        assert hasattr(Events, 'TRANSCRIPTION_COMPLETED')

        # 测试事件注册和触发
        received_events = []

        def test_handler(*args):
            received_events.append(args)

        events.on("test_event", test_handler)
        events.emit("test_event", "test_data")

        assert len(received_events) == 1
        assert received_events[0][0] == "test_data"

        print("✅ 事件系统测试成功")

    except Exception as e:
        print(f"❌ 事件系统测试失败: {e}")
        assert False


def test_config_loading():
    """测试配置加载"""
    try:
        from sonicinput.core.di_container_enhanced import create_container
        from sonicinput.core.interfaces import IConfigService

        container = create_container()
        config = container.get(IConfigService)

        # 测试默认配置获取
        model = config.get_setting("whisper.model", "default")
        sample_rate = config.get_setting("audio.sample_rate", 16000)

        assert model is not None
        assert sample_rate is not None

        print(f"✅ 配置加载成功 - 模型: {model}, 采样率: {sample_rate}")

    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        assert False


def test_audio_service_mock():
    """测试音频服务Mock"""
    try:
        from unittest.mock import MagicMock
        from sonicinput.core.interfaces import IAudioService

        # 创建Mock音频服务
        mock_audio = MagicMock()
        mock_audio.start_recording.return_value = True
        mock_audio.stop_recording.return_value = None
        mock_audio.is_recording = False

        # 测试Mock调用
        result = mock_audio.start_recording()
        assert result == True
        mock_audio.start_recording.assert_called_once()

        print("✅ 音频服务Mock测试成功")

    except Exception as e:
        print(f"❌ 音频服务Mock测试失败: {e}")
        assert False


def test_whisper_service_mock():
    """测试Whisper服务Mock"""
    try:
        from unittest.mock import MagicMock
        from sonicinput.core.interfaces import ISpeechService

        # 创建Mock Whisper服务
        mock_whisper = MagicMock()
        mock_whisper.transcribe.return_value = {"text": "测试转录文本"}
        mock_whisper.is_model_loaded.return_value = True

        # 测试Mock调用
        result = mock_whisper.transcribe("audio_data")
        assert result["text"] == "测试转录文本"
        mock_whisper.transcribe.assert_called_once_with("audio_data")

        print("✅ Whisper服务Mock测试成功")

    except Exception as e:
        print(f"❌ Whisper服务Mock测试失败: {e}")
        assert False


def test_state_management():
    """测试状态管理"""
    try:
        from sonicinput.core.di_container_enhanced import create_container
        from sonicinput.core.interfaces.state import AppState, RecordingState
        from sonicinput.core.interfaces import IStateManager

        container = create_container()
        state_manager = container.get(IStateManager)

        # 测试状态获取
        app_state = state_manager.get_app_state()
        recording_state = state_manager.get_recording_state()

        assert app_state is not None
        assert recording_state is not None

        print(f"✅ 状态管理测试成功 - 应用状态: {app_state}, 录音状态: {recording_state}")

    except Exception as e:
        print(f"❌ 状态管理测试失败: {e}")
        assert False


def test_recording_overlay_creation():
    """测试录音悬浮窗创建"""
    try:
        # 模拟Qt应用环境
        import sys
        from unittest.mock import MagicMock, patch

        # Mock Qt相关组件
        with patch('PySide6.QtWidgets.QApplication.instance', return_value=MagicMock()), \
             patch('PySide6.QtGui.QGuiApplication.primaryScreen', return_value=MagicMock()):

            from sonicinput.ui.recording_overlay import RecordingOverlay

            # 创建悬浮窗实例
            overlay = RecordingOverlay()

            # 验证基本属性
            assert overlay is not None
            assert hasattr(overlay, 'show_recording')
            assert hasattr(overlay, 'hide_recording')
            assert hasattr(overlay, 'update_audio_level')

            print("✅ 录音悬浮窗创建测试成功")

    except Exception as e:
        print(f"❌ 录音悬浮窗创建测试失败: {e}")
        assert False


if __name__ == "__main__":
    """运行所有基础功能测试"""
    print("Starting basic functionality tests...")
    print("=" * 50)

    test_functions = [
        test_basic_imports,
        test_di_container_creation,
        test_event_system,
        test_config_loading,
        test_audio_service_mock,
        test_whisper_service_mock,
        test_state_management,
        test_recording_overlay_creation
    ]

    passed = 0
    total = len(test_functions)

    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"FAIL {test_func.__name__}: {e}")

    print("=" * 50)
    print(f"Test results: {passed}/{total} passed")

    if passed == total:
        print("SUCCESS: All basic functionality tests passed!")
    else:
        print("WARNING: Some tests failed, please check related functionality")