"""常规设置标签页"""

from PySide6.QtWidgets import (QVBoxLayout, QGroupBox, QFormLayout,
                            QCheckBox, QComboBox, QSpinBox, QPushButton, QHBoxLayout, QMessageBox, QFileDialog)
from typing import Dict, Any
from .base_tab import BaseSettingsTab


class GeneralTab(BaseSettingsTab):
    """常规设置标签页

    包含：
    - 应用设置（开机启动、最小化启动、托盘通知）
    - 日志设置（日志级别、控制台输出、日志大小限制）
    - 配置管理（导出、导入、重置）
    """

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 应用设置组
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)

        # 最小化启动
        self.start_minimized_checkbox = QCheckBox("Start minimized to tray")
        app_layout.addRow("Startup:", self.start_minimized_checkbox)

        # 托盘通知
        self.tray_notifications_checkbox = QCheckBox("Show tray notifications")
        app_layout.addRow("Notifications:", self.tray_notifications_checkbox)

        layout.addWidget(app_group)

        # 日志设置组
        log_group = QGroupBox("Logging Settings")
        log_layout = QFormLayout(log_group)

        # 日志级别
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_layout.addRow("Log Level:", self.log_level_combo)

        # 控制台输出
        self.console_output_checkbox = QCheckBox("Show console output (debug mode)")
        log_layout.addRow("", self.console_output_checkbox)

        # 日志大小限制
        self.max_log_size_spinbox = QSpinBox()
        self.max_log_size_spinbox.setRange(1, 100)
        self.max_log_size_spinbox.setSuffix(" MB")
        log_layout.addRow("Max log file size:", self.max_log_size_spinbox)

        layout.addWidget(log_group)

        # 配置管理组
        config_group = QGroupBox("Configuration Management")
        config_layout = QVBoxLayout(config_group)

        config_buttons_layout = QHBoxLayout()

        self.export_config_button = QPushButton("Export Settings")
        self.export_config_button.clicked.connect(self._export_config)
        config_buttons_layout.addWidget(self.export_config_button)

        self.import_config_button = QPushButton("Import Settings")
        self.import_config_button.clicked.connect(self._import_config)
        config_buttons_layout.addWidget(self.import_config_button)

        self.reset_config_button = QPushButton("Reset to Defaults")
        self.reset_config_button.clicked.connect(self._reset_config)
        config_buttons_layout.addWidget(self.reset_config_button)

        config_layout.addLayout(config_buttons_layout)

        layout.addWidget(config_group)

        layout.addStretch()

        # 保存控件引用
        self.controls = {
            'start_minimized': self.start_minimized_checkbox,
            'tray_notifications': self.tray_notifications_checkbox,
            'log_level': self.log_level_combo,
            'console_output': self.console_output_checkbox,
            'max_log_size': self.max_log_size_spinbox,
        }

        # 暴露控件到parent_window
        self.parent_window.start_minimized_checkbox = self.start_minimized_checkbox
        self.parent_window.tray_notifications_checkbox = self.tray_notifications_checkbox
        self.parent_window.log_level_combo = self.log_level_combo
        self.parent_window.console_output_checkbox = self.console_output_checkbox
        self.parent_window.max_log_size_spinbox = self.max_log_size_spinbox

    def load_config(self, config: Dict[str, Any]) -> None:
        """从配置加载UI状态

        Args:
            config: 完整配置字典
        """
        ui_config = config.get("ui", {})

        # 加载应用设置
        self.start_minimized_checkbox.setChecked(
            ui_config.get("start_minimized", True)
        )
        self.tray_notifications_checkbox.setChecked(
            ui_config.get("tray_notifications", True)
        )

        # 加载日志设置
        logging_config = config.get("logging", {})
        self.log_level_combo.setCurrentText(
            logging_config.get("level", "INFO")
        )
        self.console_output_checkbox.setChecked(
            logging_config.get("console_output", False)
        )
        self.max_log_size_spinbox.setValue(
            logging_config.get("max_log_size_mb", 10)
        )

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        config = {
            "ui": {
                "start_minimized": self.start_minimized_checkbox.isChecked(),
                "tray_notifications": self.tray_notifications_checkbox.isChecked(),
            },
            "logging": {
                "level": self.log_level_combo.currentText(),
                "console_output": self.console_output_checkbox.isChecked(),
                "max_log_size_mb": self.max_log_size_spinbox.value(),
            }
        }

        return config

    def _export_config(self) -> None:
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_window, "Export Settings", "voice_input_settings.json", "JSON Files (*.json)"
        )
        if file_path:
            try:
                self.config_manager.export_config(file_path)
                QMessageBox.information(self.parent_window, "Export", "Settings exported successfully!")
            except Exception as e:
                QMessageBox.critical(self.parent_window, "Error", f"Failed to export settings: {e}")

    def _import_config(self) -> None:
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent_window, "Import Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                self.config_manager.import_config(file_path)
                # 通知父窗口重新加载配置
                if hasattr(self.parent_window, 'load_current_config'):
                    self.parent_window.load_current_config()
                QMessageBox.information(self.parent_window, "Import", "Settings imported successfully!")
            except Exception as e:
                QMessageBox.critical(self.parent_window, "Error", f"Failed to import settings: {e}")

    def _reset_config(self) -> None:
        """重置配置"""
        reply = QMessageBox.question(
            self.parent_window, "Reset Settings",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config_manager.reset_to_defaults()
                # 通知父窗口重新加载配置
                if hasattr(self.parent_window, 'load_current_config'):
                    self.parent_window.load_current_config()
                QMessageBox.information(self.parent_window, "Reset", "Settings reset to defaults!")
            except Exception as e:
                QMessageBox.critical(self.parent_window, "Error", f"Failed to reset settings: {e}")
