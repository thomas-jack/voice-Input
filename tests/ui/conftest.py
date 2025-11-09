"""UI测试的配置和fixtures - 确保配置文件完全隔离"""
import pytest
import os
import json
from pathlib import Path
from unittest.mock import MagicMock, Mock
from PySide6.QtWidgets import QApplication


# ============= 配置隔离 Fixtures =============

@pytest.fixture
def isolated_config(tmp_path):
    """创建隔离的临时配置文件

    这个fixture确保测试永远不会修改真实的用户配置文件。
    每个测试都会得到一个独立的临时配置文件。
    """
    config_file = tmp_path / "test_config.json"

    # 创建默认测试配置
    default_config = {
        "hotkeys": ["f12"],
        "transcription": {
            "provider": "local",
            "local": {
                "model": "base",
                "language": "zh",
                "use_gpu": False,
                "device": "cpu"
            }
        },
        "ai": {
            "enabled": False,
            "provider": "groq"
        },
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "auto_stop_enabled": True,
            "max_recording_duration": 60
        },
        "logging": {
            "level": "WARNING",
            "console_output": False
        }
    }

    # 写入配置文件
    config_file.write_text(json.dumps(default_config, indent=2))

    return config_file


@pytest.fixture
def mock_config_service(isolated_config):
    """使用临时配置的 Mock ConfigService

    这个mock确保UI组件使用隔离的配置,不会触碰真实配置。
    """
    from sonicinput.core.services.config.config_service_refactored import RefactoredConfigService

    # 创建使用临时配置文件的ConfigService
    config_service = RefactoredConfigService(
        config_path=str(isolated_config),
        event_service=None  # UI测试不需要事件服务
    )

    return config_service


@pytest.fixture
def verify_real_config_untouched():
    """验证真实配置文件未被修改的辅助fixture"""
    real_config_path = Path(os.getenv("APPDATA", ".")) / "SonicInput" / "config.json"

    # 记录初始状态
    initial_state = {
        "exists": real_config_path.exists(),
        "mtime": real_config_path.stat().st_mtime if real_config_path.exists() else None,
        "content": real_config_path.read_text() if real_config_path.exists() else None
    }

    yield

    # 验证配置文件未被修改
    if initial_state["exists"]:
        assert real_config_path.exists(), "Real config file was deleted during test!"
        assert real_config_path.stat().st_mtime == initial_state["mtime"], \
            "Real config file was modified during test!"
        assert real_config_path.read_text() == initial_state["content"], \
            "Real config file content was changed during test!"


# ============= UI组件 Mock Services =============

@pytest.fixture
def mock_ui_services():
    """创建UI组件需要的Mock服务集合"""
    services = {
        "settings": MagicMock(),
        "model": MagicMock(),
        "event_service": MagicMock(),
        "audio_service": MagicMock(),
        "speech_service": MagicMock(),
        "input_service": MagicMock(),
    }

    # 配置常用的返回值
    services["settings"].get_setting = Mock(return_value=None)
    services["settings"].set_setting = Mock()
    services["model"].get_state = Mock(return_value={"recording": False})

    return services


# ============= RecordingOverlay Fixtures =============

@pytest.fixture
def recording_overlay(qtbot):
    """创建 RecordingOverlay 实例

    RecordingOverlay不需要配置服务,所以可以直接创建。
    """
    from sonicinput.ui.recording_overlay import RecordingOverlay

    # 重置单例以确保测试隔离
    RecordingOverlay._instance = None
    RecordingOverlay._initialized = False

    overlay = RecordingOverlay()
    qtbot.addWidget(overlay)  # 确保测试结束后自动清理

    yield overlay

    # 清理:确保overlay被隐藏和删除
    if overlay.isVisible():
        overlay.hide()
    overlay.deleteLater()


# ============= SettingsWindow Fixtures =============

@pytest.fixture
def settings_window(qtbot, mock_config_service):
    """创建 SettingsWindow 实例(使用隔离配置)

    这个fixture确保SettingsWindow使用临时配置,不会修改真实配置。
    """
    from sonicinput.ui.settings_window import SettingsWindow

    # 创建mock UI服务,但使用真实的配置服务方法
    mock_ui_settings_service = MagicMock()
    mock_ui_settings_service.config_path = mock_config_service.config_path

    # 使用真实配置服务的方法
    mock_ui_settings_service.get_setting = mock_config_service.get_setting
    mock_ui_settings_service.set_setting = mock_config_service.set_setting
    mock_ui_settings_service.get_all_settings = mock_config_service.get_all_settings
    mock_ui_settings_service.save_config = mock_config_service.save_config

    # Mock其他方法
    mock_event_service = MagicMock()
    mock_event_service.on = Mock()
    mock_event_service.emit = Mock()

    mock_ui_settings_service.get_event_service = Mock(return_value=mock_event_service)
    mock_ui_settings_service.get_transcription_service = Mock(return_value=None)
    mock_ui_settings_service.get_ai_processing_controller = Mock(return_value=None)

    mock_ui_model_service = MagicMock()
    mock_ui_model_service.get_state = Mock(return_value={"recording": False})

    # 创建设置窗口
    window = SettingsWindow(
        ui_settings_service=mock_ui_settings_service,
        ui_model_service=mock_ui_model_service
    )

    qtbot.addWidget(window)

    yield window

    # 清理
    window.close()
    window.deleteLater()


# ============= SystemTray Fixtures =============

@pytest.fixture
def system_tray_widget(qtbot, mock_config_service):
    """创建 SystemTray 组件(使用隔离配置)"""
    from sonicinput.ui.components.system_tray.tray_widget import TrayWidget

    tray = TrayWidget(config_service=mock_config_service)
    qtbot.addWidget(tray)

    yield tray

    # 清理
    tray.hide()
    tray.deleteLater()


# ============= pytest-qt 配置 =============

@pytest.fixture(scope="session")
def qapp_args():
    """配置QApplication参数用于测试"""
    return ["--platform", "offscreen"]  # 无头模式,不显示窗口


@pytest.fixture
def qtbot_wait_time():
    """配置qtbot的等待超时时间"""
    return 1000  # 1秒,适合快速测试
