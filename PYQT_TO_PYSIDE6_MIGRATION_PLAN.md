# PyQt6 → PySide6 迁移计划

**项目**: SonicInput
**日期**: 2025-10-28
**状态**: 📋 规划阶段

---

## 📊 调查总结

### 影响范围
- **受影响文件**: 38 个 Python 文件
- **PyQt6 导入**: 90+ 处
- **使用的 Qt 模块**: 3 个（QtWidgets, QtCore, QtGui）
- **使用的 Qt 类**: 17+ 个
- **UI 代码总行数**: 3,984 行

### 核心依赖
```toml
# pyproject.toml (当前)
dependencies = [
    "PyQt6>=6.6.0",
    "qt-material>=2.17",
]
```

---

## 🎯 迁移目标

### 为什么迁移到 PySide6？
- ✅ **LGPL 许可证** - 更宽松的商业使用条款
- ✅ **官方支持** - Qt Company 官方维护
- ✅ **API 兼容** - 与 PyQt6 高度相似（95%+）
- ✅ **长期维护** - 更好的长期支持保证

### 预期结果
- 所有 PyQt6 导入替换为 PySide6
- 所有 PyQt6 特有 API 替换为 PySide6 等价物
- 依赖配置更新
- 功能完全兼容，无回归

---

## 📝 详细迁移清单

### 🔴 第一优先级：核心文件（4 个）

#### 1. `src/sonicinput/ui/recording_overlay.py` (1,247 行)
**复杂度**: ⭐⭐⭐⭐⭐ 最高
**关键位置**:
- **行 4-7**: PyQt6 导入
- **行 24-31**: 8 个自定义信号（`pyqtSignal` → `Signal`）
- **行 920-921**: 动画系统（QPropertyAnimation）
- **行 1017**: 自定义 paintEvent
- **行 1213**: 鼠标事件处理

**迁移重点**:
```python
# 前
from PyQt6.QtCore import pyqtSignal, Qt
show_recording_requested = pyqtSignal()

# 后
from PySide6.QtCore import Signal, Qt
show_recording_requested = Signal()
```

#### 2. `src/sonicinput/ui/settings_window.py` (1,240 行)
**复杂度**: ⭐⭐⭐⭐⭐
**关键位置**:
- **行 3-7**: PyQt6 导入
- **行 17-34**: 事件过滤器（QObject.eventFilter）
- **行 371**: 标签页管理
- **行 846, 851**: 信号槽连接
- **行 1036**: 窗口关闭事件

#### 3. `src/sonicinput/ui/main_window.py` (377 行)
**复杂度**: ⭐⭐⭐⭐
**关键位置**:
- **行 3-4**: PyQt6 导入
- **行 11-76**: ModelTestThread（QThread 子类）
- **行 225**: QMessageBox 使用
- **行 254**: QProgressDialog

#### 4. `src/sonicinput/ui/components/system_tray/tray_controller.py` (557 行)
**复杂度**: ⭐⭐⭐⭐
**关键位置**:
- **行 36-40**: QSystemTrayIcon 可用性检查
- **行 100+**: 系统托盘菜单构建

---

### 🟡 第二优先级：组件文件（10 个）

| 文件 | 行数 | 导入数 | 关键特性 |
|------|------|--------|---------|
| `components/dialogs/settings_dialog.py` | 800+ | 5 | QDialog, 标签页 |
| `components/dialogs/model_loader_dialog.py` | 200+ | 4 | QThread, 进度显示 |
| `components/system_tray/tray_widget.py` | 400+ | 5 | QSystemTrayIcon, QMenu |
| `overlay/components/status_indicator.py` | 60 | 3 | 自定义绘制 |
| `overlay/components/close_button.py` | 67 | 3 | QPainter |
| `recording_overlay_utils/animation_controller.py` | 208 | 4 | QPropertyAnimation |
| `recording_overlay_utils/audio_visualizer.py` | 150+ | 3 | QPainter, 实时绘制 |
| `controllers/animation_engine.py` | 200+ | 4 | 动画管理 |
| `components/dialogs/tabs/base_tab.py` | 100+ | 2 | QWidget 基类 |
| `utils/icon_utils.py` | 50 | 2 | QIcon, QPixmap |

---

### 🟢 第三优先级：设置标签页（8 个）

所有位于 `components/dialogs/tabs/` 目录：
- `general_tab.py` (3 导入)
- `hotkeys_tab.py` (3 导入)
- `audio_tab.py` (3 导入)
- `api_tab.py` (3 导入)
- `speech_tab.py` (3 导入)
- `ui_tab.py` (3 导入)
- `logging_tab.py` (3 导入)

**共性**: 所有继承自 `BaseTab`，主要使用标准控件（QLabel, QLineEdit, QComboBox 等）

---

### 🔵 第四优先级：工具和管理器（16 个）

简单文件，每个 1-2 个导入：
- `recording_overlay_utils/position_manager.py`
- `recording_overlay_utils/timer_manager.py`
- `recording_overlay_utils/singleton_manager.py`
- 其他工具类...

---

## 🔧 主要 API 变更

### 1. 信号和槽机制 ⭐⭐⭐⭐⭐ 最重要

```python
# PyQt6
from PyQt6.QtCore import pyqtSignal, pyqtSlot

class MyWidget(QWidget):
    my_signal = pyqtSignal(str, int)

    @pyqtSlot()
    def my_slot(self):
        pass

# PySide6
from PySide6.QtCore import Signal, Slot

class MyWidget(QWidget):
    my_signal = Signal(str, int)

    @Slot()
    def my_slot(self):
        pass
```

**影响**: 所有 38 个文件（90+ 处）

---

### 2. 枚举访问方式 ⭐⭐⭐⭐

```python
# PyQt6
Qt.AlignmentFlag.AlignCenter
Qt.Key.Key_Escape
QSystemTrayIcon.ActivationReason.Trigger

# PySide6 (相同)
Qt.AlignmentFlag.AlignCenter
Qt.Key.Key_Escape
QSystemTrayIcon.ActivationReason.Trigger
```

**好消息**: PyQt6 和 PySide6 在枚举方面已经统一！✅

---

### 3. 鼠标事件 API ⭐⭐⭐

```python
# PyQt6
def mousePressEvent(self, event):
    pos = event.globalPosition().toPoint()  # 新 API

# PySide6 (相同)
def mousePressEvent(self, event):
    pos = event.globalPosition().toPoint()  # 相同
```

**影响**: `recording_overlay.py`, `close_button.py` 等（约 5 处）

---

### 4. QThread 使用 ⭐⭐

```python
# PyQt6 & PySide6 (相同)
class WorkerThread(QThread):
    finished = Signal()  # 唯一变化：pyqtSignal → Signal

    def run(self):
        # 工作代码
        self.finished.emit()
```

**影响**: `main_window.py` 的 ModelTestThread，`model_loader_dialog.py`

---

### 5. qt-material 兼容性 ⭐⭐⭐

```python
# 当前 (PyQt6)
from qt_material import apply_stylesheet
apply_stylesheet(qt_app, theme='dark_cyan.xml')

# PySide6
# ⚠️ qt-material 2.17 已支持 PySide6！
from qt_material import apply_stylesheet
apply_stylesheet(qt_app, theme='dark_cyan.xml')
# 无需更改，但需确认 qt-material 配置正确
```

**依赖更新**:
```toml
dependencies = [
    "PySide6>=6.6.0",
    "qt-material>=2.17",  # 已支持 PySide6
]
```

---

## 🚀 迁移执行计划

### 阶段 0: 准备工作 (30 分钟)

1. **创建迁移分支**
```bash
git checkout -b feature/migrate-to-pyside6
git push -u origin feature/migrate-to-pyside6
```

2. **备份关键文件**
```bash
# 自动备份由 git 管理，额外创建快照
git tag pre-pyside6-migration
```

3. **更新依赖**
```bash
# 编辑 pyproject.toml
uv add "PySide6>=6.6.0"
uv remove PyQt6
uv sync
```

---

### 阶段 1: 自动批量替换 (1-2 小时)

#### 1.1 导入语句替换

使用 IDE 全局替换（正则表达式）:

```regex
# 查找
from PyQt6\.(QtWidgets|QtCore|QtGui)

# 替换为
from PySide6.$1
```

**或使用 sed (Windows PowerShell)**:
```powershell
Get-ChildItem -Recurse -Filter *.py | ForEach-Object {
    (Get-Content $_.FullName) -replace 'from PyQt6\.', 'from PySide6.' |
    Set-Content $_.FullName
}
```

#### 1.2 信号槽名称替换

```regex
# 查找: pyqtSignal
# 替换: Signal

# 查找: pyqtSlot
# 替换: Slot
```

**验证点**: 运行 `grep -r "pyqtSignal" src/` 应返回空

---

### 阶段 2: 手动修复和验证 (2-3 小时)

#### 2.1 检查信号定义（38 个文件）

**自动化检查脚本**:
```bash
# 检查所有 Signal 定义
grep -rn "= Signal(" src/sonicinput/ui/
```

**手动验证重点**:
- `recording_overlay.py`: 8 个信号
- `settings_window.py`: 6 个信号
- `model_loader_dialog.py`: 2 个信号

#### 2.2 检查 QThread 子类（2 处）

**位置**:
- `main_window.py:11-76` (ModelTestThread)
- `model_loader_dialog.py` (ModelLoaderThread)

**验证**:
```python
# 确认 Signal 导入
from PySide6.QtCore import Signal

class ModelTestThread(QThread):
    success = Signal(str)  # ✅ 正确
    error = Signal(str)    # ✅ 正确
```

#### 2.3 检查事件处理器（12+ 处）

**关键文件**:
- `recording_overlay.py`: paintEvent, mousePressEvent, mouseReleaseEvent
- `close_button.py`: paintEvent, enterEvent, leaveEvent
- `settings_window.py`: eventFilter, closeEvent

**验证**: 确保所有事件方法签名正确

---

### 阶段 3: 依赖和配置更新 (30 分钟)

#### 3.1 更新 pyproject.toml

```toml
# 前
dependencies = [
    "PyQt6>=6.6.0",
    "qt-material>=2.17",
]

# 后
dependencies = [
    "PySide6>=6.6.0",
    "qt-material>=2.17",  # 已支持 PySide6
]
```

#### 3.2 更新环境验证

**文件**: `src/sonicinput/utils/environment_validator.py`

```python
# 更新验证方法名称和导入
def validate_pyside6_installation(self) -> Tuple[bool, Dict[str, Any]]:
    try:
        import PySide6
        from PySide6 import QtCore, QtGui, QtWidgets
        # ... 验证逻辑
```

#### 3.3 更新文档

需要更新的文档：
- `README.md`: 依赖说明
- `CLAUDE.md`: 架构文档
- `pyproject.toml`: 项目元数据

---

### 阶段 4: 测试和验证 (2-3 小时)

#### 4.1 单元测试

```bash
# 运行所有测试
uv run pytest tests/ -v

# 预期通过的测试
- test_bug_regression.py (所有回归测试)
- tests/mocks/ (所有 mock 测试)
```

#### 4.2 功能测试清单

| 功能 | 测试方法 | 优先级 |
|------|---------|--------|
| **应用启动** | `uv run python app.py --gui` | ⭐⭐⭐⭐⭐ |
| **系统托盘** | 检查右下角托盘图标 | ⭐⭐⭐⭐⭐ |
| **设置窗口** | 双击托盘图标 | ⭐⭐⭐⭐ |
| **录音悬浮窗** | 按 F12 开始录音 | ⭐⭐⭐⭐⭐ |
| **音频可视化** | 说话时波形显示 | ⭐⭐⭐ |
| **AI 优化** | 录音后文本优化 | ⭐⭐⭐⭐ |
| **快捷键** | 所有配置的热键 | ⭐⭐⭐⭐ |
| **主题切换** | 设置 → UI → Theme | ⭐⭐ |
| **多显示器** | 跨显示器拖动窗口 | ⭐⭐⭐ |
| **窗口位置持久化** | 关闭重启后位置保持 | ⭐⭐ |
| **模型测试** | 设置 → Speech → Test Model | ⭐⭐⭐⭐ |
| **API 测试** | 设置 → AI → Test API | ⭐⭐⭐ |

#### 4.3 性能测试

```bash
# 启动时间测试
time uv run python app.py --gui

# 录音性能测试
# 1. 录音 30 秒
# 2. 检查 RTF (Real-Time Factor) < 0.5
# 3. 检查内存使用 < 500 MB
```

#### 4.4 兼容性测试

**Windows 11 特定测试**:
- ✅ 高 DPI 显示支持
- ✅ 深色模式主题
- ✅ 系统托盘行为（右键菜单、双击）
- ✅ 全局快捷键（多修饰键）

---

### 阶段 5: 问题修复和优化 (1-2 小时)

#### 5.1 常见问题和解决方案

**问题 1: qt-material 不识别 PySide6**
```bash
# 解决方案：确保 qt-material >= 2.17
uv add "qt-material>=2.17"
```

**问题 2: 信号槽连接失败**
```python
# 检查信号定义
# 前
my_signal = pyqtSignal(str, int)

# 后 - 确保参数类型正确
my_signal = Signal(str, int)
```

**问题 3: QSystemTrayIcon 不显示**
```python
# 确保 PySide6 系统托盘检查
from PySide6.QtWidgets import QSystemTrayIcon
if not QSystemTrayIcon.isSystemTrayAvailable():
    print("System tray not available")
```

**问题 4: 自定义绘制问题**
```python
# paintEvent 中确保正确的 QPainter 使用
def paintEvent(self, event):
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    # ... 绘制代码
    painter.end()  # ⚠️ 必须调用
```

---

## 📋 验收标准

### ✅ 必须通过的检查

1. **代码检查**
   - [ ] 无 `PyQt6` 导入残留
   - [ ] 无 `pyqtSignal` / `pyqtSlot` 残留
   - [ ] 所有 PySide6 导入正确
   - [ ] Ruff 检查通过：`uv run ruff check src/`
   - [ ] MyPy 类型检查通过：`uv run mypy src/`

2. **依赖检查**
   - [ ] `pyproject.toml` 已更新
   - [ ] `uv.lock` 已更新
   - [ ] `uv sync` 无错误

3. **功能检查**
   - [ ] 所有 12 项功能测试通过
   - [ ] 无 UI 闪烁或冻结
   - [ ] 录音流程完整无误
   - [ ] 系统托盘正常工作

4. **性能检查**
   - [ ] 启动时间 < 5 秒
   - [ ] 录音 RTF < 0.5
   - [ ] 内存使用正常（< 500 MB）

5. **文档检查**
   - [ ] README.md 已更新
   - [ ] CLAUDE.md 已更新
   - [ ] 迁移记录已归档

---

## 📊 工作量估算

| 阶段 | 预计时间 | 复杂度 | 风险等级 |
|------|---------|--------|---------|
| 0. 准备工作 | 0.5 小时 | ⭐ | 🟢 低 |
| 1. 批量替换 | 1-2 小时 | ⭐⭐ | 🟢 低 |
| 2. 手动修复 | 2-3 小时 | ⭐⭐⭐⭐ | 🟡 中 |
| 3. 配置更新 | 0.5 小时 | ⭐ | 🟢 低 |
| 4. 测试验证 | 2-3 小时 | ⭐⭐⭐ | 🟡 中 |
| 5. 问题修复 | 1-2 小时 | ⭐⭐⭐ | 🟡 中 |
| **总计** | **7-11 小时** | ⭐⭐⭐ | 🟡 中等 |

**最佳执行方式**: 连续 1-2 天完成，避免中断导致上下文丢失

---

## 🎯 关键成功因素

### ✅ 降低风险的策略

1. **增量迁移** - 分阶段提交，每阶段可独立验证
2. **自动化优先** - 使用脚本和正则表达式减少人工错误
3. **测试驱动** - 每修复一个模块立即测试
4. **文档同步** - 边迁移边更新文档
5. **回滚计划** - 保持 git 标签，随时可回退

### ⚠️ 潜在风险点

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| qt-material 不兼容 | 🔴 高 | 预先测试 qt-material 2.17 + PySide6 |
| 信号槽连接错误 | 🔴 高 | 逐文件验证，运行时测试 |
| 系统托盘失效 | 🟡 中 | Windows 11 实机测试 |
| 性能回退 | 🟢 低 | PySide6 性能与 PyQt6 相当 |
| 第三方工具不兼容 | 🟢 低 | 所有工具都支持 PySide6 |

---

## 📚 参考资料

### 官方文档
- [PySide6 文档](https://doc.qt.io/qtforpython-6/)
- [PyQt6 → PySide6 迁移指南](https://doc.qt.io/qtforpython-6/porting_from_pyqt.html)
- [qt-material GitHub](https://github.com/UN-GCPDS/qt-material)

### 社区资源
- Stack Overflow: "PyQt6 to PySide6 migration"
- Reddit r/Python: PySide6 discussions
- Qt Forum: PySide6 专区

---

## 📝 迁移检查清单

### 代码修改
- [ ] 所有 `from PyQt6.` → `from PySide6.`
- [ ] 所有 `pyqtSignal` → `Signal`
- [ ] 所有 `pyqtSlot` → `Slot`
- [ ] 验证所有信号定义（38 个文件）
- [ ] 验证 QThread 子类（2 处）
- [ ] 验证事件处理器（12+ 处）
- [ ] 验证 QPainter 使用（5+ 处）

### 依赖更新
- [ ] `pyproject.toml` 更新
- [ ] 运行 `uv sync`
- [ ] 验证 `uv.lock` 生成
- [ ] 确认 qt-material >= 2.17

### 测试验证
- [ ] 单元测试全部通过
- [ ] 12 项功能测试全部通过
- [ ] 性能基准测试通过
- [ ] Windows 11 兼容性测试

### 文档更新
- [ ] README.md
- [ ] CLAUDE.md
- [ ] 本迁移计划归档
- [ ] 版本历史更新

### 质量检查
- [ ] `uv run ruff check src/` 通过
- [ ] `uv run mypy src/` 通过
- [ ] 无编译器警告
- [ ] 代码审查完成

### Git 操作
- [ ] 所有修改已提交
- [ ] 提交信息清晰
- [ ] 创建 PR
- [ ] CI/CD 通过（如有）

---

## 🎉 迁移完成标志

当以下所有条件满足时，迁移成功：

1. ✅ 所有测试通过（单元 + 功能）
2. ✅ 应用可正常启动和使用
3. ✅ 无性能回退
4. ✅ 文档已更新
5. ✅ 代码质量检查通过
6. ✅ 团队审查通过（如适用）

---

**最后更新**: 2025-10-28
**计划状态**: ✅ 完成，待执行
**预计完成时间**: 1-2 天
**负责人**: 开发团队

---

## 🔗 相关文档

- [PyQt6 使用报告](./PyQt6_Usage_Report.md) - 详细代码分析
- [PyQt6 代码定位索引](./PyQt6_Code_Location_Index.md) - 快速查找
- [UI 组件迁移分析](./UI_COMPONENTS_MIGRATION_ANALYSIS.md) - 架构分析
- [迁移执行总结](./MIGRATION_EXECUTIVE_SUMMARY.md) - 管理视角

---

**祝迁移顺利！** 🚀
