"""Audio level visualizer for RecordingOverlay"""

from PyQt6.QtWidgets import QLabel
from ...utils import app_logger


class AudioVisualizer:
    """Manages audio level visualization with dynamic bar display

    Displays audio levels using a set of colored bars that light up
    based on the current audio input level.
    """

    def __init__(self, audio_level_bars: list[QLabel]):
        """Initialize audio visualizer

        Args:
            audio_level_bars: List of QLabel widgets to use as level bars
        """
        self.audio_level_bars = audio_level_bars
        self.current_audio_level = 0.0
        self._last_audio_log_time = 0
        self._last_audio_log_time_direct = 0

        app_logger.log_audio_event("Audio visualizer initialized", {
            "bar_count": len(audio_level_bars)
        })

    def update_from_audio_data(self, audio_data, is_recording: bool) -> None:
        """Update audio level display from raw audio data

        Args:
            audio_data: Raw audio data (numpy array or similar)
            is_recording: Whether recording is active
        """
        if not is_recording or audio_data is None:
            return

        try:
            import numpy as np
            # 计算音频级别 (RMS)
            if hasattr(audio_data, '__len__') and len(audio_data) > 0:
                if isinstance(audio_data, np.ndarray):
                    level = float(np.sqrt(np.mean(audio_data**2)))
                else:
                    level = float(abs(sum(audio_data)) / len(audio_data))

                # 记录原始音量级别用于调试

                # 标准化到 0-1 范围 - 大幅提高敏感度让正常说话音量也能显示
                level = min(1.0, max(0.0, level * 20))  # 提高敏感度到20倍（从8倍）
                self.current_audio_level = level

                # 调试日志：每秒记录一次音量级别（已禁用，避免日志洪流）
                # current_time = time.time()
                # if current_time - self._last_audio_log_time >= 1.0:
                #     app_logger.log_audio_event("Audio level update", {
                #         "raw_level": f"{raw_level:.6f}",
                #         "normalized_level": f"{level:.4f}",
                #         "sensitivity_multiplier": 20
                #     })
                #     self._last_audio_log_time = current_time

                # 更新音频级别条
                self._update_audio_level_bars(level)
        except Exception as e:
            # 如果计算失败，静默失败
            app_logger.log_error(e, "update_from_audio_data")

    def update_from_level(self, level: float, is_recording: bool) -> None:
        """Update audio level display from pre-calculated level

        Args:
            level: Audio level (0.0 to 1.0)
            is_recording: Whether recording is active
        """
        if not is_recording:
            return

        try:
            # 记录原始音量级别

            # 标准化到 0-1 范围 - 大幅提高敏感度让正常说话音量也能显示
            normalized_level = min(1.0, max(0.0, level * 20))  # 提高敏感度到20倍（从8倍）
            self.current_audio_level = normalized_level

            # 调试日志：每秒记录一次音量级别（已禁用，避免日志洪流）
            # current_time = time.time()
            # if current_time - self._last_audio_log_time_direct >= 1.0:
            #     app_logger.log_audio_event("Audio level update (direct)", {
            #         "raw_level": f"{raw_level:.6f}",
            #         "normalized_level": f"{normalized_level:.4f}",
            #         "sensitivity_multiplier": 20
            #     })
            #     self._last_audio_log_time_direct = current_time

            # 更新音频级别条
            self._update_audio_level_bars(normalized_level)
        except Exception as e:
            app_logger.log_error(e, "update_from_level")

    def _update_audio_level_bars(self, level: float) -> None:
        """更新音频级别条显示

        Args:
            level: Normalized audio level (0.0 to 1.0)
        """
        try:
            # 计算应该点亮的级别条数量
            active_bars = int(level * len(self.audio_level_bars))

            # 更新每个级别条
            for i, bar in enumerate(self.audio_level_bars):
                if i < active_bars:
                    # 活跃的级别条 - 绿色渐变
                    intensity = (i + 1) / len(self.audio_level_bars)
                    if intensity < 0.6:
                        color = "#4CAF50"  # 绿色
                    elif intensity < 0.8:
                        color = "#FFC107"  # 黄色
                    else:
                        color = "#FF5722"  # 红色

                    bar.setStyleSheet(f"""
                        QLabel {{
                            background-color: {color};
                            border-radius: 2px;
                        }}
                    """)
                else:
                    # 非活跃的级别条 - 灰色
                    bar.setStyleSheet("""
                        QLabel {
                            background-color: rgba(80, 80, 90, 100);
                            border-radius: 2px;
                        }
                    """)
        except Exception as e:
            app_logger.log_error(e, "_update_audio_level_bars")

    def reset(self) -> None:
        """Reset all audio level bars to inactive state"""
        try:
            for bar in self.audio_level_bars:
                bar.setStyleSheet("""
                    QLabel {
                        background-color: rgba(80, 80, 90, 100);
                        border-radius: 2px;
                    }
                """)
            self.current_audio_level = 0.0
            app_logger.log_audio_event("Audio visualizer reset", {})
        except Exception as e:
            app_logger.log_error(e, "audio_visualizer_reset")
