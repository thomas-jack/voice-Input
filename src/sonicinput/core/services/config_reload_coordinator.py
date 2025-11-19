"""配置重载协调器模块

提供配置热重载的中央协调功能，负责：
1. 监听配置变更事件
2. 计算受影响的服务
3. 构建重载执行计划（拓扑排序）
4. 执行两阶段提交重载
5. 处理失败回滚

设计原则：
- 服务无感知：服务只需实现 IConfigReloadable 接口
- 原子性：全部成功或全部回滚
- 依赖管理：自动处理服务间依赖顺序
"""

from typing import Dict, Any, List, Set, Optional
from dataclasses import dataclass, field
from loguru import logger

# 导入接口（Agent A 创建的）
from ..interfaces.config_reload import (
    ConfigDiff,
    ReloadStrategy,
)

# 导入 ServiceRegistry（Agent B 创建的）
from .service_registry import ServiceRegistry

# 导入事件管理器接口
from ..interfaces.event import IEventService, EventPriority


# ============================================================================
# 异常定义
# ============================================================================


class ConfigReloadError(Exception):
    """配置重载基础异常"""

    pass


class ReloadPrepareFailed(ConfigReloadError):
    """准备阶段失败异常"""

    pass


class ReloadCommitFailed(ConfigReloadError):
    """提交阶段失败异常"""

    pass


class CyclicDependencyError(ConfigReloadError):
    """循环依赖异常"""

    pass


# ============================================================================
# 数据类
# ============================================================================


@dataclass
class ReloadPlan:
    """配置重载执行计划

    使用拓扑排序将受影响的服务分组到不同阶段。
    同一阶段的服务可以并行重载（未来优化），不同阶段必须串行。

    Attributes:
        stages: 执行阶段列表，每个阶段包含一组服务名称
                例如：[["audio_service"], ["transcription_service", "ai_service"]]
                表示先重载 audio_service，再并行重载 transcription_service 和 ai_service
        strategy_map: 每个服务的重载策略映射
        affected_services: 所有受影响的服务集合

    Example:
        >>> plan = ReloadPlan(
        ...     stages=[["audio_service"], ["transcription_service"]],
        ...     strategy_map={
        ...         "audio_service": ReloadStrategy.PARAMETER_UPDATE,
        ...         "transcription_service": ReloadStrategy.RECREATE,
        ...     },
        ...     affected_services={"audio_service", "transcription_service"}
        ... )
    """

    stages: List[List[str]]
    strategy_map: Dict[str, ReloadStrategy]
    affected_services: Set[str] = field(default_factory=set)


# ============================================================================
# 协调器实现
# ============================================================================


class ConfigReloadCoordinator:
    """配置重载中央协调器

    职责：
    1. 监听配置变更事件
    2. 计算受影响的服务
    3. 构建重载执行计划（拓扑排序）
    4. 执行两阶段提交重载
    5. 处理失败回滚

    设计原则：
    - 服务无感知：服务只需实现 IConfigReloadable，不需要知道协调器存在
    - 原子性：全部成功或全部回滚，不允许部分成功
    - 依赖管理：自动处理服务间依赖顺序

    Example:
        >>> registry = ServiceRegistry()
        >>> coordinator = ConfigReloadCoordinator(registry, event_manager)
        >>> # 配置变更后自动触发重载
    """

    def __init__(
        self, service_registry: ServiceRegistry, event_service: IEventService
    ):
        """初始化协调器

        Args:
            service_registry: 服务注册中心
            event_service: 事件服务
        """
        self._registry = service_registry
        self._event_service = event_service

        # 订阅配置变更事件
        self._event_service.on(
            "config.changed",
            self._on_config_changed,
            priority=EventPriority.HIGH,  # 高优先级，确保早于其他订阅者处理
        )

        logger.info(
            "ConfigReloadCoordinator initialized and subscribed to config.changed"
        )

    def _on_config_changed(self, event_data: Dict[str, Any]) -> None:
        """配置变更事件处理器

        Args:
            event_data: 事件数据，应包含：
                - changed_keys: Set[str] - 变更的配置键
                - old_config: Dict[str, Any] - 旧配置
                - new_config: Dict[str, Any] - 新配置
                - timestamp: float - 变更时间戳
        """
        logger.info(
            f"Config changed event received: {event_data.get('changed_keys', set())}"
        )

        try:
            # 构建 ConfigDiff
            diff = ConfigDiff(
                changed_keys=event_data.get("changed_keys", set()),
                old_config=event_data.get("old_config", {}),
                new_config=event_data.get("new_config", {}),
                timestamp=event_data.get("timestamp", 0.0),
            )

            # 处理配置变更
            success = self.handle_config_change(diff)

            # 发出重载结果事件
            self._event_service.emit(
                "config.reload.success" if success else "config.reload.failed",
                {
                    "diff": diff,
                    "success": success,
                },
            )

        except Exception as e:
            logger.error(f"Failed to handle config change: {e}")
            self._event_service.emit("config.reload.failed", {"error": str(e)})

    def handle_config_change(self, diff: ConfigDiff) -> bool:
        """处理配置变更的主入口

        Args:
            diff: 配置变更差异

        Returns:
            是否重载成功
        """
        logger.info(f"Handling config change: {diff.changed_keys}")

        try:
            # 1. 计算受影响的服务
            affected = self._calculate_affected_services(diff)

            if not affected:
                logger.info("No services affected by config change")
                return True

            logger.info(f"Affected services: {affected}")

            # 2. 检查所有服务是否可以重载
            for name in affected:
                try:
                    service: Any = self._registry.get(name)
                except Exception as e:
                    logger.error(f"Failed to get service {name}: {e}")
                    continue

                can_reload, reason = service.can_reload_now()
                if not can_reload:
                    logger.warning(f"Service {name} cannot reload now: {reason}")
                    self._notify_restart_required(reason)
                    return False

            # 3. 构建重载计划
            plan = self._build_reload_plan(affected, diff)

            logger.info(
                f"Reload plan built: {len(plan.stages)} stages, "
                f"{len(plan.affected_services)} services"
            )

            # 4. 执行两阶段提交
            success = self._execute_reload_plan(plan, diff)

            if success:
                logger.info("Config reload completed successfully")
            else:
                logger.error("Config reload failed")

            return success

        except Exception as e:
            logger.error(f"Failed to handle config change: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _calculate_affected_services(self, diff: ConfigDiff) -> List[str]:
        """计算受影响的服务

        遍历所有已注册服务，检查其配置依赖是否与变更键有交集。

        Args:
            diff: 配置变更差异

        Returns:
            受影响的服务名称列表
        """
        affected = []

        # 获取所有已注册的服务
        all_services = self._registry.get_all_names()

        for name in all_services:
            try:
                # 获取服务实例
                service: Any = self._registry.get(name)

                # 检查是否实现了 IConfigReloadable
                if not hasattr(service, "get_config_dependencies"):
                    # 服务不支持配置重载，跳过
                    continue

                # 获取服务的配置依赖
                config_deps = service.get_config_dependencies()

                # 检查是否有交集
                if diff.changed_keys & set(config_deps):
                    affected.append(name)
                    logger.debug(
                        f"Service {name} affected by config change: "
                        f"{diff.changed_keys & set(config_deps)}"
                    )

            except Exception as e:
                logger.error(f"Failed to check service {name}: {e}")
                # 跳过有问题的服务
                continue

        return affected

    def _build_reload_plan(self, services: List[str], diff: ConfigDiff) -> ReloadPlan:
        """构建重载执行计划（拓扑排序）

        使用 Kahn's 算法对服务依赖进行拓扑排序。

        Args:
            services: 受影响的服务名称列表
            diff: 配置变更差异

        Returns:
            重载执行计划

        Raises:
            CyclicDependencyError: 如果检测到循环依赖
        """
        # 1. 构建依赖图
        graph: Dict[str, List[str]] = {}
        in_degree: Dict[str, int] = {}
        strategy_map: Dict[str, ReloadStrategy] = {}

        for name in services:
            try:
                service: Any = self._registry.get(name)

                # 获取服务依赖
                deps = service.get_service_dependencies()

                # 只关心受影响服务之间的依赖
                filtered_deps = [d for d in deps if d in services]

                graph[name] = filtered_deps
                in_degree[name] = len(filtered_deps)

                # 获取重载策略
                strategy_map[name] = service.get_reload_strategy(diff)

            except Exception as e:
                logger.error(f"Failed to build graph for service {name}: {e}")
                # 默认无依赖
                graph[name] = []
                in_degree[name] = 0
                strategy_map[name] = ReloadStrategy.PARAMETER_UPDATE

        # 2. Kahn's 算法拓扑排序
        stages: List[List[str]] = []
        remaining = set(services)

        while remaining:
            # 找出所有入度为0的服务（可以并行执行）
            current_stage = [s for s in remaining if in_degree[s] == 0]

            if not current_stage:
                # 有剩余服务但没有入度为0的，说明存在循环依赖
                raise CyclicDependencyError(
                    f"Cyclic dependency detected among services: {remaining}"
                )

            # 添加当前阶段
            stages.append(current_stage)

            # 从剩余集合中移除当前阶段的服务
            for s in current_stage:
                remaining.remove(s)

            # 更新入度（移除当前阶段服务后，依赖它们的服务入度-1）
            for name in services:
                if name in remaining:
                    # 检查当前服务的依赖中是否有当前阶段的服务
                    deps_in_current_stage = [
                        d for d in graph[name] if d in current_stage
                    ]
                    in_degree[name] -= len(deps_in_current_stage)

        logger.debug(f"Topology sort result: {stages}")

        return ReloadPlan(
            stages=stages, strategy_map=strategy_map, affected_services=set(services)
        )

    def _execute_reload_plan(self, plan: ReloadPlan, diff: ConfigDiff) -> bool:
        """执行重载计划（两阶段提交）

        Phase 1: 对所有服务调用 prepare_reload()，验证配置并保存回滚数据
        Phase 2: 对所有服务调用 commit_reload()，应用配置变更
        失败时: 调用 rollback_reload() 回滚所有已提交的变更

        Args:
            plan: 重载执行计划
            diff: 配置变更差异

        Returns:
            是否执行成功
        """
        rollback_data: Dict[str, Dict[str, Any]] = {}
        committed_services: List[str] = []

        try:
            # ===== Phase 1: Prepare All =====
            logger.info("Phase 1: Preparing all services")

            for stage_idx, stage in enumerate(plan.stages):
                logger.debug(f"Preparing stage {stage_idx + 1}: {stage}")

                for name in stage:
                    try:
                        service: Any = self._registry.get(name)

                        # 调用 prepare_reload
                        result = service.prepare_reload(diff)

                        if not result.success:
                            raise ReloadPrepareFailed(
                                f"Service {name} prepare failed: {result.message}"
                            )

                        # 保存回滚数据
                        rollback_data[name] = result.rollback_data

                        logger.debug(f"Service {name} prepared successfully")

                    except Exception as e:
                        logger.error(f"Prepare failed for {name}: {e}")
                        raise ReloadPrepareFailed(
                            f"Service {name} prepare failed: {str(e)}"
                        )

            logger.info("Phase 1 completed: All services prepared")

            # ===== Phase 2: Commit All =====
            logger.info("Phase 2: Committing all services")

            for stage_idx, stage in enumerate(plan.stages):
                logger.debug(f"Committing stage {stage_idx + 1}: {stage}")

                for name in stage:
                    try:
                        service: Any = self._registry.get(name)  # type: ignore[no-redef]
                        strategy = plan.strategy_map[name]

                        logger.debug(
                            f"Committing {name} with strategy {strategy.value}"
                        )

                        if strategy == ReloadStrategy.RECREATE:
                            # RECREATE 策略：完全重建服务
                            self._recreate_service(name, diff)
                        else:
                            # PARAMETER_UPDATE 或 REINITIALIZE：调用 commit_reload
                            result = service.commit_reload(diff)

                            if not result.success:
                                raise ReloadCommitFailed(
                                    f"Service {name} commit failed: {result.message}"
                                )

                        # 记录已提交的服务
                        committed_services.append(name)

                        logger.debug(f"Service {name} committed successfully")

                    except Exception as e:
                        logger.error(f"Commit failed for {name}: {e}")
                        raise ReloadCommitFailed(
                            f"Service {name} commit failed: {str(e)}"
                        )

            logger.info("Phase 2 completed: All services committed")
            return True

        except (ReloadPrepareFailed, ReloadCommitFailed) as e:
            logger.error(f"Reload failed: {e}")

            # 回滚所有已提交的变更
            if committed_services:
                logger.warning(
                    f"Rolling back {len(committed_services)} committed services"
                )
                self._rollback_all(rollback_data, committed_services)

            return False

        except Exception as e:
            logger.error(f"Unexpected error during reload: {e}")
            import traceback

            traceback.print_exc()

            # 尝试回滚
            if committed_services:
                self._rollback_all(rollback_data, committed_services)

            return False

    def _recreate_service(self, name: str, diff: ConfigDiff) -> None:
        """重建服务实例（RECREATE 策略）

        从 ServiceRegistry 获取工厂，创建新实例并原子替换。

        Args:
            name: 服务名称
            diff: 配置变更差异

        Raises:
            FactoryNotFoundError: 如果服务未注册工厂
        """
        logger.info(f"Recreating service: {name}")

        try:
            # 1. 获取服务工厂
            factory = self._registry.get_factory(name)

            # 2. 创建新实例
            new_instance = factory()

            logger.debug(f"New instance created for {name}: {type(new_instance)}")

            # 3. 原子替换
            old_instance = self._registry.replace(name, new_instance)

            logger.info(f"Service {name} replaced successfully")

            # 4. 清理旧实例
            if hasattr(old_instance, "cleanup"):
                try:
                    old_instance.cleanup()
                    logger.debug(f"Old instance cleaned up for {name}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup old instance of {name}: {e}")

            # 5. 验证新实例已初始化（工厂应该已经处理）
            if hasattr(new_instance, "_is_model_loaded"):
                if not new_instance._is_model_loaded:
                    logger.warning(
                        f"Service {name} factory did not initialize the service. "
                        f"This may cause runtime errors."
                    )
                else:
                    logger.debug(f"Service {name} successfully initialized by factory")
            else:
                logger.debug(f"Service {name} initialized (no model loading required)")

        except Exception as e:
            logger.error(f"Failed to recreate service {name}: {e}")
            raise

    def _rollback_all(
        self,
        rollback_data: Dict[str, Dict[str, Any]],
        committed_services: Optional[List[str]] = None,
    ) -> None:
        """回滚所有已提交的变更

        按逆序调用所有服务的 rollback_reload()。

        Args:
            rollback_data: 所有服务的回滚数据
                格式：{service_name: rollback_data}
            committed_services: 已提交的服务列表（可选）
                如果提供，只回滚这些服务；否则回滚所有
        """
        logger.info("Starting rollback process")

        # 确定需要回滚的服务
        services_to_rollback = (
            committed_services if committed_services else list(rollback_data.keys())
        )

        # 按逆序回滚
        for name in reversed(services_to_rollback):
            if name not in rollback_data:
                logger.warning(f"No rollback data for service {name}, skipping")
                continue

            try:
                service: Any = self._registry.get(name)

                success = service.rollback_reload(rollback_data[name])

                if success:
                    logger.debug(f"Service {name} rolled back successfully")
                else:
                    logger.error(f"Service {name} rollback returned False")

            except Exception as e:
                logger.error(f"Failed to rollback service {name}: {e}")
                # 继续回滚其他服务

        logger.info(
            f"Rollback process completed: {len(services_to_rollback)} services"
        )

    def _notify_restart_required(self, reason: str) -> None:
        """通知用户需要重启应用

        当某个服务的 can_reload_now() 返回 False 时调用。

        Args:
            reason: 需要重启的原因
        """
        logger.warning(f"Application restart required: {reason}")

        # 发出事件通知 UI
        self._event_service.emit("config.reload.restart_required", {"reason": reason})

        # TODO: 可以在 UI 显示提示对话框
