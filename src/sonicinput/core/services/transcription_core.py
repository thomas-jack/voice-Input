"""重构后的转录核心模块 - 纯转录功能"""

import time
from typing import Optional, Dict, Any
import numpy as np

from ...utils import app_logger, WhisperLoadError


class TranscriptionCore:
    """转录核心处理器

    负责纯转录功能，不包含模型管理、流式处理等复杂逻辑。
    职责单一，专注于音频到文本的转换。
    """

    def __init__(self, whisper_engine):
        """初始化转录核心

        Args:
            whisper_engine: Whisper引擎实例
        """
        self.whisper_engine = whisper_engine

    def transcribe_audio(
        self,
        audio_data: np.ndarray,
        language: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """执行音频转录

        Args:
            audio_data: 音频数据
            language: 指定语言（可选）
            temperature: 温度参数

        Returns:
            转录结果字典
        """
        if not self.whisper_engine.is_model_loaded:
            raise WhisperLoadError("Model not loaded. Call load_model first.")

        start_time = time.time()

        try:
            # 执行转录 - 根据引擎类型传递不同参数
            # SherpaEngine 不支持 temperature 参数
            if hasattr(self.whisper_engine, '__class__') and 'SherpaEngine' in self.whisper_engine.__class__.__name__:
                # SherpaEngine 只需要 audio_data 和 language
                result = self.whisper_engine.transcribe(
                    audio_data, language=language
                )
            else:
                # WhisperEngine 支持 temperature 参数
                result = self.whisper_engine.transcribe(
                    audio_data, language=language, temperature=temperature
                )

            processing_time = time.time() - start_time

            # 标准化结果格式
            formatted_result = self._format_transcription_result(
                result, processing_time
            )

            app_logger.log_audio_event(
                "Audio transcribed successfully",
                {
                    "duration": len(audio_data) / 16000,  # 假设16kHz采样率
                    "processing_time": processing_time,
                    "language": result.get("language"),
                    "text_length": len(result.get("text", "")),
                },
            )

            return formatted_result

        except Exception as e:
            app_logger.log_error(e, "transcribe_audio")

            # 返回错误结果
            error_result = {
                "success": False,
                "text": "",
                "error": str(e),
                "processing_time": time.time() - start_time,
                "recovery_suggestions": self._get_recovery_suggestions(e),
            }

            return error_result

    def _format_transcription_result(
        self, whisper_result: Dict[str, Any], processing_time: float
    ) -> Dict[str, Any]:
        """格式化转录结果

        Args:
            whisper_result: Whisper引擎原始结果
            processing_time: 处理时间

        Returns:
            格式化的结果
        """
        segments = whisper_result.get("segments", [])

        return {
            "success": True,
            "text": whisper_result.get("text", ""),
            "language": whisper_result.get("language"),
            "confidence": self._calculate_confidence(segments),
            "segments": segments,
            "processing_time": processing_time,
            "model_info": {
                "model_name": self.whisper_engine.model_name,
                "device": self.whisper_engine.device,
            },
        }

    def _calculate_confidence(self, segments: list) -> float:
        """计算转录置信度

        Args:
            segments: Whisper片段列表

        Returns:
            平均置信度
        """
        if not segments:
            return 0.0

        confidences = []
        for segment in segments:
            if "avg_logprob" in segment:
                # 将对数概率转换为置信度
                confidence = np.exp(segment["avg_logprob"])
                confidences.append(confidence)

        return float(np.mean(confidences)) if confidences else 0.0

    def _get_recovery_suggestions(self, error: Exception) -> list:
        """根据错误类型提供恢复建议

        Args:
            error: 异常对象

        Returns:
            恢复建议列表
        """
        error_str = str(error).lower()

        suggestions = []

        if "no such device" in error_str or "device unavailable" in error_str:
            suggestions.append("检查音频设备连接")
            suggestions.append("尝试重新插拔音频设备")
            suggestions.append("重启应用程序")

        elif "model not loaded" in error_str:
            suggestions.append("等待模型加载完成")
            suggestions.append("检查网络连接（在线模型）")
            suggestions.append("尝试重新加载模型")

        elif "cuda" in error_str or "gpu" in error_str:
            suggestions.append("检查GPU驱动程序")
            suggestions.append("尝试切换到CPU模式")
            suggestions.append("检查CUDA版本兼容性")

        elif "out of memory" in error_str:
            suggestions.append("尝试使用较小的模型")
            suggestions.append("关闭其他GPU应用程序")
            suggestions.append("重启应用程序释放内存")

        else:
            suggestions.append("检查音频文件格式")
            suggestions.append("尝试调整音频质量设置")
            suggestions.append("查看详细错误日志")

        return suggestions

    def is_ready(self) -> bool:
        """检查转录核心是否就绪

        Returns:
            True如果模型已加载且可用
        """
        return self.whisper_engine is not None and self.whisper_engine.is_model_loaded

    def get_model_info(self) -> Dict[str, Any]:
        """获取当前模型信息

        Returns:
            模型信息字典
        """
        if not self.whisper_engine:
            return {"status": "no_engine"}

        return {
            "model_name": self.whisper_engine.model_name,
            "device": self.whisper_engine.device,
            "is_loaded": self.whisper_engine.is_model_loaded,
            "use_gpu": getattr(self.whisper_engine, "use_gpu", False),
        }
