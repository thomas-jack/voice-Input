"""配置热重载接口定义

此模块定义了配置热重载系统的核心接口和数据结构。

核心概念：
- ReloadStrategy: 三种重载策略（PARAMETER_UPDATE, REINITIALIZE, RECREATE）
- ConfigDiff: 配置变更差异的数据传输对象
- ReloadResult: 重载操作的执行结果
- IConfigReloadable: 可配置重载服务的协议接口

设计理念：
- 去中心化：服务自己声明配置依赖
- 自主决策：服务自己决定重载策略
- 原子性：两阶段提交保证操作原子性
"""

from typing import Protocol, List, Tuple, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum


class ReloadStrategy(Enum):
    """配置重载策略

    定义三种不同级别的重载策略，从轻量到重量排序。

    PARAMETER_UPDATE: 仅更新参数，无需重启服务
        示例：更新日志级别、UI主题颜色
        特点：最快，无状态丢失，实时生效

    REINITIALIZE: 重新初始化服务，保持实例不变
        示例：更新API key、模型名称
        特点：中等速度，可能有短暂中断，保持服务实例

    RECREATE: 完全重建服务实例
        示例：切换提供商（local→groq）、切换热键后端（win32→pynput）
        特点：最慢，需要完整重建，涉及依赖注入重新绑定

    Example:
        >>> strategy = ReloadStrategy.PARAMETER_UPDATE
        >>> if strategy == ReloadStrategy.PARAMETER_UPDATE:
        ...     pass  # 轻量级更新
    """

    PARAMETER_UPDATE = "parameter_update"
    REINITIALIZE = "reinitialize"
    RECREATE = "recreate"


@dataclass
class ConfigDiff:
    """配置变更差异

    用于描述配置的变更内容，传递给服务进行分析。

    Attributes:
        changed_keys: 变更的配置键集合（点分隔路径，如 "transcription.provider"）
        old_config: 变更前的完整配置字典
        new_config: 变更后的完整配置字典
        timestamp: 变更发生的时间戳（秒）

    Example:
        >>> import time
        >>> diff = ConfigDiff(
        ...     changed_keys={"transcription.provider", "transcription.groq.api_key"},
        ...     old_config={"transcription": {"provider": "local"}},
        ...     new_config={"transcription": {"provider": "groq", "groq": {"api_key": "xxx"}}},
        ...     timestamp=time.time()
        ... )
        >>> print("transcription.provider" in diff.changed_keys)
        True
    """

    changed_keys: Set[str]
    old_config: Dict[str, Any]
    new_config: Dict[str, Any]
    timestamp: float


@dataclass
class ReloadResult:
    """配置重载结果

    用于服务返回重载操作的执行结果。

    Attributes:
        success: 操作是否成功
        message: 结果消息（成功或失败原因）
        rollback_data: 回滚数据（用于失败时恢复），仅在 prepare_reload() 时使用

    Example:
        >>> # 成功的 prepare
        >>> result = ReloadResult(
        ...     success=True,
        ...     message="准备成功",
        ...     rollback_data={"old_api_key": "xxx", "old_model": "yyy"}
        ... )
        >>> print(result.success)
        True
        >>>
        >>> # 失败的 commit
        >>> result = ReloadResult(
        ...     success=False,
        ...     message="API key validation failed"
        ... )
        >>> print(result.message)
        API key validation failed
    """

    success: bool
    message: str = ""
    rollback_data: Dict[str, Any] = field(default_factory=dict)


class IConfigReloadable(Protocol):
    """可配置重载服务接口

    所有支持配置热重载的服务必须实现此协议。

    设计理念：
    - 服务自己声明配置依赖（而非中心化管理）
    - 服务自己决定重载策略（而非硬编码）
    - 两阶段提交保证原子性（prepare + commit）

    使用流程：
    1. Coordinator 检测配置变更
    2. 调用 get_config_dependencies() 确定受影响服务
    3. 调用 can_reload_now() 检查是否可以重载
    4. 调用 get_reload_strategy() 确定重载策略
    5. Phase 1: 调用所有服务的 prepare_reload()
    6. Phase 2: 调用所有服务的 commit_reload()
    7. 如果失败: 调用 rollback_reload()

    Example:
        >>> class MyService(IConfigReloadable):
        ...     def get_config_dependencies(self) -> List[str]:
        ...         return ["transcription.provider"]
        ...
        ...     def get_service_dependencies(self) -> List[str]:
        ...         return ["audio_service"]
        ...
        ...     def get_reload_strategy(self, diff: ConfigDiff) -> ReloadStrategy:
        ...         if "transcription.provider" in diff.changed_keys:
        ...             return ReloadStrategy.RECREATE
        ...         return ReloadStrategy.PARAMETER_UPDATE
        ...
        ...     def can_reload_now(self) -> Tuple[bool, str]:
        ...         return True, ""
        ...
        ...     def prepare_reload(self, diff: ConfigDiff) -> ReloadResult:
        ...         return ReloadResult(success=True)
        ...
        ...     def commit_reload(self, diff: ConfigDiff) -> ReloadResult:
        ...         return ReloadResult(success=True)
        ...
        ...     def rollback_reload(self, rollback_data: Dict[str, Any]) -> bool:
        ...         return True
    """

    def get_config_dependencies(self) -> List[str]:
        """声明此服务依赖的配置键

        返回此服务关心的配置路径列表（点分隔）。
        当这些配置发生变更时，Coordinator 会将此服务纳入重载计划。

        Returns:
            配置键列表，如 ["transcription.provider", "transcription.groq.api_key"]

        Example:
            >>> class TranscriptionService(IConfigReloadable):
            ...     def get_config_dependencies(self) -> List[str]:
            ...         return [
            ...             "transcription.provider",
            ...             "transcription.local.model",
            ...             "transcription.local.streaming_mode",
            ...             "transcription.groq.api_key",
            ...             "transcription.groq.model",
            ...         ]
            ...         # 当这些配置变更时，此服务将被通知重载
        """
        ...

    def get_service_dependencies(self) -> List[str]:
        """声明此服务依赖的其他服务

        返回此服务依赖的其他服务名称列表。
        Coordinator 使用此信息进行拓扑排序，确保依赖服务先重载。

        Returns:
            服务名称列表，如 ["audio_service", "config_service"]

        Example:
            >>> class TranscriptionService(IConfigReloadable):
            ...     def get_service_dependencies(self) -> List[str]:
            ...         return ["audio_service", "config_service"]
            ...         # 表示转录服务依赖音频服务和配置服务
            ...         # 重载时会先重载这两个服务，然后才重载本服务
        """
        ...

    def get_reload_strategy(self, diff: ConfigDiff) -> ReloadStrategy:
        """根据配置变更决定重载策略

        分析配置差异，返回推荐的重载策略。

        Args:
            diff: 配置变更差异

        Returns:
            ReloadStrategy 枚举值

        Example:
            >>> def get_reload_strategy(self, diff: ConfigDiff) -> ReloadStrategy:
            ...     # 切换提供商需要重建
            ...     if "transcription.provider" in diff.changed_keys:
            ...         return ReloadStrategy.RECREATE
            ...
            ...     # API key 变更需要重新初始化
            ...     if "transcription.groq.api_key" in diff.changed_keys:
            ...         return ReloadStrategy.REINITIALIZE
            ...
            ...     # 模型名称变更需要重新初始化
            ...     if "transcription.local.model" in diff.changed_keys:
            ...         return ReloadStrategy.REINITIALIZE
            ...
            ...     # 流式模式只需更新参数
            ...     if "transcription.local.streaming_mode" in diff.changed_keys:
            ...         return ReloadStrategy.PARAMETER_UPDATE
            ...
            ...     # 其他参数只需更新
            ...     return ReloadStrategy.PARAMETER_UPDATE
        """
        ...

    def can_reload_now(self) -> Tuple[bool, str]:
        """检查当前是否可以执行重载

        检查服务当前状态，判断是否允许重载。
        如果服务正在执行关键任务（如录音、转录中），应返回 False。

        Returns:
            (是否可以重载, 原因说明)
            - True: 可以重载，原因可以为空
            - False: 不能重载，必须提供原因（用于通知用户）

        Example:
            >>> def can_reload_now(self) -> Tuple[bool, str]:
            ...     # 检查是否正在录音
            ...     if self._recording_controller.is_recording:
            ...         return False, "录音进行中，无法重载转录服务"
            ...
            ...     # 检查是否正在转录
            ...     if self._is_transcribing:
            ...         return False, "转录进行中，请稍后重试"
            ...
            ...     # 检查是否有待处理的转录队列
            ...     if self._transcription_queue.qsize() > 0:
            ...         return False, "转录队列非空，请等待处理完成"
            ...
            ...     # 可以安全重载
            ...     return True, ""
        """
        ...

    def prepare_reload(self, diff: ConfigDiff) -> ReloadResult:
        """两阶段提交 - 准备阶段

        验证新配置是否有效，准备回滚数据。
        此阶段不应修改服务状态，仅做验证和准备。

        Args:
            diff: 配置变更差异

        Returns:
            ReloadResult:
                - success=True: 准备成功，rollback_data 包含回滚信息
                - success=False: 准备失败，message 包含失败原因

        Example:
            >>> def prepare_reload(self, diff: ConfigDiff) -> ReloadResult:
            ...     new_provider = diff.new_config.get("transcription", {}).get("provider")
            ...
            ...     # 验证新配置
            ...     if new_provider == "groq":
            ...         api_key = diff.new_config.get("transcription", {}).get("groq", {}).get("api_key")
            ...         if not api_key:
            ...             return ReloadResult(
            ...                 success=False,
            ...                 message="Groq provider requires API key"
            ...             )
            ...
            ...         # 可选：验证 API key 是否有效
            ...         # if not self._validate_api_key(api_key):
            ...         #     return ReloadResult(
            ...         #         success=False,
            ...         #         message="Invalid Groq API key"
            ...         #     )
            ...
            ...     # 保存回滚数据
            ...     rollback_data = {
            ...         "provider": self._current_provider,
            ...         "service_instance": self._speech_service,
            ...         "model": self._current_model,
            ...     }
            ...
            ...     return ReloadResult(
            ...         success=True,
            ...         message="准备成功",
            ...         rollback_data=rollback_data
            ...     )
        """
        ...

    def commit_reload(self, diff: ConfigDiff) -> ReloadResult:
        """两阶段提交 - 提交阶段

        应用配置变更到服务。
        此阶段执行实际的重载操作（更新参数、重新初始化、或等待重建）。

        注意：RECREATE 策略由 Coordinator 处理，服务只需处理 PARAMETER_UPDATE 和 REINITIALIZE。

        Args:
            diff: 配置变更差异

        Returns:
            ReloadResult:
                - success=True: 提交成功
                - success=False: 提交失败，message 包含失败原因

        Example:
            >>> def commit_reload(self, diff: ConfigDiff) -> ReloadResult:
            ...     strategy = self.get_reload_strategy(diff)
            ...
            ...     try:
            ...         if strategy == ReloadStrategy.PARAMETER_UPDATE:
            ...             # 仅更新参数
            ...             new_streaming_mode = diff.new_config.get("transcription", {}).get("local", {}).get("streaming_mode")
            ...             if new_streaming_mode:
            ...                 self._streaming_mode = new_streaming_mode
            ...             return ReloadResult(success=True, message="参数更新成功")
            ...
            ...         elif strategy == ReloadStrategy.REINITIALIZE:
            ...             # 重新初始化
            ...             self._speech_service.unload_model()
            ...             new_model = diff.new_config.get("transcription", {}).get("local", {}).get("model")
            ...             self._speech_service.load_model(new_model)
            ...             self._current_model = new_model
            ...             return ReloadResult(success=True, message="重新初始化成功")
            ...
            ...         elif strategy == ReloadStrategy.RECREATE:
            ...             # RECREATE 由 Coordinator 处理，这里返回成功即可
            ...             return ReloadResult(success=True, message="等待 Coordinator 重建服务")
            ...
            ...     except Exception as e:
            ...         return ReloadResult(
            ...             success=False,
            ...             message=f"Failed to commit reload: {e}"
            ...         )
        """
        ...

    def rollback_reload(self, rollback_data: Dict[str, Any]) -> bool:
        """回滚到之前的配置状态

        当 commit_reload() 失败时，使用 prepare_reload() 保存的回滚数据恢复状态。

        Args:
            rollback_data: prepare_reload() 返回的回滚数据

        Returns:
            是否回滚成功

        Example:
            >>> def rollback_reload(self, rollback_data: Dict[str, Any]) -> bool:
            ...     try:
            ...         # 恢复服务实例
            ...         if "service_instance" in rollback_data:
            ...             self._speech_service = rollback_data["service_instance"]
            ...
            ...         # 恢复提供商
            ...         if "provider" in rollback_data:
            ...             self._current_provider = rollback_data["provider"]
            ...
            ...         # 恢复模型
            ...         if "model" in rollback_data:
            ...             self._current_model = rollback_data["model"]
            ...
            ...         return True
            ...
            ...     except Exception as e:
            ...         # 回滚失败，记录日志
            ...         self._logger.error(f"回滚失败: {e}")
            ...         return False
        """
        ...
