"""UI构建器 - 单一职责：构建RecordingOverlay的UI界面"""

from typing import Any, Dict, List

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ...utils import app_logger
from ..overlay import CloseButton, StatusIndicator
from .position_manager import PositionManager


class OverlayUIBuilder:
    """RecordingOverlay UI构建器 - 负责创建所有UI组件

    职责：
    1. 创建Material Design背景框架
    2. 创建状态指示器
    3. 创建音频级别条
    4. 创建时间标签和关闭按钮
    5. 应用样式和阴影效果
    """

    def __init__(self):
        """初始化UI构建器"""
        app_logger.log_audio_event("OverlayUIBuilder initialized", {})

    def build_ui(self, parent: QWidget, hide_recording_callback) -> Dict[str, Any]:
        """构建完整的UI并返回组件字典

        Args:
            parent: 父窗口组件
            hide_recording_callback: 关闭按钮的回调函数

        Returns:
            包含所有UI组件的字典
        """
        try:
            # 主布局 - 更紧凑的间距
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(8, 8, 8, 8)
            main_layout.setSpacing(0)

            # 创建Material Design背景框架
            background_frame = self._create_background_frame()

            # 横向布局
            frame_layout = QHBoxLayout(background_frame)
            frame_layout.setContentsMargins(8, 6, 8, 6)
            frame_layout.setSpacing(8)

            # 创建状态指示器
            status_indicator = StatusIndicator(parent)
            frame_layout.addWidget(status_indicator, 0, Qt.AlignmentFlag.AlignCenter)

            # 创建音频级别条
            audio_level_bars = self._create_audio_level_bars(frame_layout)

            # 弹性空间
            frame_layout.addStretch()

            # 创建时间标签
            time_label = self._create_time_label()
            frame_layout.addWidget(time_label)

            # 创建关闭按钮
            close_button = self._create_close_button(parent, hide_recording_callback)
            frame_layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignCenter)

            # 添加到主布局
            main_layout.addWidget(background_frame)

            # 应用阴影效果
            self._apply_shadow_effect(background_frame)

            # 设置父窗口属性
            self._setup_parent_widget(parent, main_layout)

            # 创建位置管理器
            position_manager = PositionManager(parent, config_service=None)

            app_logger.log_audio_event("UI components created successfully", {})

            return {
                "main_layout": main_layout,
                "background_frame": background_frame,
                "status_indicator": status_indicator,
                "audio_level_bars": audio_level_bars,
                "time_label": time_label,
                "close_button": close_button,
                "position_manager": position_manager,
                "current_audio_level": 0.0,  # 初始音频级别
            }

        except Exception as e:
            app_logger.log_error(e, "ui_builder_build")
            raise

    def _create_background_frame(self) -> QFrame:
        """创建Material Design背景框架

        Returns:
            配置好的QFrame背景框架
        """
        background_frame = QFrame()
        background_frame.setObjectName("recordingOverlayFrame")
        background_frame.setStyleSheet("""
            QFrame#recordingOverlayFrame {
                background-color: #303030;
                border-radius: 12px;
            }
        """)
        return background_frame

    def _create_audio_level_bars(self, layout: QHBoxLayout) -> List[QLabel]:
        """创建5个音频级别条

        Args:
            layout: 要添加级别条的布局

        Returns:
            音频级别条的列表
        """
        audio_level_bars = []

        # 创建5个音频级别条 - Material Design风格
        for i in range(5):
            bar = QLabel()
            bar.setFixedSize(4, 18)
            bar.setStyleSheet("""
                QLabel {
                    border-radius: 2px;
                }
            """)
            audio_level_bars.append(bar)
            layout.addWidget(bar)

        return audio_level_bars

    def _create_time_label(self) -> QLabel:
        """创建时间标签

        Returns:
            配置好的时间标签
        """
        time_label = QLabel("00:00")
        time_label.setFont(QFont("Segoe UI", 9))
        time_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                background: transparent;
            }
        """)
        return time_label

    def _create_close_button(self, parent: QWidget, hide_callback) -> CloseButton:
        """创建关闭按钮

        Args:
            parent: 父窗口
            hide_callback: 点击回调函数

        Returns:
            配置好的关闭按钮
        """
        close_button = CloseButton(parent)

        # 实现点击事件
        def close_button_click(event):
            if event.button() == Qt.MouseButton.LeftButton:
                hide_callback()

        close_button.mousePressEvent = close_button_click

        return close_button

    def _apply_shadow_effect(self, frame: QFrame) -> None:
        """应用Material Design阴影效果

        Args:
            frame: 要应用阴影的框架
        """
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 60))  # Material Elevation 8
        frame.setGraphicsEffect(shadow)

    def _setup_parent_widget(self, parent: QWidget, layout: QVBoxLayout) -> None:
        """设置父窗口的属性和样式

        Args:
            parent: 父窗口组件
            layout: 主布局
        """
        # 设置布局
        parent.setLayout(layout)

        # 设置固定大小 - Material Design紧凑横向布局
        parent.setFixedSize(200, 50)

        # 确保悬浮窗本身透明背景
        parent.setStyleSheet("""
            RecordingOverlay {
                background: transparent;
            }
        """)
