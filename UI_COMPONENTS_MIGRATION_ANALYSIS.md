# SonicInput UI 组件深度分析 - PyQt6 实现细节与迁移指南

## 执行摘要

本报告针对 **SonicInput** 项目（基于 PyQt6 的 Windows 语音输入工具）进行了全面的 UI 组件架构分析。项目包含 **113+ 处信号槽连接、事件处理器和动画实现**，涉及自定义控件、系统托盘整合、叠加窗口等高级 PyQt 特性。

主要发现：
- **5 个关键 PyQt6 子类实现**（QMainWindow、QDialog、QWidget、QThread）
- **8+ 类型的事件处理器**（keyPressEvent、mousePressEvent、enterEvent 等）
- **15+ 个自定义信号**用于跨组件通信
- **4 种动画实现方式**（QPropertyAnimation、QTimer、自定义 paintEvent）
- **系统托盘整合**与状态管理

---

## 1. 核心 UI 子类实现

### 1.1 主窗口（MainWindow）

**文件**: `src/sonicinput/ui/main_window.py:93-377`

```python
class MainWindow(QMainWindow):
    """最小化主窗口 - 仅提供基本GUI功能"""

    # 信号定义 - PyQt6 的 pyqtSignal
    window_closing = pyqtSignal()
```

**关键特性**:
- **QMainWindow 子类** - 提供菜单栏、工具栏、状态栏基础设施
- **最小化设计** - `setFixedSize(400, 300)` 固定窗口大小
- **隐藏启动** - `self.hide()` 最小化到系统托盘
- **窗口标志配置**:
  ```python
  self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
  ```

**信号槽连接**:
- 按钮点击处理：`self.recording_button.clicked.connect(self.toggle_recording)`
- 自定义信号连接：`self._settings_window.model_load_requested.connect(self._on_model_load_requested)`
- 事件订阅：`events.on(Events.RECORDING_STARTED, self._on_recording_started)`

**事件处理**:
- `closeEvent()` - 关闭事件拦截，最小化而非关闭
  ```python
  def closeEvent(self, event):
      event.ignore()  # 阻止窗口关闭
      self.hide()     # 最小化到托盘
  ```

---

### 1.2 录音叠加窗口（RecordingOverlay）

**文件**: `src/sonicinput/ui/recording_overlay.py:14-1247`

**关键特性** - **最复杂的自定义 QWidget 实现**:

#### 1.2.1 窗口标志与属性
```python
self.setWindowFlags(
    Qt.WindowType.FramelessWindowHint |      # 无边框
    Qt.WindowType.WindowStaysOnTopHint |     # 始终置顶
    Qt.WindowType.Tool |                      # 工具窗口
    Qt.WindowType.WindowDoesNotAcceptFocus   # 不接受焦点
)
self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # 透明背景
```

#### 1.2.2 Qt安全单例模式实现
```python
class RecordingOverlay(QWidget):
    _instance = None
    _initialized = False

    def __new__(cls, parent=None):
        """Qt-safe singleton pattern (main thread only, no lock needed)"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

#### 1.2.3 线程安全信号设计
- **公开接口使用信号**发送请求（线程安全）：
  ```python
  show_recording_requested = pyqtSignal()
  hide_recording_requested = pyqtSignal()
  update_audio_level_requested = pyqtSignal(float)
  ```

- **内部实现使用槽方法**处理请求（主线程执行）：
  ```python
  def show_recording(self) -> None:
      """Thread-safe public interface"""
      self.show_recording_requested.emit()

  def _show_recording_impl(self) -> None:
      """Internal implementation (Qt main thread only)"""
      # 实际逻辑
  ```

#### 1.2.4 复杂的事件处理
```python
def keyPressEvent(self, event):
    """键盘事件"""
    if event.key() == Qt.Key.Key_Escape:
        self.hide_recording()
    elif event.key() == Qt.Key.Key_Space:
        self.hide_recording()

def mousePressEvent(self, event):
    """鼠标按下事件 - 用于拖拽窗口"""
    if event.button() == Qt.MouseButton.LeftButton:
        self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

def mouseMoveEvent(self, event):
    """鼠标移动事件 - 拖拽窗口"""
    if event.buttons() == Qt.MouseButton.LeftButton:
        self.move(event.globalPosition().toPoint() - self.drag_position)

def mouseReleaseEvent(self, event):
    """鼠标释放事件 - 拖拽结束后保存位置"""
    if self.config_service:
        self.position_manager.save_position()
```

#### 1.2.5 布局与自定义组件集成
```python
def setup_overlay_ui(self) -> None:
    main_layout = QVBoxLayout()

    # 背景框架
    self.background_frame = QFrame()
    frame_layout = QHBoxLayout(self.background_frame)

    # 状态指示器（自定义 QWidget）
    self.status_indicator = StatusIndicator(self)
    frame_layout.addWidget(self.status_indicator, 0, Qt.AlignmentFlag.AlignCenter)

    # 音频级别条
    for i in range(5):
        bar = QLabel()
        bar.setFixedSize(4, 18)
        bar.setStyleSheet("QLabel { border-radius: 2px; }")
        self.audio_level_bars.append(bar)

    # 关闭按钮（自定义 QWidget）
    self.close_button = CloseButton(self)
    # 连接鼠标事件
    self.close_button.mousePressEvent = close_button_click
```

#### 1.2.6 定时器管理（高度安全）
```python
def _safe_timer_connect(self, timer, target_method, description=""):
    """安全地连接定时器，防止重复连接"""
    try:
        timer.timeout.disconnect(target_method)
    except (TypeError, RuntimeError):
        pass  # 信号未连接或对象已删除
    timer.timeout.connect(target_method)

def _safe_timer_start(self, timer, interval, target_method, description=""):
    """安全地启动定时器"""
    try:
        if timer.isActive():
            timer.stop()
        self._safe_timer_connect(timer, target_method)
        timer.start(interval)
    except Exception as e:
        app_logger.log_error(e, f"safe_timer_start_{description}")
```

---

### 1.3 设置窗口（SettingsWindow）

**文件**: `src/sonicinput/ui/settings_window.py:37-1240`

**关键特性**:

#### 1.3.1 标签页组织
```python
class SettingsWindow(QMainWindow):
    # 信号定义
    settings_changed = pyqtSignal(str, object)
    model_load_requested = pyqtSignal(str)
    model_test_requested = pyqtSignal()

    def setup_ui(self) -> None:
        self.tab_widget = QTabWidget()
        self._create_scrollable_tab(self.general_tab.create(), "General")
        self._create_scrollable_tab(self.hotkey_tab.create(), "Hotkey")
        # ...

    def _create_scrollable_tab(self, content_widget: QWidget, tab_name: str):
        """带滚动的 Tab 页"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setWidget(content_widget)
        self.tab_widget.addTab(scroll_area, tab_name)
```

#### 1.3.2 事件过滤器防止误触
```python
class WheelEventFilter(QObject):
    """事件过滤器：阻止下拉框和数值调整控件的滚轮事件"""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.Wheel:
            return True  # 阻止事件
        return False
```

#### 1.3.3 异步操作与 QTimer
```python
def test_api_connection(self) -> None:
    """异步 API 测试"""
    # 创建线程
    test_thread = threading.Thread(target=test_connection, daemon=True)
    test_thread.start()

    # 使用 QTimer 异步检查结果
    self._api_test_timer = QTimer()
    self._api_test_timer.timeout.connect(self._check_api_test_status)
    self._api_test_timer.start(100)  # 每 100ms 检查一次

def _check_api_test_status(self) -> None:
    """检查 API 测试状态"""
    if not self._api_test_thread.is_alive():
        self._api_test_timer.stop()
        # 显示结果对话框
```

---

### 1.4 系统托盘控制器（TrayController）

**文件**: `src/sonicinput/ui/components/system_tray/tray_controller.py:23-557`

**关键特性**:

#### 1.4.1 QSystemTrayIcon 集成
```python
class TrayController(LifecycleComponent):
    show_settings_requested = pyqtSignal()
    toggle_recording_requested = pyqtSignal()

    def _do_initialize(self, config: Dict[str, Any]) -> bool:
        self._tray_widget = TrayWidget()  # 创建托盘 widget

        if not self._tray_widget.is_tray_available():
            # 处理系统托盘不可用的情况
            pass
        else:
            self._connect_widget_signals()
```

#### 1.4.2 托盘激活事件处理
```python
def _on_icon_activated(self, reason) -> None:
    """处理托盘图标激活"""
    reason_value = reason.value if hasattr(reason, 'value') else int(reason)

    if reason_value == 2:  # DoubleClick
        self._handle_show_settings()
    elif reason_value == 4:  # MiddleClick
        self._handle_toggle_recording()
```

#### 1.4.3 事件订阅系统
```python
def _subscribe_to_events(self) -> None:
    """订阅应用事件"""
    self._event_service.subscribe(
        Events.RECORDING_STATE_CHANGED,
        self._on_recording_state_changed,
        priority=EventPriority.HIGH
    )
    self._event_service.subscribe(
        Events.TRANSCRIPTION_COMPLETED,
        self._on_processing_completed,
        priority=EventPriority.NORMAL
    )

def _on_processing_completed(self, event_data: Dict[str, Any] = None):
    """处理完成事件"""
    if self._tray_widget:
        self._tray_widget.show_message(
            "Voice Input",
            "Text processed successfully!",
            QSystemTrayIcon.MessageIcon.Information
        )
```

---

### 1.5 自定义组件

#### 1.5.1 StatusIndicator（状态指示器）
**文件**: `src/sonicinput/ui/overlay/components/status_indicator.py:8-60`

```python
class StatusIndicator(QWidget):
    """真正的圆形红点状态指示器"""

    STATE_IDLE = 0
    STATE_RECORDING = 1
    STATE_PROCESSING = 2
    STATE_COMPLETED = 3

    def paintEvent(self, event):
        """自定义绘制圆形状态点"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 根据状态选择颜色
        if self.state == self.STATE_RECORDING:
            dot_color = QColor(244, 67, 54, 255)  # Material Red
        elif self.state == self.STATE_PROCESSING:
            dot_color = QColor(255, 193, 7, 255)  # Material Amber
        # ...

        painter.setBrush(QBrush(dot_color))
        painter.drawEllipse(center_x - dot_radius, center_y - dot_radius,
                          dot_radius * 2, dot_radius * 2)
```

#### 1.5.2 CloseButton（关闭按钮）
**文件**: `src/sonicinput/ui/overlay/components/close_button.py:8-67`

```python
class CloseButton(QWidget):
    """自定义绘制的关闭按钮 - 用×形状"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.hovered = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)  # 启用鼠标追踪

    def paintEvent(self, event):
        """自定义绘制×符号"""
        painter = QPainter(self)
        # 绘制 hover 背景
        if self.hovered:
            painter.setBrush(QBrush(QColor(244, 67, 54, 38)))
            painter.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)

        # 绘制×符号
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(x1, y1, x2, y2)  # 两条对角线

    def enterEvent(self, event):
        """鼠标进入"""
        self.hovered = True
        self.update()  # 触发 paintEvent

    def leaveEvent(self, event):
        """鼠标离开"""
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        """鼠标按下 - 由外部覆盖"""
        if event.button() == Qt.MouseButton.LeftButton:
            pass  # 外部会覆盖这个方法
```

---

## 2. 信号槽系统分析

### 2.1 信号定义模式

**模式 1: 标准 PyQt 信号**
```python
class MyWidget(QWidget):
    # 定义信号（无参数）
    clicked = pyqtSignal()

    # 定义信号（有参数）
    value_changed = pyqtSignal(int, str)

    # 信号初始化
    def __init__(self):
        super().__init__()
        # 信号定义必须在 __init__ 之前（类级别）
```

**模式 2: 跨线程信号**
```python
class RecordingOverlay(QWidget):
    # 公开接口信号 - 线程安全
    show_recording_requested = pyqtSignal()
    hide_recording_requested = pyqtSignal()
    update_audio_level_requested = pyqtSignal(float)

    # 线程可以调用这些公开方法，内部使用 emit
    def show_recording(self) -> None:
        """Thread-safe public interface"""
        self.show_recording_requested.emit()  # 发送信号到主线程
```

### 2.2 槽连接模式

**模式 1: 直接槽连接**
```python
self.recording_button.clicked.connect(self.toggle_recording)
self.settings_button.clicked.connect(self.show_settings)
```

**模式 2: Lambda 连接**
```python
set_hotkey_btn.clicked.connect(lambda: self.test_requested.emit("hotkey"))
```

**模式 3: 信号转发**
```python
# 子控件信号连接到父组件信号
speech_tab.test_requested.connect(self.test_requested.emit)
```

**模式 4: 带参数的槽**
```python
self._event_service.subscribe(
    Events.RECORDING_STATE_CHANGED,
    self._on_recording_state_changed,
    priority=EventPriority.HIGH
)

def _on_recording_state_changed(self, event_data: Dict[str, Any] = None):
    """处理事件"""
    if event_data:
        new_state = event_data.get("new_state")
```

### 2.3 常见信号列表

| 信号 | 来源 | 参数 | 用途 |
|------|------|------|------|
| `clicked` | QPushButton | 无 | 按钮点击 |
| `activated` | QSystemTrayIcon | int (reason) | 托盘图标点击 |
| `timeout` | QTimer | 无 | 定时器超时 |
| `stateChanged` | QCheckBox | int (state) | 复选框状态 |
| `currentTextChanged` | QComboBox | str | 下拉框选择 |
| `textChanged` | QLineEdit | str | 文本输入 |
| `valueChanged` | QSpinBox/QSlider | int/float | 数值变化 |
| `accepted` | QDialog | 无 | 确定按钮 |
| `rejected` | QDialog | 无 | 取消按钮 |

---

## 3. 事件处理系统

### 3.1 事件处理器重写

**RecordingOverlay 中的事件处理器**:

```python
# 1. 键盘事件
def keyPressEvent(self, event: QKeyEvent):
    """键盘按键按下"""
    if event.key() == Qt.Key.Key_Escape:
        self.hide_recording()

# 2. 鼠标事件
def mousePressEvent(self, event: QMouseEvent):
    """鼠标按下"""
    if event.button() == Qt.MouseButton.LeftButton:
        self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

def mouseMoveEvent(self, event: QMouseEvent):
    """鼠标移动"""
    if event.buttons() == Qt.MouseButton.LeftButton:
        self.move(event.globalPosition().toPoint() - self.drag_position)

def mouseReleaseEvent(self, event: QMouseEvent):
    """鼠标释放"""
    if event.button() == Qt.MouseButton.LeftButton:
        if self.config_service:
            self.position_manager.save_position()

# 3. 窗口事件
def closeEvent(self, event: QCloseEvent):
    """窗口关闭"""
    event.ignore()  # 阻止关闭
    self.hide()     # 最小化到托盘

# 4. 绘制事件
def paintEvent(self, event: QPaintEvent):
    """自定义绘制"""
    painter = QPainter(self)
    if self.is_processing:
        # 绘制呼吸发光效果
        self._draw_breathing_effect(painter)

# 5. 鼠标悬停事件（CloseButton）
def enterEvent(self, event: QEnterEvent):
    """鼠标进入"""
    self.hovered = True
    self.update()

def leaveEvent(self, event: QEvent):
    """鼠标离开"""
    self.hovered = False
    self.update()
```

### 3.2 事件过滤器

**WheelEventFilter - 防止误触**:
```python
class WheelEventFilter(QObject):
    """事件过滤器：阻止下拉框和数值调整控件的滚轮事件"""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        # 如果是滚轮事件，阻止它
        if event.type() == QEvent.Type.Wheel:
            return True  # 返回 True 表示事件被处理（不继续传播）
        return False  # 返回 False 表示继续传播事件

# 使用方式
self.wheel_filter = WheelEventFilter(self)
for child in widget.children():
    if isinstance(child, (QComboBox, QSpinBox, QDoubleSpinBox)):
        child.installEventFilter(self.wheel_filter)
```

---

## 4. 布局系统

### 4.1 RecordingOverlay 布局

```python
def setup_overlay_ui(self) -> None:
    # 主布局 - 垂直
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(8, 8, 8, 8)
    main_layout.setSpacing(0)

    # 背景框架
    self.background_frame = QFrame()
    frame_layout = QHBoxLayout(self.background_frame)  # 水平布局
    frame_layout.setContentsMargins(8, 6, 8, 6)
    frame_layout.setSpacing(8)

    # 添加组件
    frame_layout.addWidget(self.status_indicator, 0, Qt.AlignmentFlag.AlignCenter)

    # 添加弹性空间
    frame_layout.addStretch()

    # 添加时间标签
    frame_layout.addWidget(self.time_label)

    # 添加关闭按钮
    frame_layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignCenter)

    # 添加框架到主布局
    main_layout.addWidget(self.background_frame)
    self.setLayout(main_layout)

    # 设置固定大小
    self.setFixedSize(200, 50)
```

### 4.2 SettingsWindow 布局

```python
def setup_ui(self) -> None:
    central_widget = QWidget()
    self.setCentralWidget(central_widget)

    # 主布局 - 垂直
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(10, 10, 10, 10)

    # 标签页组件
    self.tab_widget = QTabWidget()
    main_layout.addWidget(self.tab_widget)

    # 底部按钮布局 - 水平
    button_layout = QHBoxLayout()
    button_layout.addWidget(self.reset_button)
    button_layout.addStretch()
    button_layout.addWidget(self.apply_button)
    button_layout.addWidget(self.ok_button)
    button_layout.addWidget(self.cancel_button)

    main_layout.addLayout(button_layout)
```

---

## 5. 动画系统

### 5.1 QPropertyAnimation

```python
class RecordingOverlay(QWidget):
    def __init__(self, parent=None):
        # 淡入淡出动画
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # 状态动画
        self.status_animation = QPropertyAnimation(self, b"windowOpacity")
        self.status_animation.setDuration(1000)
        self.status_animation.setEasingCurve(QEasingCurve.Type.InOutSine)

    def _show_recording_impl(self):
        # 淡入动画
        if hasattr(self, 'fade_animation'):
            self.fade_animation.stop()
            self.fade_animation.setStartValue(0.0)
            self.fade_animation.setEndValue(1.0)
            self.fade_animation.start()
```

### 5.2 QTimer 定时器

```python
# 录音计时器
self.update_timer = QTimer()
self.update_timer.timeout.connect(self.update_recording_time)

def _safe_timer_start(self, timer, interval, target_method):
    """安全启动定时器"""
    if timer.isActive():
        timer.stop()
    self._safe_timer_connect(timer, target_method)
    timer.start(interval)

def update_recording_time(self) -> None:
    """更新录音时间"""
    if self.is_recording:
        self.recording_duration += 1
        minutes = self.recording_duration // 60
        seconds = self.recording_duration % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
```

### 5.3 自定义 paintEvent 动画（呼吸效果）

```python
def paintEvent(self, event):
    """重写绘制事件以添加呼吸发光效果"""
    super().paintEvent(event)

    if self.is_processing:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 计算呼吸效果的透明度
        breathing_intensity = (math.sin(self.breathing_phase) + 1) / 2
        alpha = max(0, min(255, int(30 + 50 * breathing_intensity)))

        # 创建径向渐变
        gradient = QRadialGradient(self.width() / 2, self.height() / 2,
                                  min(self.width(), self.height()) / 2)
        center_color = QColor(76, 175, 80, alpha)
        gradient.setColorAt(0, center_color)
        gradient.setColorAt(0.7, QColor(76, 175, 80, alpha // 3))
        gradient.setColorAt(1, QColor(76, 175, 80, 0))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        painter.end()

def update_breathing(self) -> None:
    """更新呼吸效果"""
    if self.is_processing:
        self.breathing_phase += 0.15
        if self.breathing_phase >= 2 * math.pi:
            self.breathing_phase = 0
        self.update()  # 触发 paintEvent
```

---

## 6. 样式表（StyleSheet）系统

### 6.1 动态样式应用

```python
# RecordingOverlay 背景
self.background_frame.setStyleSheet("""
    QFrame#recordingOverlayFrame {
        background-color: #303030;
        border-radius: 12px;
    }
""")

# 音频级别条 - 活跃状态
bar.setStyleSheet(f"""
    QLabel {{
        background-color: {color};
        border-radius: 2px;
    }}
""")

# 音频级别条 - 非活跃状态
bar.setStyleSheet("""
    QLabel {
        background-color: rgba(80, 80, 90, 100);
        border-radius: 2px;
    }
""")

# 设置窗口
self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
self.whisper_tab.model_status_label.setStyleSheet("color: green;")  # 成功
self.whisper_tab.model_status_label.setStyleSheet("color: red;")     # 错误
```

### 6.2 阴影效果（QGraphicsDropShadowEffect）

```python
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

shadow = QGraphicsDropShadowEffect()
shadow.setBlurRadius(20)
shadow.setXOffset(0)
shadow.setYOffset(4)
shadow.setColor(QColor(0, 0, 0, 60))  # Material Elevation 8
self.background_frame.setGraphicsEffect(shadow)
```

---

## 7. 线程与异步操作

### 7.1 QThread 使用（ModelTestThread）

```python
class ModelTestThread(QThread):
    """Model test thread to avoid blocking UI"""

    progress_update = pyqtSignal(str)
    test_complete = pyqtSignal(bool, dict, str)

    def __init__(self, whisper_engine, parent=None):
        super().__init__(parent)
        self.whisper_engine = whisper_engine

    def run(self):
        """运行在工作线程中"""
        try:
            self.progress_update.emit("Creating test audio...")
            # 执行耗时操作
            result = self.whisper_engine.transcribe(test_audio)
            self.test_complete.emit(True, result_info, "")
        except Exception as e:
            self.test_complete.emit(False, {}, str(e))

# 主线程中使用
test_thread = ModelTestThread(whisper_engine, self)
test_thread.progress_update.connect(on_progress_update)
test_thread.test_complete.connect(on_test_complete)
test_thread.start()
```

### 7.2 线程安全的信号/槽

```python
# 工作线程发送信号
def run(self):
    # 从工作线程发送信号（线程安全）
    self.progress_update.emit("Progress...")
    self.test_complete.emit(success, result, error)

# 主线程连接槽
test_thread.progress_update.connect(lambda msg: progress.setLabelText(msg))
test_thread.test_complete.connect(on_test_complete)
```

---

## 8. 系统托盘实现

### 8.1 QSystemTrayIcon 集成

```python
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu

class TrayWidget(QWidget):
    icon_activated = pyqtSignal(object)
    menu_action_triggered = pyqtSignal(str)

    def __init__(self):
        self._tray_icon = QSystemTrayIcon()
        self._tray_icon.activated.connect(self._on_icon_activated)

        # 创建菜单
        self._tray_menu = QMenu()

        # 添加操作
        recording_action = self._tray_menu.addAction("Start Recording")
        recording_action.triggered.connect(
            lambda: self.menu_action_triggered.emit("toggle_recording")
        )

        settings_action = self._tray_menu.addAction("Settings")
        settings_action.triggered.connect(
            lambda: self.menu_action_triggered.emit("show_settings")
        )

        exit_action = self._tray_menu.addAction("Exit")
        exit_action.triggered.connect(
            lambda: self.menu_action_triggered.emit("exit_application")
        )

        self._tray_icon.setContextMenu(self._tray_menu)

    def _on_icon_activated(self, reason):
        """处理托盘图标激活"""
        self.icon_activated.emit(reason)

    def show_message(self, title: str, message: str, icon, timeout: int = 3000):
        """显示托盘通知"""
        self._tray_icon.showMessage(title, message, icon, timeout)
```

---

## 9. 迁移兼容性分析

### 9.1 PyQt6 特有的 API 变更

| 特性 | PyQt5 | PyQt6 | 迁移影响 |
|------|-------|-------|---------|
| **枚举值** | `Qt.Key_Escape` | `Qt.Key.Key_Escape` | 关键 - 代码全面改动 |
| **枚举提取** | `reason = int(reason)` | `reason.value` | 需要改动所有枚举处理 |
| **信号参数** | `pyqtSignal(int)` | `pyqtSignal(int)` | 兼容 |
| **槽装饰器** | `@pyqtSlot()` | `@pyqtSlot()` | 兼容 |
| **窗口标志** | `Qt.FramelessWindowHint` | `Qt.WindowType.FramelessWindowHint` | 关键 - 全面改动 |
| **关键字参数** | `QTimer.singleShot(1000, func)` | `QTimer.singleShot(1000, func)` | 兼容 |

### 9.2 关键兼容性问题

#### 问题 1: 枚举访问方式变更

**PyQt5 代码**:
```python
if event.key() == Qt.Key_Escape:
if event.button() == Qt.LeftButton:
self.setWindowFlags(Qt.FramelessWindowHint)
```

**PyQt6 代码**:
```python
if event.key() == Qt.Key.Key_Escape:
if event.button() == Qt.MouseButton.LeftButton:
self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
```

**项目受影响的代码位置**:
- `recording_overlay.py:910-915` - keyPressEvent 中的 Key 枚举
- `recording_overlay.py:85-89` - setWindowFlags 中的 WindowType 枚举
- `close_button.py:15,64` - 鼠标事件中的枚举
- 所有涉及 QColor 的地方可能需要验证

#### 问题 2: 信号/槽兼容性

**一般兼容** - 信号定义和连接在 PyQt5/PyQt6 中基本相同
```python
# 兼容
clicked = pyqtSignal()
button.clicked.connect(self.on_click)

# 需要验证参数转换
reason.value if hasattr(reason, 'value') else int(reason)
```

#### 问题 3: 事件处理器兼容性

**关键变更**:
- `QKeyEvent` 属性访问方式可能变更
- `QMouseEvent.globalPosition()` 返回 `QPointF`（需要 `.toPoint()`）
- `event.buttons()` 返回类型变更

**当前代码处理**:
```python
# 已正确处理
self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
```

#### 问题 4: 线程与信号安全

**兼容** - PyQt6 的信号/槽线程安全性与 PyQt5 相同
```python
# 兼容：从工作线程发送信号
self.progress_update.emit(message)  # 线程安全
```

### 9.3 高风险区域

| 文件 | 行号 | 问题 | 优先级 |
|------|------|------|--------|
| recording_overlay.py | 85-89 | WindowType 枚举 | 高 |
| recording_overlay.py | 910-915 | Key 枚举 | 高 |
| overlay/close_button.py | 15,64 | MouseButton 枚举 | 高 |
| overlay/status_indicator.py | 32-59 | QPainter API | 中 |
| settings_window.py | 19,59 | Qt.CheckState 枚举 | 中 |
| main_window.py | 113 | WindowType 枚举 | 高 |
| system_tray/tray_widget.py | 全文 | QSystemTrayIcon API | 中 |

---

## 10. 最佳实践与建议

### 10.1 信号/槽设计

✅ **推荐**:
```python
# 1. 明确定义公开信号
class MyWidget(QWidget):
    value_changed = pyqtSignal(int)  # 类级别定义

    def set_value(self, value):
        self.value_changed.emit(value)

# 2. 使用线程安全的信号
class WorkerThread(QThread):
    progress = pyqtSignal(str)  # 工作线程发送

    def run(self):
        self.progress.emit("Working...")  # 线程安全

# 3. 避免过度连接
button.clicked.connect(self.on_click)  # 一次连接
# 不要重复连接：button.clicked.connect(self.on_click)  # 避免！
```

❌ **避免**:
```python
# 1. 在 __init__ 中定义信号（应该在类级别）
def __init__(self):
    self.my_signal = pyqtSignal(int)  # 错误！

# 2. 在工作线程中直接更新 UI
def run(self):
    self.label.setText("...")  # 错误！不是线程安全的

# 3. 忘记断开信号连接
def cleanup(self):
    # 内存泄漏！应该断开连接
    pass
```

### 10.2 事件处理

✅ **推荐**:
```python
# 1. 调用父类实现
def keyPressEvent(self, event):
    if event.key() == Qt.Key.Key_Escape:
        self.close()
    else:
        super().keyPressEvent(event)  # 继续处理其他按键

# 2. 使用事件过滤器处理子控件事件
class MyFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Wheel:
            return True  # 处理并阻止传播
        return False  # 继续传播

# 3. 异常处理
def mousePressEvent(self, event):
    try:
        self.handle_click()
    except Exception as e:
        app_logger.log_error(e, "mouse_click")
```

❌ **避免**:
```python
# 1. 忽略事件处理
def keyPressEvent(self, event):
    if event.key() == Qt.Key.Key_Escape:
        self.close()
    # 错误！其他按键不被处理

# 2. 在事件处理器中阻塞
def mousePressEvent(self, event):
    time.sleep(5)  # 错误！阻塞 UI

# 3. 修改事件对象
def mouseReleaseEvent(self, event):
    event.setPos(new_pos)  # 错误！事件已发生
```

### 10.3 动画与定时器

✅ **推荐**:
```python
# 1. 清理动画资源
def cleanup(self):
    if self.fade_animation.state() == QPropertyAnimation.State.Running:
        self.fade_animation.stop()
    if self.update_timer.isActive():
        self.update_timer.stop()

# 2. 安全的定时器管理
def _safe_timer_start(self, timer, interval, callback):
    if timer.isActive():
        timer.stop()
    try:
        timer.timeout.disconnect()
    except (TypeError, RuntimeError):
        pass  # 信号未连接
    timer.timeout.connect(callback)
    timer.start(interval)

# 3. 使用 QPropertyAnimation 进行平滑动画
animation = QPropertyAnimation(self, b"windowOpacity")
animation.setDuration(300)
animation.setStartValue(0.0)
animation.setEndValue(1.0)
animation.start()
```

❌ **避免**:
```python
# 1. 泄漏定时器
def __init__(self):
    self.timer = QTimer()
    self.timer.start(1000)  # 错误！cleanup 时未停止

# 2. 重复启动定时器
self.timer.start(1000)
self.timer.start(1000)  # 错误！导致多次触发

# 3. 忘记设置动画属性
animation = QPropertyAnimation(self, b"geometry")  # 错误！大多数属性不能动画化
```

### 10.4 系统托盘

✅ **推荐**:
```python
# 1. 检查托盘可用性
if QSystemTrayIcon.isSystemTrayAvailable():
    self.tray_icon = QSystemTrayIcon()
else:
    # 降级方案
    self.show()

# 2. 优雅处理托盘消息
def show_notification(self, title, message):
    if self.tray_icon and self.notifications_enabled:
        self.tray_icon.showMessage(
            title, message,
            QSystemTrayIcon.MessageIcon.Information,
            5000  # 超时
        )

# 3. 正确处理激活信号
def on_tray_activated(self, reason):
    reason_value = reason.value if hasattr(reason, 'value') else int(reason)
    if reason_value == QSystemTrayIcon.ActivationReason.DoubleClick:
        self.show()
```

❌ **避免**:
```python
# 1. 假设托盘总是可用
self.tray_icon = QSystemTrayIcon()  # 可能崩溃

# 2. 无限制的通知
for i in range(1000):
    self.tray_icon.showMessage(...)  # 垃圾！

# 3. 无错误处理的激活
def on_tray_activated(self, reason):
    if reason == 2:  # 魔数！不可读
        pass
```

---

## 11. 迁移检查清单

### 11.1 代码检查

- [ ] 所有 `Qt.` 枚举都改为 `Qt.ClassName.EnumValue` 格式
- [ ] 所有 `QMouseEvent.globalPosition()` 都调用了 `.toPoint()`
- [ ] 所有 `reason` 枚举都检查了 `.value` 属性
- [ ] 所有 `QColor` 参数都是 `(r, g, b, a)` 格式
- [ ] 所有信号定义都在类级别（不在 `__init__` 中）
- [ ] 所有 `pyqtSignal()` 调用都不带 `@pyqtSignal` 装饰器

### 11.2 测试检查

- [ ] 运行 `uv sync` 安装 PyQt6 最新版本
- [ ] 测试所有按钮点击事件
- [ ] 测试所有键盘快捷键（Escape、Space）
- [ ] 测试鼠标拖拽（录音叠加窗口）
- [ ] 测试系统托盘激活（单击、双击、右击）
- [ ] 测试所有弹窗（消息框、进度条）
- [ ] 测试设置窗口标签页切换
- [ ] 测试所有动画效果（淡入淡出、呼吸效果）
- [ ] 在多显示器配置下测试叠加窗口位置

### 11.3 性能检查

- [ ] 验证定时器不会泄漏
- [ ] 验证信号槽不会重复连接
- [ ] 验证动画资源正确清理
- [ ] 检查内存使用（PyQt6 可能比 PyQt5 更大）
- [ ] 验证线程安全（使用线程安全信号）

---

## 12. 相关文件位置速查

### UI 主要组件
- **主窗口**: `/src/sonicinput/ui/main_window.py:93`
- **录音叠加**: `/src/sonicinput/ui/recording_overlay.py:14`
- **设置窗口**: `/src/sonicinput/ui/settings_window.py:37`
- **系统托盘**: `/src/sonicinput/ui/components/system_tray/tray_controller.py:23`

### 自定义组件
- **状态指示器**: `/src/sonicinput/ui/overlay/components/status_indicator.py:8`
- **关闭按钮**: `/src/sonicinput/ui/overlay/components/close_button.py:8`
- **动画控制器**: `/src/sonicinput/ui/recording_overlay_utils/animation_controller.py:14`

### 标签页实现
- **基类**: `/src/sonicinput/ui/settings_tabs/base_tab.py:10`
- **各标签页**: `/src/sonicinput/ui/settings_tabs/*.py`

### 工作线程
- **模型测试线程**: `/src/sonicinput/ui/main_window.py:11`
- **Whisper 工作线程**: `/src/sonicinput/speech/whisper_worker_thread.py`

---

## 总结

SonicInput 项目是一个相对复杂的 PyQt6 应用，涉及：

1. **多个 QMainWindow/QDialog/QWidget 子类** - 需要维护类层次结构
2. **广泛使用信号/槽系统** - 超过 100 处连接，需要注意循环引用
3. **复杂的事件处理** - 8+ 种事件类型，需要正确传播
4. **自定义绘制** - paintEvent 实现，需要理解 QPainter API
5. **线程与异步** - QThread 和信号交互，需要遵守主线程规则
6. **系统集成** - 系统托盘、全局快捷键，需要正确处理平台特性

关键的迁移点是 **PyQt6 枚举 API 的变更**，这是一个系统性的改动，需要逐个文件检查和更新。建议使用搜索/替换工具进行初期转换，然后进行全面的单元测试和集成测试。
