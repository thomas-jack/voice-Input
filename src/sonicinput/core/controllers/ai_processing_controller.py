"""AI处理控制器

负责AI文本优化处理。
"""

import requests
from typing import Optional

from ..interfaces import (
    IAIProcessingController,
    IAIService,
    IConfigService,
    IEventService,
    IStateManager
)
from ..services.event_bus import Events
from ...utils import app_logger, OpenRouterAPIError
from ...ai import AIClientFactory


class AIProcessingController(IAIProcessingController):
    """AI处理控制器实现

    职责：
    - 处理AI文本优化
    - 动态选择AI服务提供商
    - 错误处理和回退
    - 通过 EventBus 发送AI处理事件
    """

    def __init__(
        self,
        config_service: IConfigService,
        event_service: IEventService,
        state_manager: IStateManager
    ):
        self._config = config_service
        self._events = event_service
        self._state = state_manager

        # TPS追踪（用于性能日志）
        self._last_ai_tps: float = 0.0

        # 监听转录完成事件
        self._events.on(Events.TRANSCRIPTION_COMPLETED, self._on_transcription_completed)

        app_logger.log_audio_event("AIProcessingController initialized", {})

    def _on_transcription_completed(self, data: dict) -> None:
        """处理转录完成事件

        Args:
            data: 转录结果数据
        """
        text = data.get("text", "")

        # 如果启用AI且有文本，则进行优化
        if self.is_ai_enabled() and text.strip():
            optimized_text = self.process_with_ai(text)

            # 创建data副本并移除会冲突的键（避免字典键冲突）
            data_copy = {k: v for k, v in data.items() if k != "text"}

            # 发送AI处理完成事件（携带优化后的文本）
            self._events.emit("ai_processed_text", {
                "text": optimized_text,
                "original_text": text,
                "ai_tps": self._last_ai_tps,
                **data_copy  # 保留原始数据（audio_duration等）
            })
        else:
            # 不使用AI，直接发送原文本
            # 创建data副本并移除会冲突的键
            data_copy = {k: v for k, v in data.items() if k != "text"}

            self._events.emit("ai_processed_text", {
                "text": text,
                "original_text": text,
                **data_copy
            })

    def process_with_ai(self, text: str) -> str:
        """使用AI优化文本

        Args:
            text: 原始文本

        Returns:
            优化后的文本
        """
        try:
            self._events.emit(Events.AI_PROCESSING_STARTED)

            # 获取配置
            provider = self._config.get_setting("ai.provider", "openrouter")
            model_key = f"ai.{provider}.model_id"
            model = self._config.get_setting(model_key, "anthropic/claude-3-sonnet")
            prompt_template = self._config.get_setting(
                "ai.prompt",
                "Please improve and correct the following text: {text}"
            )

            # 动态获取AI服务
            ai_service = self._get_current_ai_service()
            if not ai_service:
                app_logger.log_audio_event("AI service not available, skipping optimization", {})
                return text

            # 执行AI优化
            refined_text = ai_service.refine_text(text, prompt_template, model)

            # 保存TPS到实例变量
            self._last_ai_tps = getattr(ai_service, '_last_tps', 0.0)

            # 发送AI处理完成事件
            self._events.emit(Events.AI_PROCESSING_COMPLETED, {
                "original": text,
                "refined": refined_text
            })

            app_logger.log_audio_event("AI refine completed", {
                "model": model,
                "original_length": len(text),
                "refined_length": len(refined_text)
            })

            return refined_text

        except requests.exceptions.Timeout as e:
            error_msg = "AI request timeout - API response too slow"
            app_logger.log_audio_event(f"{error_msg} - AI optimization skipped, using original text", {
                "error": str(e),
                "provider": provider
            })
            app_logger.log_error(e, "process_with_ai")
            self._events.emit(Events.AI_PROCESSING_ERROR, error_msg)
            return text  # 回退到原文本

        except requests.exceptions.ConnectionError as e:
            error_msg = "Network connection failed - check internet connection"
            app_logger.log_audio_event(f"{error_msg} - AI optimization skipped, using original text", {
                "error": str(e),
                "provider": provider
            })
            app_logger.log_error(e, "process_with_ai")
            self._events.emit(Events.AI_PROCESSING_ERROR, error_msg)
            return text

        except OpenRouterAPIError as e:
            error_str = str(e).lower()
            if "timeout" in error_str:
                error_msg = "AI API timeout after retries"
            elif "429" in str(e) or "rate limit" in error_str:
                error_msg = "AI API rate limit exceeded"
            elif "401" in str(e) or "unauthorized" in error_str:
                error_msg = "AI API key invalid or unauthorized"
            else:
                error_msg = "AI API error"

            # 明确日志：AI 优化已跳过
            app_logger.log_audio_event(f"{error_msg} - AI optimization skipped, using original text", {
                "error": str(e),
                "provider": provider
            })
            app_logger.log_error(e, "process_with_ai")
            self._events.emit(Events.AI_PROCESSING_ERROR, error_msg)
            return text

        except Exception as e:
            error_msg = f"Unknown AI processing error: {type(e).__name__}"
            app_logger.log_audio_event(f"{error_msg} - AI optimization skipped, using original text", {
                "error": str(e),
                "provider": provider
            })
            app_logger.log_error(e, "process_with_ai")
            self._events.emit(Events.AI_PROCESSING_ERROR, error_msg)
            return text

    def is_ai_enabled(self) -> bool:
        """AI是否启用"""
        return self._config.get_setting("ai.enabled", True)

    def _get_current_ai_service(self) -> Optional[IAIService]:
        """根据当前配置动态获取 AI service 实例 - 使用 AIClientFactory

        Returns:
            AI服务实例，失败返回None
        """
        try:
            # 使用工厂从配置创建客户端（统一逻辑）
            return AIClientFactory.create_from_config(self._config)

        except Exception as e:
            app_logger.log_error(e, "_get_current_ai_service")
            return None
