"""应用设置标签页 (合并 General + UI)"""

from typing import Any, Dict

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from .base_tab import BaseSettingsTab


class ApplicationTab(BaseSettingsTab):
    """应用设置标签页

    包含：
    - 应用设置（开机启动、最小化启动、托盘通知）
    - 日志设置（日志级别、控制台输出、日志大小限制）
    - 配置管理（导出、导入、重置）
    - 录音悬浮窗设置
    - 主题设置
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

        # 悬浮窗设置组
        overlay_group = QGroupBox("Recording Overlay")
        overlay_layout = QFormLayout(overlay_group)

        # 显示悬浮窗
        self.show_overlay_checkbox = QCheckBox("Show recording overlay")
        overlay_layout.addRow("", self.show_overlay_checkbox)

        # 悬浮窗位置
        self.overlay_position_combo = QComboBox()
        self.overlay_position_combo.addItems(
            ["center", "top_left", "top_right", "bottom_left", "bottom_right"]
        )
        overlay_layout.addRow("Position:", self.overlay_position_combo)

        # 始终置顶
        self.overlay_on_top_checkbox = QCheckBox("Always on top")
        overlay_layout.addRow("", self.overlay_on_top_checkbox)

        layout.addWidget(overlay_group)

        # 主题颜色设置组
        theme_group = QGroupBox("Theme Color")
        theme_layout = QFormLayout(theme_group)

        self.theme_color_combo = QComboBox()
        self.theme_color_combo.addItems(
            [
                "Cyan",
                "Blue",
                "Teal",
                "Purple",
                "Red",
                "Pink",
                "Amber",
            ]
        )
        theme_layout.addRow("Color Theme:", self.theme_color_combo)

        # 添加提示
        theme_hint = QLabel("Changing theme requires application restart")
        theme_hint.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        theme_layout.addRow("", theme_hint)

        layout.addWidget(theme_group)

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
            "start_minimized": self.start_minimized_checkbox,
            "tray_notifications": self.tray_notifications_checkbox,
            "show_overlay": self.show_overlay_checkbox,
            "overlay_position": self.overlay_position_combo,
            "overlay_on_top": self.overlay_on_top_checkbox,
            "theme_color": self.theme_color_combo,
            "log_level": self.log_level_combo,
            "console_output": self.console_output_checkbox,
            "max_log_size": self.max_log_size_spinbox,
        }

        # 暴露控件到parent_window
        self.parent_window.start_minimized_checkbox = self.start_minimized_checkbox
        self.parent_window.tray_notifications_checkbox = (
            self.tray_notifications_checkbox
        )
        self.parent_window.show_overlay_checkbox = self.show_overlay_checkbox
        self.parent_window.overlay_position_combo = self.overlay_position_combo
        self.parent_window.overlay_on_top_checkbox = self.overlay_on_top_checkbox
        self.parent_window.theme_color_combo = self.theme_color_combo
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
        self.start_minimized_checkbox.setChecked(ui_config.get("start_minimized", True))
        self.tray_notifications_checkbox.setChecked(
            ui_config.get("tray_notifications", True)
        )

        # 加载悬浮窗设置
        self.show_overlay_checkbox.setChecked(ui_config.get("show_overlay", True))
        self.overlay_on_top_checkbox.setChecked(
            ui_config.get("overlay_always_on_top", True)
        )

        # 加载overlay position (仅加载preset值，custom模式通过拖拽窗口设置)
        overlay_position = ui_config.get("overlay_position", {})
        position_mode = overlay_position.get("mode", "preset")
        if position_mode == "preset":
            preset_value = overlay_position.get("preset", "center")
            self.overlay_position_combo.setCurrentText(preset_value)
        else:
            # custom模式：显示默认值，用户可以通过拖拽窗口来改变位置
            self.overlay_position_combo.setCurrentText("center")

        # 加载主题颜色设置
        theme_color = ui_config.get("theme_color", "cyan")
        # 映射配置值到显示文本
        color_map = {
            "cyan": "Cyan",
            "blue": "Blue",
            "teal": "Teal",
            "purple": "Purple",
            "red": "Red",
            "pink": "Pink",
            "amber": "Amber",
        }
        display_text = color_map.get(theme_color, "Cyan")
        self.theme_color_combo.setCurrentText(display_text)

        # 加载日志设置
        logging_config = config.get("logging", {})
        self.log_level_combo.setCurrentText(logging_config.get("level", "INFO"))
        self.console_output_checkbox.setChecked(
            logging_config.get("console_output", False)
        )
        self.max_log_size_spinbox.setValue(logging_config.get("max_log_size_mb", 10))

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        # 映射显示文本到配置值
        color_text = self.theme_color_combo.currentText()
        reverse_map = {
            "Cyan": "cyan",
            "Blue": "blue",
            "Teal": "teal",
            "Purple": "purple",
            "Red": "red",
            "Pink": "pink",
            "Amber": "amber",
        }
        theme_color = reverse_map.get(color_text, "cyan")

        config = {
            "ui": {
                "start_minimized": self.start_minimized_checkbox.isChecked(),
                "tray_notifications": self.tray_notifications_checkbox.isChecked(),
                "show_overlay": self.show_overlay_checkbox.isChecked(),
                "overlay_always_on_top": self.overlay_on_top_checkbox.isChecked(),
                "theme_color": theme_color,
            },
            "logging": {
                "level": self.log_level_combo.currentText(),
                "console_output": self.console_output_checkbox.isChecked(),
                "max_log_size_mb": self.max_log_size_spinbox.value(),
            },
        }

        # 处理overlay position preset设置
        # 注意：如果配置中已经存在custom模式的设置，需要保留它
        # position_manager会自动更新custom位置，这里只更新preset值
        overlay_position_text = self.overlay_position_combo.currentText()

        # 从当前配置中读取overlay_position（可能包含custom坐标）
        current_config = self.config_manager.get_all_settings()
        existing_overlay_position = current_config.get("ui", {}).get(
            "overlay_position", {}
        )

        # 如果现有配置是custom模式，保留custom数据；否则使用preset模式
        if existing_overlay_position.get("mode") == "custom":
            # 保留custom模式和坐标，但更新preset值（作为fallback）
            config["ui"]["overlay_position"] = {
                **existing_overlay_position,  # 保留所有现有字段（custom坐标等）
                "preset": overlay_position_text,  # 更新preset值
            }
        else:
            # preset模式或新配置，使用选中的preset
            config["ui"]["overlay_position"] = {
                "mode": "preset",
                "preset": overlay_position_text,
            }

        return config

    def _export_config(self) -> None:
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self.parent_window,
            "Export Settings",
            "voice_input_settings.json",
            "JSON Files (*.json)",
        )
        if file_path:
            try:
                self.config_manager.export_config(file_path)
                QMessageBox.information(
                    self.parent_window, "Export", "Settings exported successfully!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self.parent_window, "Error", f"Failed to export settings: {e}"
                )

    def _import_config(self) -> None:
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent_window, "Import Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                self.config_manager.import_config(file_path)
                # 通知父窗口重新加载配置
                if hasattr(self.parent_window, "load_current_config"):
                    self.parent_window.load_current_config()
                QMessageBox.information(
                    self.parent_window, "Import", "Settings imported successfully!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self.parent_window, "Error", f"Failed to import settings: {e}"
                )

    def _reset_config(self) -> None:
        """重置配置"""
        reply = QMessageBox.question(
            self.parent_window,
            "Reset Settings",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config_manager.reset_to_defaults()
                # 通知父窗口重新加载配置
                if hasattr(self.parent_window, "load_current_config"):
                    self.parent_window.load_current_config()
                QMessageBox.information(
                    self.parent_window, "Reset", "Settings reset to defaults!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self.parent_window, "Error", f"Failed to reset settings: {e}"
                )
