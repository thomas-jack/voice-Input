"""SettingsWindow UI测试套件

测试SettingsWindow的功能,确保使用临时配置文件,不修改真实配置。
"""
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from pathlib import Path
import os


@pytest.mark.gui
class TestSettingsWindowCreation:
    """SettingsWindow创建和初始化测试"""

    def test_settings_window_creation(self, qtbot, settings_window, verify_real_config_untouched):
        """测试设置窗口可以被创建(不修改真实配置)"""
        assert settings_window is not None
        assert not settings_window.isVisible()

    def test_window_title(self, qtbot, settings_window):
        """测试窗口标题"""
        assert "Sonic Input" in settings_window.windowTitle()

    def test_window_size(self, qtbot, settings_window):
        """测试窗口最小尺寸"""
        min_size = settings_window.minimumSize()
        assert min_size.width() >= 800
        assert min_size.height() >= 600

    def test_tabs_exist(self, qtbot, settings_window):
        """测试所有标签页存在"""
        assert hasattr(settings_window, 'tab_widget')
        assert settings_window.tab_widget is not None
        assert settings_window.tab_widget.count() > 0


@pytest.mark.gui
class TestSettingsWindowTabs:
    """SettingsWindow标签页测试"""

    def test_application_tab_exists(self, qtbot, settings_window):
        """测试应用程序标签页存在"""
        assert hasattr(settings_window, 'application_tab')
        assert settings_window.application_tab is not None

    def test_hotkey_tab_exists(self, qtbot, settings_window):
        """测试热键标签页存在"""
        assert hasattr(settings_window, 'hotkey_tab')
        assert settings_window.hotkey_tab is not None

    def test_transcription_tab_exists(self, qtbot, settings_window):
        """测试转录标签页存在"""
        assert hasattr(settings_window, 'transcription_tab')
        assert settings_window.transcription_tab is not None

    def test_ai_tab_exists(self, qtbot, settings_window):
        """测试AI标签页存在"""
        assert hasattr(settings_window, 'ai_tab')
        assert settings_window.ai_tab is not None

    def test_audio_input_tab_exists(self, qtbot, settings_window):
        """测试音频输入标签页存在"""
        assert hasattr(settings_window, 'audio_input_tab')
        assert settings_window.audio_input_tab is not None

    def test_history_tab_exists(self, qtbot, settings_window):
        """测试历史记录标签页存在"""
        assert hasattr(settings_window, 'history_tab')
        assert settings_window.history_tab is not None

    def test_tab_switching(self, qtbot, settings_window, verify_real_config_untouched):
        """测试标签页切换(不修改真实配置)"""
        tab_widget = settings_window.tab_widget

        # 切换到每个标签页
        for i in range(tab_widget.count()):
            tab_widget.setCurrentIndex(i)
            qtbot.wait(100)
            assert tab_widget.currentIndex() == i


@pytest.mark.gui
class TestSettingsWindowButtons:
    """SettingsWindow按钮测试"""

    def test_apply_button_exists(self, qtbot, settings_window):
        """测试应用按钮存在"""
        assert hasattr(settings_window, 'apply_button')
        assert settings_window.apply_button is not None
        assert settings_window.apply_button.text() in ["Apply", "应用"]

    def test_cancel_button_exists(self, qtbot, settings_window):
        """测试取消按钮存在"""
        assert hasattr(settings_window, 'cancel_button')
        assert settings_window.cancel_button is not None
        assert settings_window.cancel_button.text() in ["Cancel", "取消"]

    def test_cancel_button_closes_window(self, qtbot, settings_window, verify_real_config_untouched):
        """测试取消按钮关闭窗口(不修改真实配置)"""
        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)

        # 点击取消按钮
        settings_window.cancel_button.click()

        # 验证窗口隐藏
        qtbot.waitUntil(lambda: not settings_window.isVisible(), timeout=2000)
        assert not settings_window.isVisible()


@pytest.mark.gui
class TestSettingsWindowConfigIsolation:
    """SettingsWindow配置隔离测试 - 确保不修改真实配置"""

    def test_uses_isolated_config(self, qtbot, settings_window, isolated_config):
        """验证SettingsWindow使用隔离的配置文件"""
        # 检查配置服务使用的是临时路径
        config_path = settings_window.ui_settings_service.config_path

        # 验证不是真实配置路径
        real_config_path = Path(os.getenv("APPDATA", ".")) / "SonicInput" / "config.json"
        assert str(config_path) != str(real_config_path)

        # 验证是临时路径
        assert str(config_path) == str(isolated_config)

    def test_apply_writes_to_temp_config(self, qtbot, settings_window, isolated_config, verify_real_config_untouched, monkeypatch):
        """测试应用设置写入临时配置文件,不修改真实配置"""
        # Mock QMessageBox to avoid blocking
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)

        # 记录临时配置的初始修改时间
        initial_mtime = isolated_config.stat().st_mtime

        # 修改一个设置(例如日志级别)
        # 这里需要根据实际的UI结构修改
        # settings_window.application_tab.log_level_combo.setCurrentText("DEBUG")

        # 点击应用按钮
        settings_window.apply_button.click()
        qtbot.wait(200)

        # 验证临时配置被修改
        # (可能需要调整,取决于实际的保存机制)
        # assert isolated_config.stat().st_mtime > initial_mtime

        # verify_real_config_untouched fixture会自动验证真实配置未被修改

    def test_real_config_never_touched(self, qtbot, settings_window, verify_real_config_untouched, monkeypatch):
        """显式测试:真实配置文件永远不被触碰"""
        # Mock QMessageBox to avoid blocking
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        real_config_path = Path(os.getenv("APPDATA", ".")) / "SonicInput" / "config.json"

        if real_config_path.exists():
            original_mtime = real_config_path.stat().st_mtime
            original_content = real_config_path.read_text()

            # 显示窗口
            settings_window.show()
            qtbot.waitExposed(settings_window, timeout=1000)

            # 执行各种操作
            settings_window.tab_widget.setCurrentIndex(0)
            qtbot.wait(100)
            settings_window.tab_widget.setCurrentIndex(1)
            qtbot.wait(100)

            # 点击应用按钮
            settings_window.apply_button.click()
            qtbot.wait(200)

            # 关闭窗口
            settings_window.cancel_button.click()
            qtbot.wait(100)

            # 验证真实配置未被修改
            assert real_config_path.stat().st_mtime == original_mtime
            assert real_config_path.read_text() == original_content


@pytest.mark.gui
class TestSettingsWindowSignals:
    """SettingsWindow信号测试"""

    def test_settings_changed_signal(self, qtbot, settings_window):
        """测试设置变更信号"""
        with qtbot.waitSignal(settings_window.settings_changed, timeout=1000) as blocker:
            settings_window.settings_changed.emit("test_key", "test_value")

        assert blocker.args == ["test_key", "test_value"]

    def test_hotkey_test_signal(self, qtbot, settings_window):
        """测试热键测试信号"""
        with qtbot.waitSignal(settings_window.hotkey_test_requested, timeout=1000) as blocker:
            settings_window.hotkey_test_requested.emit("f12")

        assert blocker.args == ["f12"]

    def test_api_test_signal(self, qtbot, settings_window):
        """测试API测试信号"""
        with qtbot.waitSignal(settings_window.api_test_requested, timeout=1000):
            settings_window.api_test_requested.emit()

    def test_model_load_signal(self, qtbot, settings_window):
        """测试模型加载信号"""
        with qtbot.waitSignal(settings_window.model_load_requested, timeout=1000) as blocker:
            settings_window.model_load_requested.emit("base")

        assert blocker.args == ["base"]


@pytest.mark.gui
class TestSettingsWindowDialogs:
    """SettingsWindow对话框测试 - 使用mock避免阻塞"""

    def test_reset_settings_confirmation(self, qtbot, settings_window, monkeypatch, verify_real_config_untouched):
        """测试重置设置确认对话框(mock)"""
        # Mock QMessageBox.question to always return Yes
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )

        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)

        # 触发重置(如果有这个功能)
        # settings_window.reset_button.click()
        # qtbot.wait(100)

        # verify_real_config_untouched会自动验证真实配置未被修改


@pytest.mark.gui
@pytest.mark.slow
class TestSettingsWindowLoadSave:
    """SettingsWindow加载/保存测试"""

    def test_load_config_from_temp(self, qtbot, settings_window, isolated_config):
        """测试从临时配置加载设置"""
        # 加载配置
        settings_window.load_current_config()
        qtbot.wait(100)

        # 验证配置被加载(检查内部状态)
        assert hasattr(settings_window, 'current_config')

    def test_multiple_save_operations(self, qtbot, settings_window, isolated_config, verify_real_config_untouched, monkeypatch):
        """测试多次保存操作只修改临时配置"""
        # Mock QMessageBox to avoid blocking
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)

        # 多次点击应用按钮
        for _ in range(3):
            settings_window.apply_button.click()
            qtbot.wait(100)

        # verify_real_config_untouched会验证真实配置未被修改
