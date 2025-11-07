"""Position management and persistence for RecordingOverlay"""

from PySide6.QtGui import QGuiApplication, QScreen
from PySide6.QtCore import QPoint
from typing import Dict, Any, Optional, Tuple, TYPE_CHECKING
from ...utils import app_logger

if TYPE_CHECKING:
    from ...core.interfaces import IConfigService
    from PySide6.QtWidgets import QWidget


class PositionManager:
    """Manages overlay window positioning and persistence

    Features:
    - Multi-screen support
    - Position persistence across sessions
    - Preset positions (center, corners)
    - Custom positions with drag support
    - Screen bounds validation
    """

    def __init__(
        self, widget: "QWidget", config_service: Optional["IConfigService"] = None
    ):
        """Initialize position manager

        Args:
            widget: The widget to manage position for
            config_service: Optional config service for persistence
        """
        self.widget = widget
        self.config_service = config_service
        self.last_saved_position: Optional[QPoint] = None

        app_logger.log_audio_event("Position manager initialized", {})

    def set_config_service(self, config_service: "IConfigService") -> None:
        """Set or update the config service

        Args:
            config_service: Config service for persistence
        """
        self.config_service = config_service
        app_logger.log_audio_event("Position manager config service set", {})

    def get_current_screen_info(self) -> Dict[str, Any]:
        """获取当前屏幕信息

        Returns:
            Dictionary containing screen index, name, geometry, and DPI ratio
        """
        try:
            # 获取所有屏幕
            screens = QGuiApplication.screens()
            if not screens:
                return {}

            # 找到当前窗口所在的屏幕
            current_screen = None
            widget_center = self.widget.geometry().center()

            for i, screen in enumerate(screens):
                if screen.geometry().contains(widget_center):
                    current_screen = screen
                    screen_index = i
                    break

            # 如果没找到，使用主屏幕
            if current_screen is None:
                current_screen = QGuiApplication.primaryScreen()
                screen_index = 0

            # 构建屏幕信息字典
            screen_info = {
                "index": screen_index,
                "name": current_screen.name(),
                "geometry": (
                    f"{current_screen.geometry().width()}x{current_screen.geometry().height()}"
                    f"+{current_screen.geometry().x()}+{current_screen.geometry().y()}"
                ),
                "device_pixel_ratio": float(current_screen.devicePixelRatio()),
            }

            app_logger.log_audio_event("Current screen info collected", screen_info)
            return screen_info

        except Exception as e:
            app_logger.log_error(e, "get_current_screen_info")
            return {}

    def find_best_screen(self, target_screen_info: Dict[str, Any]) -> Optional[QScreen]:
        """根据保存的屏幕信息找到最佳匹配屏幕

        Args:
            target_screen_info: Saved screen information dictionary

        Returns:
            Best matching QScreen, or primary screen as fallback
        """
        try:
            screens = QGuiApplication.screens()
            if not screens:
                return None

            # 1. 尝试完全匹配（索引和名称）
            target_index = target_screen_info.get("index", 0)
            target_name = target_screen_info.get("name", "")

            if target_index < len(screens):
                candidate = screens[target_index]
                if candidate.name() == target_name:
                    app_logger.log_audio_event(
                        "Found exact screen match",
                        {"index": target_index, "name": target_name},
                    )
                    return candidate

            # 2. 尝试按名称匹配
            for screen in screens:
                if screen.name() == target_name:
                    app_logger.log_audio_event(
                        "Found screen by name", {"name": target_name}
                    )
                    return screen

            # 3. 尝试按几何信息相似度匹配
            target_geometry = target_screen_info.get("geometry", "")
            if target_geometry:
                for screen in screens:
                    current_geometry = (
                        f"{screen.geometry().width()}x{screen.geometry().height()}"
                        f"+{screen.geometry().x()}+{screen.geometry().y()}"
                    )
                    if current_geometry == target_geometry:
                        app_logger.log_audio_event(
                            "Found screen by geometry", {"geometry": current_geometry}
                        )
                        return screen

            # 4. 回退到主屏幕
            primary_screen = QGuiApplication.primaryScreen()
            app_logger.log_audio_event(
                "Falling back to primary screen",
                {"name": primary_screen.name() if primary_screen else "unknown"},
            )
            return primary_screen

        except Exception as e:
            app_logger.log_error(e, "find_best_screen")
            return QGuiApplication.primaryScreen()

    def ensure_position_in_bounds(
        self, x: int, y: int, screen: QScreen
    ) -> Tuple[int, int]:
        """确保位置在屏幕边界内

        Args:
            x: X coordinate
            y: Y coordinate
            screen: Target screen

        Returns:
            Tuple of (safe_x, safe_y) within screen bounds
        """
        try:
            if screen is None:
                return x, y

            screen_geometry = screen.geometry()
            window_width = self.widget.width()
            window_height = self.widget.height()

            # 安全边距
            margin = 20

            # 调整X坐标
            min_x = screen_geometry.x() + margin
            max_x = (
                screen_geometry.x() + screen_geometry.width() - window_width - margin
            )
            safe_x = max(min_x, min(x, max_x))

            # 调整Y坐标
            min_y = screen_geometry.y() + margin
            max_y = (
                screen_geometry.y() + screen_geometry.height() - window_height - margin
            )
            safe_y = max(min_y, min(y, max_y))

            # 如果位置被调整了，记录日志
            if safe_x != x or safe_y != y:
                app_logger.log_audio_event(
                    "Position adjusted to stay in bounds",
                    {
                        "original": f"{x},{y}",
                        "adjusted": f"{safe_x},{safe_y}",
                        "screen": screen.name(),
                    },
                )

            return safe_x, safe_y

        except Exception as e:
            app_logger.log_error(e, "ensure_position_in_bounds")
            return x, y

    def save_position(self) -> None:
        """保存当前位置到配置"""
        if not self.config_service:
            app_logger.log_audio_event("Position save skipped - no config service", {})
            return

        try:
            # 预检查：验证配置结构完整性
            self._ensure_overlay_config_structure()

            # 获取当前位置
            current_pos = self.widget.pos()
            current_screen_info = self.get_current_screen_info()

            # 使用单独的try-catch保存每个配置项，确保部分成功
            position_saved = False
            try:
                self.config_service.set_setting("ui.overlay_position.mode", "custom")
                position_saved = True
            except Exception as e:
                app_logger.log_error(e, "save_position_mode")

            try:
                self.config_service.set_setting(
                    "ui.overlay_position.custom.x", current_pos.x()
                )
                self.config_service.set_setting(
                    "ui.overlay_position.custom.y", current_pos.y()
                )
                position_saved = True
            except Exception as e:
                app_logger.log_error(e, "save_position_coordinates")

            try:
                self.config_service.set_setting(
                    "ui.overlay_position.last_screen", current_screen_info
                )
            except Exception as e:
                app_logger.log_error(e, "save_position_screen")

            # 即使部分保存失败，也要记住位置
            if position_saved:
                self.last_saved_position = current_pos
                app_logger.log_audio_event(
                    "Overlay position saved",
                    {
                        "position": f"{current_pos.x()},{current_pos.y()}",
                        "screen": current_screen_info.get("name", "unknown"),
                    },
                )
            else:
                app_logger.log_audio_event(
                    "Overlay position save failed",
                    {
                        "position": f"{current_pos.x()},{current_pos.y()}",
                        "fallback_memory": "position saved in memory only",
                    },
                )

        except Exception as e:
            app_logger.log_error(e, "save_position_critical")

    def _ensure_overlay_config_structure(self) -> None:
        """确保overlay配置结构完整性"""
        try:
            if not self.config_service:
                return

            # 验证ui.overlay_position存在且为字典
            overlay_pos = self.config_service.get_setting("ui.overlay_position", None)
            if not isinstance(overlay_pos, dict):
                app_logger.log_audio_event(
                    "Repairing overlay config structure",
                    {
                        "current_type": type(overlay_pos).__name__
                        if overlay_pos
                        else "None",
                        "expected": "dict",
                    },
                )
                # 重置为默认结构
                self.config_service.set_setting(
                    "ui.overlay_position",
                    {
                        "mode": "preset",
                        "preset": "center",
                        "custom": {"x": 0, "y": 0},
                        "auto_save": True,
                    },
                )

            # 验证custom子结构
            custom_pos = self.config_service.get_setting(
                "ui.overlay_position.custom", None
            )
            if not isinstance(custom_pos, dict):
                self.config_service.set_setting(
                    "ui.overlay_position.custom", {"x": 0, "y": 0}
                )

            app_logger.log_audio_event("Overlay config structure verified", {})

        except Exception as e:
            app_logger.log_error(e, "ensure_overlay_config_structure")

    def restore_position(self) -> None:
        """从配置恢复位置"""
        if not self.config_service:
            return

        try:
            # 获取配置中的位置模式
            position_mode = self.config_service.get_setting(
                "ui.overlay_position.mode", "preset"
            )

            if position_mode == "custom":
                # 自定义位置模式
                saved_x = self.config_service.get_setting(
                    "ui.overlay_position.custom.x", 0
                )
                saved_y = self.config_service.get_setting(
                    "ui.overlay_position.custom.y", 0
                )
                last_screen_info = self.config_service.get_setting(
                    "ui.overlay_position.last_screen", {}
                )

                if last_screen_info:
                    # 尝试找到最佳匹配的屏幕
                    target_screen = self.find_best_screen(last_screen_info)
                    if target_screen:
                        # 确保位置在屏幕边界内
                        safe_x, safe_y = self.ensure_position_in_bounds(
                            saved_x, saved_y, target_screen
                        )
                        self.widget.move(safe_x, safe_y)

                        app_logger.log_audio_event(
                            "Overlay position restored",
                            {
                                "position": f"{safe_x},{safe_y}",
                                "screen": target_screen.name(),
                            },
                        )
                        return

                # 如果屏幕信息无效，直接使用保存的坐标
                self.widget.move(saved_x, saved_y)
                app_logger.log_audio_event(
                    "Overlay position restored (no screen validation)",
                    {"position": f"{saved_x},{saved_y}"},
                )
            else:
                # 预设位置模式
                preset_position = self.config_service.get_setting(
                    "ui.overlay_position.preset", "center"
                )
                self.set_preset_position(preset_position)
                app_logger.log_audio_event(
                    "Overlay position restored (preset)", {"preset": preset_position}
                )

        except Exception as e:
            app_logger.log_error(e, "restore_position")
            # 发生错误时回退到中心位置
            self.center_on_screen()

    def set_preset_position(self, position: str) -> None:
        """Set window to a preset position

        Args:
            position: One of "center", "top_left", "top_right", "bottom_left", "bottom_right"
        """
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()

        if position == "center":
            self.center_on_screen()
        elif position == "top_left":
            self.widget.move(50, 50)
        elif position == "top_right":
            self.widget.move(screen_geometry.width() - self.widget.width() - 50, 50)
        elif position == "bottom_left":
            self.widget.move(50, screen_geometry.height() - self.widget.height() - 50)
        elif position == "bottom_right":
            self.widget.move(
                screen_geometry.width() - self.widget.width() - 50,
                screen_geometry.height() - self.widget.height() - 50,
            )

        app_logger.log_audio_event("Preset position set", {"position": position})

    def center_on_screen(self) -> None:
        """Center the widget on the primary screen"""
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()

        x = (screen_geometry.width() - self.widget.width()) // 2
        y = (screen_geometry.height() - self.widget.height()) // 2

        self.widget.move(x, y)
        app_logger.log_audio_event(
            "Widget centered on screen", {"position": f"{x},{y}"}
        )
