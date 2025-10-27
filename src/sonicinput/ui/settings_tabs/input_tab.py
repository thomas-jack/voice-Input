"""文本输入设置标签页"""

from PyQt6.QtWidgets import (QVBoxLayout, QGroupBox, QFormLayout, QHBoxLayout,
                            QCheckBox, QComboBox, QDoubleSpinBox, QPushButton, QLabel)
from typing import Dict, Any
from .base_tab import BaseSettingsTab


class InputTab(BaseSettingsTab):
    """文本输入设置标签页

    包含：
    - 输入方法选择（clipboard, sendinput）
    - 回退机制设置
    - 剪贴板设置
    - SendInput设置
    - 兼容性测试
    """

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 输入方法组
        method_group = QGroupBox("Text Input Method")
        method_layout = QFormLayout(method_group)

        # 首选方法
        self.input_method_combo = QComboBox()
        self.input_method_combo.addItems(["clipboard", "sendinput"])
        method_layout.addRow("Preferred Method:", self.input_method_combo)

        # 启用回退
        self.fallback_enabled_checkbox = QCheckBox("Enable fallback to alternative method")
        method_layout.addRow("", self.fallback_enabled_checkbox)

        # 自动检测终端
        self.auto_detect_checkbox = QCheckBox("Auto-detect terminal applications")
        method_layout.addRow("", self.auto_detect_checkbox)

        layout.addWidget(method_group)

        # 剪贴板设置组
        clipboard_group = QGroupBox("Clipboard Settings")
        clipboard_layout = QFormLayout(clipboard_group)

        # 恢复延迟
        self.clipboard_delay_spinbox = QDoubleSpinBox()
        self.clipboard_delay_spinbox.setRange(0.0, 10.0)
        self.clipboard_delay_spinbox.setSingleStep(0.5)
        self.clipboard_delay_spinbox.setSuffix(" seconds")
        clipboard_layout.addRow("Restore Delay:", self.clipboard_delay_spinbox)

        layout.addWidget(clipboard_group)

        # SendInput设置组
        sendinput_group = QGroupBox("SendInput Settings")
        sendinput_layout = QFormLayout(sendinput_group)

        # 输入延迟
        self.typing_delay_spinbox = QDoubleSpinBox()
        self.typing_delay_spinbox.setRange(0.0, 0.1)
        self.typing_delay_spinbox.setSingleStep(0.01)
        self.typing_delay_spinbox.setDecimals(3)
        self.typing_delay_spinbox.setSuffix(" seconds")
        sendinput_layout.addRow("Typing Delay:", self.typing_delay_spinbox)

        layout.addWidget(sendinput_group)

        # 兼容性测试组
        test_group = QGroupBox("Compatibility Testing")
        test_layout = QVBoxLayout(test_group)

        test_buttons_layout = QHBoxLayout()

        self.test_clipboard_button = QPushButton("Test Clipboard")
        self.test_clipboard_button.clicked.connect(self._test_clipboard)
        test_buttons_layout.addWidget(self.test_clipboard_button)

        self.test_sendinput_button = QPushButton("Test SendInput")
        self.test_sendinput_button.clicked.connect(self._test_sendinput)
        test_buttons_layout.addWidget(self.test_sendinput_button)

        test_layout.addLayout(test_buttons_layout)

        self.input_test_status_label = QLabel("Not tested")
        test_layout.addWidget(self.input_test_status_label)

        layout.addWidget(test_group)

        layout.addStretch()

        # 保存控件引用
        self.controls = {
            'input_method': self.input_method_combo,
            'fallback_enabled': self.fallback_enabled_checkbox,
            'auto_detect': self.auto_detect_checkbox,
            'clipboard_delay': self.clipboard_delay_spinbox,
            'typing_delay': self.typing_delay_spinbox,
            'test_status': self.input_test_status_label,
        }

        # 暴露控件到parent_window
        self.parent_window.input_method_combo = self.input_method_combo
        self.parent_window.fallback_enabled_checkbox = self.fallback_enabled_checkbox
        self.parent_window.auto_detect_checkbox = self.auto_detect_checkbox
        self.parent_window.clipboard_delay_spinbox = self.clipboard_delay_spinbox
        self.parent_window.typing_delay_spinbox = self.typing_delay_spinbox
        self.parent_window.input_test_status_label = self.input_test_status_label

    def load_config(self, config: Dict[str, Any]) -> None:
        """从配置加载UI状态

        Args:
            config: 完整配置字典
        """
        input_config = config.get("input", {})

        # Input settings
        self.input_method_combo.setCurrentText(
            input_config.get("preferred_method", "clipboard")
        )
        self.fallback_enabled_checkbox.setChecked(
            input_config.get("fallback_enabled", True)
        )
        self.auto_detect_checkbox.setChecked(
            input_config.get("auto_detect_terminal", True)
        )
        self.clipboard_delay_spinbox.setValue(
            input_config.get("clipboard_restore_delay", 0.5)
        )
        self.typing_delay_spinbox.setValue(
            input_config.get("typing_delay", 0.01)
        )

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        config = {
            "input": {
                "preferred_method": self.input_method_combo.currentText(),
                "fallback_enabled": self.fallback_enabled_checkbox.isChecked(),
                "auto_detect_terminal": self.auto_detect_checkbox.isChecked(),
                "clipboard_restore_delay": self.clipboard_delay_spinbox.value(),
                "typing_delay": self.typing_delay_spinbox.value(),
            }
        }

        return config

    def _test_clipboard(self) -> None:
        """测试剪贴板方法 - 调用父窗口的方法"""
        if hasattr(self.parent_window, 'test_clipboard'):
            self.parent_window.test_clipboard()

    def _test_sendinput(self) -> None:
        """测试SendInput方法 - 调用父窗口的方法"""
        if hasattr(self.parent_window, 'test_sendinput'):
            self.parent_window.test_sendinput()

    def update_test_status(self, status: str, is_error: bool = False) -> None:
        """更新测试状态显示

        Args:
            status: 状态文本
            is_error: 是否为错误状态
        """
        self.input_test_status_label.setText(status)
        if is_error:
            self.input_test_status_label.setStyleSheet("color: red;")
        else:
            self.input_test_status_label.setStyleSheet("color: green;")
