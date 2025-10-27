"""Close button component for recording overlay"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
from PyQt6.QtCore import Qt


class CloseButton(QWidget):
    """自定义绘制的关闭按钮 - 用×形状"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 启用鼠标追踪以支持hover效果
        self.setMouseTracking(True)

    def paintEvent(self, event):
        """自定义绘制×符号"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制背景（hover时显示）
        if self.hovered:
            painter.setBrush(QBrush(QColor(244, 67, 54, 38)))  # rgba(244, 67, 54, 0.15)
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)

        # 绘制×符号 - 两条对角线
        painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))

        # 计算×的绘制区域（留出边距），向上偏移3px与StatusIndicator对齐
        margin = 7
        center_x = self.width() // 2
        center_y = self.height() // 2 - 3  # 向上偏移3px，与StatusIndicator一致
        half_size = (self.width() - margin * 2) // 2

        # 左上到右下的对角线
        painter.drawLine(
            center_x - half_size, center_y - half_size,
            center_x + half_size, center_y + half_size
        )

        # 右上到左下的对角线
        painter.drawLine(
            center_x + half_size, center_y - half_size,
            center_x - half_size, center_y + half_size
        )

    def enterEvent(self, event):
        """鼠标进入"""
        self.hovered = True
        self.update()

    def leaveEvent(self, event):
        """鼠标离开"""
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        """鼠标按下 - 由外部连接处理"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 触发点击信号（如果需要）或直接处理
            pass  # 外部会覆盖这个方法
