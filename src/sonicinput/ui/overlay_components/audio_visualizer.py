"""音频可视化器 - 单一职责：管理音频级别显示"""

import math
from typing import List

from PySide6.QtWidgets import QLabel

from ...utils import app_logger


class AudioVisualizer:
    """音频可视化器 - 管理RecordingOverlay的音频级别显示

    职责：
    1. 管理5个音频级别条
    2. 更新音频级别显示
    3. 级别条颜色渐变（绿→黄→红）
    """

    def __init__(self, audio_level_bars: List[QLabel]):
        """初始化音频可视化器

        Args:
            audio_level_bars: 5个QLabel音频级别条的列表
        """
        if len(audio_level_bars) != 5:
            raise ValueError("AudioVisualizer需要恰好5个音频级别条")

        self.audio_level_bars = audio_level_bars
        self.current_audio_level = 0.0

        # 敏感度倍数（正常说话音量能显示）
        self.sensitivity_multiplier = 20

        app_logger.log_audio_event(
            "AudioVisualizer initialized",
            {
                "bars_count": len(self.audio_level_bars),
                "sensitivity": self.sensitivity_multiplier,
            },
        )

    def update_audio_level(self, raw_level: float) -> None:
        """更新音频级别显示

        Args:
            raw_level: 原始音频级别（通常是0-0.05范围）

        Note:
            Phase 4: Removed is_recording parameter - Caller controls when to call
            AudioVisualizer only visualizes data, doesn't manage recording state
        """

        try:
            # 使用对数刻度映射，更符合人耳对音量的感知
            # 对数映射公式: log10(level * 1000 + 1) / log10(1001)
            # 范围映射示例:
            #   0.001 -> ~0.10 (0-1格)
            #   0.01  -> ~0.35 (1-2格)
            #   0.03  -> ~0.49 (2-3格)
            #   0.05  -> ~0.57 (2-3格)
            #   0.1   -> ~0.67 (3-4格)
            #   0.5   -> ~0.91 (4-5格)
            if raw_level > 0:
                # 加1避免log(0)，乘1000扩大范围
                log_level = math.log10(raw_level * 1000 + 1) / math.log10(1001)
                normalized_level = min(1.0, max(0.0, log_level))
            else:
                normalized_level = 0.0

            self.current_audio_level = normalized_level

            # 更新音频级别条显示
            self._update_level_bars(normalized_level)

        except Exception as e:
            app_logger.log_error(e, "audio_visualizer_update")

    def _update_level_bars(self, level: float) -> None:
        """更新音频级别条显示（内部方法）

        Args:
            level: 标准化后的级别（0.0-1.0）
        """
        try:
            # 计算应该点亮的级别条数量
            active_bars = int(level * len(self.audio_level_bars))

            # 更新每个级别条
            for i, bar in enumerate(self.audio_level_bars):
                if i < active_bars:
                    # 活跃的级别条 - 绿色→黄色→红色渐变
                    color = self._get_bar_color(i)
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
            app_logger.log_error(e, "update_level_bars")

    def _get_bar_color(self, bar_index: int) -> str:
        """获取级别条颜色（渐变效果）

        Args:
            bar_index: 级别条索引（0-4）

        Returns:
            颜色字符串（CSS格式）
        """
        # 计算强度（0.2, 0.4, 0.6, 0.8, 1.0）
        intensity = (bar_index + 1) / len(self.audio_level_bars)

        # 根据强度返回不同颜色
        if intensity < 0.6:
            return "#4CAF50"  # 绿色（低音量）
        elif intensity < 0.8:
            return "#FFC107"  # 黄色（中音量）
        else:
            return "#FF5722"  # 红色（高音量）

    def reset_level_bars(self) -> None:
        """重置所有级别条为非活跃状态"""
        try:
            for bar in self.audio_level_bars:
                bar.setStyleSheet("""
                    QLabel {
                        background-color: rgba(80, 80, 90, 100);
                        border-radius: 2px;
                    }
                """)
            self.current_audio_level = 0.0

            app_logger.log_audio_event("Audio level bars reset", {})

        except Exception as e:
            app_logger.log_error(e, "reset_level_bars")

    def set_sensitivity(self, multiplier: float) -> None:
        """设置音频敏感度

        Args:
            multiplier: 敏感度倍数（建议范围1-50）
        """
        if multiplier <= 0:
            app_logger.log_audio_event(
                "Invalid sensitivity multiplier", {"multiplier": multiplier}
            )
            return

        self.sensitivity_multiplier = multiplier
        app_logger.log_audio_event(
            "Audio sensitivity updated", {"new_sensitivity": multiplier}
        )

    def get_current_level(self) -> float:
        """获取当前音频级别

        Returns:
            当前标准化的音频级别（0.0-1.0）
        """
        return self.current_audio_level

    def cleanup(self) -> None:
        """清理资源"""
        try:
            self.reset_level_bars()
            app_logger.log_audio_event("AudioVisualizer cleaned up", {})

        except Exception as e:
            app_logger.log_error(e, "audio_visualizer_cleanup")
