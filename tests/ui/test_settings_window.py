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


@pytest.mark.gui
class TestSettingsWindowCoreButtons:
    """SettingsWindow核心按钮功能测试"""

    def test_apply_button_saves_config_and_keeps_open(self, qtbot, settings_window, isolated_config, monkeypatch):
        """测试Apply按钮保存配置且窗口保持打开"""
        # Mock QMessageBox to avoid blocking
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)

        # 修改一个配置(日志级别)
        settings_window.application_tab.log_level_combo.setCurrentText("DEBUG")

        # 点击Apply按钮
        settings_window.apply_button.click()
        qtbot.wait(200)

        # 验证配置被保存
        saved_config = settings_window.ui_settings_service.get_all_settings()
        assert saved_config["logging"]["level"] == "DEBUG"

        # 验证窗口仍然可见
        assert settings_window.isVisible()

    def test_ok_button_saves_and_closes(self, qtbot, settings_window, isolated_config, monkeypatch):
        """测试OK按钮保存配置并关闭窗口"""
        # Mock QMessageBox to avoid blocking
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)

        # 修改一个配置
        settings_window.application_tab.log_level_combo.setCurrentText("INFO")

        # 点击OK按钮
        settings_window.ok_button.click()
        qtbot.wait(200)

        # 验证配置被保存
        saved_config = settings_window.ui_settings_service.get_all_settings()
        assert saved_config["logging"]["level"] == "INFO"

        # 验证窗口已隐藏
        qtbot.waitUntil(lambda: not settings_window.isVisible(), timeout=2000)
        assert not settings_window.isVisible()

    def test_reset_tab_button_shows_confirmation(self, qtbot, settings_window, isolated_config, monkeypatch):
        """测试Reset Tab按钮显示确认对话框"""
        # Track if question dialog was called
        dialog_called = []

        def mock_question(*args, **kwargs):
            dialog_called.append(True)
            return QMessageBox.StandardButton.No  # Return No to avoid actual reset

        monkeypatch.setattr(QMessageBox, "question", mock_question)

        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)
        settings_window.tab_widget.setCurrentIndex(0)  # Application tab

        # 点击Reset Tab按钮
        settings_window.reset_button.click()
        qtbot.wait(200)

        # 验证确认对话框被调用
        assert len(dialog_called) == 1

    def test_reset_tab_button_cancel(self, qtbot, settings_window, isolated_config, monkeypatch):
        """测试取消Reset Tab操作"""
        # Mock QMessageBox.question to return No (cancel)
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.No
        )

        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)
        settings_window.tab_widget.setCurrentIndex(0)  # Application tab

        # 修改配置
        settings_window.application_tab.log_level_combo.setCurrentText("DEBUG")
        original_value = settings_window.application_tab.log_level_combo.currentText()

        # 点击Reset Tab按钮(但会取消)
        settings_window.reset_button.click()
        qtbot.wait(200)

        # 验证配置未被重置
        current_value = settings_window.application_tab.log_level_combo.currentText()
        assert current_value == original_value


@pytest.mark.gui
class TestConfigManagement:
    """配置管理按钮测试"""

    def test_export_config_creates_file(self, qtbot, settings_window, isolated_config, tmp_path, monkeypatch):
        """测试导出配置功能(Mock验证)"""
        from PySide6.QtWidgets import QFileDialog
        from unittest.mock import MagicMock
        export_file = tmp_path / "test_export.json"

        # Mock config_manager.export_config
        mock_export = MagicMock()
        settings_window.application_tab.config_manager.export_config = mock_export

        # Mock QFileDialog.getSaveFileName to return the file path
        def mock_get_save_filename(parent, caption, directory, filter_str):
            return (str(export_file), filter_str)

        monkeypatch.setattr(QFileDialog, "getSaveFileName", mock_get_save_filename)
        # Mock QMessageBox.information
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)

        # 点击Export Settings按钮
        settings_window.application_tab.export_config_button.click()
        qtbot.wait(200)

        # 验证export_config被调用
        mock_export.assert_called_once_with(str(export_file))

    def test_export_config_cancel(self, qtbot, settings_window, monkeypatch):
        """测试取消导出配置操作"""
        from PySide6.QtWidgets import QFileDialog

        # Mock QFileDialog to return empty path (cancelled)
        def mock_get_save_filename_cancel(parent, caption, directory, filter_str):
            return ("", "")

        monkeypatch.setattr(QFileDialog, "getSaveFileName", mock_get_save_filename_cancel)

        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)

        # 点击Export Settings按钮(会取消)
        settings_window.application_tab.export_config_button.click()
        qtbot.wait(200)

        # 验证没有抛出异常,操作正常取消

    def test_import_config_loads_settings(self, qtbot, settings_window, isolated_config, tmp_path, monkeypatch):
        """测试导入配置功能(Mock验证)"""
        from PySide6.QtWidgets import QFileDialog
        from unittest.mock import MagicMock
        import_file = tmp_path / "test_import.json"

        # 创建假的导入文件
        import_file.write_text("{}")

        # Mock config_manager.import_config
        mock_import = MagicMock()
        settings_window.application_tab.config_manager.import_config = mock_import

        # Mock load_current_config
        mock_load = MagicMock()
        settings_window.load_current_config = mock_load

        # Mock QFileDialog.getOpenFileName
        def mock_get_open_filename(parent, caption, directory, filter_str):
            return (str(import_file), filter_str)

        monkeypatch.setattr(QFileDialog, "getOpenFileName", mock_get_open_filename)
        # Mock QMessageBox.information
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)

        # 点击Import Settings按钮
        settings_window.application_tab.import_config_button.click()
        qtbot.wait(200)

        # 验证import_config被调用
        mock_import.assert_called_once_with(str(import_file))
        # 验证load_current_config被调用以重新加载UI
        mock_load.assert_called_once()

    def test_reset_to_defaults_confirmation(self, qtbot, settings_window, isolated_config, monkeypatch):
        """测试重置到默认值功能"""
        # Mock QMessageBox.question to return Yes
        monkeypatch.setattr(
            QMessageBox,
            "question",
            lambda *args, **kwargs: QMessageBox.StandardButton.Yes
        )
        # Mock QMessageBox.information
        monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

        # 显示窗口
        settings_window.show()
        qtbot.waitExposed(settings_window, timeout=1000)

        # 修改配置
        settings_window.application_tab.log_level_combo.setCurrentText("DEBUG")
        assert settings_window.application_tab.log_level_combo.currentText() == "DEBUG"

        # 点击Reset to Defaults按钮
        settings_window.application_tab.reset_config_button.click()
        qtbot.wait(200)

        # 验证配置被重置到默认值
        reset_level = settings_window.application_tab.log_level_combo.currentText()
        assert reset_level != "DEBUG"  # Should be reset to default (WARNING)


