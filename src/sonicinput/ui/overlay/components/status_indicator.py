"""Status indicator component for recording overlay"""

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor
from PySide6.QtCore import Qt


class StatusIndicator(QWidget):
    """真正的圆形红点状态指示器，带圆角矩形背景框（支持6种状态）"""

    # 状态常量
    STATE_IDLE = 0  # 待机（暗红色）
    STATE_RECORDING = 1  # 录音中（鲜红色）
    STATE_PROCESSING = 2  # AI处理中（黄色）
    STATE_COMPLETED = 3  # 完成（绿色）
    STATE_WARNING = 4  # 警告（橙色 - AI失败但流程继续）
    STATE_ERROR = 5  # 错误（深红色 - 致命错误）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.state = self.STATE_IDLE

    @property
    def is_recording(self) -> bool:
        """从状态派生的只读属性"""
        return self.state == self.STATE_RECORDING

    def set_state(self, state: int):
        """设置状态（唯一的状态设置方法）"""
        self.state = state
        self.update()

    def paintEvent(self, event):
        """自定义绘制圆形状态点"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 根据状态选择圆点颜色 - Material Design 配色
        if self.state == self.STATE_RECORDING:
            # 录音中：Material Red 500
            dot_color = QColor(244, 67, 54, 255)  # #F44336
        elif self.state == self.STATE_PROCESSING:
            # AI处理中：Material Amber 500
            dot_color = QColor(255, 193, 7, 255)  # #FFC107
        elif self.state == self.STATE_COMPLETED:
            # 完成：Material Green 500
            dot_color = QColor(76, 175, 80, 255)  # #4CAF50
        elif self.state == self.STATE_WARNING:
            # 警告：Material Orange 500
            dot_color = QColor(255, 152, 0, 255)  # #FF9800
        elif self.state == self.STATE_ERROR:
            # 错误：Material Deep Red 700
            dot_color = QColor(211, 47, 47, 255)  # #D32F2F
        else:
            # 待机：暗红色
            dot_color = QColor(150, 50, 50, 120)

        painter.setBrush(QBrush(dot_color))
        painter.setPen(QPen(Qt.PenStyle.NoPen))

        # 在中心绘制圆形红点（向上偏移3px以视觉居中）
        center_x = self.width() // 2
        center_y = self.height() // 2 - 3  # 向上偏移3px
        dot_radius = 6  # 圆点半径
        painter.drawEllipse(
            center_x - dot_radius, center_y - dot_radius, dot_radius * 2, dot_radius * 2
        )
