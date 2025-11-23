"""批量重新处理对话框

此对话框允许用户配置批量重新处理历史记录的参数：
- CD（冷却）时间：每条记录处理之间的延迟
- 记录数量预览
- 时间估算
"""

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)


class BatchReprocessDialog(QDialog):
    """批量重新处理配置对话框"""

    def __init__(self, total_records: int, parent=None):
        """初始化对话框

        Args:
            total_records: 将要处理的记录总数
            parent: 父窗口
        """
        super().__init__(parent)
        self.total_records = total_records
        self.cd_seconds = 5  # 默认CD时间

        self.setup_ui()
        self.update_estimation()

    def setup_ui(self) -> None:
        """设置UI布局"""
        self.setWindowTitle("Batch Reprocess All Records")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # 信息组
        info_group = QGroupBox("Processing Information")
        info_layout = QFormLayout()

        self.records_label = QLabel(str(self.total_records))
        self.records_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        info_layout.addRow("Total records to process:", self.records_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # CD配置组
        cd_group = QGroupBox("Cooldown Configuration")
        cd_layout = QFormLayout()

        # CD时间输入
        self.cd_spinbox = QSpinBox()
        self.cd_spinbox.setMinimum(0)
        self.cd_spinbox.setMaximum(60)
        self.cd_spinbox.setValue(5)
        self.cd_spinbox.setSuffix(" seconds")
        self.cd_spinbox.setToolTip(
            "Delay between processing each record.\n"
            "Useful for avoiding API rate limits when using cloud transcription."
        )
        self.cd_spinbox.valueChanged.connect(self.update_estimation)

        cd_layout.addRow("Cooldown between records:", self.cd_spinbox)

        # 说明文本
        cd_help = QLabel(
            "⚠ Recommended: 5 seconds for cloud providers to avoid rate limits.\n"
            "💡 For local transcription (sherpa-onnx), 0-1 seconds is sufficient."
        )
        cd_help.setWordWrap(True)
        cd_help.setStyleSheet("color: #666; font-size: 10px;")
        cd_layout.addRow(cd_help)

        cd_group.setLayout(cd_layout)
        layout.addWidget(cd_group)

        # 时间估算组
        estimate_group = QGroupBox("Time Estimation")
        estimate_layout = QFormLayout()

        self.estimate_label = QLabel()
        self.estimate_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        estimate_layout.addRow("Estimated total time:", self.estimate_label)

        estimate_help = QLabel(
            "Based on average transcription time (5s for cloud, 0.2s for local) + CD time."
        )
        estimate_help.setWordWrap(True)
        estimate_help.setStyleSheet("color: #666; font-size: 10px;")
        estimate_layout.addRow(estimate_help)

        estimate_group.setLayout(estimate_layout)
        layout.addWidget(estimate_group)

        # 警告信息
        warning_label = QLabel(
            "⚠ WARNING: This operation will re-transcribe ALL history records.\n"
            "This may take a long time and consume API quota if using cloud providers.\n"
            "The operation can be cancelled at any time."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet(
            "background-color: #FFF3CD; color: #856404; "
            "padding: 10px; border-radius: 5px; font-size: 10px;"
        )
        layout.addWidget(warning_label)

        # 按钮组
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.ok_button = QPushButton("Start Processing")
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "padding: 8px 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("padding: 8px 16px;")

        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def update_estimation(self) -> None:
        """更新时间估算"""
        cd_seconds = self.cd_spinbox.value()

        # 估算平均转录时间（假设使用云端API约5秒，本地sherpa约0.2秒）
        # 这里使用保守估计：5秒
        avg_transcription_time = 5

        total_seconds = self.total_records * (avg_transcription_time + cd_seconds)

        # 转换为人类可读格式
        if total_seconds < 60:
            time_str = f"{total_seconds} seconds"
        elif total_seconds < 3600:
            minutes = total_seconds / 60
            time_str = f"{minutes:.1f} minutes"
        else:
            hours = total_seconds / 3600
            time_str = f"{hours:.1f} hours"

        self.estimate_label.setText(time_str)

    def get_cd_seconds(self) -> int:
        """获取用户配置的CD时间

        Returns:
            int: CD时间（秒）
        """
        return self.cd_spinbox.value()
