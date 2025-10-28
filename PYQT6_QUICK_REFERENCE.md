# PyQt6 快速参考指南 - SonicInput 项目

## 1. 枚举类型转换速查表

### Key 枚举
```
PyQt5: Qt.Key_Escape           → PyQt6: Qt.Key.Key_Escape
PyQt5: Qt.Key_Space            → PyQt6: Qt.Key.Key_Space
PyQt5: Qt.Key_Return           → PyQt6: Qt.Key.Key_Return
PyQt5: Qt.Key_Tab              → PyQt6: Qt.Key.Key_Tab
PyQt5: Qt.Key_Up               → PyQt6: Qt.Key.Key_Up
PyQt5: Qt.Key_Down             → PyQt6: Qt.Key.Key_Down
```

### MouseButton 枚举
```
PyQt5: Qt.LeftButton           → PyQt6: Qt.MouseButton.LeftButton
PyQt5: Qt.RightButton          → PyQt6: Qt.MouseButton.RightButton
PyQt5: Qt.MiddleButton         → PyQt6: Qt.MouseButton.MiddleButton
```

### MouseButton 状态
```
PyQt5: Qt.LeftButton           → PyQt6: Qt.MouseButton.LeftButton
PyQt5: event.buttons()         → PyQt6: event.buttons()  # 返回 Buttons 标志
```

### WindowType 枚举
```
PyQt5: Qt.FramelessWindowHint        → PyQt6: Qt.WindowType.FramelessWindowHint
PyQt5: Qt.WindowStaysOnTopHint       → PyQt6: Qt.WindowType.WindowStaysOnTopHint
PyQt5: Qt.Tool                       → PyQt6: Qt.WindowType.Tool
PyQt5: Qt.Window                     → PyQt6: Qt.WindowType.Window
PyQt5: Qt.WindowDoesNotAcceptFocus   → PyQt6: Qt.WindowType.WindowDoesNotAcceptFocus
```

### WidgetAttribute 枚举
```
PyQt5: Qt.WA_TranslucentBackground   → PyQt6: Qt.WidgetAttribute.WA_TranslucentBackground
```

### AlignmentFlag 枚举
```
PyQt5: Qt.AlignCenter          → PyQt6: Qt.AlignmentFlag.AlignCenter
PyQt5: Qt.AlignLeft            → PyQt6: Qt.AlignmentFlag.AlignLeft
PyQt5: Qt.AlignRight           → PyQt6: Qt.AlignmentFlag.AlignRight
PyQt5: Qt.AlignTop             → PyQt6: Qt.AlignmentFlag.AlignTop
PyQt5: Qt.AlignBottom          → PyQt6: Qt.AlignmentFlag.AlignBottom
```

### CheckState 枚举
```
PyQt5: Qt.Unchecked            → PyQt6: Qt.CheckState.Unchecked
PyQt5: Qt.Checked              → PyQt6: Qt.CheckState.Checked
PyQt5: Qt.PartiallyChecked     → PyQt6: Qt.CheckState.PartiallyChecked
```

### CursorShape 枚举
```
PyQt5: Qt.PointingHandCursor   → PyQt6: Qt.CursorShape.PointingHandCursor
PyQt5: Qt.ArrowCursor          → PyQt6: Qt.CursorShape.ArrowCursor
PyQt5: Qt.CrossCursor          → PyQt6: Qt.CursorShape.CrossCursor
PyQt5: Qt.WaitCursor           → PyQt6: Qt.CursorShape.WaitCursor
```

### PenStyle 枚举
```
PyQt5: Qt.SolidLine            → PyQt6: Qt.PenStyle.SolidLine
PyQt5: Qt.DashLine             → PyQt6: Qt.PenStyle.DashLine
PyQt5: Qt.NoPen                → PyQt6: Qt.PenStyle.NoPen
```

### PenCapStyle 枚举
```
PyQt5: Qt.RoundCap             → PyQt6: Qt.PenCapStyle.RoundCap
PyQt5: Qt.SquareCap            → PyQt6: Qt.PenCapStyle.SquareCap
PyQt5: Qt.FlatCap              → PyQt6: Qt.PenCapStyle.FlatCap
```

### Event 类型
```
PyQt5: QEvent.Wheel            → PyQt6: QEvent.Type.Wheel
PyQt5: QEvent.Close            → PyQt6: QEvent.Type.Close
PyQt5: QEvent.Paint            → PyQt6: QEvent.Type.Paint
PyQt5: QEvent.KeyPress         → PyQt6: QEvent.Type.KeyPress
PyQt5: QEvent.MouseMove        → PyQt6: QEvent.Type.MouseMove
PyQt5: QEvent.Enter            → PyQt6: QEvent.Type.Enter
PyQt5: QEvent.Leave            → PyQt6: QEvent.Type.Leave
```

### FocusPolicy 枚举
```
PyQt5: Qt.NoFocus              → PyQt6: Qt.FocusPolicy.NoFocus
PyQt5: Qt.TabFocus             → PyQt6: Qt.FocusPolicy.TabFocus
PyQt5: Qt.ClickFocus           → PyQt6: Qt.FocusPolicy.ClickFocus
PyQt5: Qt.StrongFocus          → PyQt6: Qt.FocusPolicy.StrongFocus
PyQt5: Qt.WheelFocus           → PyQt6: Qt.FocusPolicy.WheelFocus
```

---

## 2. API 变更速查表

### QSystemTrayIcon

| 功能 | PyQt5 | PyQt6 | 注意 |
|------|-------|-------|------|
| **激活原因** | `Qt.DoubleClick` | `QSystemTrayIcon.ActivationReason.DoubleClick` | 需要转换为值 |
| **消息图标** | `QSystemTrayIcon.Information` | `QSystemTrayIcon.MessageIcon.Information` | 枚举位置变更 |
| **激活信号** | `activated` | `activated` | 参数处理方式变更 |

### QMouseEvent

| 功能 | PyQt5 | PyQt6 | 注意 |
|------|-------|-------|------|
| **全局位置** | `event.globalPos()` | `event.globalPosition().toPoint()` | 返回类型变更 |
| **本地位置** | `event.pos()` | `event.position().toPoint()` | 返回类型变更 |
| **按键状态** | `event.buttons()` | `event.buttons()` | 兼容，返回 Buttons 标志 |

### QKeyEvent

| 功能 | PyQt5 | PyQt6 | 注意 |
|------|-------|-------|------|
| **按键码** | `event.key()` | `event.key()` | 兼容，但枚举值变更 |
| **文本** | `event.text()` | `event.text()` | 兼容 |

### QPropertyAnimation

| 功能 | PyQt5 | PyQt6 | 注意 |
|------|-------|-------|------|
| **状态** | `QPropertyAnimation.Running` | `QPropertyAnimation.State.Running` | 枚举位置变更 |
| **缓动曲线** | `QEasingCurve.InOutQuad` | `QEasingCurve.Type.InOutQuad` | 枚举位置变更 |

### QCheckBox

| 功能 | PyQt5 | PyQt6 | 注意 |
|------|-------|-------|------|
| **状态信号** | `stateChanged` | `stateChanged` | 兼容 |
| **检查状态** | `state == Qt.Checked` | `state == Qt.CheckState.Checked` | 枚举变更 |

---

## 3. SonicInput 项目特定的代码模式

### 模式 1: 线程安全信号（RecordingOverlay）

```python
# 1. 定义公开接口（线程安全）
class RecordingOverlay(QWidget):
    show_recording_requested = pyqtSignal()
    hide_recording_requested = pyqtSignal()

    # 2. 公开方法发送信号
    def show_recording(self) -> None:
        """Thread-safe public interface"""
        self.show_recording_requested.emit()

    # 3. 初始化时连接信号到槽
    def __init__(self):
        super().__init__()
        self.show_recording_requested.connect(self._show_recording_impl)

    # 4. 内部实现在槽中执行（主线程）
    def _show_recording_impl(self) -> None:
        """Internal implementation (Qt main thread only)"""
        self.is_recording = True
        self.show()
```

### 模式 2: 安全的定时器管理

```python
def _safe_timer_connect(self, timer, target_method):
    """安全地连接定时器"""
    try:
        timer.timeout.disconnect(target_method)  # 断开现有连接
    except (TypeError, RuntimeError):
        pass  # 信号未连接，忽略错误
    timer.timeout.connect(target_method)  # 重新连接

def _safe_timer_start(self, timer, interval, target_method):
    """安全地启动定时器"""
    if timer.isActive():
        timer.stop()  # 先停止现有定时器
    self._safe_timer_connect(timer, target_method)
    timer.start(interval)  # 启动定时器

def _safe_timer_stop(self, timer, target_method):
    """安全地停止定时器"""
    if timer.isActive():
        timer.stop()
        try:
            timer.timeout.disconnect(target_method)
        except (TypeError, RuntimeError):
            pass
```

### 模式 3: 事件过滤器

```python
class WheelEventFilter(QObject):
    """阻止下拉框和数值调整控件的滚轮事件"""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel:
            return True  # 处理事件，不继续传播
        return False  # 继续传播事件

# 使用方式
self.wheel_filter = WheelEventFilter(self)
combo_box.installEventFilter(self.wheel_filter)
```

### 模式 4: 枚举值转换

```python
# 托盘激活处理
def _on_icon_activated(self, reason) -> None:
    # PyQt6 兼容方式
    reason_value = reason.value if hasattr(reason, 'value') else int(reason)

    if reason_value == 2:  # DoubleClick
        self.show_settings()
    elif reason_value == 4:  # MiddleClick
        self.toggle_recording()
```

### 模式 5: 自定义绘制

```python
class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(24, 24)

    def paintEvent(self, event):
        """自定义绘制"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制圆形
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

        painter.end()  # 确保正确关闭
```

### 模式 6: 鼠标事件处理

```python
class DraggableWidget(QWidget):
    def mousePressEvent(self, event):
        """鼠标按下"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 获取拖拽起点（兼容 PyQt6）
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        """鼠标移动"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            # 移动窗口
            self.move(event.globalPosition().toPoint() - self.drag_position)

    def mouseReleaseEvent(self, event):
        """鼠标释放"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 保存窗口位置
            self.save_position()
```

### 模式 7: 异步操作与 QTimer

```python
def test_api_connection(self) -> None:
    """异步 API 测试"""
    # 1. 在后台线程执行操作
    test_thread = threading.Thread(target=self.test_connection, daemon=True)
    test_thread.start()

    # 2. 保存线程引用
    self._api_test_thread = test_thread
    self._api_test_result = {"success": False}

    # 3. 使用 QTimer 轮询结果（主线程）
    self._api_test_timer = QTimer()
    self._api_test_timer.timeout.connect(self._check_api_test_status)
    self._api_test_timer.start(100)  # 每 100ms 检查一次

def _check_api_test_status(self) -> None:
    """检查测试是否完成"""
    if not self._api_test_thread.is_alive():
        # 线程已完成，停止定时器
        self._api_test_timer.stop()

        # 在主线程中显示结果
        if self._api_test_result["success"]:
            QMessageBox.information(self, "Success", "API 连接成功！")
        else:
            QMessageBox.critical(self, "Error", "API 连接失败")
```

---

## 4. 常见错误及修复

### 错误 1: 枚举使用错误

```python
# 错误
if event.key() == Qt.Key_Escape:  # PyQt5 风格
    pass

# 正确
if event.key() == Qt.Key.Key_Escape:  # PyQt6 风格
    pass
```

### 错误 2: 信号重复连接

```python
# 错误 - 会导致信号被触发多次
button.clicked.connect(self.on_click)
button.clicked.connect(self.on_click)

# 正确
try:
    button.clicked.disconnect(self.on_click)
except (TypeError, RuntimeError):
    pass
button.clicked.connect(self.on_click)
```

### 错误 3: 在工作线程中直接修改 UI

```python
# 错误
def run(self):
    self.label.setText("Done")  # 不是线程安全的

# 正确
class MyThread(QThread):
    progress = pyqtSignal(str)

    def run(self):
        self.progress.emit("Done")  # 发送信号

# 主线程连接
thread.progress.connect(self.label.setText)
```

### 错误 4: 忘记调用 painter.end()

```python
# 错误
def paintEvent(self, event):
    painter = QPainter(self)
    # ... 绘制代码
    # 忘记调用 painter.end()

# 正确
def paintEvent(self, event):
    painter = QPainter(self)
    # ... 绘制代码
    painter.end()  # 必须调用
```

### 错误 5: 鼠标事件位置转换

```python
# 错误
pos = event.globalPos()  # PyQt5 风格

# 正确
pos = event.globalPosition().toPoint()  # PyQt6 风格
```

### 错误 6: 事件过滤器返回值错误

```python
# 错误
def eventFilter(self, obj, event):
    if event.type() == QEvent.Type.Wheel:
        pass  # 忘记返回 True

# 正确
def eventFilter(self, obj, event):
    if event.type() == QEvent.Type.Wheel:
        return True  # 处理事件，返回 True 阻止传播
    return False  # 不处理，继续传播
```

---

## 5. 调试技巧

### 技巧 1: 查看信号是否已连接

```python
# 检查信号连接数
print(button.clicked.receivers())  # 返回连接数

# 查看所有连接
for connection in button.clicked.receivers():
    print(connection)
```

### 技巧 2: 验证事件过滤器安装

```python
# 检查是否安装了事件过滤器
print(widget.eventFilters())  # 返回事件过滤器列表

# 移除事件过滤器
widget.removeEventFilter(filter)
```

### 技巧 3: 调试定时器

```python
# 检查定时器是否活跃
print(timer.isActive())

# 检查定时器间隔
print(timer.interval())

# 查看连接的槽
print(timer.receivers(timer.timeout))
```

### 技巧 4: 调试动画

```python
# 检查动画状态
print(animation.state())  # Running, Stopped, etc.

# 检查动画目标对象
print(animation.targetObject())

# 检查目标属性
print(animation.propertyName())
```

### 技巧 5: 启用 Qt 日志输出

```python
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'  # 调试插件加载
os.environ['QT_DEBUG_EVENTS'] = '1'   # 调试事件

from PyQt6.QtCore import QT_VERSION_STR
print(f"Qt version: {QT_VERSION_STR}")
```

---

## 6. 性能优化建议

### 优化 1: 减少信号发送频率

```python
# 不推荐 - 频繁发送信号
def on_mouse_move(self, event):
    self.position_changed.emit(event.pos())

# 推荐 - 降低发送频率
def on_mouse_move(self, event):
    if not hasattr(self, '_last_emit'):
        self._last_emit = 0
    import time
    if time.time() - self._last_emit > 0.1:  # 最多 10Hz
        self.position_changed.emit(event.pos())
        self._last_emit = time.time()
```

### 优化 2: 使用 Qt.ConnectionType.QueuedConnection 进行跨线程通信

```python
# 不推荐
worker_thread.progress.connect(self.update_label)

# 推荐 - 显式指定连接类型
worker_thread.progress.connect(
    self.update_label,
    type=Qt.ConnectionType.QueuedConnection
)
```

### 优化 3: 在渲染密集操作前调用 setUpdatesEnabled(False)

```python
# 不推荐 - 频繁重绘
for i in range(1000):
    self.label.setText(f"Item {i}")

# 推荐 - 批量操作
self.setUpdatesEnabled(False)
for i in range(1000):
    self.label.setText(f"Item {i}")
self.setUpdatesEnabled(True)
self.update()  # 一次重绘
```

---

## 7. 常用导入速查表

```python
# 核心
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject, QEvent
from PyQt6.QtGui import QPainter, QBrush, QColor, QPen, QIcon, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QSystemTrayIcon, QMessageBox,
    QPropertyAnimation, QEasingCurve
)

# 动画
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

# 特殊效果
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QRadialGradient, QLinearGradient

# 事件处理
from PyQt6.QtCore import QEvent

# 定时器
from PyQt6.QtCore import QTimer
```

---

## 8. 完整的迁移清单

### Phase 1: 枚举转换（最优先）

- [ ] 替换所有 `Qt.Key_*` 为 `Qt.Key.Key_*`
- [ ] 替换所有 `Qt.*Button` 为 `Qt.MouseButton.*`
- [ ] 替换所有 `Qt.*WindowHint` 为 `Qt.WindowType.*`
- [ ] 替换所有 `Qt.WA_*` 为 `Qt.WidgetAttribute.WA_*`
- [ ] 替换所有 `Qt.Align*` 为 `Qt.AlignmentFlag.Align*`
- [ ] 替换所有 `Qt.*Cursor` 为 `Qt.CursorShape.*Cursor`
- [ ] 替换所有 `QEvent.*` 为 `QEvent.Type.*`

### Phase 2: API 调用更新

- [ ] 更新 `event.globalPos()` 为 `event.globalPosition().toPoint()`
- [ ] 更新 `event.pos()` 为 `event.position().toPoint()`
- [ ] 更新枚举值提取方式：`reason.value if hasattr(reason, 'value') else int(reason)`

### Phase 3: 测试与验证

- [ ] 单元测试（所有信号槽）
- [ ] 集成测试（所有事件）
- [ ] 性能测试（内存、CPU）
- [ ] 跨平台测试（Windows、Linux 等）

---

## 快速参考总结

| 项目 | 优先级 | 工作量 | 风险 |
|------|--------|--------|------|
| 枚举转换 | 高 | 大 | 高 |
| API 更新 | 高 | 中 | 中 |
| 事件处理 | 中 | 小 | 低 |
| 性能优化 | 低 | 小 | 低 |

