"""历史记录标签页"""

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QMessageBox,
    QHeaderView,
    QAbstractItemView,
    QLineEdit,
    QLabel,
    QGroupBox,
    QDialog,
    QTextEdit,
    QProgressDialog,
)
from PySide6.QtCore import Qt, QThread, Signal
from typing import Dict, Any, List
from .base_tab import BaseSettingsTab


class ReprocessingWorker(QThread):
    """重新处理录音的后台工作线程"""

    # 信号定义
    progress_updated = Signal(str)  # 进度更新信号
    reprocessing_completed = Signal(dict)  # 重处理完成信号
    reprocessing_failed = Signal(str)  # 重处理失败信号

    def __init__(
        self,
        record,
        transcription_service,
        ai_processing_controller,
        config_service,
        history_service,
    ):
        super().__init__()
        self.record = record
        self.transcription_service = transcription_service
        self.ai_processing_controller = ai_processing_controller
        self.config_service = config_service
        self.history_service = history_service
        self.should_stop = False

    def run(self):
        """后台线程执行重处理流程"""
        try:
            from ...audio.recorder import AudioRecorder
            from ...utils import app_logger

            # 1. 加载音频文件
            self.progress_updated.emit("Loading audio file...")
            audio_file_path = self.record.audio_file_path

            if not audio_file_path:
                self.reprocessing_failed.emit("Audio file path not found in record")
                return

            try:
                audio_data = AudioRecorder.load_audio_from_file(audio_file_path)
                if audio_data is None or len(audio_data) == 0:
                    self.reprocessing_failed.emit("Failed to load audio data from file")
                    return
            except FileNotFoundError:
                self.reprocessing_failed.emit(f"Audio file not found: {audio_file_path}")
                return
            except Exception as e:
                self.reprocessing_failed.emit(f"Error loading audio file: {str(e)}")
                return

            if self.should_stop:
                return

            # 2. 重新转录
            self.progress_updated.emit("Transcribing audio...")

            try:
                # 获取当前转录配置
                transcription_provider = self.config_service.get_setting("transcription.provider", "local")
                language = self.config_service.get_setting(f"transcription.{transcription_provider}.language", "auto")
                temperature = self.config_service.get_setting("transcription.temperature", 0.0)

                # 调用转录服务
                transcription_result = self.transcription_service.transcribe_sync(
                    audio_data=audio_data,
                    language=language if language != "auto" else None,
                    temperature=temperature,
                )

                if not transcription_result.get("success", True):
                    error_msg = transcription_result.get("error", "Unknown transcription error")
                    self.reprocessing_failed.emit(f"Transcription failed: {error_msg}")

                    # 更新历史记录为失败状态
                    self.record.transcription_status = "failed"
                    self.record.transcription_error = error_msg
                    self.record.transcription_provider = transcription_provider
                    self.history_service.update_record(self.record)
                    return

                transcription_text = transcription_result.get("text", "")

                if not transcription_text.strip():
                    self.reprocessing_failed.emit("Transcription returned empty text")
                    return

            except Exception as e:
                app_logger.log_error(e, "reprocessing_transcription")
                self.reprocessing_failed.emit(f"Transcription error: {str(e)}")
                return

            if self.should_stop:
                return

            # 3. 重新AI优化（如果启用）
            ai_enabled = self.config_service.get_setting("ai.enabled", False)
            ai_optimized_text = None
            ai_provider = None
            ai_status = "skipped"
            ai_error = None

            if ai_enabled and transcription_text.strip():
                self.progress_updated.emit("Optimizing with AI...")

                # 检查AI控制器是否可用
                if not self.ai_processing_controller:
                    ai_status = "skipped"
                    ai_error = "AI processing controller not available"
                    ai_optimized_text = ""
                    app_logger.log_audio_event(
                        "Retry processing: AI controller not available, skipping AI optimization",
                        {"ai_enabled": ai_enabled}
                    )
                else:
                    try:
                        # 设置当前记录ID供AI控制器使用
                        self.ai_processing_controller._current_record_id = self.record.id

                        # 调用AI处理
                        ai_optimized_text = self.ai_processing_controller.process_with_ai(
                            transcription_text
                        )

                        # 获取AI提供商信息
                        ai_provider = self.config_service.get_setting("ai.provider", "groq")

                        if ai_optimized_text and ai_optimized_text.strip():
                            ai_status = "success"
                        else:
                            ai_status = "failed"
                            ai_error = "AI returned empty text"

                    except Exception as e:
                        app_logger.log_error(e, "reprocessing_ai_optimization")
                        ai_status = "failed"
                        ai_error = str(e)
                        ai_optimized_text = None

            if self.should_stop:
                return

            # 4. 更新历史记录
            self.progress_updated.emit("Updating history record...")

            # 确定最终文本
            if ai_status == "success" and ai_optimized_text:
                final_text = ai_optimized_text
            else:
                final_text = transcription_text

            # 更新记录对象
            self.record.transcription_text = transcription_text
            self.record.transcription_provider = transcription_provider
            self.record.transcription_status = "success"
            self.record.transcription_error = None
            self.record.ai_optimized_text = ai_optimized_text
            self.record.ai_provider = ai_provider
            self.record.ai_status = ai_status
            self.record.ai_error = ai_error
            self.record.final_text = final_text

            # 保存到数据库
            try:
                self.history_service.update_record(self.record)
            except Exception as e:
                app_logger.log_error(e, "reprocessing_update_record")
                self.reprocessing_failed.emit(f"Failed to update history record: {str(e)}")
                return

            # 5. 完成
            result = {
                "transcription_text": transcription_text,
                "ai_optimized_text": ai_optimized_text,
                "final_text": final_text,
                "ai_status": ai_status,
                "transcription_provider": transcription_provider,
            }

            self.reprocessing_completed.emit(result)

        except Exception as e:
            from ...utils import app_logger

            app_logger.log_error(e, "reprocessing_worker")
            self.reprocessing_failed.emit(f"Unexpected error: {str(e)}")

    def stop(self):
        """请求停止处理"""
        self.should_stop = True


class HistoryDetailDialog(QDialog):
    """历史记录详情对话框"""

    def __init__(
        self,
        record,
        parent_window,
        history_service,
        transcription_service=None,
        ai_processing_controller=None,
        config_service=None,
        parent=None,
    ):
        super().__init__(parent)
        self.record = record
        self.parent_window = parent_window
        self.history_service = history_service
        self.transcription_service = transcription_service
        self.ai_processing_controller = ai_processing_controller
        self.config_service = config_service
        self.reprocessing_worker = None
        self.progress_dialog = None
        self.setup_ui()

    def setup_ui(self):
        """设置对话框UI"""
        self.setWindowTitle("Recording Details")
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout(self)

        # 信息区域
        info_layout = QVBoxLayout()

        # 基本信息
        basic_info = QGroupBox("Basic Information")
        basic_layout = QVBoxLayout(basic_info)

        time_label = QLabel(f"<b>Time:</b> {self.record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        duration_label = QLabel(f"<b>Duration:</b> {self.record.duration:.2f}s")
        audio_path_label = QLabel(f"<b>Audio File:</b> {self.record.audio_file_path or 'N/A'}")
        audio_path_label.setWordWrap(True)

        basic_layout.addWidget(time_label)
        basic_layout.addWidget(duration_label)
        basic_layout.addWidget(audio_path_label)
        info_layout.addWidget(basic_info)

        # 原始转录信息
        trans_group = QGroupBox(f"Original Transcription ({self.record.transcription_status})")
        trans_layout = QVBoxLayout(trans_group)

        trans_provider_label = QLabel(f"<b>Provider:</b> {self.record.transcription_provider or 'N/A'}")
        trans_layout.addWidget(trans_provider_label)

        if self.record.transcription_error:
            error_label = QLabel(f"<b>Error:</b> {self.record.transcription_error}")
            error_label.setStyleSheet("color: red;")
            trans_layout.addWidget(error_label)

        self.trans_text_edit = QTextEdit()
        self.trans_text_edit.setPlainText(self.record.transcription_text or "(empty)")
        self.trans_text_edit.setReadOnly(True)
        self.trans_text_edit.setMaximumHeight(150)
        trans_layout.addWidget(self.trans_text_edit)
        info_layout.addWidget(trans_group)

        # 优化后文本（根据AI状态显示不同内容）
        ai_status_text = f"AI {self.record.ai_status.title()}" if self.record.ai_status else "AI Status Unknown"
        optimized_group = QGroupBox(f"Optimized Text ({ai_status_text})")
        optimized_layout = QVBoxLayout(optimized_group)

        # 显示 AI 提供商（如果有）
        if self.record.ai_provider:
            ai_provider_label = QLabel(f"<b>AI Provider:</b> {self.record.ai_provider}")
            optimized_layout.addWidget(ai_provider_label)

        # 显示错误（如果有）
        if self.record.ai_error:
            ai_error_label = QLabel(f"<b>Error:</b> {self.record.ai_error}")
            ai_error_label.setStyleSheet("color: red;")
            optimized_layout.addWidget(ai_error_label)

        self.optimized_text_edit = QTextEdit()
        # 根据 AI 状态显示文本
        if self.record.ai_status == "success" and self.record.ai_optimized_text:
            display_text = self.record.ai_optimized_text
        else:
            # AI 失败或跳过，显示原始文本并注明
            display_text = f"{self.record.transcription_text}\n\n(Using original transcription - AI {self.record.ai_status})"

        self.optimized_text_edit.setPlainText(display_text or "(empty)")
        self.optimized_text_edit.setReadOnly(True)
        self.optimized_text_edit.setMaximumHeight(150)
        optimized_layout.addWidget(self.optimized_text_edit)
        info_layout.addWidget(optimized_group)

        layout.addLayout(info_layout)

        # 操作按钮
        button_layout = QHBoxLayout()

        copy_button = QPushButton("Copy to Clipboard")
        copy_button.clicked.connect(self._copy_to_clipboard)
        button_layout.addWidget(copy_button)

        self.retry_button = QPushButton("Retry")
        self.retry_button.clicked.connect(self._retry_processing)
        button_layout.addWidget(self.retry_button)

        delete_button = QPushButton("Delete Record")
        delete_button.clicked.connect(self._delete_record)
        delete_button.setStyleSheet("background-color: #d32f2f; color: white;")
        button_layout.addWidget(delete_button)

        button_layout.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

    def _copy_to_clipboard(self):
        """复制优化后的文本到剪贴板"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        # 复制优化后的文本（如果 AI 成功则是AI文本，否则是转录文本）
        text_to_copy = self.optimized_text_edit.toPlainText()
        clipboard.setText(text_to_copy)
        QMessageBox.information(self, "Success", "Text copied to clipboard!")

    def _retry_processing(self):
        """重新处理录音（使用当前配置）"""
        from ...utils import app_logger

        app_logger.log_audio_event(
            "Retry processing requested",
            {
                "has_transcription_service": self.transcription_service is not None,
                "has_config_service": self.config_service is not None,
                "has_ai_controller": self.ai_processing_controller is not None,
                "transcription_service_type": type(self.transcription_service).__name__ if self.transcription_service else "None"
            }
        )

        # 检查是否有必要的服务
        if not self.transcription_service or not self.config_service:
            QMessageBox.warning(
                self,
                "Service Unavailable",
                "Retry processing requires transcription service.\n\n"
                "This feature may not be available in this context."
            )
            return

        # 确认对话框
        reply = QMessageBox.question(
            self,
            "Retry Processing",
            "This will reprocess the recording using current configuration.\n\n"
            "- Transcription will use current provider/model\n"
            "- AI optimization will use current settings\n\n"
            "The original record will be updated with new results.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 创建进度对话框
        self.progress_dialog = QProgressDialog(
            "Initializing reprocessing...",
            "Cancel",
            0,
            0,  # 不确定进度的模式
            self
        )
        self.progress_dialog.setWindowTitle("Reprocessing Recording")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

        # 创建并启动后台工作线程
        self.reprocessing_worker = ReprocessingWorker(
            record=self.record,
            transcription_service=self.transcription_service,
            ai_processing_controller=self.ai_processing_controller,
            config_service=self.config_service,
            history_service=self.history_service,
        )

        # 连接信号
        self.reprocessing_worker.progress_updated.connect(self._on_progress_updated)
        self.reprocessing_worker.reprocessing_completed.connect(self._on_reprocessing_completed)
        self.reprocessing_worker.reprocessing_failed.connect(self._on_reprocessing_failed)
        self.progress_dialog.canceled.connect(self._on_reprocessing_canceled)

        # 启动工作线程
        self.reprocessing_worker.start()

    def _on_progress_updated(self, message: str):
        """更新进度对话框"""
        if self.progress_dialog:
            self.progress_dialog.setLabelText(message)

    def _on_reprocessing_completed(self, result: dict):
        """重处理完成"""
        # 关闭进度对话框 (先断开信号避免触发canceled)
        if self.progress_dialog:
            self.progress_dialog.canceled.disconnect(self._on_reprocessing_canceled)
            self.progress_dialog.close()
            self.progress_dialog = None

        # 更新UI显示
        transcription_text = result.get("transcription_text", "")
        ai_optimized_text = result.get("ai_optimized_text", "")
        final_text = result.get("final_text", "")
        ai_status = result.get("ai_status", "skipped")

        # 更新转录文本框
        self.trans_text_edit.setPlainText(transcription_text or "(empty)")

        # 更新优化后的文本框
        if ai_status == "success" and ai_optimized_text:
            display_text = ai_optimized_text
        else:
            display_text = f"{transcription_text}\n\n(Using original transcription - AI {ai_status})"

        self.optimized_text_edit.setPlainText(display_text or "(empty)")

        # 清理worker
        self.reprocessing_worker = None

        # 显示成功消息
        QMessageBox.information(
            self,
            "Reprocessing Complete",
            "Recording has been successfully reprocessed!\n\n"
            f"Transcription Provider: {result.get('transcription_provider', 'N/A')}\n"
            f"AI Status: {ai_status}\n\n"
            "The record has been updated in the history."
        )

    def _on_reprocessing_failed(self, error_message: str):
        """重处理失败"""
        # 关闭进度对话框 (先断开信号避免触发canceled)
        if self.progress_dialog:
            self.progress_dialog.canceled.disconnect(self._on_reprocessing_canceled)
            self.progress_dialog.close()
            self.progress_dialog = None

        # 清理worker
        self.reprocessing_worker = None

        # 显示错误消息
        QMessageBox.critical(
            self,
            "Reprocessing Failed",
            f"Failed to reprocess the recording:\n\n{error_message}\n\n"
            "Please check the logs for more details."
        )

    def _on_reprocessing_canceled(self):
        """用户取消重处理"""
        if self.reprocessing_worker:
            self.reprocessing_worker.stop()
            self.reprocessing_worker.wait(2000)  # 等待最多2秒

            # 强制终止（如果还在运行）
            if self.reprocessing_worker.isRunning():
                self.reprocessing_worker.terminate()
                self.reprocessing_worker.wait()

            self.reprocessing_worker = None

        QMessageBox.information(
            self,
            "Reprocessing Canceled",
            "Reprocessing operation has been canceled."
        )

    def _delete_record(self):
        """删除记录"""
        reply = QMessageBox.question(
            self,
            "Delete Record",
            f"Are you sure you want to delete this record?\n\nTime: {self.record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.history_service.delete_record(self.record.id)
                if success:
                    QMessageBox.information(
                        self,
                        "Success",
                        "Record deleted successfully!"
                    )
                    self.accept()  # 关闭对话框
                else:
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Failed to delete record."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error deleting record: {str(e)}"
                )


class HistoryTab(BaseSettingsTab):
    """历史记录标签页

    显示所有录音历史记录，包括：
    - 录音时间
    - 时长
    - 转录结果
    - AI优化状态
    - 最终文本

    功能：
    - 查看详情
    - 删除记录
    - 搜索过滤
    - 刷新列表
    - 重新处理录音
    """

    def __init__(
        self,
        config_manager,
        parent_window,
        transcription_service=None,
        ai_processing_controller=None,
    ):
        super().__init__(config_manager, parent_window)
        self.history_service = None  # 延迟初始化
        self.transcription_service = transcription_service
        self.ai_processing_controller = ai_processing_controller
        self.current_records: List[Any] = []  # 当前显示的记录列表

        from ...utils import app_logger
        app_logger.log_audio_event(
            "HistoryTab initialized with services",
            {
                "has_transcription_service": self.transcription_service is not None,
                "has_ai_processing_controller": self.ai_processing_controller is not None,
                "transcription_service_type": type(self.transcription_service).__name__ if self.transcription_service else "None",
                "ai_controller_type": type(self.ai_processing_controller).__name__ if self.ai_processing_controller else "None"
            }
        )

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 顶部工具栏
        toolbar_layout = QHBoxLayout()

        # 搜索框
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in transcription or AI text...")
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.search_input, stretch=1)

        # 刷新按钮
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._load_history)
        toolbar_layout.addWidget(self.refresh_button)

        layout.addLayout(toolbar_layout)

        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels([
            "Time", "LEN", "Transcription", "Status"
        ])

        # 表格设置
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)

        # 双击打开详情
        self.history_table.doubleClicked.connect(self._on_row_double_clicked)

        # 列宽设置
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Time - 固定宽度
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Length - 固定宽度
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Transcription - 自动拉伸
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # AI Status - 固定宽度

        # 设置固定列宽
        self.history_table.setColumnWidth(0, 110)  # Time: MM-DD HH:MM 格式
        self.history_table.setColumnWidth(1, 80)   # Length: "0.5s" 格式
        self.history_table.setColumnWidth(3, 100)  # AI Status: 固定100px，内容居中

        layout.addWidget(self.history_table)

        # 底部统计信息
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout(stats_group)

        self.total_records_label = QLabel("Total Records: 0")
        self.total_duration_label = QLabel("Total Duration: 0.0s")
        self.success_rate_label = QLabel("Success Rate: 0%")

        stats_layout.addWidget(self.total_records_label)
        stats_layout.addWidget(self.total_duration_label)
        stats_layout.addWidget(self.success_rate_label)
        stats_layout.addStretch()

        layout.addWidget(stats_group)

        # 保存控件引用
        self.controls = {
            "history_table": self.history_table,
            "search_input": self.search_input,
            "refresh_button": self.refresh_button,
        }

    def _get_history_service(self):
        """获取HistoryStorageService实例

        通过config_manager (UISettingsServiceAdapter) 访问
        """
        if self.history_service is None:
            try:
                # 通过config_manager的get_history_service方法获取
                if hasattr(self.config_manager, 'get_history_service'):
                    self.history_service = self.config_manager.get_history_service()
                    if self.history_service is None:
                        # 记录警告但不抛出异常，让调用者处理
                        from ...utils import app_logger
                        app_logger.warning("HistoryStorageService not available from config_manager")
            except Exception as e:
                from ...utils import app_logger
                app_logger.log_error(e, "Failed to get HistoryStorageService")
                return None

        return self.history_service

    def _load_history(self) -> None:
        """加载历史记录"""
        service = self._get_history_service()
        if not service:
            QMessageBox.warning(
                self.parent_window,
                "Error",
                "History service not available. Please restart the application."
            )
            return

        try:
            # 获取所有记录（最新的在前）
            self.current_records = service.get_records(limit=1000, offset=0)

            # 应用搜索过滤
            search_text = self.search_input.text().strip().lower()
            if search_text:
                self.current_records = [
                    r for r in self.current_records
                    if (r.transcription_text and search_text in r.transcription_text.lower()) or
                       (r.ai_optimized_text and search_text in r.ai_optimized_text.lower()) or
                       (r.final_text and search_text in r.final_text.lower())
                ]

            # 更新表格
            self._update_table()

            # 更新统计信息
            self._update_statistics()

        except Exception as e:
            QMessageBox.critical(
                self.parent_window,
                "Error",
                f"Failed to load history: {str(e)}"
            )

    def _update_table(self) -> None:
        """更新表格显示"""
        self.history_table.setRowCount(0)

        for record in self.current_records:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)

            # Time - 短格式：MM-DD HH:MM
            time_str = record.timestamp.strftime("%m-%d %H:%M")
            time_item = QTableWidgetItem(time_str)
            time_item.setToolTip(record.timestamp.strftime("%Y-%m-%d %H:%M:%S"))  # 完整时间作为tooltip
            self.history_table.setItem(row, 0, time_item)

            # Duration
            duration_str = f"{record.duration:.1f}s"
            self.history_table.setItem(row, 1, QTableWidgetItem(duration_str))

            # Transcription (full text with auto-ellipsis)
            trans_text = record.transcription_text or ""
            trans_item = QTableWidgetItem(trans_text)
            trans_item.setToolTip(trans_text)
            self.history_table.setItem(row, 2, trans_item)

            # AI Status - 居中对齐
            ai_status = self._get_ai_status_display(record)
            ai_item = QTableWidgetItem(ai_status)
            ai_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # 居中对齐
            if record.ai_status == "success":
                ai_item.setForeground(Qt.GlobalColor.darkGreen)
            elif record.ai_status == "failed":
                ai_item.setForeground(Qt.GlobalColor.red)
            elif record.ai_status == "skipped":
                ai_item.setForeground(Qt.GlobalColor.gray)
            self.history_table.setItem(row, 3, ai_item)

    def _on_row_double_clicked(self, index) -> None:
        """双击行打开详情对话框"""
        row = index.row()
        if 0 <= row < len(self.current_records):
            record = self.current_records[row]
            self._show_detail_dialog(record)

    def _show_detail_dialog(self, record) -> None:
        """打开记录详情对话框"""
        service = self._get_history_service()
        if not service:
            QMessageBox.warning(
                self.parent_window,
                "Error",
                "History service not available."
            )
            return

        # 延迟获取服务：如果在初始化时没有获取到，现在从config_manager尝试获取
        transcription_service = self.transcription_service
        ai_processing_controller = self.ai_processing_controller

        if not transcription_service or not ai_processing_controller:
            from ...utils import app_logger
            app_logger.log_audio_event(
                "Attempting lazy service loading in HistoryTab",
                {
                    "has_transcription_service": transcription_service is not None,
                    "has_ai_controller": ai_processing_controller is not None
                }
            )

            # 尝试从config_manager (UISettingsServiceAdapter) 获取服务
            if hasattr(self.config_manager, 'transcription_service') and not transcription_service:
                transcription_service = self.config_manager.transcription_service
                app_logger.log_audio_event(
                    "Got transcription service from config_manager",
                    {"service_type": type(transcription_service).__name__ if transcription_service else "None"}
                )

            if hasattr(self.config_manager, 'ai_processing_controller') and not ai_processing_controller:
                ai_processing_controller = self.config_manager.ai_processing_controller
                app_logger.log_audio_event(
                    "Got AI controller from config_manager",
                    {"controller_type": type(ai_processing_controller).__name__ if ai_processing_controller else "None"}
                )

        dialog = HistoryDetailDialog(
            record=record,
            parent_window=self.parent_window,
            history_service=service,
            transcription_service=transcription_service,
            ai_processing_controller=ai_processing_controller,
            config_service=self.config_manager,
            parent=self.parent_window
        )

        result = dialog.exec()

        # 如果删除了记录或者进行了重处理，刷新列表
        if result == QDialog.DialogCode.Accepted:
            self._load_history()

    def _on_search_changed(self, text: str) -> None:
        """搜索文本变化时触发"""
        # 重新加载并过滤
        self._load_history()

    def _update_statistics(self) -> None:
        """更新统计信息"""
        total_count = len(self.current_records)
        total_duration = sum(r.duration for r in self.current_records)

        # 计算成功率（转录成功且AI成功或跳过）
        success_count = sum(
            1 for r in self.current_records
            if r.transcription_status == "success" and r.ai_status in ["success", "skipped"]
        )
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        self.total_records_label.setText(f"Total Records: {total_count}")
        self.total_duration_label.setText(f"Total Duration: {total_duration:.1f}s")
        self.success_rate_label.setText(f"Success Rate: {success_rate:.1f}%")

    @staticmethod
    def _truncate_text(text: str, max_length: int) -> str:
        """截断文本"""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

    @staticmethod
    def _get_ai_status_display(record) -> str:
        """获取AI状态显示文本"""
        status_map = {
            "success": "Success",
            "failed": "Failed",
            "skipped": "Skipped",
            "pending": "Pending",
        }
        return status_map.get(record.ai_status, "Unknown")

    def load_config(self, config: Dict[str, Any]) -> None:
        """从配置加载UI状态

        历史记录页面不需要从配置加载状态，
        而是在显示时动态加载数据
        """
        # 加载历史记录
        self._load_history()

    def save_config(self) -> Dict[str, Any]:
        """保存UI状态到配置

        历史记录页面不需要保存配置
        """
        return {}
