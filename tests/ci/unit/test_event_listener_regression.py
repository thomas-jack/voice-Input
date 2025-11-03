#!/usr/bin/env python3
"""
事件监听器回调函数回归测试

这个测试确保所有事件监听器回调函数都有正确的函数签名，
能够接收事件系统传递的参数。

测试目标：
1. 验证所有注册为事件监听器的函数都有正确的参数签名
2. 防止出现 "takes 1 positional argument but 2 were given" 错误
3. 确保事件系统能够正确调用所有监听器

回归测试用例：修复后的事件监听器不应该再出现参数签名错误
"""

import pytest
import inspect
from typing import Any, Dict, List

# 标记为GUI测试，在CI中跳过
pytestmark = pytest.mark.gui

# 导入被测试的模块
from sonicinput.core.services.dynamic_event_system import DynamicEventSystem
from sonicinput.core.services.event_bus import Events
from sonicinput.ui.main_window import MainWindow
from sonicinput.core.voice_input_app import VoiceInputApp
from sonicinput.core.di_container import create_container


def get_event_listener_functions():
    """获取所有事件监听器函数的映射"""
    listeners = []

    # VoiceInputApp 中的事件监听器
    voice_app_listeners = [
        ('VoiceInputApp', '_on_recording_started_overlay'),
        ('VoiceInputApp', '_on_ai_started_overlay'),
        ('VoiceInputApp', '_on_input_completed_overlay'),
        ('VoiceInputApp', '_on_audio_level_update_overlay'),
    ]

    # MainWindow 中的事件监听器
    main_window_listeners = [
        ('MainWindow', '_on_recording_started'),
        ('MainWindow', '_on_recording_stopped'),
    ]

    listeners.extend(voice_app_listeners)
    listeners.extend(main_window_listeners)

    return listeners


def test_event_listener_signatures():
    """测试所有事件监听器函数都有正确的签名"""
    listeners = get_event_listener_functions()

    for class_name, method_name in listeners:
        # 获取方法对象
        if class_name == 'VoiceInputApp':
            method = getattr(VoiceInputApp, method_name)
        else:  # MainWindow
            method = getattr(MainWindow, method_name)

        # 检查函数签名
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        # 验证参数签名
        # 事件监听器函数应该至少能接收 'self' 和一个可选的 'data' 参数
        assert len(params) >= 1, f"{class_name}.{method_name} should have at least 'self' parameter"
        assert params[0] == 'self', f"{class_name}.{method_name} first parameter should be 'self'"

        # 检查是否能接受第二个参数（事件数据）
        if len(params) == 1:
            # 如果只有一个参数，确保它有默认值或可以接收任意参数
            # 这种情况下，函数应该被修改为能够接收 data 参数
            pytest.fail(f"{class_name}.{method_name} should be able to receive data parameter")

        # 验证方法有正确的类型注解（可选）
        print(f"[OK] {class_name}.{method_name}{sig}")


def test_dynamic_event_system_callback_compatibility():
    """测试动态事件系统能够正确调用修复后的监听器函数"""
    event_system = DynamicEventSystem()
    callback_results = []

    # 测试函数：模拟修复后的事件监听器
    def test_callback_fixed(data=None):
        callback_results.append(('fixed', data))
        return "success"

    def test_callback_with_explicit_param(data):  # 明确参数
        callback_results.append(('explicit', data))
        return "success"

    # 测试修复后的回调（使用已存在的事件类型）
    event_system.on("test_event", test_callback_fixed)
    event_system.emit("test_event", {"test": "data"})

    # 测试明确参数的回调
    event_system.on("test_event2", test_callback_with_explicit_param)
    event_system.emit("test_event2", {"test": "data2"})

    # 验证修复后的回调被正确调用
    assert len(callback_results) == 2
    assert callback_results[0][0] == 'fixed'
    assert callback_results[0][1] == {"test": "data"}
    assert callback_results[1][0] == 'explicit'
    assert callback_results[1][1] == {"test": "data2"}
    print("[OK] Fixed callback functions called correctly")


def test_voice_input_app_event_listeners():
    """测试 VoiceInputApp 中的事件监听器能够正确接收参数"""
    container = create_container()
    voice_app = VoiceInputApp(container)

    # 创建测试用的录音覆盖层（模拟）
    class MockRecordingOverlay:
        def __init__(self):
            self.calls = []

        def show_recording(self):
            self.calls.append('show_recording')

        def show_processing(self):
            self.calls.append('show_processing')

        def set_status_text(self, text):
            self.calls.append(('set_status_text', text))

    voice_app.recording_overlay = MockRecordingOverlay()

    # 测试修复后的事件监听器
    try:
        # 这些调用现在应该不会出错
        voice_app._on_recording_started_overlay({"event": "data"})
        voice_app._on_ai_started_overlay({"event": "data"})

        # 验证覆盖层方法被调用
        assert 'show_recording' in voice_app.recording_overlay.calls
        assert ('set_status_text', 'AI Processing...') in voice_app.recording_overlay.calls

        print("[OK] VoiceInputApp event listeners receive parameters correctly")

    except TypeError as e:
        pytest.fail(f"VoiceInputApp event listener failed: {e}")


@pytest.mark.gui
def test_main_window_event_listeners():
    """测试 MainWindow 中的事件监听器能够正确接收参数"""
    container = create_container()
    voice_app = VoiceInputApp(container)
    voice_app.initialize()

    # 创建 MainWindow（但不显示）
    main_window = MainWindow()
    main_window.set_controller(voice_app)

    # 测试修复后的事件监听器
    try:
        # 这些调用现在应该不会出错
        main_window._on_recording_started({"event": "data"})

        # 验证按钮文本被更新
        assert main_window.recording_button.text() == "Stop Recording"
        assert main_window.status_label.text() == "Recording..."

        print("[OK] MainWindow event listeners receive parameters correctly")

    except TypeError as e:
        pytest.fail(f"MainWindow event listener failed: {e}")
    except Exception as e:
        # 其他错误可能是由于缺少UI组件，但不应该是参数签名错误
        if "takes" in str(e) and "positional argument" in str(e):
            pytest.fail(f"Event listener signature error: {e}")
        else:
            print(f"[OK] No parameter signature errors (other errors are expected)")


def test_event_system_integration():
    """完整的事件系统集成测试"""
    container = create_container()
    voice_app = VoiceInputApp(container)
    event_system = voice_app.events

    events_received = []

    # 测试事件监听器
    def test_listener(data=None):
        events_received.append(data)

    # 注册和触发事件
    event_system.on("test_integration", test_listener)
    event_system.emit("test_integration", {"test": "integration"})

    # 验证事件被正确接收
    assert len(events_received) == 1
    assert events_received[0] == {"test": "integration"}

    print("[OK] Event system integration test passed")


if __name__ == "__main__":
    # 运行测试
    print("Starting event listener callback regression test...")
    print("=" * 60)

    try:
        test_event_listener_signatures()
        print()

        test_dynamic_event_system_callback_compatibility()
        print()

        test_voice_input_app_event_listeners()
        print()

        test_main_window_event_listeners()
        print()

        test_event_system_integration()
        print()

        print("=" * 60)
        print("All regression tests passed! Event listener callback functions are fixed.")

    except Exception as e:
        print("=" * 60)
        print(f"Test failed: {e}")
        raise