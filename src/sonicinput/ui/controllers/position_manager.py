"""位置管理器

专门处理悬浮窗位置计算、保存和恢复的组件。
支持多屏幕、DPI缩放、预设位置和自动保存功能。
"""

from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QRect
from PySide6.QtGui import QScreen
from typing import Optional, Tuple, Dict

from ...core.interfaces.config import IConfigService
from ...core.interfaces.event import IEventService, EventPriority
from ...utils.constants import UI, ConfigKeys
from ...utils import app_logger


class PositionManager:
    """悬浮窗位置管理器

    专门负责悬浮窗的位置计算、保存和恢复。
    支持多屏幕环境、DPI缩放和预设位置。
    """

    def __init__(self, config_service: IConfigService, event_service: Optional[IEventService] = None):
        """初始化位置管理器

        Args:
            config_service: 配置服务实例
            event_service: 事件服务实例
        """
        self._config_service = config_service
        self._event_service = event_service
        self._last_saved_position: Optional[Tuple[int, int]] = None

        app_logger.log_audio_event("PositionManager initialized", {})

    def get_position(self, widget: Optional[QWidget] = None) -> Tuple[int, int]:
        """获取悬浮窗应该显示的位置

        Args:
            widget: 要定位的组件

        Returns:
            (x, y) 坐标元组
        """
        try:
            # 获取位置模式
            position_mode = self._config_service.get_setting(
                ConfigKeys.UI_OVERLAY_POSITION_MODE, "preset"
            )

            if position_mode == "custom":
                return self._get_custom_position()
            else:
                return self._get_preset_position(widget)

        except Exception as e:
            app_logger.log_error(e, "get_position")
            # 发生错误时返回屏幕中心
            return self._get_screen_center()

    def save_position(self, x: int, y: int) -> bool:
        """保存位置到配置

        Args:
            x: X坐标
            y: Y坐标

        Returns:
            是否保存成功
        """
        try:
            # 检查是否启用自动保存
            auto_save = self._config_service.get_setting(
                ConfigKeys.UI_OVERLAY_POSITION_AUTO_SAVE, True
            )

            if not auto_save:
                return True

            # 避免频繁保存相同位置
            if self._last_saved_position == (x, y):
                return True

            # 保存自定义位置
            self._config_service.set_setting(ConfigKeys.UI_OVERLAY_POSITION_CUSTOM_X, x)
            self._config_service.set_setting(ConfigKeys.UI_OVERLAY_POSITION_CUSTOM_Y, y)

            # 设置为自定义模式
            self._config_service.set_setting(ConfigKeys.UI_OVERLAY_POSITION_MODE, "custom")

            # 保存屏幕信息
            self._save_screen_info()

            self._last_saved_position = (x, y)

            # 发送位置变更事件
            if self._event_service:
                self._event_service.emit("overlay_position_changed", {
                    "x": x,
                    "y": y,
                    "mode": "custom"
                }, EventPriority.NORMAL)

            app_logger.log_audio_event("Position saved", {
                "x": x,
                "y": y,
                "mode": "custom"
            })

            return True

        except Exception as e:
            app_logger.log_error(e, "save_position")
            return False

    def restore_position(self, widget: Optional[QWidget] = None) -> Tuple[int, int]:
        """从配置恢复位置

        Args:
            widget: 要定位的组件

        Returns:
            恢复的位置坐标
        """
        try:
            position = self.get_position(widget)

            # 验证位置是否在有效屏幕范围内
            validated_position = self._validate_position(*position, widget)

            app_logger.log_audio_event("Position restored", {
                "original_x": position[0],
                "original_y": position[1],
                "validated_x": validated_position[0],
                "validated_y": validated_position[1]
            })

            return validated_position

        except Exception as e:
            app_logger.log_error(e, "restore_position")
            return self._get_screen_center()

    def set_preset_position(self, preset: str, widget: Optional[QWidget] = None) -> Tuple[int, int]:
        """设置预设位置

        Args:
            preset: 预设位置名称
            widget: 要定位的组件

        Returns:
            计算出的位置坐标
        """
        try:
            # 保存预设位置到配置
            self._config_service.set_setting(ConfigKeys.UI_OVERLAY_POSITION_MODE, "preset")
            self._config_service.set_setting(ConfigKeys.UI_OVERLAY_POSITION_PRESET, preset)

            # 计算预设位置
            position = self._calculate_preset_position(preset, widget)

            # 发送位置变更事件
            if self._event_service:
                self._event_service.emit("overlay_position_changed", {
                    "x": position[0],
                    "y": position[1],
                    "mode": "preset",
                    "preset": preset
                }, EventPriority.NORMAL)

            app_logger.log_audio_event("Preset position set", {
                "preset": preset,
                "x": position[0],
                "y": position[1]
            })

            return position

        except Exception as e:
            app_logger.log_error(e, "set_preset_position")
            return self._get_screen_center()

    def get_available_presets(self) -> Dict[str, str]:
        """获取可用的预设位置

        Returns:
            预设位置字典，键为预设名，值为描述
        """
        return {
            "top_left": "左上角",
            "top_center": "顶部居中",
            "top_right": "右上角",
            "center_left": "左侧居中",
            "center": "屏幕中心",
            "center_right": "右侧居中",
            "bottom_left": "左下角",
            "bottom_center": "底部居中",
            "bottom_right": "右下角"
        }

    def get_current_screen(self) -> Optional[QScreen]:
        """获取当前主屏幕

        Returns:
            当前屏幕对象，None 表示获取失败
        """
        try:
            app = QApplication.instance()
            if app is None:
                return None

            # 优先使用鼠标所在屏幕
            cursor_pos = app.primaryScreen().availableGeometry().center()
            for screen in app.screens():
                if screen.geometry().contains(cursor_pos):
                    return screen

            # 回退到主屏幕
            return app.primaryScreen()

        except Exception as e:
            app_logger.log_error(e, "get_current_screen")
            return None

    def _get_custom_position(self) -> Tuple[int, int]:
        """获取自定义位置

        Returns:
            自定义位置坐标
        """
        x = self._config_service.get_setting(ConfigKeys.UI_OVERLAY_POSITION_CUSTOM_X, 0)
        y = self._config_service.get_setting(ConfigKeys.UI_OVERLAY_POSITION_CUSTOM_Y, 0)
        return (x, y)

    def _get_preset_position(self, widget: Optional[QWidget] = None) -> Tuple[int, int]:
        """获取预设位置

        Args:
            widget: 要定位的组件

        Returns:
            预设位置坐标
        """
        preset = self._config_service.get_setting(
            ConfigKeys.UI_OVERLAY_POSITION_PRESET, "center"
        )
        return self._calculate_preset_position(preset, widget)

    def _calculate_preset_position(self, preset: str, widget: Optional[QWidget] = None) -> Tuple[int, int]:
        """计算预设位置的具体坐标

        Args:
            preset: 预设位置名称
            widget: 要定位的组件

        Returns:
            计算出的坐标
        """
        try:
            # 获取屏幕信息
            screen = self.get_current_screen()
            if screen is None:
                return self._get_screen_center()

            screen_rect = screen.availableGeometry()

            # 获取组件尺寸
            if widget is not None:
                widget_size = widget.size()
                widget_width = widget_size.width()
                widget_height = widget_size.height()
            else:
                widget_width = UI.OVERLAY_WIDTH
                widget_height = UI.OVERLAY_HEIGHT

            # 获取预设位置的偏移量
            preset_offset = UI.POSITION_PRESETS.get(preset, (0, 0))

            # 计算基础位置
            if preset_offset[0] == 0:  # 水平居中
                x = screen_rect.center().x() - widget_width // 2
            elif preset_offset[0] > 0:  # 从左边计算
                x = screen_rect.left() + preset_offset[0]
            else:  # 从右边计算
                x = screen_rect.right() + preset_offset[0] - widget_width

            if preset_offset[1] == 0:  # 垂直居中
                y = screen_rect.center().y() - widget_height // 2
            elif preset_offset[1] > 0:  # 从顶部计算
                y = screen_rect.top() + preset_offset[1]
            else:  # 从底部计算
                y = screen_rect.bottom() + preset_offset[1] - widget_height

            return (x, y)

        except Exception as e:
            app_logger.log_error(e, "calculate_preset_position")
            return self._get_screen_center()

    def _get_screen_center(self) -> Tuple[int, int]:
        """获取屏幕中心位置

        Returns:
            屏幕中心坐标
        """
        try:
            screen = self.get_current_screen()
            if screen is None:
                return (100, 100)  # 默认位置

            screen_rect = screen.availableGeometry()
            center_x = screen_rect.center().x() - UI.OVERLAY_WIDTH // 2
            center_y = screen_rect.center().y() - UI.OVERLAY_HEIGHT // 2

            return (center_x, center_y)

        except Exception as e:
            app_logger.log_error(e, "get_screen_center")
            return (100, 100)  # 默认位置

    def _validate_position(self, x: int, y: int, widget: Optional[QWidget] = None) -> Tuple[int, int]:
        """验证位置是否在有效屏幕范围内

        Args:
            x: X坐标
            y: Y坐标
            widget: 要定位的组件

        Returns:
            验证后的有效坐标
        """
        try:
            # 获取组件尺寸
            if widget is not None:
                widget_size = widget.size()
                widget_width = widget_size.width()
                widget_height = widget_size.height()
            else:
                widget_width = UI.OVERLAY_WIDTH
                widget_height = UI.OVERLAY_HEIGHT

            # 获取所有屏幕的联合区域
            app = QApplication.instance()
            if app is None:
                return (x, y)

            total_rect = QRect()
            for screen in app.screens():
                total_rect = total_rect.united(screen.geometry())

            # 确保组件至少部分可见
            min_visible = 50  # 至少50像素可见

            # 验证X坐标
            if x + widget_width < total_rect.left() + min_visible:
                x = total_rect.left() + min_visible - widget_width
            elif x > total_rect.right() - min_visible:
                x = total_rect.right() - min_visible

            # 验证Y坐标
            if y + widget_height < total_rect.top() + min_visible:
                y = total_rect.top() + min_visible - widget_height
            elif y > total_rect.bottom() - min_visible:
                y = total_rect.bottom() - min_visible

            return (x, y)

        except Exception as e:
            app_logger.log_error(e, "validate_position")
            return (x, y)  # 验证失败时返回原坐标

    def _save_screen_info(self) -> None:
        """保存当前屏幕信息"""
        try:
            screen = self.get_current_screen()
            if screen is None:
                return

            # 保存屏幕信息以便检测环境变化
            screen_info = {
                "name": screen.name(),
                "geometry": f"{screen.geometry().width()}x{screen.geometry().height()}",
                "device_pixel_ratio": screen.devicePixelRatio()
            }

            # 找到主屏幕的索引
            app = QApplication.instance()
            if app is not None:
                screens = app.screens()
                for i, s in enumerate(screens):
                    if s == screen:
                        screen_info["index"] = i
                        break

            # 保存到配置
            for key, value in screen_info.items():
                config_key = f"ui.overlay_position.last_screen.{key}"
                self._config_service.set_setting(config_key, value)

        except Exception as e:
            app_logger.log_error(e, "save_screen_info")

    def is_screen_environment_changed(self) -> bool:
        """检查屏幕环境是否发生变化

        Returns:
            是否发生变化
        """
        try:
            current_screen = self.get_current_screen()
            if current_screen is None:
                return True

            # 获取保存的屏幕信息
            saved_geometry = self._config_service.get_setting(
                "ui.overlay_position.last_screen.geometry", ""
            )
            saved_ratio = self._config_service.get_setting(
                "ui.overlay_position.last_screen.device_pixel_ratio", 1.0
            )

            # 比较当前屏幕信息
            current_geometry = f"{current_screen.geometry().width()}x{current_screen.geometry().height()}"
            current_ratio = current_screen.devicePixelRatio()

            return (saved_geometry != current_geometry or
                   abs(saved_ratio - current_ratio) > 0.1)

        except Exception as e:
            app_logger.log_error(e, "is_screen_environment_changed")
            return False