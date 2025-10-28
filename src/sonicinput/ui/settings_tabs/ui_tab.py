"""UI设置标签页"""

from PySide6.QtWidgets import (QVBoxLayout, QGroupBox, QFormLayout,
                            QCheckBox, QComboBox)
from typing import Dict, Any
from .base_tab import BaseSettingsTab


class UITab(BaseSettingsTab):
    """UI设置标签页

    包含：
    - 录音悬浮窗设置
    - 主题设置
    """

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 悬浮窗设置组
        overlay_group = QGroupBox("Recording Overlay")
        overlay_layout = QFormLayout(overlay_group)

        # 显示悬浮窗
        self.show_overlay_checkbox = QCheckBox("Show recording overlay")
        overlay_layout.addRow("", self.show_overlay_checkbox)

        # 悬浮窗位置
        self.overlay_position_combo = QComboBox()
        self.overlay_position_combo.addItems([
            "center", "top_left", "top_right", "bottom_left", "bottom_right"
        ])
        overlay_layout.addRow("Position:", self.overlay_position_combo)

        # 始终置顶
        self.overlay_on_top_checkbox = QCheckBox("Always on top")
        overlay_layout.addRow("", self.overlay_on_top_checkbox)

        layout.addWidget(overlay_group)

        # 主题颜色设置组
        theme_group = QGroupBox("Theme Color")
        theme_layout = QFormLayout(theme_group)

        self.theme_color_combo = QComboBox()
        self.theme_color_combo.addItems([
            "Cyan",
            "Blue",
            "Teal",
            "Purple",
            "Red",
            "Pink",
            "Amber",
        ])
        theme_layout.addRow("Color Theme:", self.theme_color_combo)

        # 添加提示
        from PySide6.QtWidgets import QLabel
        theme_hint = QLabel("⚠️ Changing theme requires application restart")
        theme_hint.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        theme_layout.addRow("", theme_hint)

        layout.addWidget(theme_group)

        layout.addStretch()

        # 保存控件引用
        self.controls = {
            'show_overlay': self.show_overlay_checkbox,
            'overlay_position': self.overlay_position_combo,
            'overlay_on_top': self.overlay_on_top_checkbox,
            'theme_color': self.theme_color_combo,
        }

        # 暴露控件到parent_window
        self.parent_window.show_overlay_checkbox = self.show_overlay_checkbox
        self.parent_window.overlay_position_combo = self.overlay_position_combo
        self.parent_window.overlay_on_top_checkbox = self.overlay_on_top_checkbox
        self.parent_window.theme_color_combo = self.theme_color_combo

    def load_config(self, config: Dict[str, Any]) -> None:
        """从配置加载UI状态

        Args:
            config: 完整配置字典
        """
        ui_config = config.get("ui", {})

        # 加载显示悬浮窗设置
        self.show_overlay_checkbox.setChecked(
            ui_config.get("show_overlay", True)
        )

        # 加载悬浮窗始终置顶设置
        self.overlay_on_top_checkbox.setChecked(
            ui_config.get("overlay_always_on_top", True)
        )

        # 加载overlay position mode
        overlay_position = ui_config.get("overlay_position", {})
        position_mode = overlay_position.get("mode", "preset")
        if position_mode == "preset":
            self.overlay_position_combo.setCurrentText("预设位置")
        elif position_mode == "custom":
            self.overlay_position_combo.setCurrentText("自定义位置")

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

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: UI配置字典
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
                "show_overlay": self.show_overlay_checkbox.isChecked(),
                "overlay_always_on_top": self.overlay_on_top_checkbox.isChecked(),
                "theme_color": theme_color,
            }
        }

        # 处理overlay position模式设置
        overlay_position_text = self.overlay_position_combo.currentText()
        if overlay_position_text == "预设位置":
            config["ui"]["overlay_position"] = {"mode": "preset"}
        elif overlay_position_text == "自定义位置":
            config["ui"]["overlay_position"] = {"mode": "custom"}

        return config
