"""UI constants for layout, animation, and styling."""


class UI:
    """UI constants for layout and animation."""

    OVERLAY_WIDTH = 400
    OVERLAY_HEIGHT = 100
    MAIN_WINDOW_WIDTH = 800
    MAIN_WINDOW_HEIGHT = 600
    SETTINGS_WINDOW_WIDTH = 600
    SETTINGS_WINDOW_HEIGHT = 500

    POSITION_PRESETS = {
        "top_left": (50, 50),
        "top_center": (0, 50),
        "top_right": (-50, 50),
        "center_left": (50, 0),
        "center": (0, 0),
        "center_right": (-50, 0),
        "bottom_left": (50, -50),
        "bottom_center": (0, -50),
        "bottom_right": (-50, -50),
    }

    FADE_DURATION = 300
    SLIDE_DURATION = 250
    BOUNCE_DURATION = 400

    COLORS = {
        "primary": "#007ACC",
        "secondary": "#005A9E",
        "success": "#28A745",
        "warning": "#FFC107",
        "error": "#DC3545",
        "info": "#17A2B8",
        "light": "#F8F9FA",
        "dark": "#343A40",
    }

    STATUS_COLORS = {
        "idle": "#6C757D",
        "recording": "#FF4444",
        "processing": "#FFC107",
        "completed": "#28A745",
        "error": "#DC3545",
    }
