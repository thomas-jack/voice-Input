"""Whisper设置标签页"""

from PySide6.QtWidgets import (QVBoxLayout, QGroupBox, QFormLayout,
                            QCheckBox, QComboBox, QDoubleSpinBox, QPushButton, QHBoxLayout, QLabel, QProgressBar, QLineEdit, QWidget)
from typing import Dict, Any
from .base_tab import BaseSettingsTab


class WhisperTab(BaseSettingsTab):
    """Whisper设置标签页

    包含：
    - 转录提供商选择（Local / Groq）
    - Local Whisper 模型配置
    - Groq API 配置
    - 模型管理（加载/卸载/测试）
    - GPU信息显示
    """

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 转录提供商选择组
        provider_group = QGroupBox("Transcription Provider")
        provider_layout = QFormLayout(provider_group)

        self.transcription_provider_combo = QComboBox()
        self.transcription_provider_combo.addItems(["local", "groq"])
        self.transcription_provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addRow("Provider:", self.transcription_provider_combo)

        layout.addWidget(provider_group)

        # Local Whisper 模型设置组
        model_group = QGroupBox("Local Whisper Configuration")
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
        self.management_group = management_group

        # Groq API 配置组
        groq_group = QGroupBox("Groq Cloud API Configuration")
        groq_layout = QFormLayout(groq_group)

        # API Key
        self.groq_api_key_edit = QLineEdit()
        self.groq_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.groq_api_key_edit.setPlaceholderText("Enter Groq API key")
        self.groq_api_key_edit.textChanged.connect(self._on_groq_api_key_changed)
        groq_layout.addRow("API Key:", self.groq_api_key_edit)

        # 模型选择
        self.groq_model_combo = QComboBox()
        self.groq_model_combo.addItems([
            "whisper-large-v3-turbo",
            "whisper-large-v3"
        ])
        groq_layout.addRow("Model:", self.groq_model_combo)

        layout.addWidget(groq_group)
        self.groq_group = groq_group

        # GPU信息组
        gpu_group = QGroupBox("GPU Information (Local Only)")
        gpu_layout = QFormLayout(gpu_group)

        self.gpu_status_label = QLabel("Checking...")
        gpu_layout.addRow("Status:", self.gpu_status_label)

        self.gpu_memory_label = QLabel("N/A")
        gpu_layout.addRow("Memory Usage:", self.gpu_memory_label)

        layout.addWidget(gpu_group)
        self.gpu_group = gpu_group
        self.model_group = model_group

        layout.addStretch()

        # 保存控件引用
        self.controls = {
            'transcription_provider': self.transcription_provider_combo,
            'whisper_model': self.whisper_model_combo,
            'whisper_language': self.whisper_language_combo,
            'use_gpu': self.use_gpu_checkbox,
            'auto_load_model': self.auto_load_model_checkbox,
            'temperature': self.whisper_temperature_spinbox,
            'groq_api_key': self.groq_api_key_edit,
            'groq_model': self.groq_model_combo,
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
        # 转录配置（新）
        transcription_config = config.get("transcription", {})
        provider = transcription_config.get("provider", "local")
        self.transcription_provider_combo.setCurrentText(provider)

        # Local Whisper settings
        local_config = transcription_config.get("local", {})
        # Fallback to old whisper config for backward compatibility
        whisper_config = config.get("whisper", {})

        self.whisper_model_combo.setCurrentText(
            local_config.get("model", whisper_config.get("model", "large-v3-turbo"))
        )
        self.whisper_language_combo.setCurrentText(
            local_config.get("language", whisper_config.get("language", "auto"))
        )
        self.use_gpu_checkbox.setChecked(
            local_config.get("use_gpu", whisper_config.get("use_gpu", True))
        )
        self.auto_load_model_checkbox.setChecked(
            local_config.get("auto_load", whisper_config.get("auto_load", True))
        )
        self.whisper_temperature_spinbox.setValue(
            local_config.get("temperature", whisper_config.get("temperature", 0.0))
        )

        # Groq settings
        groq_config = transcription_config.get("groq", {})
        self.groq_api_key_edit.setText(
            groq_config.get("api_key", "")
        )
        self.groq_model_combo.setCurrentText(
            groq_config.get("model", "whisper-large-v3-turbo")
        )

        # Update visibility based on provider
        self._on_provider_changed(provider)

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        config = {
            "transcription": {
                "provider": self.transcription_provider_combo.currentText(),
                "local": {
                    "model": self.whisper_model_combo.currentText(),
                    "language": self.whisper_language_combo.currentText(),
                    "use_gpu": self.use_gpu_checkbox.isChecked(),
                    "auto_load": self.auto_load_model_checkbox.isChecked(),
                    "temperature": self.whisper_temperature_spinbox.value(),
                },
                "groq": {
                    "api_key": self.groq_api_key_edit.text(),
                    "model": self.groq_model_combo.currentText(),
                }
            },
            # Keep old whisper config for backward compatibility
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
        """测试模型或 API 连接 - 根据提供商类型"""
        provider = self.transcription_provider_combo.currentText()

        if provider == "local":
            # Local 模式：测试本地模型
            if hasattr(self.parent_window, 'model_test_requested'):
                self.parent_window.model_test_requested.emit()
        elif provider == "groq":
            # Groq 模式：测试 API 连接
            self._test_groq_api()

    def _test_groq_api(self) -> None:
        """测试 Groq API 连接"""
        from PySide6.QtWidgets import QMessageBox
        import numpy as np

        # 检查 API key
        api_key = self.groq_api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(
                self.parent_window,
                "API Key Missing",
                "Please enter your Groq API key first."
            )
            return

        # 显示测试中状态
        self.model_status_label.setText("Testing API connection...")

        try:
            # 导入并创建 Groq 服务 - 使用绝对导入
            from sonicinput.speech import GroqSpeechService

            model = self.groq_model_combo.currentText()
            service = GroqSpeechService(api_key=api_key, model=model)

            # 尝试初始化客户端
            success = service.load_model()

            if success:
                self.model_status_label.setText("API connection successful")
                QMessageBox.information(
                    self.parent_window,
                    "API Test Successful",
                    f"Successfully connected to Groq API!\n\nModel: {model}\n\nYou can now use cloud transcription."
                )
            else:
                self.model_status_label.setText("API connection failed")
                QMessageBox.critical(
                    self.parent_window,
                    "API Test Failed",
                    "Failed to connect to Groq API.\n\nPlease check:\n- API key is valid\n- Internet connection\n- Groq service status"
                )

        except Exception as e:
            self.model_status_label.setText("API test error")
            QMessageBox.critical(
                self.parent_window,
                "API Test Error",
                f"Error testing Groq API:\n\n{str(e)}\n\nPlease check your API key and try again."
            )

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

    def _on_provider_changed(self, provider: str) -> None:
        """当转录提供商改变时更新UI显示

        Args:
            provider: 提供商名称 ("local" 或 "groq")
        """
        is_local = provider == "local"

        # 显示/隐藏 Local Whisper 配置
        self.model_group.setVisible(is_local)
        self.gpu_group.setVisible(is_local)

        # 显示/隐藏 Groq 配置
        self.groq_group.setVisible(not is_local)

        # 调整 Model Management 区域
        if is_local:
            # Local 模式：显示模型管理
            self.management_group.setTitle("Model Management")
            self.model_status_label.setText("Model not loaded" if not hasattr(self, '_model_loaded') else
                                           ("Model loaded" if self._model_loaded else "Model not loaded"))
            self.load_model_button.setVisible(True)
            self.unload_model_button.setVisible(True)
            self.test_model_button.setText("Test Model")
        else:
            # Groq 模式：显示 API 测试
            self.management_group.setTitle("API Connection Test")
            self.model_status_label.setText("API key configured" if self.groq_api_key_edit.text().strip() else "API key not configured")
            self.load_model_button.setVisible(False)
            self.unload_model_button.setVisible(False)
            self.test_model_button.setText("Test API Connection")

    def _on_groq_api_key_changed(self, text: str) -> None:
        """当 Groq API key 改变时更新状态

        Args:
            text: API key 文本
        """
        # 只在 Groq 模式下更新状态
        provider = self.transcription_provider_combo.currentText()
        if provider == "groq":
            if text.strip():
                self.model_status_label.setText("API key configured")
            else:
                self.model_status_label.setText("API key not configured")
