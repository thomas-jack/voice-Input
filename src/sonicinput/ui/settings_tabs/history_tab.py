"""历史记录标签页"""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QCoreApplication, Qt, QThread, Signal, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from .base_tab import BaseSettingsTab


class ReprocessingWorker(QThread):
    """重新处理录音的后台工作线程"""

    # 信号定义
    progress_updated = Signal(str)  # 进度更新信号
    reprocessing_completed = Signal(dict)  # 重处理完成信号
    reprocessing_failed = Signal(str)  # 重处理失败信号

    def __init__(
        self,
        record_id: str,
        audio_file_path: str,
        transcription_service,
        ai_processing_controller,
        config_service,
        history_service,
    ):
        super().__init__()
        self.record_id = record_id  # 使用不可变的 ID
        self.audio_file_path = audio_file_path  # 使用不可变的路径
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
            self.progress_updated.emit(
                QCoreApplication.translate("HistoryTab", "Loading audio file...")
            )
            audio_file_path = self.audio_file_path  # 使用创建时捕获的路径

            if not audio_file_path:
                self.reprocessing_failed.emit(
                    QCoreApplication.translate(
                        "HistoryTab", "Audio file path not found in record"
                    )
                )
                return

            try:
                audio_data = AudioRecorder.load_audio_from_file(audio_file_path)
                if audio_data is None or len(audio_data) == 0:
                    self.reprocessing_failed.emit(
                        QCoreApplication.translate(
                            "HistoryTab", "Failed to load audio data from file"
                        )
                    )
                    return
            except FileNotFoundError:
                self.reprocessing_failed.emit(
                    QCoreApplication.translate(
                        "HistoryTab", "Audio file not found: {path}"
                    ).format(path=audio_file_path)
                )
                return
            except Exception as e:
                self.reprocessing_failed.emit(
                    QCoreApplication.translate(
                        "HistoryTab", "Error loading audio file: {error}"
                    ).format(error=str(e))
                )
                return

            if self.should_stop:
                return

            # 2. 重新转录
            self.progress_updated.emit(
                QCoreApplication.translate("HistoryTab", "Transcribing audio...")
            )

            try:
                # 获取当前转录配置
                transcription_provider = self.config_service.get_setting(
                    "transcription.provider", "local"
                )
                if transcription_provider == "local":
                    language = self.config_service.get_setting(
                        "transcription.local.language", "zh"
                    )
                else:
                    language = "auto"

                temperature = 0.0

                # 调用转录服务
                transcription_result = self.transcription_service.transcribe_sync(
                    audio_data=audio_data,
                    language=language if language != "auto" else None,
                    temperature=temperature,
                )

                if not transcription_result.get("success", True):
                    error_msg = transcription_result.get(
                        "error",
                        QCoreApplication.translate(
                            "HistoryTab", "Unknown transcription error"
                        ),
                    )
                    self.reprocessing_failed.emit(
                        QCoreApplication.translate(
                            "HistoryTab", "Transcription failed: {error}"
                        ).format(error=error_msg)
                    )

                    # 更新历史记录为失败状态
                    # 从数据库获取最新的 record 并更新
                    record = self.history_service.get_record_by_id(self.record_id)
                    if record:
                        record.transcription_status = "failed"
                        record.transcription_error = error_msg
                        record.transcription_provider = transcription_provider
                        self.history_service.update_record(record)
                    return

                transcription_text = transcription_result.get("text", "")

                if not transcription_text.strip():
                    self.reprocessing_failed.emit(
                        QCoreApplication.translate(
                            "HistoryTab", "Transcription returned empty text"
                        )
                    )
                    return

            except Exception as e:
                app_logger.log_error(e, "reprocessing_transcription")
                self.reprocessing_failed.emit(
                    QCoreApplication.translate(
                        "HistoryTab", "Transcription error: {error}"
                    ).format(error=str(e))
                )
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
                self.progress_updated.emit(
                    QCoreApplication.translate("HistoryTab", "Optimizing with AI...")
                )

                # 检查AI控制器是否可用
                if not self.ai_processing_controller:
                    ai_status = "skipped"
                    ai_error = QCoreApplication.translate(
                        "HistoryTab", "AI processing controller not available"
                    )
                    ai_optimized_text = ""
                    app_logger.log_audio_event(
                        "Retry processing: AI controller not available, skipping AI optimization",
                        {"ai_enabled": ai_enabled},
                    )
                else:
                    try:
                        # 调用AI处理，显式传递record_id
                        ai_optimized_text = (
                            self.ai_processing_controller.process_with_ai(
                                transcription_text,
                                record_id=self.record_id,  # 使用不可变的 ID
                            )
                        )

                        # 获取AI提供商信息
                        ai_provider = self.config_service.get_setting(
                            "ai.provider", "groq"
                        )

                        if ai_optimized_text and ai_optimized_text.strip():
                            ai_status = "success"
                        else:
                            ai_status = "failed"
                            ai_error = QCoreApplication.translate(
                                "HistoryTab", "AI returned empty text"
                            )

                    except Exception as e:
                        app_logger.log_error(e, "reprocessing_ai_optimization")
                        ai_status = "failed"
                        ai_error = str(e)
                        ai_optimized_text = None

            if self.should_stop:
                return

            # 4. 更新历史记录
            self.progress_updated.emit(
                QCoreApplication.translate("HistoryTab", "Updating history record...")
            )

            # 确定最终文本
            if ai_status == "success" and ai_optimized_text:
                final_text = ai_optimized_text
            else:
                final_text = transcription_text

            # 从数据库获取最新的 record 并更新
            # 这确保我们更新的是正确的记录，避免对象引用问题
            record = self.history_service.get_record_by_id(self.record_id)
            if not record:
                self.reprocessing_failed.emit(
                    QCoreApplication.translate(
                        "HistoryTab", "Record not found: {record_id}"
                    ).format(record_id=self.record_id)
                )
                return

            record.transcription_text = transcription_text
            record.transcription_provider = transcription_provider
            record.transcription_status = "success"
            record.transcription_error = None
            record.ai_optimized_text = ai_optimized_text
            record.ai_provider = ai_provider
            record.ai_status = ai_status
            record.ai_error = ai_error
            record.final_text = final_text

            # 保存到数据库
            try:
                self.history_service.update_record(record)
            except Exception as e:
                app_logger.log_error(e, "reprocessing_update_record")
                self.reprocessing_failed.emit(
                    QCoreApplication.translate(
                        "HistoryTab",
                        "Failed to update history record: {error}",
                    ).format(error=str(e))
                )
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
            self.reprocessing_failed.emit(
                QCoreApplication.translate(
                    "HistoryTab", "Unexpected error: {error}"
                ).format(error=str(e))
            )

    def stop(self):
        """请求停止处理"""
        self.should_stop = True


class BatchReprocessingWorker(QThread):
    """批量重新处理录音的后台工作线程"""

    # 信号定义
    progress_updated = Signal(int, int, str)  # (current, total, record_id)
    batch_completed = Signal(dict)  # 批处理完成信号，包含统计结果
    record_processed = Signal(str, bool)  # (record_id, success) - 单条记录处理完成

    def __init__(
        self,
        total_records: int,
        cd_seconds: int,
        transcription_service,
        ai_processing_controller,
        config_service,
        history_service,
        page_size: int = 500,
    ):
        super().__init__()
        self.total_records = total_records
        self.page_size = page_size
        self.cd_seconds = cd_seconds
        self.transcription_service = transcription_service
        self.ai_processing_controller = ai_processing_controller
        self.config_service = config_service
        self.history_service = history_service
        self.should_stop = False
        self.stats = {"total": 0, "success": 0, "skipped": 0, "failed": 0, "errors": []}

    def run(self):
        """后台线程执行批量重处理流程"""
        import time

        from ...utils import app_logger

        total_records = max(int(self.total_records or 0), 0)
        self.stats["total"] = total_records

        processed = 0
        offset = 0
        page_size = max(int(self.page_size or 0), 1)

        while not self.should_stop and processed < total_records:
            records = self.history_service.get_records(limit=page_size, offset=offset)
            if not records:
                break

            for record in records:
                if self.should_stop or processed >= total_records:
                    break

                processed += 1

                # 发送进度更新
                self.progress_updated.emit(processed, total_records, record.id)

                # 处理单条记录
                success = self._process_single_record(record)

                # 发送单条记录完成信号
                self.record_processed.emit(record.id, success)

                # CD间隔（除了最后一条记录）
                if processed < total_records and self.cd_seconds > 0:
                    time.sleep(self.cd_seconds)

            offset += len(records)

        if self.should_stop:
            app_logger.log_audio_event(
                "Batch reprocessing cancelled by user",
                {"processed": processed, "total": total_records},
            )

        # 发送批处理完成信号
        self.batch_completed.emit(self.stats)

    def _process_single_record(self, record) -> bool:
        """处理单条记录

        Args:
            record: 历史记录对象

        Returns:
            bool: 是否成功
        """
        from ...audio.recorder import AudioRecorder
        from ...utils import app_logger

        try:
            # 1. 加载音频文件
            audio_file_path = record.audio_file_path

            if not audio_file_path:
                self.stats["skipped"] += 1
                self.stats["errors"].append(
                    QCoreApplication.translate(
                        "HistoryTab", "[SKIP] {record_id}: No audio file path"
                    ).format(record_id=record.id)
                )
                return False

            try:
                audio_data = AudioRecorder.load_audio_from_file(audio_file_path)
                if audio_data is None or len(audio_data) == 0:
                    self.stats["skipped"] += 1
                    self.stats["errors"].append(
                        QCoreApplication.translate(
                            "HistoryTab", "[SKIP] {record_id}: Failed to load audio"
                        ).format(record_id=record.id)
                    )
                    return False
            except FileNotFoundError:
                self.stats["skipped"] += 1
                self.stats["errors"].append(
                    QCoreApplication.translate(
                        "HistoryTab", "[SKIP] {record_id}: Audio file not found"
                    ).format(record_id=record.id)
                )
                return False
            except Exception as e:
                self.stats["skipped"] += 1
                self.stats["errors"].append(
                    QCoreApplication.translate(
                        "HistoryTab",
                        "[SKIP] {record_id}: Error loading audio - {error}",
                    ).format(record_id=record.id, error=str(e))
                )
                return False

            # 2. 重新转录
            try:
                transcription_provider = self.config_service.get_setting(
                    "transcription.provider", "local"
                )
                if transcription_provider == "local":
                    language = self.config_service.get_setting(
                        "transcription.local.language", "zh"
                    )
                else:
                    language = "auto"

                temperature = 0.0

                transcription_result = self.transcription_service.transcribe_sync(
                    audio_data=audio_data,
                    language=language if language != "auto" else None,
                    temperature=temperature,
                )

                if not transcription_result.get("success", True):
                    error_msg = transcription_result.get(
                        "error",
                        QCoreApplication.translate("HistoryTab", "Unknown error"),
                    )
                    self.stats["failed"] += 1
                    self.stats["errors"].append(
                        QCoreApplication.translate(
                            "HistoryTab",
                            "[FAIL] {record_id}: Transcription failed - {error}",
                        ).format(record_id=record.id, error=error_msg)
                    )
                    return False

                transcription_text = transcription_result.get("text", "")

                if not transcription_text.strip():
                    self.stats["failed"] += 1
                    self.stats["errors"].append(
                        QCoreApplication.translate(
                            "HistoryTab", "[FAIL] {record_id}: Empty transcription"
                        ).format(record_id=record.id)
                    )
                    return False

            except Exception as e:
                app_logger.log_error(e, "batch_reprocessing_transcription")
                self.stats["failed"] += 1
                self.stats["errors"].append(
                    QCoreApplication.translate(
                        "HistoryTab",
                        "[FAIL] {record_id}: Transcription error - {error}",
                    ).format(record_id=record.id, error=str(e))
                )
                return False

            # 3. 重新AI优化（如果启用）
            ai_enabled = self.config_service.get_setting("ai.enabled", False)
            ai_optimized_text = None
            ai_provider = None
            ai_status = "skipped"
            ai_error = None

            if ai_enabled and transcription_text.strip():
                if not self.ai_processing_controller:
                    ai_status = "skipped"
                    ai_error = QCoreApplication.translate(
                        "HistoryTab", "AI controller not available"
                    )
                else:
                    try:
                        ai_optimized_text = (
                            self.ai_processing_controller.process_with_ai(
                                transcription_text, record_id=record.id
                            )
                        )
                        ai_provider = self.config_service.get_setting(
                            "ai.provider", "groq"
                        )

                        if ai_optimized_text and ai_optimized_text.strip():
                            ai_status = "success"
                        else:
                            ai_status = "failed"
                            ai_error = QCoreApplication.translate(
                                "HistoryTab", "AI returned empty text"
                            )

                    except Exception as e:
                        app_logger.log_error(e, "batch_reprocessing_ai")
                        ai_status = "failed"
                        ai_error = str(e)

            # 4. 更新数据库
            final_text = (
                ai_optimized_text
                if (ai_status == "success" and ai_optimized_text)
                else transcription_text
            )

            # 从数据库重新获取记录以确保最新状态
            fresh_record = self.history_service.get_record_by_id(record.id)
            if not fresh_record:
                self.stats["failed"] += 1
                self.stats["errors"].append(
                    QCoreApplication.translate(
                        "HistoryTab",
                        "[FAIL] {record_id}: Record not found in database",
                    ).format(record_id=record.id)
                )
                return False

            fresh_record.transcription_text = transcription_text
            fresh_record.transcription_provider = transcription_provider
            fresh_record.transcription_status = "success"
            fresh_record.transcription_error = None
            fresh_record.ai_optimized_text = ai_optimized_text
            fresh_record.ai_provider = ai_provider
            fresh_record.ai_status = ai_status
            fresh_record.ai_error = ai_error
            fresh_record.final_text = final_text

            try:
                self.history_service.update_record(fresh_record)
                self.stats["success"] += 1
                return True
            except Exception as e:
                app_logger.log_error(e, "batch_reprocessing_update")
                self.stats["failed"] += 1
                self.stats["errors"].append(
                    QCoreApplication.translate(
                        "HistoryTab",
                        "[FAIL] {record_id}: Database update failed - {error}",
                    ).format(record_id=record.id, error=str(e))
                )
                return False

        except Exception as e:
            from ...utils import app_logger

            app_logger.log_error(e, "batch_reprocessing_worker")
            self.stats["failed"] += 1
            self.stats["errors"].append(
                QCoreApplication.translate(
                    "HistoryTab",
                    "[FAIL] {record_id}: Unexpected error - {error}",
                ).format(record_id=record.id, error=str(e))
            )
            return False

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

        self._event_service = None
        if self.parent_window and hasattr(self.parent_window, "ui_settings_service"):
            from ...core.services.events import Events

            self._event_service = (
                self.parent_window.ui_settings_service.get_event_service()
            )
            if self._event_service:
                self._event_service.on(
                    Events.UI_LANGUAGE_CHANGED, self._on_language_changed
                )

    def setup_ui(self):
        """设置对话框UI"""
        self.setWindowTitle(
            QCoreApplication.translate("HistoryDetailDialog", "Recording Details")
        )
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout(self)

        # 信息区域
        info_layout = QVBoxLayout()

        # 基本信息
        self.basic_info_group = QGroupBox("Basic Information")
        basic_layout = QVBoxLayout(self.basic_info_group)

        self.time_label = QLabel(
            f"<b>Time:</b> {self.record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.duration_label = QLabel(f"<b>Duration:</b> {self.record.duration:.2f}s")
        self.audio_path_label = QLabel(
            f"<b>Audio File:</b> {self.record.audio_file_path or 'N/A'}"
        )
        self.audio_path_label.setWordWrap(True)

        basic_layout.addWidget(self.time_label)
        basic_layout.addWidget(self.duration_label)
        basic_layout.addWidget(self.audio_path_label)
        info_layout.addWidget(self.basic_info_group)

        # 原始转录信息
        transcription_status = self._status_display(self.record.transcription_status)
        self.trans_group = QGroupBox(
            QCoreApplication.translate(
                "HistoryDetailDialog", "Original Transcription ({status})"
            ).format(status=transcription_status)
        )
        trans_layout = QVBoxLayout(self.trans_group)

        self.trans_provider_label = QLabel(
            f"<b>Provider:</b> {self.record.transcription_provider or 'N/A'}"
        )
        trans_layout.addWidget(self.trans_provider_label)

        if self.record.transcription_error:
            self.trans_error_label = QLabel(
                f"<b>Error:</b> {self.record.transcription_error}"
            )
            self.trans_error_label.setStyleSheet("color: red;")
            trans_layout.addWidget(self.trans_error_label)
        else:
            self.trans_error_label = None

        self.trans_text_edit = QTextEdit()
        self.trans_text_edit.setPlainText(
            self.record.transcription_text
            or QCoreApplication.translate("HistoryDetailDialog", "(empty)")
        )
        self.trans_text_edit.setReadOnly(True)
        self.trans_text_edit.setMaximumHeight(150)
        trans_layout.addWidget(self.trans_text_edit)
        info_layout.addWidget(self.trans_group)

        # 优化后文本（根据AI状态显示不同内容）
        if self.record.ai_status:
            ai_status_label = self._status_display(self.record.ai_status)
            ai_status_text = QCoreApplication.translate(
                "HistoryDetailDialog", "AI {status}"
            ).format(status=ai_status_label)
        else:
            ai_status_text = QCoreApplication.translate(
                "HistoryDetailDialog", "AI Status Unknown"
            )
        self.optimized_group = QGroupBox(
            QCoreApplication.translate(
                "HistoryDetailDialog", "Optimized Text ({status})"
            ).format(status=ai_status_text)
        )
        optimized_layout = QVBoxLayout(self.optimized_group)

        # 显示 AI 提供商（如果有）
        if self.record.ai_provider:
            self.ai_provider_label = QLabel(
                f"<b>AI Provider:</b> {self.record.ai_provider}"
            )
            optimized_layout.addWidget(self.ai_provider_label)
        else:
            self.ai_provider_label = None

        # 显示错误（如果有）
        if self.record.ai_error:
            self.ai_error_label = QLabel(f"<b>Error:</b> {self.record.ai_error}")
            self.ai_error_label.setStyleSheet("color: red;")
            optimized_layout.addWidget(self.ai_error_label)
        else:
            self.ai_error_label = None

        self.optimized_text_edit = QTextEdit()
        # 根据 AI 状态显示文本
        if self.record.ai_status == "success" and self.record.ai_optimized_text:
            display_text = self.record.ai_optimized_text
        else:
            # AI 失败或跳过，显示原始文本并注明
            display_text = QCoreApplication.translate(
                "HistoryDetailDialog",
                "{text}\n\n(Using original transcription - AI {status})",
            ).format(text=self.record.transcription_text, status=self.record.ai_status)

        self.optimized_text_edit.setPlainText(
            display_text or QCoreApplication.translate("HistoryDetailDialog", "(empty)")
        )
        self.optimized_text_edit.setReadOnly(True)
        self.optimized_text_edit.setMaximumHeight(150)
        optimized_layout.addWidget(self.optimized_text_edit)
        info_layout.addWidget(self.optimized_group)

        layout.addLayout(info_layout)

        # 操作按钮
        button_layout = QHBoxLayout()

        self.copy_button = QPushButton("Copy to Clipboard")
        self.copy_button.clicked.connect(self._copy_to_clipboard)
        button_layout.addWidget(self.copy_button)

        self.retry_button = QPushButton("Retry")
        self.retry_button.clicked.connect(self._retry_processing)
        button_layout.addWidget(self.retry_button)

        self.delete_button = QPushButton("Delete Record")
        self.delete_button.clicked.connect(self._delete_record)
        self.delete_button.setStyleSheet("background-color: #d32f2f; color: white;")
        button_layout.addWidget(self.delete_button)

        button_layout.addStretch()

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)
        self.retranslate_ui()

    def _status_display(self, status: Optional[str]) -> str:
        """Return localized status label."""
        status_map = {
            "success": QCoreApplication.translate("HistoryDetailDialog", "Success"),
            "failed": QCoreApplication.translate("HistoryDetailDialog", "Failed"),
            "skipped": QCoreApplication.translate("HistoryDetailDialog", "Skipped"),
            "pending": QCoreApplication.translate("HistoryDetailDialog", "Pending"),
        }
        return status_map.get(
            status, QCoreApplication.translate("HistoryDetailDialog", "Unknown")
        )

    def _on_language_changed(self, data: object = None) -> None:
        """Handle runtime UI language change."""
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Update dialog text for the current language."""
        self.setWindowTitle(
            QCoreApplication.translate("HistoryDetailDialog", "Recording Details")
        )
        self.basic_info_group.setTitle(
            QCoreApplication.translate("HistoryDetailDialog", "Basic Information")
        )

        timestamp_text = self.record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(
            QCoreApplication.translate(
                "HistoryDetailDialog", "<b>Time:</b> {time}"
            ).format(time=timestamp_text)
        )
        self.duration_label.setText(
            QCoreApplication.translate(
                "HistoryDetailDialog", "<b>Duration:</b> {duration:.2f}s"
            ).format(duration=self.record.duration)
        )
        audio_path = self.record.audio_file_path or QCoreApplication.translate(
            "HistoryDetailDialog", "N/A"
        )
        self.audio_path_label.setText(
            QCoreApplication.translate(
                "HistoryDetailDialog", "<b>Audio File:</b> {path}"
            ).format(path=audio_path)
        )

        transcription_status = self._status_display(self.record.transcription_status)
        self.trans_group.setTitle(
            QCoreApplication.translate(
                "HistoryDetailDialog", "Original Transcription ({status})"
            ).format(status=transcription_status)
        )
        self.trans_provider_label.setText(
            QCoreApplication.translate(
                "HistoryDetailDialog", "<b>Provider:</b> {provider}"
            ).format(
                provider=self.record.transcription_provider
                or QCoreApplication.translate("HistoryDetailDialog", "N/A")
            )
        )
        if self.trans_error_label:
            self.trans_error_label.setText(
                QCoreApplication.translate(
                    "HistoryDetailDialog", "<b>Error:</b> {error}"
                ).format(error=self.record.transcription_error)
            )

        transcription_text = self.record.transcription_text or ""
        self.trans_text_edit.setPlainText(
            transcription_text
            or QCoreApplication.translate("HistoryDetailDialog", "(empty)")
        )

        if self.record.ai_status:
            ai_status_label = self._status_display(self.record.ai_status)
            ai_status_text = QCoreApplication.translate(
                "HistoryDetailDialog", "AI {status}"
            ).format(status=ai_status_label)
        else:
            ai_status_text = QCoreApplication.translate(
                "HistoryDetailDialog", "AI Status Unknown"
            )

        self.optimized_group.setTitle(
            QCoreApplication.translate(
                "HistoryDetailDialog", "Optimized Text ({status})"
            ).format(status=ai_status_text)
        )

        if self.ai_provider_label:
            self.ai_provider_label.setText(
                QCoreApplication.translate(
                    "HistoryDetailDialog", "<b>AI Provider:</b> {provider}"
                ).format(provider=self.record.ai_provider)
            )
        if self.ai_error_label:
            self.ai_error_label.setText(
                QCoreApplication.translate(
                    "HistoryDetailDialog", "<b>Error:</b> {error}"
                ).format(error=self.record.ai_error)
            )

        if self.record.ai_status == "success" and self.record.ai_optimized_text:
            display_text = self.record.ai_optimized_text
        else:
            display_text = QCoreApplication.translate(
                "HistoryDetailDialog",
                "{text}\n\n(Using original transcription - AI {status})",
            ).format(
                text=self.record.transcription_text or "",
                status=self.record.ai_status
                or QCoreApplication.translate("HistoryDetailDialog", "Unknown"),
            )

        self.optimized_text_edit.setPlainText(
            display_text or QCoreApplication.translate("HistoryDetailDialog", "(empty)")
        )

        self.copy_button.setText(
            QCoreApplication.translate("HistoryDetailDialog", "Copy to Clipboard")
        )
        self.retry_button.setText(
            QCoreApplication.translate("HistoryDetailDialog", "Retry")
        )
        self.delete_button.setText(
            QCoreApplication.translate("HistoryDetailDialog", "Delete Record")
        )
        self.close_button.setText(
            QCoreApplication.translate("HistoryDetailDialog", "Close")
        )

    def _copy_to_clipboard(self):
        """复制优化后的文本到剪贴板"""
        from PySide6.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        # 复制优化后的文本（如果 AI 成功则是AI文本，否则是转录文本）
        text_to_copy = self.optimized_text_edit.toPlainText()
        clipboard.setText(text_to_copy)
        QMessageBox.information(
            self,
            QCoreApplication.translate("HistoryDetailDialog", "Success"),
            QCoreApplication.translate(
                "HistoryDetailDialog", "Text copied to clipboard!"
            ),
        )

    def _retry_processing(self):
        """重新处理录音（使用当前配置）"""
        from ...utils import app_logger

        app_logger.log_audio_event(
            "Retry processing requested",
            {
                "has_transcription_service": self.transcription_service is not None,
                "has_config_service": self.config_service is not None,
                "has_ai_controller": self.ai_processing_controller is not None,
                "transcription_service_type": type(self.transcription_service).__name__
                if self.transcription_service
                else "None",
            },
        )

        # 检查是否有必要的服务
        if not self.transcription_service or not self.config_service:
            QMessageBox.warning(
                self,
                QCoreApplication.translate(
                    "HistoryDetailDialog", "Service Unavailable"
                ),
                QCoreApplication.translate(
                    "HistoryDetailDialog",
                    "Retry processing requires transcription service.\n\n"
                    "This feature may not be available in this context.",
                ),
            )
            return

        # 确认对话框
        reply = QMessageBox.question(
            self,
            QCoreApplication.translate("HistoryDetailDialog", "Retry Processing"),
            QCoreApplication.translate(
                "HistoryDetailDialog",
                "This will reprocess the recording using current configuration.\n\n"
                "- Transcription will use current provider/model\n"
                "- AI optimization will use current settings\n\n"
                "The original record will be updated with new results.\n\n"
                "Continue?",
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # 创建进度对话框
        self.progress_dialog = QProgressDialog(
            QCoreApplication.translate(
                "HistoryDetailDialog", "Initializing reprocessing..."
            ),
            QCoreApplication.translate("HistoryDetailDialog", "Cancel"),
            0,
            0,  # 不确定进度的模式
            self,
        )
        self.progress_dialog.setWindowTitle(
            QCoreApplication.translate("HistoryDetailDialog", "Reprocessing Recording")
        )
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()

        # 创建并启动后台工作线程
        # 传递不可变数据而不是对象引用，避免并发问题
        self.reprocessing_worker = ReprocessingWorker(
            record_id=self.record.id,
            audio_file_path=self.record.audio_file_path,
            transcription_service=self.transcription_service,
            ai_processing_controller=self.ai_processing_controller,
            config_service=self.config_service,
            history_service=self.history_service,
        )

        # 连接信号
        self.reprocessing_worker.progress_updated.connect(self._on_progress_updated)
        self.reprocessing_worker.reprocessing_completed.connect(
            self._on_reprocessing_completed
        )
        self.reprocessing_worker.reprocessing_failed.connect(
            self._on_reprocessing_failed
        )
        self.progress_dialog.canceled.connect(self._on_reprocessing_canceled)

        # 启动工作线程
        self.reprocessing_worker.start()

    def _on_progress_updated(self, message: str):
        """更新进度对话框"""
        if self.progress_dialog:
            self.progress_dialog.setLabelText(message)

    def _on_reprocessing_completed(self, result: dict):
        """重处理完成"""
        from ...utils import app_logger

        # 防御性检查：确保对话框仍然有效
        if not self.isVisible():
            app_logger.log_audio_event(
                "Reprocessing completed but dialog no longer visible",
                {"result": result},
            )
            return

        try:
            # 关闭进度对话框 (先断开信号避免触发canceled)
            if self.progress_dialog:
                try:
                    self.progress_dialog.canceled.disconnect(
                        self._on_reprocessing_canceled
                    )
                except RuntimeError:
                    # 信号可能已经断开
                    pass
                self.progress_dialog.close()
                self.progress_dialog = None

            # 更新UI显示
            transcription_text = result.get("transcription_text", "")
            ai_optimized_text = result.get("ai_optimized_text", "")
            final_text = result.get("final_text", "")
            ai_status = result.get("ai_status", "skipped")

            # 更新转录文本框
            self.trans_text_edit.setPlainText(
                transcription_text
                or QCoreApplication.translate("HistoryDetailDialog", "(empty)")
            )

            # 更新优化后的文本框
            if ai_status == "success" and ai_optimized_text:
                display_text = ai_optimized_text
            else:
                display_text = QCoreApplication.translate(
                    "HistoryDetailDialog",
                    "{text}\n\n(Using original transcription - AI {status})",
                ).format(text=transcription_text, status=ai_status)

            self.optimized_text_edit.setPlainText(
                display_text
                or QCoreApplication.translate("HistoryDetailDialog", "(empty)")
            )

            # 清理worker (安全清理，等待线程结束)
            if self.reprocessing_worker:
                if self.reprocessing_worker.isRunning():
                    self.reprocessing_worker.wait(1000)
                self.reprocessing_worker = None

            self.record.transcription_text = transcription_text
            self.record.ai_optimized_text = ai_optimized_text
            self.record.final_text = final_text
            self.record.ai_status = ai_status
            self.record.transcription_provider = result.get(
                "transcription_provider", self.record.transcription_provider
            )

            # 显示成功消息
            QMessageBox.information(
                self,
                QCoreApplication.translate(
                    "HistoryDetailDialog", "Reprocessing Complete"
                ),
                QCoreApplication.translate(
                    "HistoryDetailDialog",
                    "Recording has been successfully reprocessed!\n\n"
                    "Transcription Provider: {provider}\n"
                    "AI Status: {status}\n\n"
                    "The record has been updated in the history.",
                ).format(
                    provider=result.get(
                        "transcription_provider",
                        QCoreApplication.translate("HistoryDetailDialog", "N/A"),
                    ),
                    status=ai_status,
                ),
            )
        except Exception as e:
            app_logger.log_error(e, "reprocessing_completed_handler")

    def _on_reprocessing_failed(self, error_message: str):
        """重处理失败"""
        from ...utils import app_logger

        # 防御性检查：确保对话框仍然有效
        if not self.isVisible():
            app_logger.log_audio_event(
                "Reprocessing failed but dialog no longer visible",
                {"error": error_message},
            )
            return

        try:
            # 关闭进度对话框 (先断开信号避免触发canceled)
            if self.progress_dialog:
                try:
                    self.progress_dialog.canceled.disconnect(
                        self._on_reprocessing_canceled
                    )
                except RuntimeError:
                    pass
                self.progress_dialog.close()
                self.progress_dialog = None

            # 清理worker (安全清理)
            if self.reprocessing_worker:
                if self.reprocessing_worker.isRunning():
                    self.reprocessing_worker.wait(1000)
                self.reprocessing_worker = None

            # 显示错误消息
            QMessageBox.critical(
                self,
                QCoreApplication.translate(
                    "HistoryDetailDialog", "Reprocessing Failed"
                ),
                QCoreApplication.translate(
                    "HistoryDetailDialog",
                    "Failed to reprocess the recording:\n\n{error}\n\n"
                    "Please check the logs for more details.",
                ).format(error=error_message),
            )
        except Exception as e:
            app_logger.log_error(e, "reprocessing_failed_handler")

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
            QCoreApplication.translate("HistoryDetailDialog", "Reprocessing Canceled"),
            QCoreApplication.translate(
                "HistoryDetailDialog", "Reprocessing operation has been canceled."
            ),
        )

    def _delete_record(self):
        """删除记录"""
        reply = QMessageBox.question(
            self,
            QCoreApplication.translate("HistoryDetailDialog", "Delete Record"),
            QCoreApplication.translate(
                "HistoryDetailDialog",
                "Are you sure you want to delete this record?\n\nTime: {time}",
            ).format(time=self.record.timestamp.strftime("%Y-%m-%d %H:%M:%S")),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                success = self.history_service.delete_record(self.record.id)
                if success:
                    QMessageBox.information(
                        self,
                        QCoreApplication.translate("HistoryDetailDialog", "Success"),
                        QCoreApplication.translate(
                            "HistoryDetailDialog", "Record deleted successfully!"
                        ),
                    )
                    self.accept()  # 关闭对话框
                else:
                    QMessageBox.warning(
                        self,
                        QCoreApplication.translate("HistoryDetailDialog", "Warning"),
                        QCoreApplication.translate(
                            "HistoryDetailDialog", "Failed to delete record."
                        ),
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    QCoreApplication.translate("HistoryDetailDialog", "Error"),
                    QCoreApplication.translate(
                        "HistoryDetailDialog", "Error deleting record: {error}"
                    ).format(error=str(e)),
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
        self.batch_worker = None  # 批量处理Worker
        self.batch_progress_dialog = None  # 批量处理进度对话框
        self._search_debounce_timer: Optional[QTimer] = None

        # History pagination (keeps UI responsive for large history)
        self._page_size = 200
        self._page_offset = 0
        self._has_more_pages = True
        self._is_loading_page = False
        self._active_query = ""

        from ...utils import app_logger

        app_logger.log_audio_event(
            "HistoryTab initialized with services",
            {
                "has_transcription_service": self.transcription_service is not None,
                "has_ai_processing_controller": self.ai_processing_controller
                is not None,
                "transcription_service_type": type(self.transcription_service).__name__
                if self.transcription_service
                else "None",
                "ai_controller_type": type(self.ai_processing_controller).__name__
                if self.ai_processing_controller
                else "None",
            },
        )

    def _setup_ui(self) -> None:
        """设置UI"""
        layout = QVBoxLayout(self.widget)

        # 顶部工具栏
        toolbar_layout = QHBoxLayout()

        # 搜索框
        self.search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in transcription or AI text...")
        self.search_input.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(self.search_label)
        toolbar_layout.addWidget(self.search_input, stretch=1)

        # 刷新按钮
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._load_history)
        toolbar_layout.addWidget(self.refresh_button)

        # 批量重新处理按钮
        self.batch_reprocess_button = QPushButton("Batch Reprocess")
        self.batch_reprocess_button.clicked.connect(self._on_batch_reprocess_clicked)
        self.batch_reprocess_button.setToolTip(
            "Re-transcribe all history records with customizable cooldown delay"
        )
        toolbar_layout.addWidget(self.batch_reprocess_button)

        layout.addLayout(toolbar_layout)

        # 历史记录表格
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(
            ["Time", "LEN", "Transcription", "Status"]
        )

        # 表格设置
        self.history_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.history_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)

        # 双击打开详情
        self.history_table.doubleClicked.connect(self._on_row_double_clicked)
        self.history_table.verticalScrollBar().valueChanged.connect(
            self._on_history_table_scrolled
        )

        # 列宽设置
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Time - 固定宽度
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )  # Length - 固定宽度
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )  # Transcription - 自动拉伸
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )  # AI Status - 固定宽度

        # 设置固定列宽
        self.history_table.setColumnWidth(0, 110)  # Time: MM-DD HH:MM 格式
        self.history_table.setColumnWidth(1, 80)  # Length: "0.5s" 格式
        self.history_table.setColumnWidth(3, 100)  # AI Status: 固定100px，内容居中

        layout.addWidget(self.history_table)

        # 底部统计信息
        stats_group = QGroupBox("Statistics")
        stats_layout = QHBoxLayout(stats_group)
        self.stats_group = stats_group

        self.total_records_label = QLabel("Total Records: 0")
        self.total_duration_label = QLabel("Total Duration: 0.0s")
        self.success_rate_label = QLabel("Success Rate: 0%")

        stats_layout.addWidget(self.total_records_label)
        stats_layout.addWidget(self.total_duration_label)
        stats_layout.addWidget(self.success_rate_label)
        stats_layout.addStretch()

        layout.addWidget(stats_group)

        # Debounce search to avoid querying on every keypress
        self._search_debounce_timer = QTimer(self.widget)
        self._search_debounce_timer.setSingleShot(True)
        self._search_debounce_timer.setInterval(250)
        self._search_debounce_timer.timeout.connect(self._load_history)
        self.retranslate_ui()

        # 保存控件引用
        self.controls = {
            "history_table": self.history_table,
            "search_input": self.search_input,
            "refresh_button": self.refresh_button,
        }

    def retranslate_ui(self) -> None:
        """Update UI text for the current language."""
        self.search_label.setText(QCoreApplication.translate("HistoryTab", "Search:"))
        self.search_input.setPlaceholderText(
            QCoreApplication.translate(
                "HistoryTab", "Search in transcription or AI text..."
            )
        )
        self.refresh_button.setText(QCoreApplication.translate("HistoryTab", "Refresh"))
        self.batch_reprocess_button.setText(
            QCoreApplication.translate("HistoryTab", "Batch Reprocess")
        )
        self.batch_reprocess_button.setToolTip(
            QCoreApplication.translate(
                "HistoryTab",
                "Re-transcribe all history records with customizable cooldown delay",
            )
        )
        self.history_table.setHorizontalHeaderLabels(
            [
                QCoreApplication.translate("HistoryTab", "Time"),
                QCoreApplication.translate("HistoryTab", "LEN"),
                QCoreApplication.translate("HistoryTab", "Transcription"),
                QCoreApplication.translate("HistoryTab", "Status"),
            ]
        )
        self.stats_group.setTitle(
            QCoreApplication.translate("HistoryTab", "Statistics")
        )
        self._update_statistics()

    def _get_history_service(self):
        """获取HistoryStorageService实例

        通过config_manager (UISettingsServiceAdapter) 访问
        """
        if self.history_service is None:
            try:
                # 通过config_manager的get_history_service方法获取
                if hasattr(self.config_manager, "get_history_service"):
                    self.history_service = self.config_manager.get_history_service()
                    if self.history_service is None:
                        # 记录警告但不抛出异常，让调用者处理
                        from ...utils import app_logger

                        app_logger.warning(
                            "HistoryStorageService not available from config_manager"
                        )
            except Exception as e:
                from ...utils import app_logger

                app_logger.log_error(e, "Failed to get HistoryStorageService")
                return None

        return self.history_service

    def _load_history(self) -> None:
        """加载历史记录（分页，支持无限滚动）"""
        service = self._get_history_service()
        if not service:
            QMessageBox.warning(
                self.parent_window,
                QCoreApplication.translate("HistoryTab", "Error"),
                QCoreApplication.translate(
                    "HistoryTab",
                    "History service not available. Please restart the application.",
                ),
            )
            return

        try:
            self._reset_pagination()

            # Load first page
            self._load_next_page()

            # 更新统计信息（基于数据库全量数据）
            self._update_statistics()

        except Exception as e:
            QMessageBox.critical(
                self.parent_window,
                QCoreApplication.translate("HistoryTab", "Error"),
                QCoreApplication.translate(
                    "HistoryTab", "Failed to load history: {error}"
                ).format(error=str(e)),
            )

    def _reset_pagination(self) -> None:
        """重置分页状态并清空表格"""
        self._page_offset = 0
        self._has_more_pages = True
        self._is_loading_page = False
        self._active_query = self.search_input.text().strip()

        self.current_records = []
        self.history_table.setRowCount(0)
        self.history_table.scrollToTop()

    def _load_next_page(self) -> None:
        """加载下一页并追加到表格"""
        if self._is_loading_page or not self._has_more_pages:
            return

        service = self._get_history_service()
        if not service:
            return

        self._is_loading_page = True
        try:
            query = self._active_query
            if query:
                page_records = service.search_records(
                    query=query, limit=self._page_size, offset=self._page_offset
                )
            else:
                page_records = service.get_records(
                    limit=self._page_size, offset=self._page_offset
                )

            if not page_records:
                self._has_more_pages = False
                return

            self.current_records.extend(page_records)
            self._append_rows(page_records)

            self._page_offset += len(page_records)
            self._has_more_pages = len(page_records) >= self._page_size

        finally:
            self._is_loading_page = False

        # If the view isn't scrollable yet, auto-fetch more pages (until it is or no more data)
        QTimer.singleShot(0, self._ensure_table_scrollable)

    def _ensure_table_scrollable(self) -> None:
        if self._is_loading_page or not self._has_more_pages:
            return

        if self.history_table.verticalScrollBar().maximum() == 0:
            self._load_next_page()

    def _on_history_table_scrolled(self, value: int) -> None:
        """滚动接近底部时自动加载更多"""
        if self._is_loading_page or not self._has_more_pages:
            return

        scrollbar = self.history_table.verticalScrollBar()
        if value >= scrollbar.maximum() - 50:
            self._load_next_page()

    def _append_rows(self, records: List[Any]) -> None:
        """向表格追加多行"""
        if not records:
            return

        start_row = self.history_table.rowCount()
        self.history_table.setUpdatesEnabled(False)
        try:
            self.history_table.setRowCount(start_row + len(records))

            for row_offset, record in enumerate(records):
                row = start_row + row_offset

                # Time - 短格式：MM-DD HH:MM
                time_str = record.timestamp.strftime("%m-%d %H:%M")
                time_item = QTableWidgetItem(time_str)
                time_item.setToolTip(
                    record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                )  # 完整时间作为tooltip
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
        finally:
            self.history_table.setUpdatesEnabled(True)

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
                QCoreApplication.translate("HistoryTab", "Error"),
                QCoreApplication.translate(
                    "HistoryTab", "History service not available."
                ),
            )
            return

        from ...utils import app_logger

        # 总是从 config_manager 获取最新的服务引用
        # 这确保热重载后使用的是最新的服务实例
        transcription_service = None
        ai_processing_controller = None

        # 尝试从 config_manager (UISettingsServiceAdapter) 获取最新服务
        if hasattr(self.config_manager, "get_transcription_service"):
            transcription_service = self.config_manager.get_transcription_service()
        elif hasattr(self.config_manager, "transcription_service"):
            transcription_service = self.config_manager.transcription_service

        if hasattr(self.config_manager, "ai_processing_controller"):
            ai_processing_controller = self.config_manager.ai_processing_controller

        # 如果从 config_manager 获取失败，回退到初始化时保存的引用
        if not transcription_service:
            transcription_service = self.transcription_service
        if not ai_processing_controller:
            ai_processing_controller = self.ai_processing_controller

        app_logger.log_audio_event(
            "HistoryTab preparing dialog with services",
            {
                "transcription_service_type": type(transcription_service).__name__
                if transcription_service
                else "None",
                "ai_controller_type": type(ai_processing_controller).__name__
                if ai_processing_controller
                else "None",
            },
        )

        dialog = HistoryDetailDialog(
            record=record,
            parent_window=self.parent_window,
            history_service=service,
            transcription_service=transcription_service,
            ai_processing_controller=ai_processing_controller,
            config_service=self.config_manager,
            parent=self.parent_window,
        )

        result = dialog.exec()

        # 如果删除了记录或者进行了重处理，刷新列表
        if result == QDialog.DialogCode.Accepted:
            self._load_history()

    def _on_search_changed(self, text: str) -> None:
        """搜索文本变化时触发"""
        if self._search_debounce_timer is None:
            self._load_history()
            return

        # 重新加载（分页 + DB查询）
        self._search_debounce_timer.start()

    def _update_statistics(self) -> None:
        """更新统计信息"""
        service = self._get_history_service()
        if not service:
            self.total_records_label.setText(
                QCoreApplication.translate(
                    "HistoryTab", "Total Records: {count}"
                ).format(count=0)
            )
            self.total_duration_label.setText(
                QCoreApplication.translate(
                    "HistoryTab", "Total Duration: {seconds:.1f}s"
                ).format(seconds=0.0)
            )
            self.success_rate_label.setText(
                QCoreApplication.translate(
                    "HistoryTab", "Success Rate: {rate:.1f}%"
                ).format(rate=0.0)
            )
            return

        query = self._active_query or self.search_input.text().strip()
        query = query if query else None

        total_count, total_duration, success_count = service.get_aggregate_stats(
            query=query
        )
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0

        self.total_records_label.setText(
            QCoreApplication.translate("HistoryTab", "Total Records: {count}").format(
                count=total_count
            )
        )
        self.total_duration_label.setText(
            QCoreApplication.translate(
                "HistoryTab", "Total Duration: {seconds:.1f}s"
            ).format(seconds=total_duration)
        )
        self.success_rate_label.setText(
            QCoreApplication.translate(
                "HistoryTab", "Success Rate: {rate:.1f}%"
            ).format(rate=success_rate)
        )

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
            "success": QCoreApplication.translate("HistoryTab", "Success"),
            "failed": QCoreApplication.translate("HistoryTab", "Failed"),
            "skipped": QCoreApplication.translate("HistoryTab", "Skipped"),
            "pending": QCoreApplication.translate("HistoryTab", "Pending"),
        }
        return status_map.get(
            record.ai_status, QCoreApplication.translate("HistoryTab", "Unknown")
        )

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

    def _on_batch_reprocess_clicked(self) -> None:
        """处理批量重新处理按钮点击"""
        from ..dialogs.batch_reprocess_dialog import BatchReprocessDialog

        # 获取所有历史记录
        service = self._get_history_service()
        if not service:
            QMessageBox.warning(
                self.parent_window,
                QCoreApplication.translate("HistoryTab", "Error"),
                QCoreApplication.translate(
                    "HistoryTab",
                    "History service not available. Please restart the application.",
                ),
            )
            return

        try:
            total_records = service.get_total_count()
            if total_records <= 0:
                QMessageBox.information(
                    self.parent_window,
                    QCoreApplication.translate("HistoryTab", "No Records"),
                    QCoreApplication.translate(
                        "HistoryTab", "No history records found to reprocess."
                    ),
                )
                return

            # 显示配置对话框
            dialog = BatchReprocessDialog(total_records, self.parent_window)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            cd_seconds = dialog.get_cd_seconds()

            # 确认操作
            reply = QMessageBox.question(
                self.parent_window,
                QCoreApplication.translate("HistoryTab", "Confirm Batch Reprocessing"),
                QCoreApplication.translate(
                    "HistoryTab",
                    "You are about to re-transcribe {total} records.\n\n"
                    "Cooldown: {cooldown} seconds between records\n"
                    "This operation may take a long time and consume API quota.\n\n"
                    "Are you sure you want to continue?",
                ).format(total=total_records, cooldown=cd_seconds),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # 启动批量处理
            self._start_batch_reprocessing(total_records, cd_seconds)

        except Exception as e:
            QMessageBox.critical(
                self.parent_window,
                QCoreApplication.translate("HistoryTab", "Error"),
                QCoreApplication.translate(
                    "HistoryTab", "Failed to start batch reprocessing: {error}"
                ).format(error=str(e)),
            )

    def _start_batch_reprocessing(self, total_records: int, cd_seconds: int) -> None:
        """启动批量重新处理流程

        Args:
            total_records: 要处理的记录总数
            cd_seconds: CD时间（秒）
        """
        # 获取必要的服务
        transcription_service = self.transcription_service
        ai_processing_controller = self.ai_processing_controller
        history_service = self._get_history_service()

        if not transcription_service or not history_service:
            QMessageBox.critical(
                self.parent_window,
                QCoreApplication.translate("HistoryTab", "Error"),
                QCoreApplication.translate(
                    "HistoryTab",
                    "Required services not available. Please restart the application.",
                ),
            )
            return

        # 创建进度对话框
        self.batch_progress_dialog = QProgressDialog(
            QCoreApplication.translate("HistoryTab", "Starting batch reprocessing..."),
            QCoreApplication.translate("HistoryTab", "Cancel"),
            0,
            total_records,
            self.parent_window,
        )
        self.batch_progress_dialog.setWindowTitle(
            QCoreApplication.translate("HistoryTab", "Batch Reprocessing")
        )
        self.batch_progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.batch_progress_dialog.setMinimumDuration(0)
        self.batch_progress_dialog.setValue(0)

        # 创建Worker线程
        self.batch_worker = BatchReprocessingWorker(
            total_records=total_records,
            cd_seconds=cd_seconds,
            transcription_service=transcription_service,
            ai_processing_controller=ai_processing_controller,
            config_service=self.config_manager,
            history_service=history_service,
        )

        # 连接信号
        self.batch_worker.progress_updated.connect(self._on_batch_progress_updated)
        self.batch_worker.batch_completed.connect(self._on_batch_completed)
        self.batch_progress_dialog.canceled.connect(self._on_batch_canceled)

        # 启动Worker
        self.batch_worker.start()

    def _on_batch_progress_updated(
        self, current: int, total: int, record_id: str
    ) -> None:
        """批量处理进度更新

        Args:
            current: 当前处理的索引（1-based）
            total: 总记录数
            record_id: 当前记录ID
        """
        if self.batch_progress_dialog:
            self.batch_progress_dialog.setValue(current)
            self.batch_progress_dialog.setLabelText(
                QCoreApplication.translate(
                    "HistoryTab",
                    "Processing {current}/{total} records...\n"
                    "Current record: {record_id}...",
                ).format(current=current, total=total, record_id=record_id[:16])
            )

    def _on_batch_completed(self, stats: dict) -> None:
        """批量处理完成

        Args:
            stats: 统计结果字典
        """
        # 关闭进度对话框
        if self.batch_progress_dialog:
            self.batch_progress_dialog.close()
            self.batch_progress_dialog = None

        # 清理Worker
        if self.batch_worker:
            self.batch_worker.wait()
            self.batch_worker = None

        # 刷新历史记录列表
        self._load_history()

        # 显示完成报告
        total = stats.get("total", 0)
        success = stats.get("success", 0)
        skipped = stats.get("skipped", 0)
        failed = stats.get("failed", 0)
        errors = stats.get("errors", [])

        # 构建报告消息
        report_lines = [
            QCoreApplication.translate("HistoryTab", "Batch Reprocessing Complete!"),
            "",
            QCoreApplication.translate("HistoryTab", "Total records: {total}").format(
                total=total
            ),
            QCoreApplication.translate("HistoryTab", "Successful: {success}").format(
                success=success
            ),
            QCoreApplication.translate("HistoryTab", "Skipped: {skipped}").format(
                skipped=skipped
            ),
            QCoreApplication.translate("HistoryTab", "Failed: {failed}").format(
                failed=failed
            ),
        ]

        if errors:
            report_lines.append("")
            report_lines.append(
                QCoreApplication.translate(
                    "HistoryTab", "First {count} errors:"
                ).format(count=min(5, len(errors)))
            )
            report_lines.extend([f"  {error}" for error in errors[:5]])
            if len(errors) > 5:
                report_lines.append(
                    QCoreApplication.translate(
                        "HistoryTab", "... and {count} more errors"
                    ).format(count=len(errors) - 5)
                )

        QMessageBox.information(
            self.parent_window,
            QCoreApplication.translate("HistoryTab", "Batch Reprocessing Complete"),
            "\n".join(report_lines),
        )

    def _on_batch_canceled(self) -> None:
        """用户取消批量处理"""
        if self.batch_worker:
            self.batch_worker.stop()
            self.batch_worker.wait(5000)  # 等待最多5秒

            # 强制终止（如果还在运行）
            if self.batch_worker.isRunning():
                self.batch_worker.terminate()
                self.batch_worker.wait()

            self.batch_worker = None

        QMessageBox.information(
            self.parent_window,
            QCoreApplication.translate("HistoryTab", "Batch Reprocessing Canceled"),
            QCoreApplication.translate(
                "HistoryTab", "Batch reprocessing operation has been canceled."
            ),
        )
