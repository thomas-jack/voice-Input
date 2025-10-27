"""Whisper设置标签页"""

from PyQt6.QtWidgets import (QVBoxLayout, QGroupBox, QFormLayout,
                            QCheckBox, QComboBox, QDoubleSpinBox, QPushButton, QHBoxLayout, QLabel, QProgressBar)
from typing import Dict, Any
from .base_tab import BaseSettingsTab


class WhisperTab(BaseSettingsTab):
    """Whisper设置标签页

    包含：
    - 模型选择
    - 语言设置
    - GPU设置
    - 模型管理（加载/卸载/测试）
    - GPU信息显示
    """

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 模型设置组
        model_group = QGroupBox("Whisper Model Configuration")
        model_layout = QFormLayout(model_group)

        # 模型选择
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems([
            "tiny", "base", "small", "medium",
            "large-v3", "large-v3-turbo",
            "turbo"
        ])
        model_layout.addRow("Model:", self.whisper_model_combo)

        # 语言设置
        self.whisper_language_combo = QComboBox()
        self.whisper_language_combo.addItems([
            "auto", "en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt", "ru"
        ])
        model_layout.addRow("Language:", self.whisper_language_combo)

        # GPU使用
        self.use_gpu_checkbox = QCheckBox("Use GPU acceleration (CUDA)")
        model_layout.addRow("GPU:", self.use_gpu_checkbox)

        # 自动加载
        self.auto_load_model_checkbox = QCheckBox("Load model on startup")
        model_layout.addRow("", self.auto_load_model_checkbox)

        # Temperature
        self.whisper_temperature_spinbox = QDoubleSpinBox()
        self.whisper_temperature_spinbox.setRange(0.0, 1.0)
        self.whisper_temperature_spinbox.setSingleStep(0.1)
        self.whisper_temperature_spinbox.setDecimals(1)
        model_layout.addRow("Temperature:", self.whisper_temperature_spinbox)

        layout.addWidget(model_group)

        # 模型管理组
        management_group = QGroupBox("Model Management")
        management_layout = QVBoxLayout(management_group)

        # 当前状态
        self.model_status_label = QLabel("Model not loaded")
        management_layout.addWidget(self.model_status_label)

        # 操作按钮
        model_buttons_layout = QHBoxLayout()

        self.load_model_button = QPushButton("Load Model")
        self.load_model_button.clicked.connect(self._load_model)
        model_buttons_layout.addWidget(self.load_model_button)

        self.unload_model_button = QPushButton("Unload Model")
        self.unload_model_button.clicked.connect(self._unload_model)
        model_buttons_layout.addWidget(self.unload_model_button)

        self.test_model_button = QPushButton("Test Model")
        self.test_model_button.clicked.connect(self._test_model)
        model_buttons_layout.addWidget(self.test_model_button)

        management_layout.addLayout(model_buttons_layout)

        # 进度条
        self.model_progress = QProgressBar()
        self.model_progress.hide()
        management_layout.addWidget(self.model_progress)

        layout.addWidget(management_group)

        # GPU信息组
        gpu_group = QGroupBox("GPU Information")
        gpu_layout = QFormLayout(gpu_group)

        self.gpu_status_label = QLabel("Checking...")
        gpu_layout.addRow("Status:", self.gpu_status_label)

        self.gpu_memory_label = QLabel("N/A")
        gpu_layout.addRow("Memory Usage:", self.gpu_memory_label)

        layout.addWidget(gpu_group)

        layout.addStretch()

        # 保存控件引用
        self.controls = {
            'whisper_model': self.whisper_model_combo,
            'whisper_language': self.whisper_language_combo,
            'use_gpu': self.use_gpu_checkbox,
            'auto_load_model': self.auto_load_model_checkbox,
            'temperature': self.whisper_temperature_spinbox,
            'model_status': self.model_status_label,
            'gpu_status': self.gpu_status_label,
            'gpu_memory': self.gpu_memory_label,
        }

        # 暴露控件到parent_window
        self.parent_window.whisper_model_combo = self.whisper_model_combo
        self.parent_window.whisper_language_combo = self.whisper_language_combo
        self.parent_window.use_gpu_checkbox = self.use_gpu_checkbox
        self.parent_window.auto_load_model_checkbox = self.auto_load_model_checkbox
        self.parent_window.whisper_temperature_spinbox = self.whisper_temperature_spinbox
        self.parent_window.model_status_label = self.model_status_label
        self.parent_window.gpu_status_label = self.gpu_status_label
        self.parent_window.gpu_memory_label = self.gpu_memory_label

    def load_config(self, config: Dict[str, Any]) -> None:
        """从配置加载UI状态

        Args:
            config: 完整配置字典
        """
        whisper_config = config.get("whisper", {})

        # Whisper settings
        self.whisper_model_combo.setCurrentText(
            whisper_config.get("model", "large-v3-turbo")
        )
        self.whisper_language_combo.setCurrentText(
            whisper_config.get("language", "auto")
        )
        self.use_gpu_checkbox.setChecked(
            whisper_config.get("use_gpu", True)
        )
        self.auto_load_model_checkbox.setChecked(
            whisper_config.get("auto_load", True)
        )
        self.whisper_temperature_spinbox.setValue(
            whisper_config.get("temperature", 0.0)
        )

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        config = {
            "whisper": {
                "model": self.whisper_model_combo.currentText(),
                "language": self.whisper_language_combo.currentText(),
                "use_gpu": self.use_gpu_checkbox.isChecked(),
                "auto_load": self.auto_load_model_checkbox.isChecked(),
                "temperature": self.whisper_temperature_spinbox.value(),
            }
        }

        return config

    def _load_model(self) -> None:
        """加载模型 - 发送信号到父窗口"""
        model_name = self.whisper_model_combo.currentText()
        if hasattr(self.parent_window, 'model_load_requested'):
            self.parent_window.model_load_requested.emit(model_name)

    def _unload_model(self) -> None:
        """卸载模型 - 发送信号到父窗口"""
        if hasattr(self.parent_window, 'unload_model'):
            self.parent_window.unload_model()

    def _test_model(self) -> None:
        """测试模型 - 发送信号到父窗口"""
        if hasattr(self.parent_window, 'model_test_requested'):
            self.parent_window.model_test_requested.emit()

    def update_model_status(self, status: str) -> None:
        """更新模型状态显示

        Args:
            status: 状态文本
        """
        self.model_status_label.setText(status)

    def update_gpu_status(self, status: str) -> None:
        """更新GPU状态显示

        Args:
            status: 状态文本
        """
        self.gpu_status_label.setText(status)

    def update_gpu_memory(self, memory: str) -> None:
        """更新GPU内存显示

        Args:
            memory: 内存信息文本
        """
        self.gpu_memory_label.setText(memory)

    def show_progress(self, visible: bool = True) -> None:
        """显示/隐藏进度条

        Args:
            visible: 是否显示
        """
        if visible:
            self.model_progress.show()
        else:
            self.model_progress.hide()

    def set_progress(self, value: int) -> None:
        """设置进度条值

        Args:
            value: 进度值 (0-100)
        """
        self.model_progress.setValue(value)
