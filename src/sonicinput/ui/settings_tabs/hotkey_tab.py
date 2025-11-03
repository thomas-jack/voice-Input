"""快捷键设置标签页"""

from PySide6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QListWidget,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import QTimer
from typing import Dict, Any
from .base_tab import BaseSettingsTab
from ...utils import app_logger


class HotkeyTab(BaseSettingsTab):
    """快捷键设置标签页

    包含：
    - 快捷键列表管理
    - 快捷键捕获功能
    - 建议的快捷键
    """

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 快捷键列表组
        hotkey_list_group = QGroupBox("Registered Hotkeys")
        hotkey_list_layout = QVBoxLayout(hotkey_list_group)

        # 快捷键列表
        self.hotkeys_list = QListWidget()
        self.hotkeys_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.hotkeys_list.itemDoubleClicked.connect(self._edit_hotkey_item)
        hotkey_list_layout.addWidget(self.hotkeys_list)

        # 列表操作按钮
        list_buttons_layout = QHBoxLayout()

        self.add_hotkey_button = QPushButton("Add Hotkey")
        self.add_hotkey_button.clicked.connect(self._add_new_hotkey)
        list_buttons_layout.addWidget(self.add_hotkey_button)

        self.remove_hotkey_button = QPushButton("Remove Selected")
        self.remove_hotkey_button.clicked.connect(self._remove_selected_hotkey)
        list_buttons_layout.addWidget(self.remove_hotkey_button)

        self.capture_hotkey_button = QPushButton("Capture New")
        self.capture_hotkey_button.clicked.connect(self._capture_hotkey)
        list_buttons_layout.addWidget(self.capture_hotkey_button)

        hotkey_list_layout.addLayout(list_buttons_layout)

        layout.addWidget(hotkey_list_group)

        # 保留单个热键输入（向后兼容/临时输入）
        hotkey_input_group = QGroupBox("Quick Add")
        hotkey_input_layout = QHBoxLayout(hotkey_input_group)

        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("e.g., ctrl+shift+v or f12")
        hotkey_input_layout.addWidget(self.hotkey_input)

        self.add_from_input_button = QPushButton("Add")
        self.add_from_input_button.clicked.connect(self._add_hotkey_from_input)
        hotkey_input_layout.addWidget(self.add_from_input_button)

        layout.addWidget(hotkey_input_group)

        # 状态提示标签
        self.hotkey_status_label = QLabel("Ready to capture hotkeys")
        self.hotkey_status_label.setWordWrap(True)
        self.hotkey_status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.hotkey_status_label)

        # 建议的快捷键
        suggestions_group = QGroupBox("Suggested Hotkeys")
        suggestions_layout = QVBoxLayout(suggestions_group)

        self.hotkey_suggestions = QListWidget()
        suggested_keys = [
            "ctrl+shift+v",
            "ctrl+alt+v",
            "ctrl+shift+space",
            "alt+shift+v",
            "win+shift+v",
            "f12",
            "ctrl+f12",
            "shift+f12",
        ]

        for key in suggested_keys:
            self.hotkey_suggestions.addItem(key)

        self.hotkey_suggestions.itemClicked.connect(self._on_suggestion_clicked)
        suggestions_layout.addWidget(self.hotkey_suggestions)

        layout.addWidget(suggestions_group)

        layout.addStretch()

        # 保存控件引用
        self.controls = {
            "hotkeys_list": self.hotkeys_list,
            "hotkey_input": self.hotkey_input,
            "hotkey_status_label": self.hotkey_status_label,
        }

        # 暴露控件到parent_window
        self.parent_window.hotkeys_list = self.hotkeys_list
        self.parent_window.hotkey_input = self.hotkey_input
        self.parent_window.hotkey_status_label = self.hotkey_status_label

    def load_config(self, config: Dict[str, Any]) -> None:
        """从配置加载UI状态

        Args:
            config: 完整配置字典
        """
        # 快捷键列表（支持多个）
        self.hotkeys_list.clear()
        hotkeys = config.get("hotkeys", None)
        if hotkeys is None:  # 向后兼容单个hotkey
            single_hotkey = config.get("hotkey", "ctrl+shift+v")
            hotkeys = [single_hotkey]

        for hotkey in hotkeys:
            if hotkey and hotkey.strip():
                self.hotkeys_list.addItem(hotkey.strip())

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        # 快捷键列表（保存为数组）
        hotkeys_list = []
        for i in range(self.hotkeys_list.count()):
            hotkey_text = self.hotkeys_list.item(i).text().strip()
            if hotkey_text and not hotkey_text.startswith(
                "(New hotkey"
            ):  # 跳过未编辑的新项
                hotkeys_list.append(hotkey_text)

        config = {
            "hotkeys": hotkeys_list
            if hotkeys_list
            else ["ctrl+shift+v"]  # 至少保留一个默认值
        }

        return config

    def _add_new_hotkey(self) -> None:
        """添加新的空白快捷键到列表"""
        self.hotkeys_list.addItem("(New hotkey - double click to edit)")

    def _remove_selected_hotkey(self) -> None:
        """移除选中的快捷键"""
        current_row = self.hotkeys_list.currentRow()
        if current_row >= 0:
            self.hotkeys_list.takeItem(current_row)

    def _add_hotkey_from_input(self) -> None:
        """从输入框添加快捷键"""
        hotkey_text = self.hotkey_input.text().strip()
        if hotkey_text:
            # 检查是否已存在
            existing_items = [
                self.hotkeys_list.item(i).text()
                for i in range(self.hotkeys_list.count())
            ]
            if hotkey_text not in existing_items:
                self.hotkeys_list.addItem(hotkey_text)
                self.hotkey_input.clear()
            else:
                QMessageBox.warning(
                    self.parent_window,
                    "Duplicate Hotkey",
                    f"Hotkey '{hotkey_text}' already exists in the list.",
                )

    def _edit_hotkey_item(self, item) -> None:
        """双击编辑快捷键列表项"""
        current_text = item.text()
        from PySide6.QtWidgets import QInputDialog

        new_text, ok = QInputDialog.getText(
            self.parent_window,
            "Edit Hotkey",
            "Enter hotkey combination:",
            QLineEdit.EchoMode.Normal,
            current_text,
        )
        if ok and new_text.strip():
            # 检查是否与其他项重复
            existing_items = [
                self.hotkeys_list.item(i).text()
                for i in range(self.hotkeys_list.count())
            ]
            if new_text.strip() != current_text and new_text.strip() in existing_items:
                QMessageBox.warning(
                    self.parent_window,
                    "Duplicate Hotkey",
                    f"Hotkey '{new_text.strip()}' already exists.",
                )
            else:
                item.setText(new_text.strip())

    def _on_suggestion_clicked(self, item) -> None:
        """点击快捷键建议"""
        self.hotkey_input.setText(item.text())

    def _capture_hotkey(self) -> None:
        """捕获用户按下的快捷键组合 - 使用pynput"""
        try:
            from pynput import keyboard as pynput_keyboard
            from pynput.keyboard import Key

            # 禁用按钮，防止重复点击
            self.capture_hotkey_button.setEnabled(False)
            self.capture_hotkey_button.setText("Press hotkey...")

            # 清空输入框
            self.hotkey_input.clear()
            self._update_hotkey_status(
                "Press your desired hotkey combination...", False
            )

            # 记录按下的键
            pressed_keys = set()
            captured_hotkey = None
            listener = None

            def format_hotkey(keys: set) -> str:
                """将pynput按键集转换为标准hotkey字符串"""
                parts = []
                modifiers = []
                normal_keys = []

                for key in keys:
                    # 修饰键
                    if key in [Key.ctrl, Key.ctrl_l, Key.ctrl_r]:
                        if "ctrl" not in modifiers:
                            modifiers.append("ctrl")
                    elif key in [Key.alt, Key.alt_l, Key.alt_r]:
                        if "alt" not in modifiers:
                            modifiers.append("alt")
                    elif key in [Key.shift, Key.shift_l, Key.shift_r]:
                        if "shift" not in modifiers:
                            modifiers.append("shift")
                    elif key in [Key.cmd, Key.cmd_l, Key.cmd_r]:
                        if "cmd" not in modifiers:
                            modifiers.append("cmd")
                    # 普通字符键
                    elif hasattr(key, "char") and key.char:
                        normal_keys.append(key.char)
                    # 特殊键名
                    elif hasattr(key, "name"):
                        normal_keys.append(key.name)

                # 排序修饰键
                modifier_order = {"ctrl": 0, "alt": 1, "shift": 2, "cmd": 3}
                modifiers.sort(key=lambda x: modifier_order.get(x, 99))

                # 构建快捷键字符串
                parts.extend(modifiers)
                parts.extend(normal_keys)

                return "+".join(parts) if parts else None

            def on_press(key):
                nonlocal captured_hotkey, listener
                pressed_keys.add(key)

                # 检测有效组合（至少有修饰键或单个特殊键）
                has_modifier = any(
                    k
                    in [
                        Key.ctrl,
                        Key.ctrl_l,
                        Key.ctrl_r,
                        Key.alt,
                        Key.alt_l,
                        Key.alt_r,
                        Key.shift,
                        Key.shift_l,
                        Key.shift_r,
                        Key.cmd,
                        Key.cmd_l,
                        Key.cmd_r,
                    ]
                    for k in pressed_keys
                )

                if has_modifier or len(pressed_keys) >= 2:
                    # 有修饰键或多个键，准备捕获
                    pass

            def on_release(key):
                nonlocal captured_hotkey, listener

                # 键松开时捕获当前组合
                if len(pressed_keys) >= 1:
                    captured_hotkey = format_hotkey(pressed_keys)
                    if captured_hotkey:
                        # 停止listener
                        if listener:
                            listener.stop()
                        return False  # 停止监听

                # 移除松开的键
                if key in pressed_keys:
                    pressed_keys.remove(key)

            # 创建listener
            listener = pynput_keyboard.Listener(
                on_press=on_press, on_release=on_release
            )
            listener.start()

            # 设置超时
            def capture_timeout():
                nonlocal captured_hotkey, listener
                if captured_hotkey is None:
                    if listener:
                        listener.stop()
                    self._update_hotkey_status(
                        "Capture timed out. Please try again.", True
                    )
                    self._restore_capture_button()

            timeout_timer = QTimer()
            timeout_timer.timeout.connect(capture_timeout)
            timeout_timer.setSingleShot(True)
            timeout_timer.start(5000)

            # 使用QTimer检查捕获结果
            def check_capture_result():
                nonlocal captured_hotkey, listener
                if captured_hotkey:
                    timeout_timer.stop()

                    # 停止listener - pynput不会阻塞
                    if listener:
                        listener.stop()

                    # 更新输入框并自动添加到列表
                    self.hotkey_input.setText(captured_hotkey)

                    # 检查是否已存在
                    existing_items = [
                        self.hotkeys_list.item(i).text()
                        for i in range(self.hotkeys_list.count())
                    ]
                    if captured_hotkey not in existing_items:
                        self.hotkeys_list.addItem(captured_hotkey)

                    self._restore_capture_button()
                else:
                    # 继续检查
                    QTimer.singleShot(100, check_capture_result)

            # 开始检查
            QTimer.singleShot(100, check_capture_result)

        except Exception as e:
            app_logger.log_error(e, "capture_hotkey")
            self._update_hotkey_status(f"Error capturing hotkey: {str(e)}", True)
            self._restore_capture_button()

    def _restore_capture_button(self):
        """恢复capture按钮状态"""
        self.capture_hotkey_button.setEnabled(True)
        self.capture_hotkey_button.setText("Capture New")

    def _update_hotkey_status(self, status: str, is_error: bool = False) -> None:
        """更新快捷键状态显示"""
        self.hotkey_status_label.setText(status)
        if is_error:
            self.hotkey_status_label.setStyleSheet("color: red;")
        else:
            self.hotkey_status_label.setStyleSheet("color: green;")
