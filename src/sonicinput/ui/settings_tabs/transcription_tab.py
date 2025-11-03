"""Transcription设置标签页"""

from PySide6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QLineEdit,
)
from typing import Dict, Any, Optional
from .base_tab import BaseSettingsTab


class TranscriptionTab(BaseSettingsTab):
    """Transcription设置标签页

    包含：
    - 转录提供商选择（Local Whisper / Groq / SiliconFlow / Doubao）
    - Local Whisper 模型配置
    - 云服务 API 配置（Groq / SiliconFlow / Doubao）
    - 模型管理（加载/卸载/测试）
    - GPU信息显示（仅本地模式）
    """

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 转录提供商选择组
        provider_group = QGroupBox("Transcription Provider")
        provider_layout = QFormLayout(provider_group)

        self.transcription_provider_combo = QComboBox()
        self.transcription_provider_combo.addItems(["local", "groq", "siliconflow", "doubao"])
        self.transcription_provider_combo.currentTextChanged.connect(
            self._on_provider_changed
        )
        provider_layout.addRow("Provider:", self.transcription_provider_combo)

        layout.addWidget(provider_group)

        # Local Whisper 模型设置组
        model_group = QGroupBox("Local Whisper Configuration")
        model_layout = QFormLayout(model_group)

        # 模型选择
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems(
            ["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo", "turbo"]
        )
        model_layout.addRow("Model:", self.whisper_model_combo)

        # 语言设置
        self.whisper_language_combo = QComboBox()
        self.whisper_language_combo.addItems(
            ["auto", "en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt", "ru"]
        )
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

        # Base URL
        self.groq_base_url_edit = QLineEdit()
        self.groq_base_url_edit.setPlaceholderText("Leave empty to restore default")
        groq_layout.addRow("Base URL:", self.groq_base_url_edit)

        # 模型选择（支持自定义输入）
        self.groq_model_combo = QComboBox()
        self.groq_model_combo.setEditable(True)  # 允许用户自定义输入
        self.groq_model_combo.addItems(["whisper-large-v3-turbo", "whisper-large-v3"])
        groq_layout.addRow("Model:", self.groq_model_combo)

        # 超时设置
        self.groq_timeout_spinbox = QSpinBox()
        self.groq_timeout_spinbox.setRange(5, 120)
        self.groq_timeout_spinbox.setValue(30)
        self.groq_timeout_spinbox.setSuffix("s")
        groq_layout.addRow("Timeout:", self.groq_timeout_spinbox)

        # 重试设置
        self.groq_max_retries_spinbox = QSpinBox()
        self.groq_max_retries_spinbox.setRange(0, 10)
        self.groq_max_retries_spinbox.setValue(3)
        groq_layout.addRow("Max Retries:", self.groq_max_retries_spinbox)

        layout.addWidget(groq_group)
        self.groq_group = groq_group

        # SiliconFlow API 配置组
        siliconflow_group = QGroupBox("SiliconFlow Cloud API Configuration")
        siliconflow_layout = QFormLayout(siliconflow_group)

        # API Key
        self.siliconflow_api_key_edit = QLineEdit()
        self.siliconflow_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.siliconflow_api_key_edit.setPlaceholderText("Enter SiliconFlow API key")
        self.siliconflow_api_key_edit.textChanged.connect(
            self._on_siliconflow_api_key_changed
        )
        siliconflow_layout.addRow("API Key:", self.siliconflow_api_key_edit)

        # Base URL
        self.siliconflow_base_url_edit = QLineEdit()
        self.siliconflow_base_url_edit.setPlaceholderText(
            "Leave empty to restore default"
        )
        siliconflow_layout.addRow("Base URL:", self.siliconflow_base_url_edit)

        # 模型选择（支持自定义输入）
        self.siliconflow_model_combo = QComboBox()
        self.siliconflow_model_combo.setEditable(True)  # 允许用户自定义输入
        self.siliconflow_model_combo.addItems(
            ["FunAudioLLM/SenseVoiceSmall", "TeleAI/TeleSpeechASR"]
        )
        self.siliconflow_model_combo.setCurrentText("FunAudioLLM/SenseVoiceSmall")
        siliconflow_layout.addRow("Model:", self.siliconflow_model_combo)

        # 超时设置
        self.siliconflow_timeout_spinbox = QSpinBox()
        self.siliconflow_timeout_spinbox.setRange(5, 120)
        self.siliconflow_timeout_spinbox.setValue(30)
        self.siliconflow_timeout_spinbox.setSuffix("s")
        siliconflow_layout.addRow("Timeout:", self.siliconflow_timeout_spinbox)

        # 重试设置
        self.siliconflow_max_retries_spinbox = QSpinBox()
        self.siliconflow_max_retries_spinbox.setRange(0, 10)
        self.siliconflow_max_retries_spinbox.setValue(3)
        siliconflow_layout.addRow("Max Retries:", self.siliconflow_max_retries_spinbox)

        layout.addWidget(siliconflow_group)
        self.siliconflow_group = siliconflow_group

        # Doubao API 配置组
        doubao_group = QGroupBox("Doubao (ByteDance) Cloud API Configuration")
        doubao_layout = QFormLayout(doubao_group)

        # API Key / Token
        self.doubao_api_key_edit = QLineEdit()
        self.doubao_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.doubao_api_key_edit.setPlaceholderText("Enter Doubao API key or token")
        self.doubao_api_key_edit.textChanged.connect(
            self._on_doubao_api_key_changed
        )
        doubao_layout.addRow("API Key/Token:", self.doubao_api_key_edit)

        # App ID
        self.doubao_app_id_edit = QLineEdit()
        self.doubao_app_id_edit.setPlaceholderText("App ID (numeric, default: 388808087185088)")
        doubao_layout.addRow("App ID:", self.doubao_app_id_edit)

        # Model Type
        self.doubao_model_type_combo = QComboBox()
        self.doubao_model_type_combo.addItems(["standard", "fast"])
        self.doubao_model_type_combo.setToolTip("Standard: Higher accuracy, slower. Fast: Lower accuracy, faster.")
        doubao_layout.addRow("Model Type:", self.doubao_model_type_combo)

        # Cluster (auto-filled based on model type)
        self.doubao_cluster_edit = QLineEdit()
        self.doubao_cluster_edit.setPlaceholderText("Auto-filled based on model type")
        self.doubao_cluster_edit.setReadOnly(True)
        doubao_layout.addRow("Cluster:", self.doubao_cluster_edit)

        # Base URL
        self.doubao_base_url_edit = QLineEdit()
        self.doubao_base_url_edit.setPlaceholderText(
            "Leave empty to restore default"
        )
        doubao_layout.addRow("Base URL:", self.doubao_base_url_edit)

        # 超时设置
        self.doubao_timeout_spinbox = QSpinBox()
        self.doubao_timeout_spinbox.setRange(10, 180)
        self.doubao_timeout_spinbox.setValue(30)
        self.doubao_timeout_spinbox.setSuffix("s")
        doubao_layout.addRow("Timeout:", self.doubao_timeout_spinbox)

        # 重试设置
        self.doubao_max_retries_spinbox = QSpinBox()
        self.doubao_max_retries_spinbox.setRange(0, 10)
        self.doubao_max_retries_spinbox.setValue(3)
        doubao_layout.addRow("Max Retries:", self.doubao_max_retries_spinbox)

        layout.addWidget(doubao_group)
        self.doubao_group = doubao_group

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
            "transcription_provider": self.transcription_provider_combo,
            "whisper_model": self.whisper_model_combo,
            "whisper_language": self.whisper_language_combo,
            "use_gpu": self.use_gpu_checkbox,
            "auto_load_model": self.auto_load_model_checkbox,
            "temperature": self.whisper_temperature_spinbox,
            "groq_api_key": self.groq_api_key_edit,
            "groq_base_url": self.groq_base_url_edit,
            "groq_model": self.groq_model_combo,
            "groq_timeout": self.groq_timeout_spinbox,
            "groq_max_retries": self.groq_max_retries_spinbox,
            "siliconflow_api_key": self.siliconflow_api_key_edit,
            "siliconflow_base_url": self.siliconflow_base_url_edit,
            "siliconflow_model": self.siliconflow_model_combo,
            "siliconflow_timeout": self.siliconflow_timeout_spinbox,
            "siliconflow_max_retries": self.siliconflow_max_retries_spinbox,
            "doubao_api_key": self.doubao_api_key_edit,
            "doubao_app_id": self.doubao_app_id_edit,
            "doubao_model_type": self.doubao_model_type_combo,
            "doubao_cluster": self.doubao_cluster_edit,
            "doubao_base_url": self.doubao_base_url_edit,
            "doubao_timeout": self.doubao_timeout_spinbox,
            "doubao_max_retries": self.doubao_max_retries_spinbox,
            "model_status": self.model_status_label,
            "gpu_status": self.gpu_status_label,
            "gpu_memory": self.gpu_memory_label,
        }

        # 暴露控件到parent_window
        self.parent_window.whisper_model_combo = self.whisper_model_combo
        self.parent_window.whisper_language_combo = self.whisper_language_combo
        self.parent_window.use_gpu_checkbox = self.use_gpu_checkbox
        self.parent_window.auto_load_model_checkbox = self.auto_load_model_checkbox
        self.parent_window.whisper_temperature_spinbox = (
            self.whisper_temperature_spinbox
        )
        self.parent_window.model_status_label = self.model_status_label
        self.parent_window.gpu_status_label = self.gpu_status_label
        self.parent_window.gpu_memory_label = self.gpu_memory_label

        # Connect Doubao model type change signal
        self.doubao_model_type_combo.currentTextChanged.connect(self._on_doubao_model_type_changed)

        # Initialize cluster display
        self._update_doubao_cluster_display()

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
        self.groq_api_key_edit.setText(groq_config.get("api_key", ""))
        self.groq_base_url_edit.setText(
            groq_config.get("base_url", "https://api.groq.com/openai/v1")
        )
        self.groq_model_combo.setCurrentText(
            groq_config.get("model", "whisper-large-v3-turbo")
        )
        self.groq_timeout_spinbox.setValue(groq_config.get("timeout", 30))
        self.groq_max_retries_spinbox.setValue(groq_config.get("max_retries", 3))

        # SiliconFlow settings
        siliconflow_config = transcription_config.get("siliconflow", {})
        self.siliconflow_api_key_edit.setText(siliconflow_config.get("api_key", ""))
        self.siliconflow_base_url_edit.setText(
            siliconflow_config.get("base_url", "https://api.siliconflow.cn/v1")
        )
        self.siliconflow_model_combo.setCurrentText(
            siliconflow_config.get("model", "FunAudioLLM/SenseVoiceSmall")
        )
        self.siliconflow_timeout_spinbox.setValue(siliconflow_config.get("timeout", 30))
        self.siliconflow_max_retries_spinbox.setValue(
            siliconflow_config.get("max_retries", 3)
        )

        # Doubao settings
        doubao_config = transcription_config.get("doubao", {})
        self.doubao_api_key_edit.setText(doubao_config.get("api_key", ""))
        self.doubao_app_id_edit.setText(doubao_config.get("app_id", "388808087185088"))
        self.doubao_model_type_combo.setCurrentText(doubao_config.get("model_type", "standard"))
        self.doubao_cluster_edit.setText(doubao_config.get("cluster", "volc_asr_public"))
        self.doubao_base_url_edit.setText(
            doubao_config.get("base_url", "https://openspeech.bytedance.com")
        )
        self.doubao_timeout_spinbox.setValue(doubao_config.get("timeout", 30))
        self.doubao_max_retries_spinbox.setValue(doubao_config.get("max_retries", 3))

        # Update cluster display based on model type
        self._update_doubao_cluster_display()

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
                    "base_url": self.groq_base_url_edit.text().strip()
                    or "https://api.groq.com/openai/v1",
                    "model": self.groq_model_combo.currentText(),
                    "timeout": self.groq_timeout_spinbox.value(),
                    "max_retries": self.groq_max_retries_spinbox.value(),
                },
                "siliconflow": {
                    "api_key": self.siliconflow_api_key_edit.text(),
                    "base_url": self.siliconflow_base_url_edit.text().strip()
                    or "https://api.siliconflow.cn/v1",
                    "model": self.siliconflow_model_combo.currentText(),
                    "timeout": self.siliconflow_timeout_spinbox.value(),
                    "max_retries": self.siliconflow_max_retries_spinbox.value(),
                },
                "doubao": {
                    "api_key": self.doubao_api_key_edit.text(),
                    "app_id": self.doubao_app_id_edit.text().strip()
                    or "388808087185088",
                    "token": self.doubao_api_key_edit.text(),  # Same as api_key for compatibility
                    "model_type": self.doubao_model_type_combo.currentText(),
                    "cluster": self.doubao_cluster_edit.text().strip()
                    or ("common" if self.doubao_model_type_combo.currentText() == "fast" else "volc_asr_public"),
                    "base_url": self.doubao_base_url_edit.text().strip()
                    or "https://openspeech.bytedance.com",
                    "timeout": self.doubao_timeout_spinbox.value(),
                    "max_retries": self.doubao_max_retries_spinbox.value(),
                },
            },
            # Keep old whisper config for backward compatibility
            "whisper": {
                "model": self.whisper_model_combo.currentText(),
                "language": self.whisper_language_combo.currentText(),
                "use_gpu": self.use_gpu_checkbox.isChecked(),
                "auto_load": self.auto_load_model_checkbox.isChecked(),
                "temperature": self.whisper_temperature_spinbox.value(),
            },
        }

        return config

    def _load_model(self) -> None:
        """加载模型 - 发送信号到父窗口"""
        model_name = self.whisper_model_combo.currentText()
        if hasattr(self.parent_window, "model_load_requested"):
            self.parent_window.model_load_requested.emit(model_name)

    def _unload_model(self) -> None:
        """卸载模型 - 发送信号到父窗口"""
        if hasattr(self.parent_window, "unload_model"):
            self.parent_window.unload_model()

    def _test_model(self) -> None:
        """测试模型或 API 连接 - 根据提供商类型"""
        provider = self.transcription_provider_combo.currentText()

        if provider == "local":
            # Local 模式：测试本地模型
            if hasattr(self.parent_window, "model_test_requested"):
                self.parent_window.model_test_requested.emit()
        elif provider == "groq":
            # Groq 模式：测试 API 连接
            self._test_groq_api()
        elif provider == "siliconflow":
            # SiliconFlow 模式：测试 API 连接
            self._test_siliconflow_api()
        elif provider == "doubao":
            # Doubao 模式：测试 API 连接
            self._test_doubao_api()

    def _test_groq_api(self) -> None:
        """测试 Groq API 连接（异步，不阻塞UI）"""
        from PySide6.QtWidgets import QMessageBox, QApplication
        from PySide6.QtCore import QTimer
        import threading
        import time

        # 检查 API key
        api_key = self.groq_api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(
                self.parent_window,
                "API Key Missing",
                "Please enter your Groq API key first.",
            )
            return

        # 显示测试中对话框
        model = self.groq_model_combo.currentText()
        progress_dialog = QMessageBox(self.parent_window)
        progress_dialog.setWindowTitle("Testing Groq API")
        progress_dialog.setText(
            f"Testing Groq API connection...\n\nModel: {model}\n\nThis may take a few seconds."
        )
        progress_dialog.setStandardButtons(QMessageBox.StandardButton.Cancel)
        progress_dialog.show()

        # 处理事件以显示对话框
        QApplication.processEvents()

        # 创建后台线程运行测试
        result_container = {"success": False, "error": ""}

        def test_connection_thread():
            try:
                from sonicinput.speech import GroqSpeechService

                service = GroqSpeechService(api_key=api_key, model=model)
                success = service.load_model()
                result_container["success"] = success

                if not success:
                    result_container["error"] = "Failed to initialize Groq client"

            except Exception as e:
                result_container["success"] = False
                result_container["error"] = str(e)

        # 启动测试线程
        test_thread = threading.Thread(target=test_connection_thread, daemon=True)
        test_thread.start()

        # 保存测试状态
        self._groq_test_thread = test_thread
        self._groq_test_result = result_container
        self._groq_progress_dialog = progress_dialog
        self._groq_test_start_time = time.time()
        self._groq_test_model = model

        # 创建定时器轮询测试状态
        self._groq_test_timer = QTimer()
        self._groq_test_timer.timeout.connect(self._check_groq_test_status)
        self._groq_test_timer.start(100)  # 每100ms检查一次

    def _check_groq_test_status(self) -> None:
        """检查 Groq API 测试状态"""
        from PySide6.QtWidgets import QMessageBox
        import time

        try:
            thread_alive = self._groq_test_thread.is_alive()
            elapsed_time = time.time() - self._groq_test_start_time

            # 检查测试线程是否完成
            if not thread_alive:
                # 测试完成，停止定时器
                self._groq_test_timer.stop()
                self._groq_progress_dialog.close()

                # 显示结果
                if self._groq_test_result["success"]:
                    self.model_status_label.setText("API connection successful")
                    QMessageBox.information(
                        self.parent_window,
                        "API Test Successful",
                        f"Successfully connected to Groq API!\n\nModel: {self._groq_test_model}\n\nYou can now use cloud transcription.",
                    )
                else:
                    error_msg = self._groq_test_result["error"] or "Unknown error"
                    self.model_status_label.setText("API connection failed")
                    QMessageBox.critical(
                        self.parent_window,
                        "API Test Failed",
                        f"Failed to connect to Groq API.\n\nError: {error_msg}\n\nPlease check:\n- API key is valid\n- Internet connection\n- Groq service status",
                    )
                return

            # 检查用户是否点击了取消
            if (
                hasattr(self, "_groq_progress_dialog")
                and self._groq_progress_dialog.result() == QMessageBox.StandardButton.Cancel
            ):
                self._groq_test_timer.stop()
                self._groq_progress_dialog.close()
                self.model_status_label.setText("API test cancelled")
                return

            # 不强制超时，由底层 API 的 timeout 配置控制
            # 用户可以在配置中设置 groq.timeout

        except Exception as e:
            self._groq_test_timer.stop()
            self._groq_progress_dialog.close()
            self.model_status_label.setText("API test error")
            QMessageBox.critical(
                self.parent_window,
                "API Test Error",
                f"Error during API test: {str(e)}",
            )

    def _test_siliconflow_api(self) -> None:
        """测试 SiliconFlow API 连接（异步，不阻塞UI）"""
        from PySide6.QtWidgets import QMessageBox, QApplication
        from PySide6.QtCore import QTimer
        import threading
        import time

        # 检查 API key
        api_key = self.siliconflow_api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(
                self.parent_window,
                "API Key Missing",
                "Please enter your SiliconFlow API key first.",
            )
            return

        # 显示测试中对话框
        model = self.siliconflow_model_combo.currentText()
        progress_dialog = QMessageBox(self.parent_window)
        progress_dialog.setWindowTitle("Testing SiliconFlow API")
        progress_dialog.setText(
            f"Testing SiliconFlow API connection...\n\nModel: {model}\n\nThis may take up to 30 seconds."
        )
        progress_dialog.setStandardButtons(QMessageBox.StandardButton.Cancel)
        progress_dialog.show()

        # 处理事件以显示对话框
        QApplication.processEvents()

        # 创建后台线程运行测试
        result_container = {"success": False, "error": ""}

        def test_connection_thread():
            try:
                from sonicinput.speech.siliconflow_engine import SiliconFlowEngine

                service = SiliconFlowEngine(api_key=api_key, model_name=model)
                success = service.test_connection()
                result_container["success"] = success

                if not success:
                    result_container["error"] = "Connection test failed"

            except Exception as e:
                result_container["success"] = False
                result_container["error"] = str(e)

        # 启动测试线程
        test_thread = threading.Thread(target=test_connection_thread, daemon=True)
        test_thread.start()

        # 保存测试状态
        self._siliconflow_test_thread = test_thread
        self._siliconflow_test_result = result_container
        self._siliconflow_progress_dialog = progress_dialog
        self._siliconflow_test_start_time = time.time()
        self._siliconflow_test_model = model

        # 创建定时器轮询测试状态
        self._siliconflow_test_timer = QTimer()
        self._siliconflow_test_timer.timeout.connect(self._check_siliconflow_test_status)
        self._siliconflow_test_timer.start(100)  # 每100ms检查一次

    def _check_siliconflow_test_status(self) -> None:
        """检查 SiliconFlow API 测试状态"""
        from PySide6.QtWidgets import QMessageBox
        import time

        try:
            thread_alive = self._siliconflow_test_thread.is_alive()
            elapsed_time = time.time() - self._siliconflow_test_start_time

            # 检查测试线程是否完成
            if not thread_alive:
                # 测试完成，停止定时器
                self._siliconflow_test_timer.stop()
                self._siliconflow_progress_dialog.close()

                # 显示结果
                if self._siliconflow_test_result["success"]:
                    self.model_status_label.setText("API connection successful")
                    QMessageBox.information(
                        self.parent_window,
                        "API Test Successful",
                        f"Successfully connected to SiliconFlow API!\n\nModel: {self._siliconflow_test_model}\n\nYou can now use cloud transcription.",
                    )
                else:
                    error_msg = self._siliconflow_test_result["error"] or "Unknown error"
                    self.model_status_label.setText("API connection failed")
                    QMessageBox.critical(
                        self.parent_window,
                        "API Test Failed",
                        f"Failed to connect to SiliconFlow API.\n\nError: {error_msg}\n\nPlease check:\n- API key is valid\n- Internet connection\n- SiliconFlow service status",
                    )
                return

            # 检查用户是否点击了取消
            if (
                hasattr(self, "_siliconflow_progress_dialog")
                and self._siliconflow_progress_dialog.result() == QMessageBox.StandardButton.Cancel
            ):
                self._siliconflow_test_timer.stop()
                self._siliconflow_progress_dialog.close()
                self.model_status_label.setText("API test cancelled")
                return

            # 不强制超时，由底层 API 的 timeout 配置控制
            # 用户可以在配置中设置 siliconflow.timeout

        except Exception as e:
            self._siliconflow_test_timer.stop()
            self._siliconflow_progress_dialog.close()
            self.model_status_label.setText("API test error")
            QMessageBox.critical(
                self.parent_window,
                "API Test Error",
                f"Error during API test: {str(e)}",
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
            provider: 提供商名称 ("local", "groq", "siliconflow", 或 "doubao")
        """
        is_local = provider == "local"
        is_groq = provider == "groq"
        is_siliconflow = provider == "siliconflow"
        is_doubao = provider == "doubao"

        # 显示/隐藏 Local Whisper 配置
        self.model_group.setVisible(is_local)
        self.gpu_group.setVisible(is_local)

        # 显示/隐藏 Groq 配置
        self.groq_group.setVisible(is_groq)

        # 显示/隐藏 SiliconFlow 配置
        self.siliconflow_group.setVisible(is_siliconflow)

        # 显示/隐藏 Doubao 配置
        self.doubao_group.setVisible(is_doubao)

        # 调整 Model Management 区域
        if is_local:
            # Local 模式：显示模型管理
            self.management_group.setTitle("Model Management")
            self.model_status_label.setText(
                "Model not loaded"
                if not hasattr(self, "_model_loaded")
                else ("Model loaded" if self._model_loaded else "Model not loaded")
            )
            self.load_model_button.setVisible(True)
            self.unload_model_button.setVisible(True)
            self.test_model_button.setText("Test Model")
        elif is_groq:
            # Groq 模式：显示 API 测试
            self.management_group.setTitle("API Connection Test")
            self.model_status_label.setText(
                "API key configured"
                if self.groq_api_key_edit.text().strip()
                else "API key not configured"
            )
            self.load_model_button.setVisible(False)
            self.unload_model_button.setVisible(False)
            self.test_model_button.setText("Test API Connection")
        elif is_siliconflow:
            # SiliconFlow 模式：显示 API 测试
            self.management_group.setTitle("API Connection Test")
            self.model_status_label.setText(
                "API key configured"
                if self.siliconflow_api_key_edit.text().strip()
                else "API key not configured"
            )
            self.load_model_button.setVisible(False)
            self.unload_model_button.setVisible(False)
            self.test_model_button.setText("Test API Connection")
        elif is_doubao:
            # Doubao 模式：显示 API 测试
            self.management_group.setTitle("API Connection Test")
            self.model_status_label.setText(
                "API key configured"
                if self.doubao_api_key_edit.text().strip()
                else "API key not configured"
            )
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

    def _on_siliconflow_api_key_changed(self, text: str) -> None:
        """当 SiliconFlow API key 改变时更新状态

        Args:
            text: API key 文本
        """
        # 只在 SiliconFlow 模式下更新状态
        provider = self.transcription_provider_combo.currentText()
        if provider == "siliconflow":
            if text.strip():
                self.model_status_label.setText("API key configured")
            else:
                self.model_status_label.setText("API key not configured")

    def _on_doubao_api_key_changed(self, text: str) -> None:
        """当 Doubao API key 改变时更新状态

        Args:
            text: API key 文本
        """
        # 只在 Doubao 模式下更新状态
        provider = self.transcription_provider_combo.currentText()
        if provider == "doubao":
            if text.strip():
                self.model_status_label.setText("API key configured")
            else:
                self.model_status_label.setText("API key not configured")

    def _on_doubao_model_type_changed(self, model_type: str) -> None:
        """当 Doubao 模型类型改变时更新集群显示

        Args:
            model_type: 模型类型 ("standard" 或 "fast")
        """
        self._update_doubao_cluster_display()

    def _update_doubao_cluster_display(self) -> None:
        """更新 Doubao 集群显示（基于模型类型）"""
        model_type = self.doubao_model_type_combo.currentText()
        cluster = "common" if model_type == "fast" else "volc_asr_public"
        self.doubao_cluster_edit.setText(cluster)

    def _test_doubao_api(self) -> None:
        """测试 Doubao API 连接（异步，不阻塞UI）"""
        from PySide6.QtWidgets import QMessageBox, QApplication
        from PySide6.QtCore import QTimer
        import threading
        import time

        # 检查 API key
        api_key = self.doubao_api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(
                self.parent_window,
                "API Key Missing",
                "Please enter your Doubao API key first.",
            )
            return

        # 显示测试中对话框
        model_type = self.doubao_model_type_combo.currentText()
        progress_dialog = QMessageBox(self.parent_window)
        progress_dialog.setWindowTitle("Testing API Connection")
        progress_dialog.setText(f"Testing Doubao ({model_type}) API connection...\n\nThis may take a moment.")
        progress_dialog.setStandardButtons(QMessageBox.StandardButton.Cancel)
        progress_dialog.show()

        # 启动后台测试线程
        def test_api():
            try:
                from ...speech.speech_service_factory import SpeechServiceFactory

                # 创建 Doubao 服务实例
                service = SpeechServiceFactory.create_service(
                    provider="doubao",
                    api_key=api_key,
                    app_id=self.doubao_app_id_edit.text().strip() or "388808087185088",
                    model_type=model_type,
                    base_url=self.doubao_base_url_edit.text().strip()
                    or "https://openspeech.bytedance.com",
                )

                # 执行连接测试
                success = service.test_connection()

                # 更新UI（必须在主线程中执行）
                QTimer.singleShot(0, lambda: self._check_doubao_test_status(success, model_type))

            except Exception as e:
                error_msg = str(e)
                QTimer.singleShot(0, lambda: self._check_doubao_test_status(None, model_type, error_msg))

        # 启动线程
        test_thread = threading.Thread(target=test_api, daemon=True)
        test_thread.start()

        # 设置定时器检查是否取消
        self._doubao_progress_dialog = progress_dialog
        self._doubao_test_timer = QTimer()
        self._doubao_test_timer.timeout.connect(
            lambda: self._check_doubao_test_cancelled()
        )
        self._doubao_test_timer.start(500)  # 每500ms检查一次

    def _check_doubao_test_cancelled(self) -> None:
        """检查用户是否取消了 Doubao API 测试"""
        if (
            hasattr(self, "_doubao_progress_dialog")
            and self._doubao_progress_dialog.result() == QMessageBox.StandardButton.Cancel
        ):
            self._doubao_test_timer.stop()
            self._doubao_progress_dialog.close()
            self.model_status_label.setText("API test cancelled")

    def _check_doubao_test_status(self, success: Optional[bool], model_type: str, error_msg: Optional[str] = None) -> None:
        """检查 Doubao API 测试结果并显示相应消息

        Args:
            success: 测试是否成功
            model_type: 模型类型
            error_msg: 错误消息（如果有）
        """
        from PySide6.QtWidgets import QMessageBox

        # 停止检查定时器并关闭进度对话框
        if hasattr(self, "_doubao_test_timer"):
            self._doubao_test_timer.stop()
        if hasattr(self, "_doubao_progress_dialog"):
            self._doubao_progress_dialog.close()

        if success:
            # 测试成功
            self.model_status_label.setText(f"API connection successful ({model_type})")
            QMessageBox.information(
                self.parent_window,
                "API Test Successful",
                f"Doubao ({model_type}) API connection test successful!\n\nThe service is ready to use.",
            )
        else:
            # 测试失败
            self.model_status_label.setText("API connection failed")
            QMessageBox.critical(
                self.parent_window,
                "API Test Failed",
                f"Failed to connect to Doubao ({model_type}) API.\n\nError: {error_msg or 'Unknown error'}\n\nPlease check:\n- API key/token is valid\n- App ID is correct\n- Model type and cluster match\n- Internet connection\n- Doubao service status",
            )
