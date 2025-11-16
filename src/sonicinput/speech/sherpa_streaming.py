"""sherpa-onnx 流式转录会话管理

支持真正的实时流式转录
"""

import numpy as np
from typing import Dict, Any
from loguru import logger


class SherpaStreamingSession:
    """sherpa-onnx 流式转录会话（真实时）

    用于实时模式：边录边转，逐字显示
    """

    def __init__(self, recognizer, stream):
        """初始化流式会话

        Args:
            recognizer: sherpa_onnx.OnlineRecognizer 实例
            stream: sherpa_onnx.OnlineStream 实例
        """
        self.recognizer = recognizer
        self.stream = stream
        self.is_active = True
        self.sample_rate = 16000
        self._last_result = ""

    def add_samples(self, samples: np.ndarray) -> None:
        """添加音频样本（实时推送）

        Args:
            samples: 音频样本数组，应该是 float32 类型
        """
        if not self.is_active:
            logger.warning("Stream is not active, ignoring samples")
            return

        try:
            # 确保是 float32 类型
            if samples.dtype != np.float32:
                samples = samples.astype(np.float32)

            # 推送到 sherpa-onnx
            self.stream.accept_waveform(self.sample_rate, samples)

        except Exception as e:
            logger.error(f"Error adding samples to stream: {e}")
            raise

    def get_partial_result(self) -> str:
        """获取部分结果（实时文本）

        改进：不在检测到端点时立即reset，而是累积完整句子。
        这样可以避免在用户说话过程中截断文本。

        Returns:
            当前识别的部分文本
        """
        if not self.is_active:
            return self._last_result

        try:
            # 持续解码直到所有可用帧处理完毕
            decode_count = 0
            max_decode_per_call = 10  # 防止无限循环
            while (
                self.recognizer.is_ready(self.stream)
                and decode_count < max_decode_per_call
            ):
                self.recognizer.decode_stream(self.stream)
                decode_count += 1

            # 获取当前结果
            result = self.recognizer.get_result(self.stream)

            # 检查是否到达端点（句子结束）
            is_endpoint = self.recognizer.is_endpoint(self.stream)

            if is_endpoint:
                # 端点检测：句子可能结束
                # 关键修复：不立即reset，而是标记端点并继续累积
                if result.strip():
                    self._last_result = result
                    # 注意：这里不调用 reset()
                    # reset()延迟到 get_final_result() 或确认无新音频时
            else:
                # 部分结果：句子未结束
                if result.strip():
                    self._last_result = result

            return self._last_result

        except Exception as e:
            logger.error(f"Error getting partial result: {e}")
            return self._last_result

    def get_final_result(self) -> Dict[str, Any]:
        """获取最终结果

        Returns:
            完整转录结果字典
        """
        if not self.is_active:
            logger.warning("Stream already finalized")
            return {"text": self._last_result, "language": "zh"}

        try:
            # 标记输入结束
            self.stream.input_finished()

            # 解码剩余音频
            while self.recognizer.is_ready(self.stream):
                self.recognizer.decode_stream(self.stream)

            # 获取最终结果
            result = self.recognizer.get_result(self.stream)
            self._last_result = result

            self.is_active = False

            return {
                "text": result,
                "language": "zh",  # sherpa-onnx 不提供语言检测
            }

        except Exception as e:
            logger.error(f"Error getting final result: {e}")
            self.is_active = False
            return {"text": self._last_result, "language": "zh"}

    def reset(self) -> None:
        """重置会话（重新开始）"""
        try:
            # 创建新流
            self.stream = self.recognizer.create_stream()
            self.is_active = True
            self._last_result = ""
            logger.info("Stream reset successfully")

        except Exception as e:
            logger.error(f"Error resetting stream: {e}")
            raise

    def is_endpoint_detected(self) -> bool:
        """检测是否到达端点（句子结束）

        Returns:
            True if endpoint detected, False otherwise
        """
        try:
            return self.recognizer.is_endpoint(self.stream)
        except Exception as e:
            logger.error(f"Error detecting endpoint: {e}")
            return False

    def __del__(self):
        """清理资源"""
        if self.is_active:
            try:
                self.stream.input_finished()
                self.is_active = False
            except Exception:
                pass
