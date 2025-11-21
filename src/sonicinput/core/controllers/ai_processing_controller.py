"""AI处理控制器

负责AI文本优化处理。
"""

import requests
from typing import Optional

from ..base.lifecycle_component import LifecycleComponent
from ..interfaces import (
    IAIProcessingController,
    IAIService,
    IConfigService,
    IEventService,
    IStateManager,
    IHistoryStorageService,
)
from ..services.event_bus import Events
from ..services.config import ConfigKeys
from ...utils import app_logger, OpenRouterAPIError
from ...ai import AIClientFactory
from .base_controller import BaseController


class AIProcessingController(
    LifecycleComponent, BaseController, IAIProcessingController
):
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
        state_manager: IStateManager,
        history_service: IHistoryStorageService,
    ):
        # Initialize LifecycleComponent
        LifecycleComponent.__init__(self, "AIProcessingController")

        # Initialize base controller
        BaseController.__init__(self, config_service, event_service, state_manager)

        # Controller-specific services
        self._history_service = history_service

        # TPS追踪（用于性能日志）
        self._last_ai_tps: float = 0.0

        # 当前处理的记录ID
        self._current_record_id: Optional[str] = None

        # Register event listeners and log initialization
        self._register_event_listeners()
        self._log_initialization()

    def _do_start(self) -> bool:
        """Initialize AI processing resources

        Returns:
            True if start successful
        """
        # AI processing controller has no resources to initialize at start
        # Event listeners are already registered in __init__
        app_logger.log_audio_event(
            "AI processing controller ready", {"ai_enabled": self.is_ai_enabled()}
        )
        return True

    def _do_stop(self) -> bool:
        """Cleanup AI processing resources

        Returns:
            True if stop successful
        """
        # Clear current record ID
        self._current_record_id = None
        self._last_ai_tps = 0.0

        app_logger.log_audio_event("AI processing controller stopped", {})
        return True

    def _register_event_listeners(self) -> None:
        """Register event listeners for AI processing events"""
        self._events.on(
            Events.TRANSCRIPTION_COMPLETED, self._on_transcription_completed
        )

    def _on_transcription_completed(self, data: dict) -> None:
        """处理转录完成事件

        Args:
            data: 转录结果数据（可能包含 streaming_mode）
        """
        text = data.get("text", "")
        self._current_record_id = data.get("record_id")
        streaming_mode = data.get("streaming_mode", "chunked")

        # 实现混合 AI 策略
        should_use_ai = False

        if streaming_mode == "realtime":
            # Realtime 模式：永不使用 AI（优先速度）
            app_logger.log_audio_event(
                "Realtime mode: skipping AI processing", {"text_length": len(text)}
            )
            should_use_ai = False
        elif streaming_mode == "chunked":
            # Chunked 模式：尊重 AI 开关（可选质量优化）
            should_use_ai = self.is_ai_enabled()
            if should_use_ai:
                app_logger.log_audio_event(
                    "Chunked mode: AI enabled, will optimize",
                    {"text_length": len(text)},
                )
            else:
                app_logger.log_audio_event(
                    "Chunked mode: AI disabled, skipping", {"text_length": len(text)}
                )

        # 根据策略决定是否使用 AI
        if should_use_ai and text.strip():
            optimized_text = self.process_with_ai(text)

            # 创建data副本并移除会冲突的键（避免字典键冲突）
            data_copy = {k: v for k, v in data.items() if k != "text"}

            # 发送AI处理完成事件（携带优化后的文本）
            self._events.emit(
                "ai_processed_text",
                {
                    "text": optimized_text,
                    "original_text": text,
                    "ai_tps": self._last_ai_tps,
                    "streaming_mode": streaming_mode,
                    **data_copy,  # 保留原始数据（audio_duration等）
                },
            )
        else:
            # 不使用AI：更新历史记录
            skip_reason = (
                "realtime_mode"
                if streaming_mode == "realtime"
                else "ai_disabled"
                if not self.is_ai_enabled()
                else "no_text"
            )

            if self._current_record_id:
                self._update_ai_status(
                    record_id=self._current_record_id,
                    ai_text=None,
                    status="skipped",
                    error=None,
                    final_text=text,
                )

            # 不使用AI，直接发送原文本
            # 创建data副本并移除会冲突的键
            data_copy = {k: v for k, v in data.items() if k != "text"}

            self._events.emit(
                "ai_processed_text",
                {
                    "text": text,
                    "original_text": text,
                    "streaming_mode": streaming_mode,
                    "skip_reason": skip_reason,
                    **data_copy,
                },
            )

    def process_with_ai(self, text: str, record_id: Optional[str] = None) -> str:
        """使用AI优化文本

        Args:
            text: 原始文本
            record_id: 历史记录ID（可选，用于更新历史记录）

        Returns:
            优化后的文本
        """
        # 确定使用哪个record_id：优先使用传入的，fallback到实例变量
        actual_record_id = (
            record_id if record_id is not None else self._current_record_id
        )

        try:
            self._events.emit(Events.AI_PROCESSING_STARTED)

            # 获取配置
            provider = self._config.get_setting(ConfigKeys.AI_PROVIDER, "openrouter")
            model_key = f"ai.{provider}.model_id"
            model = self._config.get_setting(model_key, "anthropic/claude-3-sonnet")
            prompt_template = self._config.get_setting(
                ConfigKeys.AI_PROMPT,
                "Please improve and correct the following text: {text}",
            )

            # 动态获取AI服务
            ai_service = self._get_current_ai_service()
            if not ai_service:
                app_logger.log_audio_event(
                    "AI service not available, skipping optimization", {}
                )
                return text

            # 执行AI优化
            refined_text = ai_service.refine_text(text, prompt_template, model)

            # 保存TPS到实例变量
            self._last_ai_tps = getattr(ai_service, "_last_tps", 0.0)

            # 更新历史记录（AI成功）
            if actual_record_id:
                self._update_ai_status(
                    record_id=actual_record_id,
                    ai_text=refined_text,
                    status="success",
                    error=None,
                    final_text=refined_text,
                )

            # 发送AI处理完成事件
            self._events.emit(
                Events.AI_PROCESSING_COMPLETED,
                {"original": text, "refined": refined_text},
            )

            app_logger.log_audio_event(
                "AI refine completed",
                {
                    "model": model,
                    "original_length": len(text),
                    "refined_length": len(refined_text),
                },
            )

            return refined_text

        except requests.exceptions.Timeout as e:
            error_msg = "AI request timeout - API response too slow"
            app_logger.log_audio_event(
                f"{error_msg} - AI optimization skipped, using original text",
                {"error": str(e), "provider": provider},
            )
            app_logger.log_error(e, "process_with_ai")

            # 更新历史记录（AI失败）
            if actual_record_id:
                self._update_ai_status(
                    record_id=actual_record_id,
                    ai_text=None,
                    status="failed",
                    error=error_msg,
                    final_text=text,
                )

            self._events.emit(Events.AI_PROCESSING_ERROR, error_msg)
            return text  # 回退到原文本

        except requests.exceptions.ConnectionError as e:
            error_msg = "Network connection failed - check internet connection"
            app_logger.log_audio_event(
                f"{error_msg} - AI optimization skipped, using original text",
                {"error": str(e), "provider": provider},
            )
            app_logger.log_error(e, "process_with_ai")

            # 更新历史记录（AI失败）
            if actual_record_id:
                self._update_ai_status(
                    record_id=actual_record_id,
                    ai_text=None,
                    status="failed",
                    error=error_msg,
                    final_text=text,
                )

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
            app_logger.log_audio_event(
                f"{error_msg} - AI optimization skipped, using original text",
                {"error": str(e), "provider": provider},
            )
            app_logger.log_error(e, "process_with_ai")

            # 更新历史记录（AI失败）
            if actual_record_id:
                self._update_ai_status(
                    record_id=actual_record_id,
                    ai_text=None,
                    status="failed",
                    error=error_msg,
                    final_text=text,
                )

            self._events.emit(Events.AI_PROCESSING_ERROR, error_msg)
            return text

        except Exception as e:
            error_msg = f"Unknown AI processing error: {type(e).__name__}"
            app_logger.log_audio_event(
                f"{error_msg} - AI optimization skipped, using original text",
                {"error": str(e), "provider": provider},
            )
            app_logger.log_error(e, "process_with_ai")

            # 更新历史记录（AI失败）
            if actual_record_id:
                self._update_ai_status(
                    record_id=actual_record_id,
                    ai_text=None,
                    status="failed",
                    error=error_msg,
                    final_text=text,
                )

            self._events.emit(Events.AI_PROCESSING_ERROR, error_msg)
            return text

    def is_ai_enabled(self) -> bool:
        """AI是否启用"""
        return self._config.get_setting(ConfigKeys.AI_ENABLED, True)

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

    def _update_ai_status(
        self,
        record_id: str,
        ai_text: Optional[str],
        status: str,
        error: Optional[str],
        final_text: str,
    ) -> None:
        """更新历史记录的AI处理状态

        Args:
            record_id: 历史记录ID
            ai_text: AI优化后的文本（成功时）
            status: AI状态 ("success" | "failed" | "skipped")
            error: 错误信息（失败时）
            final_text: 最终文本（成功时为AI文本，失败/跳过时为转录文本）
        """
        try:
            # 获取现有记录
            record = self._history_service.get_record_by_id(record_id)
            if not record:
                app_logger.log_audio_event(
                    "Cannot update AI status - record not found",
                    {"record_id": record_id},
                )
                return

            # 获取AI提供商
            provider = self._config.get_setting(ConfigKeys.AI_PROVIDER, "openrouter")

            # 更新AI相关字段
            record.ai_optimized_text = ai_text
            record.ai_provider = provider if status == "success" else None
            record.ai_status = status
            record.ai_error = error
            record.final_text = final_text

            # 更新现有记录（使用 UPDATE 而不是 INSERT）
            update_success = self._history_service.update_record(record)

            if update_success:
                app_logger.log_audio_event(
                    "AI status updated in history",
                    {
                        "record_id": record_id,
                        "status": status,
                        "ai_text_length": len(ai_text) if ai_text else 0,
                    },
                )
            else:
                app_logger.log_audio_event(
                    "Failed to update AI status in history", {"record_id": record_id}
                )

        except Exception as e:
            app_logger.log_error(e, "_update_ai_status")
