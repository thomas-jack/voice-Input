# PyQt6 Code Location Index

## Quick Reference Guide - Find PyQt Code Quickly

---

## MOST IMPORTANT LOCATIONS (Start Here)

### Recording Overlay - Complex Animation System
**File**: `C:\Users\Oxidane\Documents\projects\New folder\src\sonicinput\ui\recording_overlay.py`
- **Lines 4-7**: Import statements
  - QtWidgets: QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect
  - QtCore: Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
  - QtGui: QFont, QColor
- **Lines 14-31**: Class definition with 8 custom signals
- **Lines 24-31**: Signal definitions for UI state management
- **Line 920**: QApplication import (late binding)
- **Line 921**: QGuiApplication import (late binding)
- **Line 1017**: QGuiApplication import (screen access)
- **Line 1213**: Graphics imports (QPainter, QBrush, QRadialGradient)
- **Key Features**: Singleton pattern, animations, gradients, custom painting

### Settings Window - Complex Configuration UI
**File**: `C:\Users\Oxidane\Documents\projects\New folder\src\sonicinput\ui\settings_window.py`
- **Lines 3-7**: Import statements
  - QtWidgets: QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QPushButton, etc.
  - QtCore: Qt, pyqtSignal, QObject, QEvent
- **Lines 17-34**: WheelEventFilter class (prevent scroll accidents)
- **Lines 371, 846, 851, 1036**: Conditional QTimer imports (debouncing)
- **Key Features**: Event filtering, multi-tab interface, delayed updates

### Main Window - Application Entry Point
**File**: `C:\Users\Oxidane\Documents\projects\New folder\src\sonicinput\ui\main_window.py`
- **Lines 3-4**: Import statements
  - QtWidgets: QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QSystemTrayIcon, QProgressDialog, QMessageBox
  - QtCore: Qt, pyqtSignal, QThread
- **Lines 11-76**: ModelTestThread (QThread subclass)
  - Line 11: Inherits from QThread
  - Lines 14-15: Signal definitions (progress_update, test_complete)
  - Line 21: Run method (executes in separate thread)
- **Line 225**: QApplication import (get app instance)
- **Line 254**: QTimer import (progress dialog management)
- **Key Features**: Threading, progress dialogs, tray integration

---

## COMPONENT ORGANIZATION BY LAYER

### Layer 1: UI Components (Heavy PyQt Usage)

#### Recording System
- **RecordingOverlay**: `ui/recording_overlay.py` (7 imports, Lines 4-7, 920-921, 1017, 1213)
- **AnimationController**: `ui/recording_overlay_utils/animation_controller.py` (4 imports, Lines 4-6, 11)
- **PositionManager**: `ui/recording_overlay_utils/position_manager.py` (3 imports, Lines 3-4, 10)
- **AudioVisualizer**: `ui/recording_overlay_utils/audio_visualizer.py` (1 import, Line 3)
- **TimerManager**: `ui/recording_overlay_utils/timer_manager.py` (1 import, Line 3)

#### Overlay Components
- **StatusIndicator**: `ui/overlay/components/status_indicator.py` (3 imports, Lines 3-5)
  - Custom painted indicator with Qt enums
- **CloseButton**: `ui/overlay/components/close_button.py` (3 imports, Lines 3-5)
  - Custom button with painting

#### Main Windows
- **MainWindow**: `ui/main_window.py` (4 imports, Lines 3-4, 225, 254)
- **SettingsWindow**: `ui/settings_window.py` (6 imports, Lines 3, 7, 371, 846, 851, 1036)

#### System Tray
- **TrayWidget**: `ui/components/system_tray/tray_widget.py` (5 imports, Lines 7-9, 70-71)
  - Custom gradient icon rendering
- **TrayController**: `ui/components/system_tray/tray_controller.py` (2 imports, Lines 10-11)

#### Dialog Components
- **SettingsDialog**: `ui/components/dialogs/settings_dialog.py` (2 imports, Lines 7, 11)
- **ModelLoaderDialog**: `ui/components/dialogs/model_loader_dialog.py` (3 imports, Lines 7, 9-10)

#### Settings Tabs (New Style - Dialogs)
- **BaseTab**: `ui/components/dialogs/tabs/base_tab.py` (1 import, Line 3)
- **ApiTab**: `ui/components/dialogs/tabs/api_tab.py` (2 imports, Lines 3, 5)
- **AudioTab**: `ui/components/dialogs/tabs/audio_tab.py` (2 imports, Lines 3, 5)
- **GeneralTab**: `ui/components/dialogs/tabs/general_tab.py` (2 imports, Lines 3, 5)
- **HotkeysTab**: `ui/components/dialogs/tabs/hotkeys_tab.py` (2 imports, Lines 3, 5)
- **LoggingTab**: `ui/components/dialogs/tabs/logging_tab.py` (2 imports, Lines 3, 5)
- **SpeechTab**: `ui/components/dialogs/tabs/speech_tab.py` (2 imports, Lines 3, 5)
- **UITab**: `ui/components/dialogs/tabs/ui_tab.py` (2 imports, Lines 3, 5)

#### Settings Tabs (Old Style - Legacy)
- **BaseTab**: `ui/settings_tabs/base_tab.py` (1 import, Line 6)
- **GeneralTab**: `ui/settings_tabs/general_tab.py` (1 import, Line 3)
- **HotkeyTab**: `ui/settings_tabs/hotkey_tab.py` (3 imports, Lines 3, 5, 173)
- **WhisperTab**: `ui/settings_tabs/whisper_tab.py` (1 import, Line 3)
- **AITab**: `ui/settings_tabs/ai_tab.py` (2 imports, Lines 3, 6)
- **AudioTab**: `ui/settings_tabs/audio_tab.py` (1 import, Line 3)
- **InputTab**: `ui/settings_tabs/input_tab.py` (1 import, Line 3)
- **UITab**: `ui/settings_tabs/ui_tab.py` (2 imports, Lines 3, 59)

#### Controllers
- **PositionManager**: `ui/controllers/position_manager.py` (3 imports, Lines 7-9)
- **AnimationEngine**: `ui/controllers/animation_engine.py` (2 imports, Lines 7-8)

#### Visualizers & Audio
- **Visualizer**: `audio/visualizer.py` (4 imports, Lines 4-7)

---

### Layer 2: Infrastructure & Threading

#### Speech Processing
- **WhisperWorkerThread**: `speech/whisper_worker_thread.py` (1 import, Line 9)
  - Uses: QThread, pyqtSignal

#### Core Components
- **LifecycleComponent**: `core/base/lifecycle_component.py` (1 import, Line 11)
  - Uses: QObject (base for signals/slots)
- **UIInterface**: `core/interfaces/ui.py` (1 import, Line 5)
  - Uses: QWidget (protocol definition)

#### Utilities
- **EnvironmentValidator**: `utils/environment_validator.py` (4 imports, Lines 44, 46, 51, 130)
  - Try/except validation of PyQt6 installation
- **IconUtils**: `ui/utils/icon_utils.py` (1 import, Line 8)
  - Uses: QIcon
- **CommonUtils**: `utils/common_utils.py` (1 import, Line 12)
  - Uses: QTimer, QObject

---

## PYQT6 CLASS USAGE QUICK LOOKUP

### By Class Name

#### Core Window Classes
- **QMainWindow**: `main_window.py` (L3), `settings_window.py` (L3)
- **QWidget**: Used in 10+ files as base class
- **QDialog**: `model_loader_dialog.py` (L7), `settings_dialog.py` (L7)

#### Layout Classes
- **QVBoxLayout**: 13 files, primary in settings tabs
- **QHBoxLayout**: 6 files, horizontal arrangement
- **QFormLayout**: 13 files, form field layouts
- **QGroupBox**: 14 files, grouped containers

#### Interactive Widgets
- **QPushButton**: `main_window.py`, `model_loader_dialog.py`
- **QLabel**: Multiple files for text/image display
- **QComboBox**: Settings window (line not specific)
- **QSpinBox**: Settings window
- **QDoubleSpinBox**: Settings window
- **QInputDialog**: `hotkey_tab.py` (Line 173)
- **QFileDialog**: Settings window
- **QMessageBox**: `main_window.py`, `tray_controller.py`
- **QProgressDialog**: `main_window.py` (L3)

#### Animation & Graphics
- **QPropertyAnimation**: `animation_engine.py` (L7), `recording_overlay.py` (L6), `animation_controller.py` (L4)
- **QEasingCurve**: Same files as above
- **QPainter**: `visualizer.py` (L6), `tray_widget.py` (L9), `close_button.py` (L4), `status_indicator.py` (L4), `recording_overlay.py` (L1213), `animation_controller.py` (L5)
- **QBrush**: Graphics files (paired with QPainter)
- **QPen**: Graphics files (paired with QPainter)
- **QColor**: Used throughout for color management
- **QFont**: `recording_overlay.py` (L7), `model_loader_dialog.py` (L10)
- **QRadialGradient**: `recording_overlay.py` (L1213), `animation_controller.py` (L5)
- **QLinearGradient**: `tray_widget.py` (L71)

#### System Integration
- **QSystemTrayIcon**: `tray_widget.py` (L7), `tray_controller.py` (L11), `main_window.py` (L3), `environment_validator.py` (L130)
- **QMenu**: `tray_widget.py` (L7)
- **QAction**: `tray_widget.py` (L9)

#### Thread & Signal Classes
- **QThread**: `main_window.py` (L4), `whisper_worker_thread.py` (L9)
- **pyqtSignal**: Used in 13+ files for signals
- **QObject**: Base class in 4+ files

#### Screen/Display
- **QApplication**: Used in multiple files (Lines 225 in main_window, 51 in environment_validator, etc.)
- **QGuiApplication**: `recording_overlay.py` (L921, 1017), `recording_overlay_utils/position_manager.py` (L3), `environment_validator.py` (L46)
- **QScreen**: `position_manager.py` (L9), `recording_overlay_utils/position_manager.py` (L3)
- **QRect**: `position_manager.py` (L8)
- **QPoint**: `recording_overlay_utils/position_manager.py` (L4)

#### Other
- **QIcon**: `icon_utils.py` (L8), `tray_widget.py` (L9)
- **QPixmap**: `tray_widget.py` (L9)
- **QGraphicsOpacityEffect**: `animation_engine.py` (L8)
- **QGraphicsDropShadowEffect**: `recording_overlay.py` (L4)
- **QScrollArea**: Settings window
- **QFrame**: Settings window
- **QTabWidget**: Settings window
- **Qt**: Used in 16 files as constants namespace
- **QEvent**: `settings_window.py` (L7) for event filtering
- **QRectF**: `tray_widget.py` (L70) for graphics operations

---

## FINDING SPECIFIC FUNCTIONALITY

### Looking for Signal Definitions?
1. **RecordingOverlay signals**: `recording_overlay.py`, Lines 24-31
2. **ModelTestThread signals**: `main_window.py`, Lines 14-15
3. **All pyqtSignal imports**: Search for "pyqtSignal" - appears in 13+ files

### Looking for Animation Code?
1. **Main animation engine**: `ui/controllers/animation_engine.py`, Lines 7-8
2. **Recording overlay animations**: `recording_overlay.py`, Lines 6, 1213
3. **Recording overlay utils**: `recording_overlay_utils/animation_controller.py`, Lines 4-6

### Looking for Threading Code?
1. **ModelTestThread**: `main_window.py`, Lines 11-76
2. **WhisperWorkerThread**: `speech/whisper_worker_thread.py`, Line 9
3. **QThread imports**: Present in 2 files

### Looking for Custom Painting?
1. **Visualizer**: `audio/visualizer.py`, Lines 6-7
2. **Close Button**: `ui/overlay/components/close_button.py`, Lines 3-5
3. **Status Indicator**: `ui/overlay/components/status_indicator.py`, Lines 3-5
4. **Tray Widget**: `ui/components/system_tray/tray_widget.py`, Lines 70-71, 1213

### Looking for System Tray Code?
1. **Tray Widget**: `ui/components/system_tray/tray_widget.py`, Lines 7-9, 70-71
2. **Tray Controller**: `ui/components/system_tray/tray_controller.py`, Lines 10-11

### Looking for Layout Code?
All settings tabs use QVBoxLayout + QFormLayout pattern:
- **Pattern location**: `ui/settings_tabs/` or `ui/components/dialogs/tabs/`
- **Example files**:
  - `ui/settings_tabs/audio_tab.py`, Line 3
  - `ui/components/dialogs/tabs/audio_tab.py`, Line 3

### Looking for Dialogs?
1. **Model Loader Dialog**: `ui/components/dialogs/model_loader_dialog.py`, Lines 7, 9-10
2. **Settings Dialog**: `ui/components/dialogs/settings_dialog.py`, Lines 7, 11
3. **Event Filter**: `ui/settings_window.py`, Lines 17-34

### Looking for Screen Management?
1. **Position Manager**: `ui/controllers/position_manager.py`, Lines 7-9
2. **Overlay Position Manager**: `ui/recording_overlay_utils/position_manager.py`, Lines 3-4, 10

---

## MODULE IMPORT PATTERNS

### Pattern 1: Direct Import
```python
from PyQt6.QtCore import QTimer, QObject
from PyQt6.QtGui import QIcon
```
**Files**: Simple utility modules
**Examples**: `icon_utils.py`, `timer_manager.py`, `lifecycle_component.py`

### Pattern 2: Multi-line Import
```python
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QLabel, QPushButton, ...
)
from PyQt6.QtCore import Qt, pyqtSignal
```
**Files**: Complex UI components
**Examples**: All settings tabs, main_window.py, settings_window.py

### Pattern 3: Conditional/Late Binding
**Found in**:
- `settings_window.py` (Lines 371, 846, 851, 1036)
- `recording_overlay.py` (Lines 920-921, 1017)
- `hotkey_tab.py` (Line 173)

**Reason**: Lazy loading, avoid circular imports

### Pattern 4: Try/Except Validation
**Found in**: `utils/environment_validator.py` (Lines 44-130)
**Reason**: Environment validation before main app

---

## QUICK STATISTICS

### By File Size (PyQt Import Count)
- **7 imports**: recording_overlay.py
- **6 imports**: settings_window.py
- **5 imports**: tray_widget.py
- **4 imports**: visualizer.py, main_window.py, animation_controller.py, environment_validator.py
- **3 imports**: 7 files
- **2 imports**: 9 files
- **1 import**: 19 files

### By Module
- **QtWidgets**: 38 files (100% of PyQt files)
- **QtCore**: 36 files (94.7%)
- **QtGui**: 15 files (39.5%)

### By Functional Area
- **UI Components**: 23 files (60%)
- **Utilities**: 8 files (21%)
- **Core/Base**: 4 files (11%)
- **Audio/Speech**: 3 files (8%)

---

## HOW TO ADD NEW PyQt COMPONENTS

### Step 1: Choose the Right Base Class
- **For windows**: Inherit from `QMainWindow`
- **For dialogs**: Inherit from `QDialog`
- **For widgets**: Inherit from `QWidget`
- **For items with signals**: Inherit from `QObject`

### Step 2: Add Imports at Top
```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, ...
from PyQt6.QtCore import Qt, pyqtSignal, ...
from PyQt6.QtGui import QColor, QPainter, ...
```

### Step 3: Use Layout Managers
```python
layout = QVBoxLayout()
layout.addWidget(some_widget)
self.setLayout(layout)
```

### Step 4: Define Signals (if needed)
```python
class MyComponent(QObject):
    state_changed = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
```

### Step 5: Connect Signals
```python
self.state_changed.connect(other_component.on_state_changed)
```

---

## DEBUGGING PYQT ISSUES

### Signal Not Firing?
- Check signal definition spelling
- Verify `.connect()` called with correct receiver
- Check receiver method signature matches signal

### UI Not Updating?
- Ensure layout is set with `setLayout()`
- Verify widgets added to layout with `addWidget()`
- Check QTimer is restarted if continuous updates needed

### Slow Rendering?
- Profile with QTimer to find bottleneck
- Reduce QPainter operations in paintEvent
- Cache expensive calculations
- Use QPixmapCache for repeated images

### Threading Issues?
- Only update UI from main thread
- Use signals for cross-thread communication
- Don't block in QThread.run()
- Properly cleanup threads on app exit

---

**Last Updated**: 2025-10-28
**File Count**: 38 files with PyQt6
**Total Imports**: 91 statements
**Quick Reference**: Use Ctrl+F to search this document
