"""音频和输入设置标签页 (合并 Audio + Input)"""

from PySide6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QHBoxLayout,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QLabel,
)
from typing import Dict, Any
from .base_tab import BaseSettingsTab


class AudioInputTab(BaseSettingsTab):
    """音频和输入设置标签页

    包含：
    - 音频设备选择
    - 音频参数（采样率、声道数、缓冲区大小）
    - 流式转录设置
    - 输入方法选择（clipboard, sendinput）
    - 回退机制设置
    - 剪贴板设置
    - SendInput设置
    - 兼容性测试
    """

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 音频设备组
        device_group = QGroupBox("Audio Device Settings")
        device_layout = QFormLayout(device_group)

        # 输入设备
        self.audio_device_combo = QComboBox()
        self.refresh_devices_button = QPushButton("Refresh")
        self.refresh_devices_button.clicked.connect(self._refresh_audio_devices)

        device_input_layout = QHBoxLayout()
        device_input_layout.addWidget(self.audio_device_combo)
        device_input_layout.addWidget(self.refresh_devices_button)

        device_layout.addRow("Input Device:", device_input_layout)

        layout.addWidget(device_group)

        # 音频参数组
        params_group = QGroupBox("Audio Parameters")
        params_layout = QFormLayout(params_group)

        # 采样率
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["8000", "16000", "22050", "44100", "48000"])
        params_layout.addRow("Sample Rate:", self.sample_rate_combo)

        # 声道数
        self.channels_spinbox = QSpinBox()
        self.channels_spinbox.setRange(1, 2)
        params_layout.addRow("Channels:", self.channels_spinbox)

        # 缓冲区大小
        self.chunk_size_spinbox = QSpinBox()
        self.chunk_size_spinbox.setRange(512, 8192)
        self.chunk_size_spinbox.setSingleStep(512)
        params_layout.addRow("Chunk Size:", self.chunk_size_spinbox)

        # 流式转录块大小
        self.streaming_chunk_duration_spinbox = QDoubleSpinBox()
        self.streaming_chunk_duration_spinbox.setRange(5.0, 60.0)
        self.streaming_chunk_duration_spinbox.setSingleStep(5.0)
        self.streaming_chunk_duration_spinbox.setSuffix(" seconds")
        self.streaming_chunk_duration_spinbox.setToolTip(
            "Duration of each audio chunk for streaming transcription (5-60 seconds)"
        )
        params_layout.addRow(
            "Streaming Chunk Duration:", self.streaming_chunk_duration_spinbox
        )

        layout.addWidget(params_group)

        # 输入方法组
        method_group = QGroupBox("Text Input Method")
        method_layout = QFormLayout(method_group)

        # 首选方法
        self.input_method_combo = QComboBox()
        self.input_method_combo.addItems(["clipboard", "sendinput"])
        method_layout.addRow("Preferred Method:", self.input_method_combo)

        # 启用回退
        self.fallback_enabled_checkbox = QCheckBox(
            "Enable fallback to alternative method"
        )
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
            "audio_device": self.audio_device_combo,
            "sample_rate": self.sample_rate_combo,
            "channels": self.channels_spinbox,
            "chunk_size": self.chunk_size_spinbox,
            "streaming_chunk_duration": self.streaming_chunk_duration_spinbox,
            "input_method": self.input_method_combo,
            "fallback_enabled": self.fallback_enabled_checkbox,
            "auto_detect": self.auto_detect_checkbox,
            "clipboard_delay": self.clipboard_delay_spinbox,
            "typing_delay": self.typing_delay_spinbox,
            "test_status": self.input_test_status_label,
        }

        # 暴露控件到parent_window
        self.parent_window.audio_device_combo = self.audio_device_combo
        self.parent_window.sample_rate_combo = self.sample_rate_combo
        self.parent_window.channels_spinbox = self.channels_spinbox
        self.parent_window.chunk_size_spinbox = self.chunk_size_spinbox
        self.parent_window.streaming_chunk_duration_spinbox = (
            self.streaming_chunk_duration_spinbox
        )
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
        audio_config = config.get("audio", {})
        input_config = config.get("input", {})

        # Audio settings
        self.sample_rate_combo.setCurrentText(
            str(audio_config.get("sample_rate", 16000))
        )
        self.channels_spinbox.setValue(audio_config.get("channels", 1))
        self.chunk_size_spinbox.setValue(audio_config.get("chunk_size", 1024))

        # Streaming settings
        streaming_config = audio_config.get("streaming", {})
        self.streaming_chunk_duration_spinbox.setValue(
            streaming_config.get("chunk_duration", 30.0)
        )

        # Audio device - 使用 itemData 查找真实设备 ID
        device_id = audio_config.get("device_id")
        # 在下拉框中查找匹配的设备 ID
        if device_id is not None:
            for i in range(self.audio_device_combo.count()):
                if self.audio_device_combo.itemData(i) == device_id:
                    self.audio_device_combo.setCurrentIndex(i)
                    break

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
        self.typing_delay_spinbox.setValue(input_config.get("typing_delay", 0.01))

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        # 使用 currentData() 获取真实的 PyAudio 设备 ID
        device_id = self.audio_device_combo.currentData()

        config = {
            "audio": {
                "sample_rate": int(self.sample_rate_combo.currentText()),
                "channels": self.channels_spinbox.value(),
                "chunk_size": self.chunk_size_spinbox.value(),
                "device_id": device_id,  # 保存真实的设备 ID，而不是下拉框索引
                "streaming": {
                    "chunk_duration": self.streaming_chunk_duration_spinbox.value(),
                },
            },
            "input": {
                "preferred_method": self.input_method_combo.currentText(),
                "fallback_enabled": self.fallback_enabled_checkbox.isChecked(),
                "auto_detect_terminal": self.auto_detect_checkbox.isChecked(),
                "clipboard_restore_delay": self.clipboard_delay_spinbox.value(),
                "typing_delay": self.typing_delay_spinbox.value(),
            },
        }

        return config

    def _refresh_audio_devices(self) -> None:
        """刷新音频设备列表 - 调用父窗口的方法"""
        if hasattr(self.parent_window, "refresh_audio_devices"):
            self.parent_window.refresh_audio_devices()

    def update_device_list(self, devices: list) -> None:
        """更新设备列表

        Args:
            devices: 设备名称列表
        """
        current_index = self.audio_device_combo.currentIndex()
        self.audio_device_combo.clear()
        self.audio_device_combo.addItems(devices)

        # 尝试恢复之前选中的设备
        if current_index >= 0 and current_index < len(devices):
            self.audio_device_combo.setCurrentIndex(current_index)

    def _test_clipboard(self) -> None:
        """测试剪贴板方法 - 调用父窗口的方法"""
        if hasattr(self.parent_window, "test_clipboard"):
            self.parent_window.test_clipboard()

    def _test_sendinput(self) -> None:
        """测试SendInput方法 - 调用父窗口的方法"""
        if hasattr(self.parent_window, "test_sendinput"):
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
