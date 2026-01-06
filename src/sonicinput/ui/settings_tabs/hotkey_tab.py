"""快捷键设置标签页"""

from typing import Any, Dict

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QMessageBox,
    QPushButton,
    QGroupBox,
    QVBoxLayout,
)

from ...utils import app_logger
from .base_tab import BaseSettingsTab


class HotkeyTab(BaseSettingsTab):
    """快捷键设置标签页

    包含：
    - 快捷键列表管理
    - 快捷键捕获功能
    - 快捷键后端选择
    """

    def _setup_ui(self) -> None:
        """??UI"""
        layout = QVBoxLayout(self.widget)

        # ??????
        hotkey_list_group = QGroupBox("Registered Hotkeys")
        hotkey_list_layout = QVBoxLayout(hotkey_list_group)

        actions_layout = QHBoxLayout()
        self.hotkey_count_label = QLabel()
        actions_layout.addWidget(self.hotkey_count_label)
        actions_layout.addStretch()

        self.capture_hotkey_button = QPushButton("Capture")
        self.capture_hotkey_button.clicked.connect(self._capture_hotkey)
        actions_layout.addWidget(self.capture_hotkey_button)

        self.remove_hotkey_button = QPushButton("Remove")
        self.remove_hotkey_button.setEnabled(False)
        self.remove_hotkey_button.clicked.connect(self._remove_selected_hotkey)
        actions_layout.addWidget(self.remove_hotkey_button)

        hotkey_list_layout.addLayout(actions_layout)

        self.hotkeys_list = QListWidget()
        self.hotkeys_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.hotkeys_list.itemDoubleClicked.connect(self._edit_hotkey_item)
        self.hotkeys_list.itemSelectionChanged.connect(self._refresh_hotkey_list_ui)
        self.hotkeys_list.setSpacing(6)
        self.hotkeys_list.setFlow(QListView.Flow.LeftToRight)
        self.hotkeys_list.setWrapping(True)
        self.hotkeys_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.hotkeys_list.setUniformItemSizes(True)
        self.hotkeys_list.setWordWrap(False)
        self.hotkeys_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.hotkeys_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.hotkeys_list.setGridSize(QSize(140, 32))
        hotkey_list_layout.addWidget(self.hotkeys_list)

        self.hotkey_hint_label = QLabel("Double-click a hotkey to edit.")
        self.hotkey_hint_label.setStyleSheet("color: #888; font-size: 10px;")
        hotkey_list_layout.addWidget(self.hotkey_hint_label)

        self.hotkey_status_label = QLabel("Ready to capture hotkeys")
        self.hotkey_status_label.setWordWrap(True)
        self.hotkey_status_label.setStyleSheet("color: gray; font-style: italic;")
        hotkey_list_layout.addWidget(self.hotkey_status_label)

        layout.addWidget(hotkey_list_group)

        # Hotkey Backend Selection
        backend_group = QGroupBox("Hotkey Backend")
        backend_layout = QVBoxLayout(backend_group)

        backend_selector_layout = QHBoxLayout()
        backend_label = QLabel("Backend:")
        backend_selector_layout.addWidget(backend_label)

        self.backend_combo = QComboBox()
        self.backend_combo.addItem("Auto (Recommended)", "auto")
        self.backend_combo.addItem("Win32 RegisterHotKey (No admin needed)", "win32")
        self.backend_combo.addItem("Pynput (Admin recommended)", "pynput")
        self.backend_combo.currentIndexChanged.connect(self._on_backend_changed)
        backend_selector_layout.addWidget(self.backend_combo)
        backend_layout.addLayout(backend_selector_layout)

        # Backend info label
        self.backend_info_label = QLabel()
        self.backend_info_label.setWordWrap(True)
        self.backend_info_label.setStyleSheet(
            "color: #888; font-size: 10px; padding: 5px;"
        )
        backend_layout.addWidget(self.backend_info_label)

        layout.addWidget(backend_group)

        layout.addStretch()

        # ??????
        self.controls = {
            "hotkeys_list": self.hotkeys_list,
            "hotkey_status_label": self.hotkey_status_label,
        }

        # ?????parent_window
        self.parent_window.hotkeys_list = self.hotkeys_list
        self.parent_window.hotkey_status_label = self.hotkey_status_label

    def load_config(self, config: Dict[str, Any]) -> None:
        """从配置加载UI状态

        Args:
            config: 完整配置字典
        """
        # 快捷键列表（支持多个）
        self.hotkeys_list.clear()
        hotkeys_config = config.get("hotkeys", None)

        # 支持新旧格式
        if isinstance(hotkeys_config, dict):
            # 新格式: {"keys": [...], "backend": "auto"}
            hotkeys = hotkeys_config.get("keys", ["ctrl+shift+v"])
            backend = hotkeys_config.get("backend", "auto")
        elif isinstance(hotkeys_config, list):
            # 旧格式: ["ctrl+shift+v", "f12"]
            hotkeys = hotkeys_config
            backend = "auto"
        elif hotkeys_config is None:
            # 向后兼容单个hotkey
            single_hotkey = config.get("hotkey", "ctrl+shift+v")
            hotkeys = [single_hotkey]
            backend = "auto"
        else:
            hotkeys = ["ctrl+shift+v"]
            backend = "auto"

        # 加载快捷键到列表
        for hotkey in hotkeys:
            if hotkey and hotkey.strip():
                self.hotkeys_list.addItem(hotkey.strip())

        self._refresh_hotkey_list_ui()
        # 加载后端设置
        backend_index = self.backend_combo.findData(backend)
        if backend_index >= 0:
            self.backend_combo.setCurrentIndex(backend_index)

        # 更新后端信息显示
        self._update_backend_info(backend)

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        # 快捷键列表（保存为数组）
        hotkeys_list = []
        for i in range(self.hotkeys_list.count()):
            hotkey_text = self.hotkeys_list.item(i).text().strip()
            if hotkey_text:
                hotkeys_list.append(hotkey_text)

        # 获取后端设置
        backend = self.backend_combo.currentData()

        # 使用新格式保存：{"keys": [...], "backend": "..."}
        config = {
            "hotkeys": {
                "keys": hotkeys_list if hotkeys_list else ["ctrl+shift+v"],
                "backend": backend if backend else "auto",
            }
        }

        return config

    def _remove_selected_hotkey(self) -> None:
        """移除选中的快捷键"""
        current_row = self.hotkeys_list.currentRow()
        if current_row >= 0:
            self.hotkeys_list.takeItem(current_row)
        self._refresh_hotkey_list_ui()

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

    def _on_backend_changed(self) -> None:
        """Handle backend selection change"""
        backend = self.backend_combo.currentData()
        self._update_backend_info(backend)
        app_logger.log_audio_event("Hotkey backend changed", {"backend": backend})

    def _update_backend_info(self, backend: str) -> None:
        """Update backend information label"""
        info_map = {
            "auto": (
                "Automatically selects the best backend.\n"
                "Admin: Pynput (hooks). Non-admin: Win32 RegisterHotKey."
            ),
            "win32": (
                "Uses Windows RegisterHotKey API.\n"
                "Pros: No admin privileges required, works across privilege boundaries.\n"
                "Cons: Cannot suppress hotkey events (they still reach active window)."
            ),
            "pynput": (
                "Uses low-level keyboard hooks (SetWindowsHookEx).\n"
                "Pros: Can suppress hotkey events.\n"
                "Cons: Requires admin privileges for reliable operation, may not work across elevated windows."
            ),
        }
        info_text = info_map.get(backend, "")
        self.backend_info_label.setText(info_text)

    def _capture_hotkey(self) -> None:
        """捕获用户按下的快捷键组合 - 使用pynput"""
        try:
            from pynput import keyboard as pynput_keyboard
            from pynput.keyboard import Key

            # 禁用按钮，防止重复点击
            self.capture_hotkey_button.setEnabled(False)
            self.capture_hotkey_button.setText("Press hotkey...")

            # 清空输入框
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
            timeout_timer.start(3000)  # 3 second timeout

            # 使用QTimer检查捕获结果
            def check_capture_result():
                nonlocal captured_hotkey, listener
                if captured_hotkey:
                    timeout_timer.stop()

                    # 停止listener - pynput不会阻塞
                    if listener:
                        listener.stop()

                    # 更新输入框并自动添加到列表
                    # 检查是否已存在
                    existing_items = [
                        self.hotkeys_list.item(i).text()
                        for i in range(self.hotkeys_list.count())
                    ]
                    if captured_hotkey not in existing_items:
                        self.hotkeys_list.addItem(captured_hotkey)
                        self._refresh_hotkey_list_ui()

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
        self.capture_hotkey_button.setText("Capture")

    def _update_hotkey_status(self, status: str, is_error: bool = False) -> None:
        """更新快捷键状态显示"""
        self.hotkey_status_label.setText(status)
        if is_error:
            self.hotkey_status_label.setStyleSheet("color: red;")
        else:
            self.hotkey_status_label.setStyleSheet("color: green;")

    def _refresh_hotkey_list_ui(self) -> None:
        """Update list header and action state."""
        count = self.hotkeys_list.count()
        if count == 1:
            count_text = "1 hotkey"
        else:
            count_text = f"{count} hotkeys"
        self.hotkey_count_label.setText(count_text)
        self.remove_hotkey_button.setEnabled(self.hotkeys_list.currentRow() >= 0)

        grid = self.hotkeys_list.gridSize()
        grid_width = max(1, grid.width())
        grid_height = max(1, grid.height())
        available_width = max(1, self.hotkeys_list.viewport().width())
        columns = max(1, available_width // grid_width)
        rows = max(1, (count + columns - 1) // columns)
        self.hotkeys_list.setFixedHeight(rows * grid_height + 8)
