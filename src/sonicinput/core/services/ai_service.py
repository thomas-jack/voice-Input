"""AI服务

负责AI文本优化处理，支持配置热重载。
"""

from typing import Any, Dict, List, Optional, Tuple

from ...ai.factory import AIClientFactory
from ...utils import app_logger
from ..base.lifecycle_component import LifecycleComponent
from ..interfaces.ai import IAIService
from ..interfaces.config import IConfigService
from ..interfaces.config_reload import (
    ConfigDiff,
    ReloadResult,
    ReloadStrategy,
)


class AIService(LifecycleComponent):  # type: ignore[metaclass]
    """AI服务（支持配置热重载）

    职责：
    - 管理AI客户端实例
    - 提供文本优化功能
    - 支持配置热重载
    - 处理提供商切换

    实现 IConfigReloadable 协议的所有方法：
    - get_config_dependencies(): 声明配置依赖
    - get_service_dependencies(): 声明服务依赖
    - get_reload_strategy(): 决定重载策略
    - can_reload_now(): 检查是否可以重载
    - prepare_reload(): 两阶段提交-准备
    - commit_reload(): 两阶段提交-提交
    - rollback_reload(): 回滚配置
    """

    def __init__(self, config_service: IConfigService):
        """初始化AI服务

        Args:
            config_service: 配置服务实例
        """
        super().__init__("AIService")

        # 保存配置服务引用
        self._config_service = config_service

        # AI客户端和配置
        self._client: Optional[IAIService] = None
        self._current_provider: str = ""

        # AI配置参数
        self._enabled: bool = True
        self._filter_thinking: bool = True
        self._prompt: str = ""
        self._timeout: int = 30
        self._retries: int = 3

        # 性能追踪
        self._last_tps: float = 0.0

    # ==================== LifecycleComponent Implementation ====================

    def _do_start(self) -> bool:
        """启动AI服务并初始化客户端

        Returns:
            是否启动成功
        """
        try:
            # 获取配置
            config = self._config_service.get_config()
            ai_config = config.get("ai", {})

            # 加载配置参数
            self._enabled = ai_config.get("enabled", True)
            self._filter_thinking = ai_config.get("filter_thinking", True)
            self._prompt = ai_config.get("prompt", "")
            self._timeout = ai_config.get("timeout", 30)
            self._retries = ai_config.get("retries", 3)

            # 创建AI客户端
            if self._enabled and self._config_service:
                self._current_provider = ai_config.get("provider", "groq")
                self._client = AIClientFactory.create_from_config(self._config_service)

                if self._client:
                    app_logger.log_audio_event(
                        "AI client initialized", {"provider": self._current_provider}
                    )
                else:
                    app_logger.log_audio_event(
                        "AI client creation failed",
                        {"provider": self._current_provider},
                    )

            return True

        except Exception as e:
            app_logger.log_error(e, "AIService._do_start")
            return False

    def _do_stop(self) -> bool:
        """停止AI服务并清理资源

        Returns:
            是否停止成功
        """
        try:
            # 清理AI客户端
            self._client = None
            app_logger.log_audio_event("AI service stopped and cleaned up", {})
            return True

        except Exception as e:
            app_logger.log_error(e, "AIService._do_stop")
            return False

    # ==================== AI Service Methods ====================

    def refine_text(self, text: str, prompt_template: str, model: str) -> str:
        """优化文本

        Args:
            text: 要优化的文本
            prompt_template: 提示模板
            model: 使用的AI模型

        Returns:
            优化后的文本
        """
        if not self._enabled or not self._client:
            return text

        try:
            refined_text = self._client.refine_text(text, prompt_template, model)

            # 保存TPS（如果客户端提供）
            if hasattr(self._client, "_last_tps"):
                self._last_tps = self._client._last_tps

            return refined_text

        except Exception as e:
            app_logger.log_error(e, "AIService.refine_text")
            return text

    def is_enabled(self) -> bool:
        """检查AI是否启用

        Returns:
            是否启用
        """
        return self._enabled

    def get_current_provider(self) -> str:
        """获取当前提供商

        Returns:
            提供商名称
        """
        return self._current_provider

    @property
    def last_tps(self) -> float:
        """获取最后一次处理的TPS

        Returns:
            TPS值
        """
        return self._last_tps

    # ==================== IConfigReloadable Implementation ====================

    def get_config_dependencies(self) -> List[str]:
        """声明此服务依赖的配置键

        Returns:
            配置键列表
        """
        return [
            "ai.provider",
            "ai.enabled",
            "ai.filter_thinking",
            "ai.prompt",
            "ai.timeout",
            "ai.retries",
            "ai.groq.api_key",
            "ai.groq.model_id",
            "ai.nvidia.api_key",
            "ai.nvidia.model_id",
            "ai.openrouter.api_key",
            "ai.openrouter.model_id",
            "ai.openai_compatible.api_key",
            "ai.openai_compatible.base_url",
            "ai.openai_compatible.model_id",
        ]

    def get_service_dependencies(self) -> List[str]:
        """声明此服务依赖的其他服务

        Returns:
            服务名称列表
        """
        return ["config_service"]

    def get_reload_strategy(self, diff: ConfigDiff) -> ReloadStrategy:
        """根据配置变更决定重载策略

        Args:
            diff: 配置变更差异

        Returns:
            重载策略
        """
        # 检查是否切换提供商
        if "ai.provider" in diff.changed_keys:
            return ReloadStrategy.RECREATE

        # 检查是否变更需要重新初始化的配置
        reinit_keys = {
            "ai.groq.api_key",
            "ai.groq.model_id",
            "ai.nvidia.api_key",
            "ai.nvidia.model_id",
            "ai.openrouter.api_key",
            "ai.openrouter.model_id",
            "ai.openai_compatible.api_key",
            "ai.openai_compatible.base_url",
            "ai.openai_compatible.model_id",
        }
        if diff.changed_keys & reinit_keys:
            return ReloadStrategy.REINITIALIZE

        # 其他变更（enabled、filter_thinking、prompt、timeout）仅需参数更新
        return ReloadStrategy.PARAMETER_UPDATE

    def can_reload_now(self) -> Tuple[bool, str]:
        """检查当前是否可以执行重载

        Returns:
            (是否可以重载, 原因说明)
        """
        # AI服务通常可以随时重载（处理是同步的，无长期任务）
        return True, ""

    def prepare_reload(self, diff: ConfigDiff) -> ReloadResult:
        """准备重载：验证新配置，保存回滚数据

        Args:
            diff: 配置变更差异

        Returns:
            重载结果
        """
        try:
            # 获取新配置
            new_config = diff.new_config
            ai_config = new_config.get("ai", {})
            new_provider = ai_config.get("provider", "groq")

            # 验证新配置的有效性
            if new_provider == "groq":
                api_key = ai_config.get("groq", {}).get("api_key")
                if not api_key:
                    return ReloadResult(
                        success=False, message="Groq provider requires API key"
                    )

            elif new_provider == "nvidia":
                api_key = ai_config.get("nvidia", {}).get("api_key")
                if not api_key:
                    return ReloadResult(
                        success=False, message="NVIDIA provider requires API key"
                    )

            elif new_provider == "openrouter":
                api_key = ai_config.get("openrouter", {}).get("api_key")
                if not api_key:
                    return ReloadResult(
                        success=False, message="OpenRouter provider requires API key"
                    )

            elif new_provider == "openai_compatible":
                api_key = ai_config.get("openai_compatible", {}).get("api_key")
                base_url = ai_config.get("openai_compatible", {}).get("base_url")
                if not api_key or not base_url:
                    return ReloadResult(
                        success=False,
                        message="OpenAI compatible provider requires API key and base URL",
                    )

            # 保存回滚数据
            rollback_data = {
                "provider": self._current_provider,
                "client": self._client,
                "enabled": self._enabled,
                "filter_thinking": self._filter_thinking,
                "prompt": self._prompt,
                "timeout": self._timeout,
                "retries": self._retries,
            }

            app_logger.log_audio_event(
                "AIService prepare_reload success",
                {
                    "old_provider": self._current_provider,
                    "new_provider": new_provider,
                    "strategy": self.get_reload_strategy(diff).value,
                },
            )

            return ReloadResult(
                success=True,
                message="Preparation successful",
                rollback_data=rollback_data,
            )

        except Exception as e:
            app_logger.log_error(e, "AIService.prepare_reload")
            return ReloadResult(success=False, message=f"Preparation failed: {str(e)}")

    def commit_reload(self, diff: ConfigDiff) -> ReloadResult:
        """提交重载：应用配置变更

        Args:
            diff: 配置变更差异

        Returns:
            重载结果
        """
        try:
            strategy = self.get_reload_strategy(diff)
            new_config = diff.new_config
            ai_config = new_config.get("ai", {})

            if strategy == ReloadStrategy.PARAMETER_UPDATE:
                # 仅更新参数（enabled、filter_thinking、prompt、timeout、retries）
                self._enabled = ai_config.get("enabled", True)
                self._filter_thinking = ai_config.get("filter_thinking", True)
                self._prompt = ai_config.get("prompt", "")
                self._timeout = ai_config.get("timeout", 30)
                self._retries = ai_config.get("retries", 3)

                app_logger.log_audio_event(
                    "AI parameters updated",
                    {
                        "enabled": self._enabled,
                        "filter_thinking": self._filter_thinking,
                        "timeout": self._timeout,
                    },
                )

                return ReloadResult(success=True, message="Parameters updated")

            elif strategy == ReloadStrategy.REINITIALIZE:
                # 重新初始化（如更换 API key、model_id）
                app_logger.log_audio_event("Reinitializing AI client", {})

                # 使用工厂重新创建客户端（基于新配置）
                new_provider = ai_config.get("provider", "groq")

                if not self._config_service:
                    return ReloadResult(
                        success=False, message="Config service not available"
                    )

                new_client = AIClientFactory.create_from_config(self._config_service)

                if new_client is None:
                    return ReloadResult(
                        success=False, message="Failed to create new AI client"
                    )

                # 替换客户端
                self._client = new_client
                self._current_provider = new_provider

                # 同时更新其他参数
                self._enabled = ai_config.get("enabled", True)
                self._filter_thinking = ai_config.get("filter_thinking", True)
                self._prompt = ai_config.get("prompt", "")
                self._timeout = ai_config.get("timeout", 30)
                self._retries = ai_config.get("retries", 3)

                app_logger.log_audio_event(
                    "AI client reinitialized", {"provider": self._current_provider}
                )

                return ReloadResult(success=True, message="Client reinitialized")

            elif strategy == ReloadStrategy.RECREATE:
                # RECREATE 策略由 Coordinator 处理
                app_logger.log_audio_event(
                    "RECREATE strategy should be handled by Coordinator", {}
                )
                return ReloadResult(
                    success=True, message="RECREATE handled by Coordinator"
                )

            else:
                return ReloadResult(
                    success=False, message=f"Unknown strategy: {strategy}"
                )

        except Exception as e:
            app_logger.log_error(e, "AIService.commit_reload")
            return ReloadResult(success=False, message=f"Commit failed: {str(e)}")

    def rollback_reload(self, rollback_data: Dict[str, Any]) -> bool:
        """回滚到之前的配置状态

        Args:
            rollback_data: prepare_reload 返回的回滚数据

        Returns:
            是否回滚成功
        """
        try:
            # 恢复客户端状态
            if "client" in rollback_data:
                self._client = rollback_data["client"]

            if "provider" in rollback_data:
                self._current_provider = rollback_data["provider"]

            if "enabled" in rollback_data:
                self._enabled = rollback_data["enabled"]

            if "filter_thinking" in rollback_data:
                self._filter_thinking = rollback_data["filter_thinking"]

            if "prompt" in rollback_data:
                self._prompt = rollback_data["prompt"]

            if "timeout" in rollback_data:
                self._timeout = rollback_data["timeout"]

            if "retries" in rollback_data:
                self._retries = rollback_data["retries"]

            app_logger.log_audio_event(
                "AIService rollback successful", {"provider": self._current_provider}
            )

            return True

        except Exception as e:
            app_logger.log_error(e, "AIService.rollback_reload")
            return False
