"""Recording Overlay - Main module and utilities

This package provides the RecordingOverlay class and its modular utilities.

Main Class:
- RecordingOverlay: The main recording overlay window (imported from parent module)

Utility Components:
- SingletonMixin: Thread-safe singleton pattern implementation
- TimerManager: QTimer lifecycle management utilities
- AnimationController: Animation management for overlay effects
- AudioVisualizer: Audio level visualization
- PositionManager: Window positioning and persistence

Usage:
    from sonicinput.ui.recording_overlay import RecordingOverlay

Note:
    The RecordingOverlay class is re-exported from the parent module
    for backward compatibility.
"""

# Import utility components
from .animation_controller import AnimationController
from .audio_visualizer import AudioVisualizer
from .position_manager import PositionManager
from .singleton_manager import SingletonMixin
from .timer_manager import TimerManager

# NOTE: RecordingOverlay import removed to avoid circular dependency
# RecordingOverlay now imports PositionManager, so we cannot import RecordingOverlay here
# Users should import RecordingOverlay directly from: from sonicinput.ui.recording_overlay import RecordingOverlay

__all__ = [
    # "RecordingOverlay",  # Removed to avoid circular import
    "SingletonMixin",
    "TimerManager",
    "AnimationController",
    "AudioVisualizer",
    "PositionManager",
]
