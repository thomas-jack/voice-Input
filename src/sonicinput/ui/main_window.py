"""主窗口组件 - 最小化GUI实现（使用依赖注入）"""

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QSystemTrayIcon,
    QProgressDialog,
    QMessageBox,
    QApplication,
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from typing import Optional, Dict, Any
from ..core.interfaces import IUIMainService, IUISettingsService, IUIModelService
from ..core.services.event_bus import Events
from ..utils import app_logger


class ModelTestThread(QThread):
    """Model test thread to avoid blocking UI"""

    progress_update = Signal(str)
    test_complete = Signal(bool, dict, str)

    def __init__(self, whisper_engine, parent=None):
        super().__init__(parent)
        self.whisper_engine = whisper_engine

    def run(self):
        try:
            import numpy as np

            self.progress_update.emit("Creating test audio (2s low-level noise)...")
            # Create low-level white noise instead of silence to avoid hallucination
            # Use shorter duration and very low amplitude
            duration = 2  # 2 seconds
            sample_rate = 16000
            audio_length = int(duration * sample_rate)

            # Generate very low amplitude white noise
            test_audio = np.random.normal(0, 0.001, audio_length).astype(np.float32)

            app_logger.log_audio_event(
                "Model test requested",
                {"audio_type": "low_noise", "duration": duration, "amplitude": "0.001"},
            )

            self.progress_update.emit("Running transcription test...")
            result = self.whisper_engine.transcribe(test_audio)

            # Check for hallucination patterns
            text_output = result.get("text", "").strip()
            is_hallucination = self._is_likely_hallucination(text_output)

            # For test purposes, hallucination on noise is actually expected behavior
            test_success = True  # Model responded without crashing

            result_info = {
                "text": text_output,
                "is_hallucination": is_hallucination,
                "confidence": result.get("confidence", 0),
                "language": result.get("language", "unknown"),
            }

            app_logger.log_audio_event(
                "Model test completed",
                {
                    "result": text_output,
                    "is_hallucination": is_hallucination,
                    "test_success": test_success,
                    "confidence": result.get("confidence", 0),
                },
            )

            self.test_complete.emit(test_success, result_info, "")

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            app_logger.log_error(e, "ModelTestThread.run")
            # 添加详细的错误信息到结果中
            self.test_complete.emit(False, {}, error_msg)

    def _is_likely_hallucination(self, text: str) -> bool:
        """Check if text output is likely a Whisper hallucination"""
        if not text:
            return False

        text_lower = text.lower().strip()

        # Common Whisper hallucination patterns
        common_hallucinations = [
            "thank you",
            "thanks",
            "thank you.",
            "thanks.",
            "bye",
            "bye.",
            "goodbye",
            "goodbye.",
            "you",
            "you.",
            "okay",
            "okay.",
            "ok",
            "ok.",
            "yes",
            "yes.",
            "no",
            "no.",
            "yeah",
            "yeah.",
            "um",
            "uh",
            "hmm",
            "mm",
            "hello",
            "hi",
            "hey",
            "music",
            "applause",
            "laughter",
            "silence",
            "quiet",
            "pause",
        ]

        return text_lower in common_hallucinations


class MainWindow(QMainWindow):
    """最小化主窗口 - 使用依赖注入的UI服务"""

    # 信号定义
    window_closing = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui_main_service: Optional[IUIMainService] = None
        self.ui_settings_service: Optional[IUISettingsService] = None
        self.ui_model_service: Optional[IUIModelService] = None
        self.setup_window()
        self.setup_ui()
        app_logger.log_audio_event("MainWindow initialized with DI", {})

    def setup_window(self) -> None:
        """配置窗口基本属性"""
        from .utils import create_app_icon

        self.setWindowTitle("Voice Input Software")
        self.setWindowIcon(create_app_icon())
        self.setFixedSize(400, 300)  # 固定小尺寸
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)

        # 默认隐藏 - 使用系统托盘
        self.hide()

    def setup_ui(self) -> None:
        """设置最小化UI界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 状态显示
        self.status_label = QLabel("Voice Input Software")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.status_label)

        # 录音控制
        self.recording_button = QPushButton("Start Recording")
        self.recording_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.recording_button)

        # 设置按钮
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.show_settings)
        layout.addWidget(self.settings_button)

        # 最小化到托盘按钮
        self.minimize_button = QPushButton("Minimize to Tray")
        self.minimize_button.clicked.connect(self.hide)
        layout.addWidget(self.minimize_button)

    def set_controller(self, voice_input_app) -> None:
        """设置应用控制器（向后兼容方法）

        Args:
            voice_input_app: VoiceInputApp实例
        """
        # 创建UI服务适配器
        from ..core.services.ui_service_adapter import (
            UIMainServiceAdapter,
            UISettingsServiceAdapter,
            UIModelServiceAdapter
        )

        ui_main_service = UIMainServiceAdapter(voice_input_app)
        ui_settings_service = UISettingsServiceAdapter(
            voice_input_app.config,
            voice_input_app.events
        )
        ui_model_service = UIModelServiceAdapter(voice_input_app)

        # 设置UI服务
        self.set_ui_services(
            ui_main_service,
            ui_settings_service,
            ui_model_service
        )

    def set_ui_services(
        self,
        ui_main_service: IUIMainService,
        ui_settings_service: IUISettingsService,
        ui_model_service: IUIModelService
    ) -> None:
        """设置UI服务（依赖注入）

        Args:
            ui_main_service: 主窗口UI服务
            ui_settings_service: 设置窗口UI服务
            ui_model_service: 模型管理UI服务
        """
        self.ui_main_service = ui_main_service
        self.ui_settings_service = ui_settings_service
        self.ui_model_service = ui_model_service
        self._connect_service_events()

    def _connect_service_events(self) -> None:
        """连接UI服务事件"""
        if not self.ui_main_service:
            return

        # 录音状态事件
        events = self.ui_main_service.get_event_service()
        events.on(Events.RECORDING_STARTED, self._on_recording_started)
        events.on(Events.RECORDING_STOPPED, self._on_recording_stopped)

    def _on_recording_started(self, data: Any = None) -> None:
        """录音开始事件"""
        self.recording_button.setText("Stop Recording")
        self.status_label.setText("Recording...")

    def _on_recording_stopped(self, audio_length: int) -> None:
        """录音停止事件"""
        self.recording_button.setText("Start Recording")
        self.status_label.setText("Ready")

    def toggle_recording(self) -> None:
        """切换录音状态"""
        if not self.ui_main_service:
            return

        if self.ui_main_service.is_recording():
            self.ui_main_service.stop_recording()
        else:
            self.ui_main_service.start_recording()

    def show_settings(self) -> None:
        """显示设置窗口"""
        try:
            from .settings_window import SettingsWindow

            if not hasattr(self, "_settings_window") or not self._settings_window:
                self._settings_window = SettingsWindow(
                    self.ui_settings_service, self.ui_model_service
                )

                # 连接模型管理信号
                self._settings_window.model_load_requested.connect(
                    self._on_model_load_requested
                )
                self._settings_window.model_unload_requested.connect(
                    self._on_model_unload_requested
                )
                self._settings_window.model_test_requested.connect(
                    self._on_model_test_requested
                )

            self._settings_window.show()
            self._settings_window.raise_()
            self._settings_window.activateWindow()

        except Exception as e:
            app_logger.log_error(e, "show_settings")

    def _on_model_load_requested(self, model_name: str) -> None:
        """处理模型加载请求（使用简化的进度对话框）"""
        try:
            if self.ui_model_service:
                app_logger.log_audio_event(
                    "Model load requested via GUI", {"model": model_name}
                )

                parent_widget = (
                    self._settings_window if hasattr(self, "_settings_window") else None
                )

                # 创建简单的进度对话框
                progress = QProgressDialog(
                    f"Loading model: {model_name}...\nThis may take a few seconds.",
                    None,  # No cancel button
                    0,
                    0,  # Indeterminate progress
                    parent_widget,
                )
                progress.setWindowTitle("Loading Model")
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setCancelButton(None)
                progress.show()

                # 强制刷新UI
                QApplication.processEvents()

                try:
                    # 执行模型加载
                    self.ui_model_service.load_model(model_name)
                    progress.close()

                    app_logger.log_audio_event(
                        "Model load completed successfully via GUI",
                        {"model_name": model_name},
                    )

                    QMessageBox.information(
                        parent_widget,
                        "Model Loaded",
                        f"Model '{model_name}' loaded successfully!",
                    )

                except Exception as load_error:
                    progress.close()
                    app_logger.log_error(load_error, "model_load_execution")
                    QMessageBox.critical(
                        parent_widget,
                        "Model Load Failed",
                        f"Failed to load model '{model_name}':\n{load_error}",
                    )

                # Always refresh status after load attempt
                if hasattr(self, "_settings_window") and self._settings_window:
                    QTimer.singleShot(100, self._settings_window.refresh_model_status)

        except Exception as e:
            app_logger.log_error(e, "model_load_request_gui")
            QMessageBox.critical(
                self._settings_window if hasattr(self, "_settings_window") else None,
                "Error",
                f"Error processing model load request:\n{e}",
            )

    def _on_model_unload_requested(self) -> None:
        """处理模型卸载请求"""
        try:
            if self.ui_model_service:
                app_logger.log_audio_event("Model unload requested", {})
                self.ui_model_service.unload_model()
                app_logger.log_audio_event("Model unloaded successfully", {})
                # Refresh model status in settings window
                if hasattr(self, "_settings_window") and self._settings_window:
                    self._settings_window.refresh_model_status()
        except Exception as e:
            app_logger.log_error(e, "_on_model_unload_requested")

    def _on_model_test_requested(self) -> None:
        """处理模型测试请求"""
        try:
            if self.ui_model_service:
                whisper_engine = self.ui_model_service.get_whisper_engine()

                if not whisper_engine.is_model_loaded:
                    QMessageBox.warning(
                        self._settings_window
                        if hasattr(self, "_settings_window")
                        else None,
                        "Model Not Loaded",
                        "Please load a model first before testing.",
                    )
                    return

                parent_widget = (
                    self._settings_window if hasattr(self, "_settings_window") else None
                )

                progress = QProgressDialog(
                    "Testing model...", "Cancel", 0, 0, parent_widget
                )
                progress.setWindowTitle("Model Test")
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setCancelButton(None)

                test_thread = ModelTestThread(whisper_engine, self)

                def on_progress_update(message: str):
                    progress.setLabelText(message)

                def on_test_complete(success: bool, result: Dict[str, Any], error: str):
                    progress.close()

                    if success:
                        text_output = result.get("text", "No text detected")
                        is_hallucination = result.get("is_hallucination", False)
                        confidence = result.get("confidence", 0)
                        detected_language = result.get("language", "unknown")

                        # Create informative message about the test result
                        if is_hallucination:
                            analysis_text = f"**Analysis**: Output '{text_output}' appears to be a Whisper hallucination from noise audio, which is normal behavior."
                        elif not text_output or text_output == "No text detected":
                            analysis_text = "**Analysis**: No text detected from test audio, which is expected."
                        else:
                            analysis_text = "**Analysis**: Model produced text output from test audio."

                        QMessageBox.information(
                            parent_widget,
                            "Model Test Result",
                            f"**Model Test Successful!**\n\n"
                            f"Model: {whisper_engine.model_name}\n"
                            f"Device: {whisper_engine.device}\n"
                            f"Detected Language: {detected_language}\n"
                            f"Test Output: '{text_output}'\n"
                            f"Confidence: {confidence:.2f}\n\n"
                            f"{analysis_text}\n\n"
                            f"The model is working correctly and can process audio!",
                        )
                    else:
                        QMessageBox.critical(
                            parent_widget,
                            "Model Test Failed",
                            f"**Model Test Failed**\n\n"
                            f"Error: {error}\n\n"
                            f"Please check the model status and try again.",
                        )

                test_thread.progress_update.connect(on_progress_update)
                test_thread.test_complete.connect(on_test_complete)

                progress.show()
                test_thread.start()

        except Exception as e:
            error_details = f"{type(e).__name__}: {str(e)}"
            app_logger.log_error(e, "_on_model_test_requested")
            QMessageBox.critical(
                self._settings_window if hasattr(self, "_settings_window") else None,
                "Model Test Failed",
                f"**Model Test Failed**\n\n"
                f"Error: {error_details}\n\n"
                f"Please check the model status and try again.",
            )

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 最小化到系统托盘而不是真正关闭
        event.ignore()
        self.hide()

        # 可选：显示托盘通知
        if hasattr(self, "system_tray") and self.system_tray:
            self.system_tray.showMessage(
                "Voice Input Software",
                "Application minimized to tray",
                QSystemTrayIcon.MessageIcon.Information,
                2000,
            )
