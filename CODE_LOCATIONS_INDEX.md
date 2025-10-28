# SonicInput UI 组件代码位置索引

## 快速导航

本文档提供所有 UI 相关代码的精确位置，便于快速查找和修改。

---

## 1. 主要窗口类

### MainWindow - 主应用窗口
**文件**: `/src/sonicinput/ui/main_window.py`

| 功能 | 行号 | 说明 |
|------|------|------|
| 类定义 | 93 | QMainWindow 子类 |
| __init__ | 99 | 构造函数 |
| setup_window() | 106 | 窗口配置 |
| setup_ui() | 118 | UI 布局 |
| set_controller() | 148 | 设置控制器 |
| _connect_controller_events() | 153 | 事件连接 |
| toggle_recording() | 173 | 切换录音 |
| show_settings() | 183 | 显示设置窗口 |
| _on_model_load_requested() | 203 | 模型加载请求处理 |
| _on_model_test_requested() | 278 | 模型测试请求处理 |
| closeEvent() | 364 | 窗口关闭事件 |

**关键信号**:
- `window_closing` - 窗口关闭信号 (98)

**关键控件**:
- `status_label` - 状态标签 (128)
- `recording_button` - 录音按钮 (134)
- `settings_button` - 设置按钮 (139)
- `minimize_button` - 最小化按钮 (144)

**需要迁移的 PyQt6 特性**:
- `Qt.WindowType.Window` (113)
- `Qt.WindowType.WindowCloseButtonHint` (113)
- `Qt.AlignmentFlag.AlignCenter` (129)

---

### RecordingOverlay - 录音叠加窗口
**文件**: `/src/sonicinput/ui/recording_overlay.py`

#### 核心类
| 功能 | 行号 | 说明 |
|------|------|------|
| 类定义 | 14 | QWidget 子类，无边框浮窗 |
| __new__() | 33 | Qt 安全单例模式 |
| __init__() | 46 | 构造函数，多阶段初始化 |
| setup_overlay_ui() | 448 | UI 布局设置 |

#### 信号定义（线程安全）
| 信号 | 行号 | 说明 |
|------|------|------|
| show_recording_requested | 24 | 显示录音请求 |
| hide_recording_requested | 25 | 隐藏录音请求 |
| set_status_requested | 26 | 设置状态请求 |
| update_waveform_requested | 27 | 波形更新请求 |
| update_audio_level_requested | 28 | 音频级别更新 |
| start_processing_animation_requested | 29 | 启动动画请求 |
| stop_processing_animation_requested | 30 | 停止动画请求 |

#### 公开 API（线程安全）
| 方法 | 行号 | 说明 |
|------|------|------|
| show_recording() | 548 | 显示录音状态 |
| hide_recording() | 598 | 隐藏录音状态 |
| show_completed() | 602 | 显示完成状态 |
| show_processing() | 616 | 显示处理状态 |
| update_waveform() | 706 | 更新波形 |
| update_audio_level() | 780 | 更新音频级别 |
| set_status_text() | 810 | 设置状态文本 |
| start_processing_animation() | 1168 | 启动处理动画 |
| stop_processing_animation() | 1178 | 停止处理动画 |

#### 内部实现槽（主线程执行）
| 方法 | 行号 | 说明 |
|------|------|------|
| _show_recording_impl() | 552 | 显示实现 |
| _hide_recording_impl() | 629 | 隐藏实现 |
| _update_waveform_impl() | 710 | 波形更新实现 |
| _update_audio_level_impl() | 784 | 音频级别实现 |
| _set_status_text_impl() | 814 | 状态文本实现 |

#### 事件处理
| 事件 | 行号 | 说明 |
|------|------|------|
| keyPressEvent() | 910 | 键盘事件（Escape、Space） |
| mousePressEvent() | 890 | 鼠标按下（拖拽起点） |
| mouseMoveEvent() | 896 | 鼠标移动（拖拽） |
| mouseReleaseEvent() | 902 | 鼠标释放（保存位置） |
| paintEvent() | 1207 | 自定义绘制（呼吸效果） |

#### 定时器管理
| 方法 | 行号 | 说明 |
|------|------|------|
| _safe_timer_connect() | 162 | 安全连接定时器 |
| _safe_timer_start() | 178 | 安全启动定时器 |
| _safe_timer_stop() | 199 | 安全停止定时器 |
| update_recording_time() | 860 | 更新录音时间 |
| update_breathing() | 1189 | 更新呼吸效果 |

#### 关键属性
| 属性 | 行号 | 说明 |
|------|------|------|
| is_recording | 74 | 录音状态 |
| recording_duration | 76 | 录音时长（秒） |
| breathing_phase | 125 | 呼吸动画阶段 |
| is_processing | 128 | 处理状态 |
| current_audio_level | 478 | 当前音频级别 |

#### 关键布局和组件
| 项目 | 行号 | 说明 |
|------|------|------|
| background_frame | 456 | 背景框架（QFrame） |
| status_indicator | 472 | 状态指示器 |
| audio_level_bars | 477 | 音频级别条列表 |
| time_label | 497 | 录音时间标签 |
| close_button | 508 | 关闭按钮 |
| position_manager | 542 | 位置管理器 |

#### 需要迁移的 PyQt6 特性
- `Qt.WindowType.FramelessWindowHint` (85)
- `Qt.WindowType.WindowStaysOnTopHint` (86)
- `Qt.WindowType.Tool` (87)
- `Qt.WindowType.WindowDoesNotAcceptFocus` (88)
- `Qt.WidgetAttribute.WA_TranslucentBackground` (91)
- `Qt.Key.Key_Escape` (912)
- `Qt.Key.Key_Space` (914)
- `Qt.MouseButton.LeftButton` (892, 898)

---

### SettingsWindow - 设置窗口
**文件**: `/src/sonicinput/ui/settings_window.py`

| 功能 | 行号 | 说明 |
|------|------|------|
| WheelEventFilter 类 | 17 | 滚轮事件过滤器 |
| SettingsWindow 类 | 37 | 设置窗口主类 |
| __init__() | 48 | 构造函数 |
| setup_ui() | 93 | 主 UI 设置 |
| _install_wheel_filters() | 119 | 安装滚轮过滤器 |
| test_api_connection() | 251 | API 连接测试（异步） |
| _check_api_test_status() | 385 | 检查测试状态 |
| apply_settings() | 496 | 应用设置 |
| refresh_gpu_info() | 786 | 刷新 GPU 信息 |
| refresh_model_status() | 901 | 刷新模型状态 |

**关键事件过滤器**:
- `WheelEventFilter.eventFilter()` (20) - 阻止滚轮事件

**需要迁移的 PyQt6 特性**:
- `QEvent.Type.Wheel` (31)
- `Qt.CheckState.Checked` (48-51)

---

## 2. 自定义组件

### StatusIndicator - 状态指示器
**文件**: `/src/sonicinput/ui/overlay/components/status_indicator.py`

| 项目 | 行号 | 说明 |
|------|------|------|
| 类定义 | 8 | 状态指示器自定义控件 |
| 状态常量 | 11-15 | STATE_IDLE, STATE_RECORDING 等 |
| __init__() | 17 | 构造函数 |
| paintEvent() | 32 | 自定义绘制 |
| set_state() | 27 | 设置状态方法 |

**4 种状态**:
- `STATE_IDLE = 0` - 暗红色
- `STATE_RECORDING = 1` - 鲜红色（#F44336）
- `STATE_PROCESSING = 2` - 黄色（#FFC107）
- `STATE_COMPLETED = 3` - 绿色（#4CAF50）

---

### CloseButton - 关闭按钮
**文件**: `/src/sonicinput/ui/overlay/components/close_button.py`

| 项目 | 行号 | 说明 |
|------|------|------|
| 类定义 | 8 | 自定义关闭按钮 |
| __init__() | 11 | 构造函数 |
| paintEvent() | 20 | 自定义绘制（×符号） |
| enterEvent() | 52 | 鼠标进入 |
| leaveEvent() | 57 | 鼠标离开 |
| mousePressEvent() | 62 | 鼠标按下 |

**需要迁移的 PyQt6 特性**:
- `Qt.CursorShape.PointingHandCursor` (15)
- `Qt.MouseButton.LeftButton` (64)

---

### AnimationController - 动画控制器
**文件**: `/src/sonicinput/ui/recording_overlay_utils/animation_controller.py`

| 项目 | 行号 | 说明 |
|------|------|------|
| 类定义 | 14 | 动画管理器 |
| __init__() | 23 | 初始化动画对象 |
| start_breathing_animation() | 50 | 启动呼吸动画 |
| stop_breathing_animation() | 61 | 停止呼吸动画 |
| update_breathing() | 69 | 更新呼吸效果 |
| paint_breathing_effect() | 87 | 绘制呼吸效果 |
| ensure_animation_state() | 134 | 确保动画状态一致 |

**关键动画对象**:
- `breathing_timer` - QTimer (34)
- `fade_animation` - QPropertyAnimation (38)
- `status_animation` - QPropertyAnimation (44)

**需要迁移的 PyQt6 特性**:
- `QEasingCurve.Type.InOutQuad` (40)
- `QEasingCurve.Type.InOutSine` (46)

---

## 3. 系统托盘

### TrayController - 托盘控制器
**文件**: `/src/sonicinput/ui/components/system_tray/tray_controller.py`

| 项目 | 行号 | 说明 |
|------|------|------|
| 类定义 | 23 | 托盘业务逻辑控制器 |
| __init__() | 35 | 构造函数 |
| _do_initialize() | 61 | 初始化 |
| _connect_widget_signals() | 164 | 连接信号 |
| _subscribe_to_events() | 175 | 订阅应用事件 |
| _on_icon_activated() | 239 | 托盘图标激活处理 |
| _on_menu_action() | 280 | 菜单动作处理 |
| _update_ui_for_recording_state() | 410 | 更新录音状态 UI |
| show_notification() | 511 | 显示通知 |

**关键信号**:
- `show_settings_requested` (31)
- `toggle_recording_requested` (32)
- `exit_application_requested` (33)

**关键枚举处理**:
- 托盘激活原因处理 (248) - 需要 `.value` 转换

---

### TrayWidget - 托盘 Widget
**文件**: `/src/sonicinput/ui/components/system_tray/tray_widget.py`

| 项目 | 行号 | 说明 |
|------|------|------|
| 类定义 | - | 托盘 UI 组件 |
| __init__() | - | 创建托盘图标和菜单 |
| _on_icon_activated() | - | 处理图标激活 |
| show_message() | - | 显示托盘通知 |

---

## 4. 标签页系统

### BaseTab - 基类
**文件**: `/src/sonicinput/ui/settings_tabs/base_tab.py`

| 项目 | 行号 | 说明 |
|------|------|------|
| 类定义 | 10 | 标签页基类 |
| __init__() | 16 | 构造函数 |
| create() | 28 | 创建 UI |
| _setup_ui() | 39 | 设置 UI（子类实现） |
| load_config() | 43 | 加载配置（子类实现） |
| save_config() | 51 | 保存配置（子类实现） |
| _get_nested_config() | 59 | 获取嵌套配置 |
| _set_nested_config() | 78 | 设置嵌套配置 |

### 具体标签页
**文件**: `/src/sonicinput/ui/settings_tabs/`

| 文件 | 功能 | 关键方法 |
|------|------|---------|
| general_tab.py | 通用设置 | _setup_ui(), load_config(), save_config() |
| hotkey_tab.py | 快捷键设置 | - |
| whisper_tab.py | 语音模型设置 | - |
| audio_tab.py | 音频设置 | - |
| input_tab.py | 输入方法设置 | - |
| ui_tab.py | UI 外观设置 | - |

---

## 5. 线程相关

### ModelTestThread - 模型测试线程
**文件**: `/src/sonicinput/ui/main_window.py`

| 项目 | 行号 | 说明 |
|------|------|------|
| 类定义 | 11 | QThread 子类 |
| __init__() | 17 | 构造函数 |
| run() | 21 | 线程主函数 |
| progress_update 信号 | 14 | 进度更新 |
| test_complete 信号 | 15 | 测试完成 |

**关键信号**:
- `progress_update = pyqtSignal(str)` (14)
- `test_complete = pyqtSignal(bool, dict, str)` (15)

---

### WhisperWorkerThread
**文件**: `/src/sonicinput/speech/whisper_worker_thread.py`

Whisper 语音识别在独立线程中运行，通过信号与主线程通信。

---

## 6. 关键信号与槽连接

### 信号连接总览

**RecordingOverlay**:
```python
# 行 143-151：连接线程安全信号
self.show_recording_requested.connect(self._show_recording_impl)
self.hide_recording_requested.connect(self._hide_recording_impl)
self.set_status_requested.connect(self._set_status_text_impl)
self.update_waveform_requested.connect(self._update_waveform_impl)
self.update_audio_level_requested.connect(self._update_audio_level_impl)
self.start_processing_animation_requested.connect(self._start_processing_animation_impl)
self.stop_processing_animation_requested.connect(self._stop_processing_animation_impl)
```

**MainWindow**:
```python
# 行 135-146：按钮连接
self.recording_button.clicked.connect(self.toggle_recording)
self.settings_button.clicked.connect(self.show_settings)
self.minimize_button.clicked.connect(self.hide)

# 行 192-194：设置窗口信号
self._settings_window.model_load_requested.connect(self._on_model_load_requested)
self._settings_window.model_unload_requested.connect(self._on_model_unload_requested)
self._settings_window.model_test_requested.connect(self._on_model_test_requested)
```

**SettingsWindow**:
```python
# 行 161-179：底部按钮
self.reset_button.clicked.connect(self.reset_current_tab)
self.apply_button.clicked.connect(self.apply_settings)
self.ok_button.clicked.connect(self.accept_settings)
self.cancel_button.clicked.connect(self.close)
```

---

## 7. 关键枚举使用位置

### Qt.Key 枚举
- `Qt.Key.Key_Escape` - recording_overlay.py:912
- `Qt.Key.Key_Space` - recording_overlay.py:914

### Qt.MouseButton 枚举
- `Qt.MouseButton.LeftButton` - close_button.py:64, recording_overlay.py:892,898

### Qt.WindowType 枚举
- `Qt.WindowType.FramelessWindowHint` - recording_overlay.py:85
- `Qt.WindowType.WindowStaysOnTopHint` - recording_overlay.py:86
- `Qt.WindowType.Tool` - recording_overlay.py:87
- `Qt.WindowType.WindowDoesNotAcceptFocus` - recording_overlay.py:88
- `Qt.WindowType.Window` - main_window.py:113
- `Qt.WindowType.WindowCloseButtonHint` - main_window.py:113

### Qt.WidgetAttribute 枚举
- `Qt.WidgetAttribute.WA_TranslucentBackground` - recording_overlay.py:91

### Qt.AlignmentFlag 枚举
- `Qt.AlignmentFlag.AlignCenter` - 多个位置，约 25 处
- 主要在 recording_overlay.py 和 main_window.py

### QEvent.Type 枚举
- `QEvent.Type.Wheel` - settings_window.py:31

### QEasingCurve.Type 枚举
- `QEasingCurve.Type.InOutQuad` - recording_overlay.py:115
- `QEasingCurve.Type.InOutSine` - recording_overlay.py:134

---

## 8. 关键 API 调用

### 鼠标事件位置
```python
# 需要从 globalPos() 改为 globalPosition().toPoint()
# recording_overlay.py:893 - mousePressEvent
self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

# recording_overlay.py:899 - mouseMoveEvent
self.move(event.globalPosition().toPoint() - self.drag_position)
```

### 枚举值提取
```python
# tray_controller.py:248
reason_value = reason.value if hasattr(reason, 'value') else int(reason)
```

---

## 9. 样式表使用

### 动态样式
```python
# recording_overlay.py - 背景框架
self.background_frame.setStyleSheet("""
    QFrame#recordingOverlayFrame {
        background-color: #303030;
        border-radius: 12px;
    }
""")

# recording_overlay.py - 时间标签
self.time_label.setStyleSheet("""
    QLabel {
        color: #CCCCCC;
        background: transparent;
    }
""")

# 音频级别条（动态）
bar.setStyleSheet(f"""
    QLabel {{
        background-color: {color};
        border-radius: 2px;
    }}
""")
```

---

## 10. 快速查找指南

### 我想找...

**所有 PyQt6 枚举**:
```bash
grep -r "Qt\.[A-Z]" src/sonicinput/ui --include="*.py" | grep -v "Qt\.QtCore\|Qt\.QtGui\|Qt\.QtWidgets"
```

**所有信号定义**:
```bash
grep -r "pyqtSignal" src/sonicinput/ui --include="*.py"
```

**所有信号连接**:
```bash
grep -r "\.connect(" src/sonicinput/ui --include="*.py"
```

**所有事件处理器**:
```bash
grep -r "def.*Event(" src/sonicinput/ui --include="*.py"
```

**所有定时器**:
```bash
grep -r "QTimer\|timeout" src/sonicinput/ui --include="*.py"
```

**所有样式表**:
```bash
grep -r "setStyleSheet\|stylesheet" src/sonicinput/ui --include="*.py"
```

---

**最后更新**: 2025-10-28
**版本**: 1.0
**用于**: SonicInput PyQt6 迁移参考

