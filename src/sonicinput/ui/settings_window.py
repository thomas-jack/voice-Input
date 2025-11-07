"""设置窗口"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QPushButton,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox,
    QMessageBox,
    QFileDialog,
    QApplication,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from typing import Dict, Any
import time
from ..utils import app_logger
from ..core.interfaces import IUISettingsService, IUIModelService, IUIAudioService, IUIGPUService
from .settings_tabs import (
    ApplicationTab,
    HotkeyTab,
    TranscriptionTab,
    AITab,
    AudioInputTab,
    HistoryTab,
)


class WheelEventFilter(QObject):
    """事件过滤器：阻止下拉框和数值调整控件的滚轮事件，防止误触"""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """过滤滚轮事件

        Args:
            obj: 事件目标对象
            event: 事件

        Returns:
            True 表示事件被处理（阻止），False 表示事件继续传播
        """
        # 如果是滚轮事件，阻止它
        if event.type() == QEvent.Type.Wheel:
            return True
        # 其他事件正常传播
        return False


class SettingsWindow(QMainWindow):
    """设置窗口"""

    # 信号
    settings_changed = Signal(str, object)  # key, value
    hotkey_test_requested = Signal(str)
    api_test_requested = Signal()
    model_load_requested = Signal(str)
    model_unload_requested = Signal()
    model_test_requested = Signal()

    def __init__(self, ui_settings_service: IUISettingsService, ui_model_service: IUIModelService, parent=None):
        super().__init__(parent)

        self.ui_settings_service = ui_settings_service
        self.ui_model_service = ui_model_service
        self.ui_audio_service = None  # 可选，在需要时初始化
        self.ui_gpu_service = None     # 可选，在需要时初始化
        self.current_config = {}

        # 设置窗口属性
        self.setWindowTitle("Voice Input Software - Settings")
        self.setMinimumSize(800, 600)  # 最小尺寸
        self.resize(800, 600)  # 默认大小，但允许用户调整
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)

        # 创建滚轮事件过滤器（防止误触）
        self.wheel_filter = WheelEventFilter(self)

        # 创建标签页实例
        self.application_tab = ApplicationTab(self.ui_settings_service, self)
        self.hotkey_tab = HotkeyTab(self.ui_settings_service, self)
        self.transcription_tab = TranscriptionTab(self.ui_settings_service, self)
        self.ai_tab = AITab(self.ui_settings_service, self)
        self.audio_input_tab = AudioInputTab(self.ui_settings_service, self)
        self.history_tab = HistoryTab(self.ui_settings_service, self)

        # 初始化UI
        self.setup_ui()

        # 为所有下拉框和数值调整控件安装滚轮事件过滤器
        self._install_wheel_filters()

        # 监听模型加载完成事件
        if self.ui_settings_service:
            from ..utils.constants import Events

            events = self.ui_settings_service.get_event_service()
            events.on(Events.MODEL_LOADING_COMPLETED, self._on_model_loaded)

            # 检查模型是否已经加载（如果SettingsWindow创建晚于模型加载）
            self._check_initial_model_status()

        # 加载当前配置
        self.load_current_config()

        app_logger.log_audio_event("Settings window initialized", {})

    def setup_ui(self) -> None:
        """设置UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 使用独立的标签页模块
        self._create_scrollable_tab(self.application_tab.create(), "Application")
        self._create_scrollable_tab(self.hotkey_tab.create(), "Hotkeys")
        self._create_scrollable_tab(self.transcription_tab.create(), "Transcription")
        self._create_scrollable_tab(self.ai_tab.create(), "AI Processing")
        self._create_scrollable_tab(self.audio_input_tab.create(), "Audio and Input")
        self._create_scrollable_tab(self.history_tab.create(), "History")

        main_layout.addWidget(self.tab_widget)

        # 底部按钮
        self.setup_bottom_buttons(main_layout)

    def _install_wheel_filters(self) -> None:
        """为所有下拉框和数值调整控件安装滚轮事件过滤器，防止误触"""
        # 递归查找所有需要过滤的控件类型
        target_types = (QComboBox, QSpinBox, QDoubleSpinBox)

        # 从中央widget开始递归查找所有子控件
        def install_filter_recursive(widget: QWidget) -> None:
            # 检查当前控件是否是目标类型
            if isinstance(widget, target_types):
                widget.installEventFilter(self.wheel_filter)

            # 递归处理所有子控件
            for child in widget.children():
                if isinstance(child, QWidget):
                    install_filter_recursive(child)

        # 从中央widget开始递归安装
        if self.centralWidget():
            install_filter_recursive(self.centralWidget())

        app_logger.log_audio_event(
            "Wheel event filters installed for QComboBox, QSpinBox, QDoubleSpinBox", {}
        )

    def _create_scrollable_tab(self, content_widget: QWidget, tab_name: str) -> None:
        """创建带滚动的Tab页

        Args:
            content_widget: Tab内容widget
            tab_name: Tab名称
        """
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)  # 无边框，更现代
        scroll_area.setWidget(content_widget)
        self.tab_widget.addTab(scroll_area, tab_name)

    def setup_bottom_buttons(self, main_layout: QVBoxLayout) -> None:
        """设置底部按钮"""
        button_layout = QHBoxLayout()

        # 重置按钮
        self.reset_button = QPushButton("Reset Tab")
        self.reset_button.clicked.connect(self.reset_current_tab)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()

        # 应用按钮
        self.apply_button = QPushButton("Apply")
        self.apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_button)

        # 确定按钮
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_button)

        # 取消按钮
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

    def load_current_config(self) -> None:
        """加载当前配置"""
        self.current_config = self.ui_settings_service.get_all_settings()
        self.update_ui_from_config()

        # Initialize audio devices
        self.refresh_audio_devices()

        # Initialize GPU information
        self.refresh_gpu_info()

        # Initialize model status
        self.refresh_model_status()

    def update_ui_from_config(self) -> None:
        """从配置更新UI"""
        # 使用各标签页的 load_config 方法
        self.application_tab.load_config(self.current_config)
        self.hotkey_tab.load_config(self.current_config)
        self.transcription_tab.load_config(self.current_config)
        self.ai_tab.load_config(self.current_config)
        self.audio_input_tab.load_config(self.current_config)
        self.history_tab.load_config(self.current_config)

    def test_hotkey(self) -> None:
        """测试快捷键"""
        hotkey = self.hotkey_input.text().strip()

        if not hotkey:
            self.update_hotkey_status("Please enter a hotkey to test", True)
            return

        try:
            # Import the hotkey manager class to use for testing
            from ..core.hotkey_manager import HotkeyManager

            # Create a temporary hotkey manager for testing
            def test_callback(action):
                pass

            temp_manager = HotkeyManager(test_callback)

            # Validate hotkey format
            validation_result = temp_manager.validate_hotkey(hotkey)

            if not validation_result["valid"]:
                issues = "; ".join(validation_result["issues"])
                self.update_hotkey_status(f"Invalid hotkey: {issues}", True)
                return

            # Test hotkey availability
            test_result = temp_manager.test_hotkey_availability(hotkey)

            if test_result["success"]:
                self.update_hotkey_status(test_result["message"], False)
            else:
                self.update_hotkey_status(test_result["message"], True)

            app_logger.log_audio_event(
                "Hotkey tested",
                {
                    "hotkey": hotkey,
                    "valid": validation_result["valid"],
                    "available": test_result["success"],
                },
            )

        except Exception as e:
            app_logger.log_error(e, "test_hotkey")
            self.update_hotkey_status(f"Test failed: {str(e)}", True)

    def test_api_connection(self) -> None:
        """测试API连接"""
        try:
            # 获取当前选择的提供商
            current_provider = self.ai_provider_combo.currentText()

            # 根据提供商获取对应的API密钥
            if current_provider == "OpenRouter":
                api_key = self.api_key_input.text().strip()
                provider_name = "OpenRouter"
            elif current_provider == "Groq":
                api_key = self.groq_api_key_input.text().strip()
                provider_name = "Groq"
            elif current_provider == "NVIDIA":
                api_key = self.nvidia_api_key_input.text().strip()
                provider_name = "NVIDIA"
            elif current_provider == "OpenAI Compatible":
                api_key = self.openai_compatible_api_key_input.text().strip()
                base_url = self.openai_compatible_base_url_input.text().strip()
                provider_name = "OpenAI Compatible"

                # Base URL 必填检查
                if not base_url:
                    QMessageBox.warning(
                        self,
                        "API Connection Test",
                        "⚠️ Please enter the Base URL for OpenAI Compatible service.",
                    )
                    return
            else:
                provider_name = "Unknown"
                api_key = ""

            # OpenAI Compatible 的 API Key 是可选的
            if not api_key and current_provider != "OpenAI Compatible":
                QMessageBox.warning(
                    self,
                    "API Connection Test",
                    f"⚠️ Please enter your {provider_name} API key first.",
                )
                return

            # 显示测试开始对话框
            progress_dialog = QMessageBox(self)
            progress_dialog.setWindowTitle("Testing API Connection")
            progress_dialog.setText(
                f"🔄 Testing {provider_name} API connection...\n\nThis may take a few seconds."
            )
            progress_dialog.setStandardButtons(QMessageBox.StandardButton.Cancel)
            progress_dialog.show()

            # 记录对话框创建
            app_logger.log_audio_event(
                "API test dialog created",
                {"type": "progress", "provider": provider_name},
            )

            # 处理事件以显示对话框
            QApplication.processEvents()

            # 根据提供商创建对应的客户端进行测试
            if current_provider == "OpenRouter":
                from ..ai.openrouter import OpenRouterClient

                test_client = OpenRouterClient(api_key)
            elif current_provider == "Groq":
                from ..ai.groq import GroqClient

                test_client = GroqClient(api_key)
            elif current_provider == "NVIDIA":
                from ..ai.nvidia import NvidiaClient

                test_client = NvidiaClient(api_key)
            elif current_provider == "OpenAI Compatible":
                from ..ai.openai_compatible import OpenAICompatibleClient

                test_client = OpenAICompatibleClient(api_key, base_url)
            else:
                QMessageBox.warning(
                    self,
                    "API Connection Test",
                    f"⚠️ Unknown provider: {current_provider}",
                )
                return

            # 保存provider_name为实例变量，供结果显示使用
            self._api_test_provider_name = provider_name

            # 异步测试连接
            import threading

            result_container = {"success": False, "error": ""}

            def test_connection():
                try:
                    app_logger.log_audio_event("API test thread started", {})
                    success = test_client.test_connection()
                    result_container["success"] = success

                    app_logger.log_audio_event(
                        "API test thread setting result",
                        {
                            "success": success,
                            "container_before": dict(result_container),
                        },
                    )

                    if not success:
                        result_container["error"] = (
                            "Connection test failed - please check your API key and network connection"
                        )

                    app_logger.log_audio_event(
                        "API test thread completed",
                        {"success": success, "container_after": dict(result_container)},
                    )

                except Exception as e:
                    result_container["success"] = False
                    result_container["error"] = str(e)
                    app_logger.log_audio_event(
                        "API test thread exception",
                        {"error": str(e), "container_final": dict(result_container)},
                    )

            # 运行测试
            test_thread = threading.Thread(target=test_connection, daemon=True)
            test_thread.start()

            # 使用QTimer异步检查测试完成状态
            self._api_test_thread = test_thread
            self._api_test_result = result_container
            self._api_progress_dialog = progress_dialog
            self._api_test_start_time = time.time()

            # 创建定时器轮询测试状态
            from PySide6.QtCore import QTimer

            self._api_test_timer = QTimer()
            self._api_test_timer.timeout.connect(self._check_api_test_status)
            self._api_test_timer.start(100)  # 每100ms检查一次

        except Exception as e:
            QMessageBox.critical(
                self,
                "API Connection Test",
                f"❌ **Test Error**\n\n"
                f"Failed to run connection test: {str(e)}\n\n"
                "Please try again or check the application logs.",
            )

    def _check_api_test_status(self) -> None:
        """检查API测试状态的异步方法"""
        import time

        try:
            # 添加详细日志追踪
            thread_alive = self._api_test_thread.is_alive()
            elapsed_time = time.time() - self._api_test_start_time

            app_logger.log_audio_event(
                "API test status check",
                {
                    "thread_alive": thread_alive,
                    "elapsed_time": f"{elapsed_time:.2f}s",
                    "result_success": self._api_test_result.get("success", None),
                    "result_error": self._api_test_result.get("error", None),
                },
            )

            # 检查测试线程是否完成
            if not thread_alive:
                # 测试完成，停止定时器
                self._api_test_timer.stop()

                app_logger.log_audio_event(
                    "API test completed, closing dialog",
                    {
                        "success": self._api_test_result.get("success", False),
                        "total_time": f"{elapsed_time:.2f}s",
                    },
                )

                # 关闭进度对话框
                self._api_progress_dialog.close()

                # 显示结果
                if self._api_test_result["success"]:
                    QMessageBox.information(
                        self,
                        "API Connection Test",
                        f"✅ **Connection Successful!**\n\n"
                        f"Your {self._api_test_provider_name} API key is valid and the service is accessible.\n\n"
                        f"You can now use AI text optimization features.",
                    )
                else:
                    error_msg = (
                        self._api_test_result["error"] or "Unknown error occurred"
                    )
                    QMessageBox.critical(
                        self,
                        "API Connection Test",
                        f"❌ **Connection Failed**\n\n"
                        f"Error: {error_msg}\n\n"
                        f"Please check:\n"
                        f"• Your API key is correct\n"
                        f"• You have internet connection\n"
                        f"• {self._api_test_provider_name} service is available",
                    )
                return

            # 检查用户是否点击了取消按钮
            if (
                hasattr(self, "_api_progress_dialog")
                and self._api_progress_dialog.result()
                == QMessageBox.StandardButton.Cancel
            ):
                # 用户取消，停止定时器
                self._api_test_timer.stop()
                app_logger.log_audio_event("API test cancelled by user", {})

                # 关闭对话框
                self._api_progress_dialog.close()
                return

            # 检查超时（15秒强制超时，防止卡死）
            if elapsed_time > 15:
                # 超时，停止定时器
                self._api_test_timer.stop()

                # 关闭进度对话框
                self._api_progress_dialog.close()

                # 显示超时错误
                app_logger.log_audio_event(
                    "API test forced timeout", {"elapsed_time": f"{elapsed_time:.2f}s"}
                )
                QMessageBox.critical(
                    self,
                    "API Connection Test",
                    "❌ **Test Timeout**\n\n"
                    f"The API connection test took too long (>{elapsed_time:.1f} seconds).\n\n"
                    "This may indicate a stuck dialog issue. Please check:\n"
                    "• Your internet connection\n"
                    "• OpenRouter service availability\n"
                    "• Try again later",
                )

        except Exception as e:
            # 异常处理，停止定时器
            self._api_test_timer.stop()
            self._api_progress_dialog.close()

            QMessageBox.critical(
                self,
                "API Connection Test",
                f"❌ **Test Error**\n\n"
                f"An error occurred during testing: {str(e)}\n\n"
                "Please try again.",
            )

    def _flatten_config(
        self, config: Dict[str, Any], prefix: str = ""
    ) -> Dict[str, Any]:
        """将嵌套配置展平为点分隔的键值对

        例如: {"ui": {"auto_start": True}} -> {"ui.auto_start": True}
        """
        flat = {}
        for key, value in config.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                # 递归展平嵌套字典
                flat.update(self._flatten_config(value, full_key))
            else:
                flat[full_key] = value
        return flat

    def apply_settings(self) -> None:
        """应用设置"""
        # 收集所有设置
        new_config = self.collect_settings_from_ui()

        # 保存配置
        try:
            # 将嵌套配置展平并逐个更新（新API方式）
            flat_config = self._flatten_config(new_config)
            for key, value in flat_config.items():
                try:
                    self.ui_settings_service.set_setting(key, value)
                except Exception as setting_error:
                    app_logger.log_error(setting_error, f"Failed to set config: {key}")

            # 立即保存配置并触发config.changed事件
            if hasattr(self.ui_settings_service, 'save_config'):
                self.ui_settings_service.save_config()

            # 实时应用日志配置（无需重启）
            app_logger._logger.set_log_level(new_config["logging"]["level"])
            app_logger._logger.set_console_output(
                new_config["logging"]["console_output"]
            )

            # 实时应用快捷键配置（无需重启）
            # 这里需要通过UI服务来触发快捷键重载
            # 具体实现取决于UI主服务的功能

            QMessageBox.information(self, "Settings", "Settings applied successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def accept_settings(self) -> None:
        """接受设置并关闭"""
        self.apply_settings()
        self.close()

    def collect_settings_from_ui(self) -> Dict[str, Any]:
        """从UI收集所有设置

        Returns:
            Dict[str, Any]: 配置字典
        """
        config = {}

        # 从各标签页收集配置
        for tab_config in [
            self.application_tab.save_config(),
            self.hotkey_tab.save_config(),
            self.transcription_tab.save_config(),
            self.ai_tab.save_config(),
            self.audio_input_tab.save_config(),
            self.history_tab.save_config(),
        ]:
            # 深度合并配置
            for key, value in tab_config.items():
                if key not in config:
                    config[key] = value
                elif isinstance(value, dict) and isinstance(config[key], dict):
                    config[key].update(value)
                else:
                    config[key] = value

        return config

    def export_config(self) -> None:
        """导出配置"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "voice_input_settings.json", "JSON Files (*.json)"
        )
        if file_path:
            try:
                self.ui_settings_service.export_config(file_path)
                QMessageBox.information(
                    self, "Export", "Settings exported successfully!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export settings: {e}")

    def import_config(self) -> None:
        """导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            try:
                self.ui_settings_service.import_config(file_path)
                self.load_current_config()
                QMessageBox.information(
                    self, "Import", "Settings imported successfully!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import settings: {e}")

    def reset_config(self) -> None:
        """重置配置"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.ui_settings_service.reset_to_defaults()
                self.load_current_config()
                QMessageBox.information(self, "Reset", "Settings reset to defaults!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to reset settings: {e}")

    def load_model(self) -> None:
        """加载模型"""
        model_name = self.whisper_model_combo.currentText()
        self.model_load_requested.emit(model_name)

    def unload_model(self) -> None:
        """卸载模型"""
        try:
            # 发送模型卸载请求信号
            self.model_unload_requested.emit()

            # 更新UI状态
            reply = QMessageBox.question(
                self,
                "Unload Model",
                "Are you sure you want to unload the current Whisper model?\n\nThis will free up memory but you'll need to reload it before using voice input.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                QMessageBox.information(
                    self,
                    "Model Unload",
                    "✅ Model unload request sent. Check the system tray for status updates.",
                )

        except Exception as e:
            QMessageBox.critical(
                self, "Unload Model Error", f"❌ Failed to unload model: {str(e)}"
            )

    def _check_initial_model_status(self) -> None:
        """检查模型初始状态（如果SettingsWindow创建晚于模型加载）"""
        try:
            if not self.ui_model_service:
                return

            # 使用 UI 模型服务检查模型状态
            if self.ui_model_service.is_model_loaded():
                # 模型已加载，获取信息并更新UI
                model_info = self.ui_model_service.get_model_info()

                # 调用事件处理器更新UI
                self._on_model_loaded(model_info)

        except Exception as e:
            from ..utils import app_logger

            app_logger.log_error(e, "_check_initial_model_status")

    def _on_model_loaded(self, event_data: dict = None) -> None:
        """模型加载完成事件处理器

        Args:
            event_data: 事件数据，包含 model_name, load_time, device, GPU信息等 (可选)
        """
        try:
            if event_data is None:
                event_data = {}

            model_name = event_data.get("model_name", "Unknown")
            device = event_data.get("device", "Unknown")

            # 更新模型状态标签 - 移除 emoji 以免编码问题
            status_text = f"Model loaded: {model_name} ({device})"
            self.transcription_tab.model_status_label.setText(status_text)
            self.transcription_tab.model_status_label.setStyleSheet(
                "QLabel { color: #4CAF50; }"
            )  # Material Green

            # 如果有GPU信息，更新显存使用
            if "allocated_gb" in event_data:
                allocated = event_data["allocated_gb"]
                total = event_data.get("total_gb", 0)
                if total > 0:
                    percent = (allocated / total) * 100
                    self.transcription_tab.gpu_memory_label.setText(
                        f"{allocated:.2f}GB / {total:.1f}GB ({percent:.1f}%)"
                    )

        except Exception as e:
            from ..utils import app_logger

            app_logger.log_error(e, "_on_model_loaded")

    def test_model(self) -> None:
        """测试模型"""
        try:
            # 发送模型测试请求信号
            self.model_test_requested.emit()

            # 显示信息对话框
            QMessageBox.information(
                self,
                "Model Test",
                "📋 Model test initiated.\n\n"
                "This will:\n"
                "1. Check if the model is loaded\n"
                "2. Test with a sample audio (if available)\n"
                "3. Verify transcription functionality\n\n"
                "Please check the system tray and logs for test results.",
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Model Test Error", f"❌ Failed to test model: {str(e)}"
            )

    def refresh_audio_devices(self) -> None:
        """刷新音频设备"""
        try:
            # Clear current items
            self.audio_device_combo.clear()

            # Add default option
            self.audio_device_combo.addItem("System Default", None)

            # Get available devices from the audio recorder
            # We need to access the recorder through the app controller
            from ..audio.recorder import AudioRecorder

            temp_recorder = AudioRecorder()
            devices = temp_recorder.get_audio_devices()
            temp_recorder.cleanup()

            # Add devices to combo box
            for device in devices:
                device_name = f"{device['name']} (ID: {device['index']})"
                self.audio_device_combo.addItem(device_name, device["index"])

            # Select current device from config
            current_device_id = self.ui_settings_service.get_setting("audio.device_id")
            if current_device_id is not None:
                # Find and select the current device
                for i in range(self.audio_device_combo.count()):
                    if self.audio_device_combo.itemData(i) == current_device_id:
                        self.audio_device_combo.setCurrentIndex(i)
                        break

            # Connect change handler
            self.audio_device_combo.currentIndexChanged.connect(
                self.on_audio_device_changed
            )

            app_logger.log_audio_event(
                "Audio devices refreshed", {"device_count": len(devices)}
            )

        except Exception as e:
            app_logger.log_error(e, "refresh_audio_devices")
            QMessageBox.warning(
                self, "Warning", f"Failed to refresh audio devices: {e}"
            )

    def on_audio_device_changed(self) -> None:
        """音频设备选择变化处理"""
        try:
            selected_device_id = self.audio_device_combo.currentData()

            # Update configuration
            self.ui_settings_service.set_setting("audio.device_id", selected_device_id)

            app_logger.log_audio_event(
                "Audio device changed", {"device_id": selected_device_id}
            )

        except Exception as e:
            app_logger.log_error(e, "on_audio_device_changed")

    def refresh_gpu_info(self) -> None:
        """刷新GPU信息显示 - 带超时的异步版本"""
        try:
            # 显示检查状态
            self.gpu_status_label.setText("🔄 Checking GPU...")
            self.gpu_status_label.setStyleSheet("color: blue;")
            self.transcription_tab.gpu_memory_label.setText("Detecting...")

            # 创建后台线程获取GPU信息，带超时控制
            import threading
            import time

            gpu_check_result = {"info": None, "completed": False, "error": None}

            def get_gpu_info():
                try:
                    # 尝试导入GPU管理器
                    from ..speech.gpu_manager import GPUManager

                    # 创建临时GPU管理器获取信息
                    temp_gpu_manager = GPUManager()
                    gpu_info = temp_gpu_manager.get_device_info()

                    gpu_check_result["info"] = gpu_info
                    gpu_check_result["completed"] = True

                except Exception as e:
                    app_logger.log_error(e, "get_gpu_info_background")
                    gpu_check_result["error"] = str(e)
                    gpu_check_result["completed"] = True

            # 启动后台线程
            gpu_thread = threading.Thread(target=get_gpu_info, daemon=True)
            gpu_thread.start()

            # 设置超时检查
            timeout_seconds = 10  # 10秒超时

            def check_gpu_result():
                if gpu_check_result["completed"]:
                    # GPU检查完成
                    if gpu_check_result["error"]:
                        gpu_info = {"error": gpu_check_result["error"]}
                    else:
                        gpu_info = gpu_check_result["info"] or {
                            "error": "No result returned"
                        }

                    self._update_gpu_display_from_info(gpu_info)
                else:
                    # 检查是否超时
                    elapsed = time.time() - start_time
                    if elapsed > timeout_seconds:
                        # 超时处理
                        app_logger.log_audio_event(
                            "GPU check timeout", {"timeout": timeout_seconds}
                        )
                        timeout_info = {
                            "error": f"GPU check timed out after {timeout_seconds} seconds",
                            "suggestion": "GPU drivers may be unresponsive",
                        }
                        self._update_gpu_display_from_info(timeout_info)
                    else:
                        # 继续等待，每500ms检查一次
                        from PySide6.QtCore import QTimer

                        QTimer.singleShot(500, check_gpu_result)

            # 开始检查
            start_time = time.time()
            from PySide6.QtCore import QTimer

            QTimer.singleShot(100, check_gpu_result)  # 100ms后开始检查

        except Exception as e:
            app_logger.log_error(e, "refresh_gpu_info")
            self.gpu_status_label.setText("❌ Error initializing GPU check")
            self.gpu_status_label.setStyleSheet("color: red;")
            self.transcription_tab.gpu_memory_label.setText("Error")

    def _update_gpu_display_from_info(self, gpu_info: dict) -> None:
        """从GPU信息更新显示 - 在主线程中调用"""
        try:
            if "error" in gpu_info:
                self.gpu_status_label.setText("❌ Error checking GPU")
                self.gpu_status_label.setStyleSheet("color: red;")
                self.transcription_tab.gpu_memory_label.setText("Error")
                return

            # 更新GPU状态显示
            if gpu_info.get("cuda_available", False):
                device_name = gpu_info.get("device_name", "Unknown GPU")
                self.gpu_status_label.setText(f"✅ {device_name}")
                self.gpu_status_label.setStyleSheet("color: green;")

                # 更新显存使用信息
                # 优先使用get_memory_usage返回的字段
                used_memory = gpu_info.get(
                    "allocated_gb", gpu_info.get("used_memory_gb", 0)
                )
                total_memory = gpu_info.get(
                    "total_gb", gpu_info.get("total_memory_gb", 0)
                )

                if total_memory > 0:
                    memory_percent = (used_memory / total_memory) * 100
                    self.transcription_tab.gpu_memory_label.setText(
                        f"{used_memory:.1f}GB / {total_memory:.1f}GB ({memory_percent:.1f}%)"
                    )
                else:
                    self.transcription_tab.gpu_memory_label.setText("Memory info unavailable")
            else:
                self.gpu_status_label.setText("❌ CUDA not available")
                self.gpu_status_label.setStyleSheet("color: red;")
                self.transcription_tab.gpu_memory_label.setText("N/A")

            app_logger.log_audio_event(
                "GPU info updated",
                {
                    "cuda_available": gpu_info.get("cuda_available", False),
                    "device_name": gpu_info.get("device_name", "N/A"),
                },
            )

        except Exception as e:
            app_logger.log_error(e, "_update_gpu_display_from_info")
            self.gpu_status_label.setText("❌ Error updating GPU display")
            self.gpu_status_label.setStyleSheet("color: red;")
            self.transcription_tab.gpu_memory_label.setText("Error")

    def refresh_model_status(self) -> None:
        """刷新模型状态显示"""
        try:
            # 显示检查状态
            self.transcription_tab.model_status_label.setText("Checking model status...")
            self.transcription_tab.model_status_label.setStyleSheet("color: blue;")

            # 使用 UI 模型服务获取模型信息
            if not self.ui_model_service:
                self.transcription_tab.model_status_label.setText("Model service not available")
                self.transcription_tab.model_status_label.setStyleSheet("color: red;")
                return

            # 获取模型信息并更新显示
            model_info = self.ui_model_service.get_model_info()
            self._update_model_display_from_info(model_info)

            app_logger.log_audio_event("Model status refreshed", {})

        except Exception as e:
            app_logger.log_error(e, "refresh_model_status")
            self.transcription_tab.model_status_label.setText(
                "Error checking model status"
            )
            self.transcription_tab.model_status_label.setStyleSheet("color: red;")

    def _update_model_display_from_info(self, model_info: dict) -> None:
        """从模型信息更新显示 - 在主线程中调用"""
        try:
            if not model_info.get("is_loaded", False):
                self.transcription_tab.model_status_label.setText("Model not loaded")
                self.transcription_tab.model_status_label.setStyleSheet("color: red;")
                return

            # 构建状态文本
            model_name = model_info.get("model_name", "Unknown")
            device = model_info.get("device", "Unknown")
            engine_type = model_info.get("engine_type", "unknown")
            load_time = model_info.get("load_time")
            cache_used = model_info.get("cache_used", False)

            # 基础状态文本 - 移除 emoji 以免编码问题
            status_parts = [f"{model_name}"]

            # 添加设备信息
            if device:
                status_parts.append(f"({device})")

            # 添加引擎类型
            if engine_type and engine_type != device:
                status_parts.append(f"[{engine_type}]")

            # 添加加载时间
            if load_time is not None:
                status_parts.append(f"- loaded in {load_time:.2f}s")

            # 添加缓存状态
            if cache_used:
                status_parts.append("(cached)")

            status_text = " ".join(status_parts)
            self.transcription_tab.model_status_label.setText(status_text)
            self.transcription_tab.model_status_label.setStyleSheet(
                "color: #4CAF50;"
            )  # Material Green

            app_logger.log_audio_event(
                "Model status display updated",
                {"model_name": model_name, "loaded": True, "engine_type": engine_type},
            )

        except Exception as e:
            app_logger.log_error(e, "_update_model_display_from_info")
            self.transcription_tab.model_status_label.setText(
                "❌ Error updating model display"
            )
            self.transcription_tab.model_status_label.setStyleSheet("color: red;")

    def test_clipboard(self) -> None:
        """测试剪贴板"""
        original_content = None
        try:
            import pyperclip

            # Backup original clipboard content
            try:
                original_content = pyperclip.paste()
            except Exception:
                original_content = ""

            # Test writing to clipboard
            test_text = "Voice Input Software Test"
            pyperclip.copy(test_text)

            # Test reading from clipboard
            clipboard_content = pyperclip.paste()

            # Restore original clipboard content
            if original_content is not None:
                pyperclip.copy(original_content)

            if clipboard_content == test_text:
                QMessageBox.information(
                    self,
                    "Clipboard Test",
                    "✅ Clipboard test successful!\n(Original clipboard content restored)",
                )
            else:
                QMessageBox.warning(
                    self, "Clipboard Test", "⚠️ Clipboard test failed - content mismatch"
                )

        except Exception as e:
            # Try to restore original content even if test failed
            if original_content is not None:
                try:
                    import pyperclip

                    pyperclip.copy(original_content)
                except Exception:
                    pass
            QMessageBox.critical(
                self, "Clipboard Test", f"❌ Clipboard test failed: {str(e)}"
            )

    def test_sendinput(self) -> None:
        """测试SendInput"""
        try:
            # Import Windows API components

            # Show warning dialog
            reply = QMessageBox.question(
                self,
                "SendInput Test",
                "This will test Windows SendInput functionality.\n\n"
                "Click 'Yes' and then quickly click in a text field to see test text appear.\n\n"
                "The test will start in 3 seconds after clicking 'Yes'.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Import timer for delay
                from PySide6.QtCore import QTimer

                # Delay before sending input
                QTimer.singleShot(3000, self._send_test_input)

                QMessageBox.information(
                    self,
                    "SendInput Test",
                    "Test initiated! Click in a text field now - test text will appear in 3 seconds.",
                )

        except Exception as e:
            QMessageBox.critical(
                self, "SendInput Test", f"❌ SendInput test failed: {str(e)}"
            )

    def _send_test_input(self) -> None:
        """Send test input using Windows SendInput"""
        try:
            import win32api
            import win32con
            import time

            test_text = "Voice Input Software SendInput Test"

            for char in test_text:
                # Send key down event
                win32api.keybd_event(ord(char.upper()), 0, 0, 0)
                # Send key up event
                win32api.keybd_event(ord(char.upper()), 0, win32con.KEYEVENTF_KEYUP, 0)
                time.sleep(0.01)  # Small delay between characters

        except Exception as e:
            QMessageBox.critical(
                self, "SendInput Test", f"❌ SendInput execution failed: {str(e)}"
            )

    def reset_current_tab(self) -> None:
        """重置当前标签页"""
        try:
            # 获取当前标签页索引和名称
            current_index = self.tab_widget.currentIndex()
            tab_names = [
                "Application",
                "Hotkeys",
                "Transcription",
                "AI Processing",
                "Audio and Input",
                "History",
            ]

            if current_index < 0 or current_index >= len(tab_names):
                QMessageBox.warning(
                    self, "Reset Tab", "❌ Unable to determine current tab."
                )
                return

            current_tab_name = tab_names[current_index]

            # 确认对话框
            reply = QMessageBox.question(
                self,
                "Reset Tab Settings",
                f"🔄 **Reset {current_tab_name} Tab**\n\n"
                f"Are you sure you want to reset all settings in the '{current_tab_name}' tab to their default values?\n\n"
                "⚠️ This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # 获取默认配置
            default_config = self.ui_settings_service.get_default_config()

            # 根据标签页重置相应设置
            if current_index == 0:  # Application
                self._reset_application_tab(default_config)
            elif current_index == 1:  # Hotkeys
                self._reset_hotkey_tab(default_config)
            elif current_index == 2:  # Transcription
                self._reset_transcription_tab(default_config)
            elif current_index == 3:  # AI Processing
                self._reset_ai_tab(default_config)
            elif current_index == 4:  # Audio and Input
                self._reset_audio_input_tab(default_config)
            elif current_index == 5:  # History
                self._reset_history_tab(default_config)

            # 显示成功消息
            QMessageBox.information(
                self,
                "Reset Complete",
                f"✅ **{current_tab_name} Tab Reset**\n\n"
                f"All settings in the '{current_tab_name}' tab have been reset to their default values.\n\n"
                "Click 'Apply' or 'OK' to save the changes.",
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Reset Error",
                f"❌ **Reset Failed**\n\n"
                f"Failed to reset tab settings: {str(e)}\n\n"
                "Please try again or check the application logs.",
            )

    def _reset_application_tab(self, default_config) -> None:
        """重置应用设置标签页 (Application Tab - merged General + UI)"""
        ui_config = default_config.get("ui", {})
        logging_config = default_config.get("logging", {})

        # 重置UI设置
        self.config_manager.set_setting(
            "ui.start_minimized", ui_config.get("start_minimized", True)
        )
        self.config_manager.set_setting(
            "ui.tray_notifications", ui_config.get("tray_notifications", True)
        )
        self.config_manager.set_setting(
            "ui.show_overlay", ui_config.get("show_overlay", True)
        )
        self.config_manager.set_setting(
            "ui.overlay_always_on_top", ui_config.get("overlay_always_on_top", True)
        )
        self.config_manager.set_setting(
            "ui.theme_color", ui_config.get("theme_color", "cyan")
        )

        # 重置overlay_position
        default_overlay_position = ui_config.get(
            "overlay_position",
            {
                "mode": "preset",
                "preset": "center",
                "custom": {"x": 0, "y": 0},
                "last_screen": {
                    "index": 0,
                    "name": "",
                    "geometry": "",
                    "device_pixel_ratio": 1.0,
                },
                "auto_save": True,
            },
        )
        self.config_manager.set_setting("ui.overlay_position", default_overlay_position)

        # 重置日志设置
        self.config_manager.set_setting(
            "logging.level", logging_config.get("level", "INFO")
        )
        self.config_manager.set_setting(
            "logging.console_output", logging_config.get("console_output", False)
        )
        self.config_manager.set_setting(
            "logging.max_log_size_mb", logging_config.get("max_log_size_mb", 10)
        )

        self.update_ui_from_config()

    def _reset_hotkey_tab(self, default_config) -> None:
        """重置热键标签页"""
        hotkeys = default_config.get("hotkeys", ["ctrl+shift+v"])

        # 清空列表并添加默认快捷键
        self.hotkeys_list.clear()
        for hotkey in hotkeys:
            self.hotkeys_list.addItem(hotkey)

    def _reset_transcription_tab(self, default_config) -> None:
        """重置Transcription标签页"""
        whisper_config = default_config.get("whisper", {})

        # 重置模型选择
        model = whisper_config.get("model", "large-v3-turbo")
        index = self.whisper_model_combo.findText(model)
        if index >= 0:
            self.whisper_model_combo.setCurrentIndex(index)

        # 重置其他设置
        self.config_manager.set_setting("whisper.model", model)
        self.config_manager.set_setting(
            "whisper.language", whisper_config.get("language", "auto")
        )
        self.config_manager.set_setting(
            "whisper.use_gpu", whisper_config.get("use_gpu", True)
        )
        self.config_manager.set_setting(
            "whisper.temperature", whisper_config.get("temperature", 0.0)
        )

    def _reset_ai_tab(self, default_config) -> None:
        """重置AI设置标签页"""
        ai_config = default_config.get("ai", {})
        openrouter_config = ai_config.get("openrouter", {})

        # 重置API密钥为空（安全起见）
        self.api_key_input.clear()

        # 重置模型ID和提示词（使用新路径）
        model_id = openrouter_config.get("model_id", "anthropic/claude-3-sonnet")
        default_system_prompt = (
            "You are a professional transcription refinement specialist. "
            "Your task is to correct and improve text that has been transcribed by an automatic speech recognition (ASR) system.\n\n"
            "Your responsibilities:\n"
            "1. Remove filler words (um, uh, like, you know, etc.) and disfluencies\n"
            "2. Correct homophones and misrecognized words to their contextually appropriate forms\n"
            "3. Fix grammatical errors and improve sentence structure\n"
            "4. Preserve the original meaning and intent of the speaker\n"
            "5. Maintain natural language flow\n\n"
            "Important constraints:\n"
            "- Output ONLY the corrected text, nothing else\n"
            "- Do NOT add explanations, comments, or metadata\n"
            "- Do NOT change the core message or add information not present in the original\n"
            "- Maintain the speaker's tone and style"
        )
        prompt = ai_config.get("prompt", default_system_prompt)

        self.ai_model_input.setText(model_id)
        self.prompt_text_edit.setPlainText(prompt)

        # 保存到配置（新路径）
        self.config_manager.set_setting("ai.openrouter.model_id", model_id)
        self.config_manager.set_setting("ai.prompt", prompt)

    def _reset_audio_input_tab(self, default_config) -> None:
        """重置音频和输入设置标签页 (Audio and Input Tab - merged Audio + Input)"""
        audio_config = default_config.get("audio", {})
        input_config = default_config.get("input", {})

        # 重置音频设备为默认
        self.audio_device_combo.setCurrentIndex(0)  # 通常第一个是默认设备

        # 重置音频设置
        self.config_manager.set_setting(
            "audio.sample_rate", audio_config.get("sample_rate", 16000)
        )
        self.config_manager.set_setting(
            "audio.channels", audio_config.get("channels", 1)
        )
        self.config_manager.set_setting(
            "audio.chunk_size", audio_config.get("chunk_size", 1024)
        )

        # 重置输入方法设置
        self.config_manager.set_setting(
            "input.preferred_method", input_config.get("preferred_method", "clipboard")
        )
        self.config_manager.set_setting(
            "input.fallback_enabled", input_config.get("fallback_enabled", True)
        )
        self.config_manager.set_setting(
            "input.auto_detect_terminal", input_config.get("auto_detect_terminal", True)
        )
        self.config_manager.set_setting(
            "input.method", input_config.get("method", "smart")
        )
        self.config_manager.set_setting(
            "input.clipboard_restore_delay",
            input_config.get("clipboard_restore_delay", 2.0),
        )
        self.config_manager.set_setting(
            "input.typing_delay", input_config.get("typing_delay", 0.01)
        )
        self.update_ui_from_config()

    def _reset_history_tab(self, default_config) -> None:
        """重置历史记录标签页"""
        # History tab doesn't have configuration settings - it only displays data
        pass

    def _reset_ui_tab(self, default_config) -> None:
        """重置UI设置标签页"""
        ui_config = default_config.get("ui", {})

        # 重置UI设置 - 修复字段名称和复杂结构处理
        self.config_manager.set_setting(
            "ui.start_minimized", ui_config.get("start_minimized", True)
        )
        self.config_manager.set_setting(
            "ui.show_overlay", ui_config.get("show_overlay", True)
        )
        self.config_manager.set_setting(
            "ui.overlay_always_on_top", ui_config.get("overlay_always_on_top", True)
        )

        # 正确处理复杂的overlay_position结构
        default_overlay_position = ui_config.get(
            "overlay_position",
            {
                "mode": "preset",
                "preset": "center",
                "custom": {"x": 0, "y": 0},
                "last_screen": {
                    "index": 0,
                    "name": "",
                    "geometry": "",
                    "device_pixel_ratio": 1.0,
                },
                "auto_save": True,
            },
        )
        self.config_manager.set_setting("ui.overlay_position", default_overlay_position)
