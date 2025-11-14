"""Transcription设置标签页"""

from PySide6.QtWidgets import (
    QVBoxLayout,
    QGroupBox,
    QFormLayout,
    QCheckBox,
    QComboBox,
    QSpinBox,
    QPushButton,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QLineEdit,
    QMessageBox,
    QApplication,
)
from typing import Dict, Any
from .base_tab import BaseSettingsTab


class TranscriptionTab(BaseSettingsTab):
    """Transcription设置标签页

    包含：
    - 转录提供商选择（sherpa-onnx / Groq / SiliconFlow / Qwen）
    - sherpa-onnx 本地模型配置
    - 云服务 API 配置（Groq / SiliconFlow / Qwen）
    - 模型管理（加载/卸载/测试）
    """

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 转录提供商选择组
        provider_group = QGroupBox("Transcription Provider")
        provider_layout = QFormLayout(provider_group)

        self.transcription_provider_combo = QComboBox()
        self.transcription_provider_combo.addItems(["local", "groq", "siliconflow", "qwen"])
        self.transcription_provider_combo.currentTextChanged.connect(
            self._on_provider_changed
        )
        provider_layout.addRow("Provider:", self.transcription_provider_combo)

        layout.addWidget(provider_group)

        # sherpa-onnx 本地模型设置组
        model_group = QGroupBox("sherpa-onnx Configuration")
        model_layout = QFormLayout(model_group)

        # 模型选择
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems(
            ["paraformer", "zipformer-small"]
        )
        model_layout.addRow("Model:", self.whisper_model_combo)

        # 语言设置
        self.whisper_language_combo = QComboBox()
        self.whisper_language_combo.addItems(
            ["auto", "en", "zh", "ja", "ko", "es", "fr", "de", "it", "pt", "ru"]
        )
        model_layout.addRow("Language:", self.whisper_language_combo)

        # 流式模式选择
        self.streaming_mode_combo = QComboBox()
        self.streaming_mode_combo.addItems(["chunked", "realtime"])
        self.streaming_mode_combo.setToolTip(
            "chunked: 30s segments with AI optimization (recommended)\n"
            "realtime: Edge-to-edge streaming with lowest latency"
        )
        model_layout.addRow("Streaming Mode:", self.streaming_mode_combo)

        # 自动加载
        self.auto_load_model_checkbox = QCheckBox("Load model on startup")
        model_layout.addRow("", self.auto_load_model_checkbox)

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

        # Qwen API 配置组
        qwen_group = QGroupBox("Qwen ASR (Alibaba Cloud) API Configuration")
        qwen_layout = QFormLayout(qwen_group)

        # API Key
        self.qwen_api_key_edit = QLineEdit()
        self.qwen_api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.qwen_api_key_edit.setPlaceholderText("Enter DashScope API key")
        self.qwen_api_key_edit.textChanged.connect(
            self._on_qwen_api_key_changed
        )
        qwen_layout.addRow("API Key:", self.qwen_api_key_edit)

        # Model
        self.qwen_model_combo = QComboBox()
        self.qwen_model_combo.addItems(["qwen3-asr-flash"])
        self.qwen_model_combo.setToolTip("Qwen ASR model with emotion and language detection")
        qwen_layout.addRow("Model:", self.qwen_model_combo)

        # Base URL
        self.qwen_base_url_edit = QLineEdit()
        self.qwen_base_url_edit.setPlaceholderText(
            "Leave empty to use default (https://dashscope.aliyuncs.com)"
        )
        qwen_layout.addRow("Base URL:", self.qwen_base_url_edit)

        # Enable ITN (Inverse Text Normalization)
        self.qwen_enable_itn_checkbox = QCheckBox("Enable Inverse Text Normalization")
        self.qwen_enable_itn_checkbox.setToolTip("Convert spoken numbers to digits (e.g., '一千' -> '1000')")
        self.qwen_enable_itn_checkbox.setChecked(True)
        qwen_layout.addRow("ITN:", self.qwen_enable_itn_checkbox)

        # Timeout
        self.qwen_timeout_spinbox = QSpinBox()
        self.qwen_timeout_spinbox.setRange(10, 180)
        self.qwen_timeout_spinbox.setValue(30)
        self.qwen_timeout_spinbox.setSuffix("s")
        qwen_layout.addRow("Timeout:", self.qwen_timeout_spinbox)

        # Max Retries
        self.qwen_max_retries_spinbox = QSpinBox()
        self.qwen_max_retries_spinbox.setRange(0, 10)
        self.qwen_max_retries_spinbox.setValue(3)
        qwen_layout.addRow("Max Retries:", self.qwen_max_retries_spinbox)

        # Test button
        test_qwen_button = QPushButton("Test Qwen API Connection")
        test_qwen_button.clicked.connect(self._test_qwen_api)
        qwen_layout.addRow("", test_qwen_button)

        layout.addWidget(qwen_group)
        self.qwen_group = qwen_group

        self.model_group = model_group

        layout.addStretch()

        # 保存控件引用
        self.controls = {
            "transcription_provider": self.transcription_provider_combo,
            "whisper_model": self.whisper_model_combo,
            "whisper_language": self.whisper_language_combo,
            "streaming_mode": self.streaming_mode_combo,
            "auto_load_model": self.auto_load_model_checkbox,
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
            "qwen_api_key": self.qwen_api_key_edit,
            "qwen_model": self.qwen_model_combo,
            "qwen_base_url": self.qwen_base_url_edit,
            "qwen_enable_itn": self.qwen_enable_itn_checkbox,
            "qwen_timeout": self.qwen_timeout_spinbox,
            "qwen_max_retries": self.qwen_max_retries_spinbox,
            "model_status": self.model_status_label,
        }

        # 暴露控件到parent_window
        self.parent_window.whisper_model_combo = self.whisper_model_combo
        self.parent_window.whisper_language_combo = self.whisper_language_combo
        self.parent_window.streaming_mode_combo = self.streaming_mode_combo
        self.parent_window.auto_load_model_checkbox = self.auto_load_model_checkbox
        self.parent_window.model_status_label = self.model_status_label

    def load_config(self, config: Dict[str, Any]) -> None:
        """从配置加载UI状态

        Args:
            config: 完整配置字典
        """
        # 转录配置（新）
        transcription_config = config.get("transcription", {})
        provider = transcription_config.get("provider", "local")
        self.transcription_provider_combo.setCurrentText(provider)

        # sherpa-onnx local settings
        local_config = transcription_config.get("local", {})
        # Fallback to old whisper config for backward compatibility
        whisper_config = config.get("whisper", {})

        self.whisper_model_combo.setCurrentText(
            local_config.get("model", whisper_config.get("model", "paraformer"))
        )
        self.whisper_language_combo.setCurrentText(
            local_config.get("language", whisper_config.get("language", "auto"))
        )
        # streaming_mode只在local provider下有效
        if provider == "local":
            self.streaming_mode_combo.setCurrentText(
                local_config.get("streaming_mode", "chunked")
            )
        self.auto_load_model_checkbox.setChecked(
            local_config.get("auto_load", whisper_config.get("auto_load", True))
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

        # Qwen settings
        qwen_config = transcription_config.get("qwen", {})
        self.qwen_api_key_edit.setText(qwen_config.get("api_key", ""))
        self.qwen_model_combo.setCurrentText(qwen_config.get("model", "qwen3-asr-flash"))
        self.qwen_base_url_edit.setText(
            qwen_config.get("base_url", "https://dashscope.aliyuncs.com")
        )
        self.qwen_enable_itn_checkbox.setChecked(qwen_config.get("enable_itn", True))
        self.qwen_timeout_spinbox.setValue(qwen_config.get("timeout", 30))
        self.qwen_max_retries_spinbox.setValue(qwen_config.get("max_retries", 3))

        # Update visibility based on provider
        self._on_provider_changed(provider)

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        Returns:
            Dict[str, Any]: 配置字典
        """
        # 获取当前provider
        current_provider = self.transcription_provider_combo.currentText()

        # 构建完整配置（保存所有provider）
        config = {
            "transcription": {
                "provider": current_provider,
                "local": {
                    "model": self.whisper_model_combo.currentText(),
                    "language": self.whisper_language_combo.currentText(),
                    "auto_load": self.auto_load_model_checkbox.isChecked(),
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
                "qwen": {
                    "api_key": self.qwen_api_key_edit.text(),
                    "model": self.qwen_model_combo.currentText(),
                    "base_url": self.qwen_base_url_edit.text().strip()
                    or "https://dashscope.aliyuncs.com",
                    "enable_itn": self.qwen_enable_itn_checkbox.isChecked(),
                    "timeout": self.qwen_timeout_spinbox.value(),
                    "max_retries": self.qwen_max_retries_spinbox.value(),
                },
            },
        }

        # streaming_mode只在local provider下才从UI读取并保存
        if current_provider == "local":
            config["transcription"]["local"]["streaming_mode"] = (
                self.streaming_mode_combo.currentText()
            )
        # 否则不添加streaming_mode字段（保持config文件中的原值）

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
        elif provider == "qwen":
            # Qwen 模式：测试 API 连接
            self._test_qwen_api()

    def _test_groq_api(self) -> None:
        """测试 Groq API 连接（异步，不阻塞UI）"""
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
            provider: 提供商名称 ("local", "groq", "siliconflow", 或 "qwen")
        """
        is_local = provider == "local"
        is_groq = provider == "groq"
        is_siliconflow = provider == "siliconflow"
        is_qwen = provider == "qwen"

        # 显示/隐藏 sherpa-onnx 配置
        self.model_group.setVisible(is_local)

        # 显示/隐藏 Groq 配置
        self.groq_group.setVisible(is_groq)

        # 显示/隐藏 SiliconFlow 配置
        self.siliconflow_group.setVisible(is_siliconflow)

        # 显示/隐藏 Qwen 配置
        self.qwen_group.setVisible(is_qwen)

        # 调整 Model Management 区域
        if is_local:
            # Local 模式：显示模型管理
            self.management_group.setTitle("Model Management")

            # 从运行时状态获取真实模型信息
            if hasattr(self.parent_window, 'ui_model_service'):
                runtime_info = self.parent_window.ui_model_service.get_model_info()
                is_loaded = runtime_info.get("is_loaded", False)
                model_name = runtime_info.get("model_name", "Unknown")
                device = runtime_info.get("device", "Unknown")

                if is_loaded and model_name != "Unknown":
                    self.model_status_label.setText(f"Model loaded: {model_name} ({device})")
                    self.model_status_label.setStyleSheet("QLabel { color: #4CAF50; }")  # Green
                else:
                    self.model_status_label.setText("Model not loaded")
                    self.model_status_label.setStyleSheet("QLabel { color: #757575; }")  # Gray
            else:
                self.model_status_label.setText("Model service not available")
                self.model_status_label.setStyleSheet("QLabel { color: #F44336; }")  # Red

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
        elif is_qwen:
            # Qwen 模式：显示 API 测试
            self.management_group.setTitle("API Connection Test")
            self.model_status_label.setText(
                "API key configured"
                if self.qwen_api_key_edit.text().strip()
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

    # ==================== Qwen API Methods ====================

    def _on_qwen_api_key_changed(self, text: str) -> None:
        """当 Qwen API key 改变时更新状态

        Args:
            text: API key 文本
        """
        # 只在 Qwen 模式下更新状态
        provider = self.transcription_provider_combo.currentText()
        if provider == "qwen":
            if text.strip():
                self.model_status_label.setText("API key configured")
            else:
                self.model_status_label.setText("API key not configured")

    def _test_qwen_api(self) -> None:
        """测试 Qwen API 连接（异步，不阻塞UI）"""
        from PySide6.QtCore import QTimer
        import threading
        import time

        # 检查 API key
        api_key = self.qwen_api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(
                self.parent_window,
                "API Key Missing",
                "Please enter your Qwen (DashScope) API key first.",
            )
            return

        # 显示测试中对话框
        model = self.qwen_model_combo.currentText()
        progress_dialog = QMessageBox(self.parent_window)
        progress_dialog.setWindowTitle("Testing Qwen API")
        progress_dialog.setText(
            f"Testing Qwen ASR API connection...\n\nModel: {model}\n\nThis may take a few seconds."
        )
        progress_dialog.setStandardButtons(QMessageBox.StandardButton.Cancel)
        progress_dialog.show()

        # 处理事件以显示对话框
        QApplication.processEvents()

        # 创建后台线程运行测试
        result_container = {"success": False, "error": ""}

        def test_connection_thread():
            try:
                from ...speech.speech_service_factory import SpeechServiceFactory

                # 创建 Qwen 服务实例
                service = SpeechServiceFactory.create_service(
                    provider="qwen",
                    api_key=api_key,
                    model=model,
                    base_url=self.qwen_base_url_edit.text().strip()
                    or "https://dashscope.aliyuncs.com",
                    enable_itn=self.qwen_enable_itn_checkbox.isChecked(),
                )

                # 执行连接测试
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
        self._qwen_test_thread = test_thread
        self._qwen_test_result = result_container
        self._qwen_progress_dialog = progress_dialog
        self._qwen_test_start_time = time.time()
        self._qwen_test_model = model

        # 创建定时器轮询测试状态
        self._qwen_test_timer = QTimer()
        self._qwen_test_timer.timeout.connect(self._check_qwen_test_status)
        self._qwen_test_timer.start(100)  # 每100ms检查一次

    def _check_qwen_test_status(self) -> None:
        """检查 Qwen API 测试状态"""
        import time

        try:
            thread_alive = self._qwen_test_thread.is_alive()
            elapsed_time = time.time() - self._qwen_test_start_time

            # 检查测试线程是否完成
            if not thread_alive:
                # 测试完成，停止定时器
                self._qwen_test_timer.stop()
                self._qwen_progress_dialog.close()

                # 显示结果
                if self._qwen_test_result["success"]:
                    self.model_status_label.setText("API connection successful")
                    QMessageBox.information(
                        self.parent_window,
                        "API Test Successful",
                        f"Successfully connected to Qwen ASR API!\n\nModel: {self._qwen_test_model}\n\nYou can now use cloud transcription.",
                    )
                else:
                    error_msg = self._qwen_test_result["error"] or "Unknown error"
                    self.model_status_label.setText("API connection failed")
                    QMessageBox.critical(
                        self.parent_window,
                        "API Test Failed",
                        f"Failed to connect to Qwen ASR API.\n\nError: {error_msg}\n\nPlease check:\n- DashScope API key is valid\n- Internet connection\n- Qwen service status",
                    )
                return

            # 检查用户是否点击了取消
            if (
                hasattr(self, "_qwen_progress_dialog")
                and self._qwen_progress_dialog.result() == QMessageBox.StandardButton.Cancel
            ):
                self._qwen_test_timer.stop()
                self._qwen_progress_dialog.close()
                self.model_status_label.setText("API test cancelled")
                return

            # 不强制超时，由底层 API 的 timeout 配置控制
            # 用户可以在配置中设置 qwen.timeout

        except Exception as e:
            self._qwen_test_timer.stop()
            self._qwen_progress_dialog.close()
            self.model_status_label.setText("API test error")
            QMessageBox.critical(
                self.parent_window,
                "API Test Error",
                f"Error during API test: {str(e)}",
            )
