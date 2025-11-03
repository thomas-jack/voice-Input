"""RecordingOverlay组件模块

将RecordingOverlay的各个功能拆分为独立的组件类：
- AnimationController: 动画管理
- AudioVisualizer: 音频可视化
- TimerManager: 定时器管理
- OverlayUIBuilder: UI构建
"""

from .animation_controller import AnimationController
from .audio_visualizer import AudioVisualizer
from .timer_manager import TimerManager
from .ui_builder import OverlayUIBuilder

__all__ = ["AnimationController", "AudioVisualizer", "TimerManager", "OverlayUIBuilder"]
