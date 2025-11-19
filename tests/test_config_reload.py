"""配置热重载系统测试套件

测试覆盖：
- ServiceRegistry 单元测试
- ConfigReloadCoordinator 单元测试
- IConfigReloadable 实现测试
- 端到端集成测试
"""

import time
from typing import Any, Dict, List, Set, Tuple
from unittest.mock import Mock

import pytest

# 导入被测试的模块
from sonicinput.core.interfaces.config_reload import (
    ConfigDiff,
    IConfigReloadable,
    ReloadResult,
    ReloadStrategy,
)
from sonicinput.core.services.config_reload_coordinator import (
    ConfigReloadCoordinator,
    CyclicDependencyError,
    ReloadPlan,
)
from sonicinput.core.services.service_registry import (
    FactoryNotFoundError,
    ServiceNotFoundError,
    ServiceRegistry,
)


# ========== 测试辅助类 ==========


class MockConfigReloadableService:
    """模拟实现 IConfigReloadable 的服务"""

    def __init__(
        self,
        config_deps: List[str],
        service_deps: List[str],
        can_reload: bool = True,
        prepare_success: bool = True,
        commit_success: bool = True,
    ):
        self.config_deps = config_deps
        self.service_deps = service_deps
        self._can_reload = can_reload
        self._prepare_success = prepare_success
        self._commit_success = commit_success

        # 调用跟踪
        self.prepare_called = False
        self.commit_called = False
        self.rollback_called = False
        self.rollback_data_received = None

    def get_config_dependencies(self) -> List[str]:
        return self.config_deps

    def get_service_dependencies(self) -> List[str]:
        return self.service_deps

    def get_reload_strategy(self, diff: ConfigDiff) -> ReloadStrategy:
        # 简单逻辑：根据配置键决定
        if any("provider" in key for key in diff.changed_keys):
            return ReloadStrategy.RECREATE
        elif any("api_key" in key or "model" in key for key in diff.changed_keys):
            return ReloadStrategy.REINITIALIZE
        else:
            return ReloadStrategy.PARAMETER_UPDATE

    def can_reload_now(self) -> Tuple[bool, str]:
        if self._can_reload:
            return True, ""
        else:
            return False, "Service is busy"

    def prepare_reload(self, diff: ConfigDiff) -> ReloadResult:
        self.prepare_called = True

        if self._prepare_success:
            return ReloadResult(success=True, rollback_data={"state": "saved"})
        else:
            return ReloadResult(success=False, message="Prepare failed")

    def commit_reload(self, diff: ConfigDiff) -> ReloadResult:
        self.commit_called = True

        if self._commit_success:
            return ReloadResult(success=True)
        else:
            return ReloadResult(success=False, message="Commit failed")

    def rollback_reload(self, rollback_data: Dict[str, Any]) -> bool:
        self.rollback_called = True
        self.rollback_data_received = rollback_data
        return True


# ========== ServiceRegistry 单元测试 ==========


class TestServiceRegistry:
    """ServiceRegistry 单元测试"""

    def test_register_and_get(self):
        """测试注册和获取服务"""
        registry = ServiceRegistry()
        service = MockConfigReloadableService([], [])

        registry.register("test_service", service)

        retrieved = registry.get("test_service")
        assert retrieved is service

    def test_get_nonexistent_service(self):
        """测试获取不存在的服务"""
        registry = ServiceRegistry()

        with pytest.raises(ServiceNotFoundError):
            registry.get("nonexistent")

    def test_replace_service(self):
        """测试服务替换"""
        registry = ServiceRegistry()
        old_service = MockConfigReloadableService([], [])
        new_service = MockConfigReloadableService([], [])

        registry.register("test", old_service)
        returned = registry.replace("test", new_service)

        assert returned is old_service
        assert registry.get("test") is new_service

    def test_replace_nonexistent_service(self):
        """测试替换不存在的服务"""
        registry = ServiceRegistry()
        new_service = MockConfigReloadableService([], [])

        with pytest.raises(ServiceNotFoundError):
            registry.replace("nonexistent", new_service)

    def test_register_with_factory(self):
        """测试注册服务工厂"""
        registry = ServiceRegistry()
        service = MockConfigReloadableService([], [])
        factory = lambda: MockConfigReloadableService([], [])

        registry.register("test", service, factory=factory)

        assert registry.has_factory("test")
        retrieved_factory = registry.get_factory("test")
        assert callable(retrieved_factory)

    def test_get_factory_nonexistent(self):
        """测试获取不存在的工厂"""
        registry = ServiceRegistry()

        with pytest.raises(FactoryNotFoundError):
            registry.get_factory("nonexistent")

    def test_has_service(self):
        """测试检查服务是否存在"""
        registry = ServiceRegistry()
        service = MockConfigReloadableService([], [])

        assert not registry.has_service("test")
        registry.register("test", service)
        assert registry.has_service("test")

    def test_get_all_names(self):
        """测试获取所有服务名称"""
        registry = ServiceRegistry()

        registry.register("service1", MockConfigReloadableService([], []))
        registry.register("service2", MockConfigReloadableService([], []))

        names = registry.get_all_names()
        assert set(names) == {"service1", "service2"}

    def test_unregister(self):
        """测试取消注册"""
        registry = ServiceRegistry()
        service = MockConfigReloadableService([], [])

        registry.register("test", service)
        returned = registry.unregister("test")

        assert returned is service
        assert not registry.has_service("test")

    def test_clear(self):
        """测试清空注册表"""
        registry = ServiceRegistry()

        registry.register("service1", MockConfigReloadableService([], []))
        registry.register("service2", MockConfigReloadableService([], []))

        assert len(registry.get_all_names()) == 2

        registry.clear()

        assert len(registry.get_all_names()) == 0


# ========== ConfigReloadCoordinator 单元测试 ==========


class TestConfigReloadCoordinator:
    """ConfigReloadCoordinator 单元测试"""

    def test_calculate_affected_services_simple(self):
        """测试计算受影响服务（简单场景）"""
        registry = ServiceRegistry()
        service1 = MockConfigReloadableService(
            config_deps=["transcription.provider"], service_deps=[]
        )
        service2 = MockConfigReloadableService(
            config_deps=["ai.enabled"], service_deps=[]
        )

        registry.register("service1", service1)
        registry.register("service2", service2)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"transcription.provider"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        affected = coordinator._calculate_affected_services(diff)

        assert affected == ["service1"]

    def test_calculate_affected_services_multiple(self):
        """测试计算受影响服务（多个服务）"""
        registry = ServiceRegistry()
        service1 = MockConfigReloadableService(
            config_deps=["transcription.provider", "transcription.model"],
            service_deps=[],
        )
        service2 = MockConfigReloadableService(
            config_deps=["transcription.model"], service_deps=[]
        )

        registry.register("service1", service1)
        registry.register("service2", service2)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"transcription.model"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        affected = coordinator._calculate_affected_services(diff)

        assert set(affected) == {"service1", "service2"}

    def test_calculate_affected_services_no_match(self):
        """测试计算受影响服务（无匹配）"""
        registry = ServiceRegistry()
        service1 = MockConfigReloadableService(
            config_deps=["transcription.provider"], service_deps=[]
        )

        registry.register("service1", service1)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"ai.enabled"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        affected = coordinator._calculate_affected_services(diff)

        assert affected == []

    def test_build_reload_plan_simple(self):
        """测试构建重载计划（无依赖）"""
        registry = ServiceRegistry()
        service1 = MockConfigReloadableService(config_deps=["key1"], service_deps=[])
        service2 = MockConfigReloadableService(config_deps=["key2"], service_deps=[])

        registry.register("service1", service1)
        registry.register("service2", service2)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"key1", "key2"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        plan = coordinator._build_reload_plan(["service1", "service2"], diff)

        # 无依赖，应该在同一阶段
        assert len(plan.stages) == 1
        assert set(plan.stages[0]) == {"service1", "service2"}

    def test_build_reload_plan_with_dependencies(self):
        """测试构建重载计划（有依赖）"""
        registry = ServiceRegistry()
        service1 = MockConfigReloadableService(
            config_deps=["key1"], service_deps=[]  # 无依赖
        )
        service2 = MockConfigReloadableService(
            config_deps=["key2"], service_deps=["service1"]  # 依赖 service1
        )

        registry.register("service1", service1)
        registry.register("service2", service2)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"key1", "key2"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        plan = coordinator._build_reload_plan(["service1", "service2"], diff)

        # 应该分成2个阶段
        assert len(plan.stages) == 2
        assert plan.stages[0] == ["service1"]  # service1 先执行
        assert plan.stages[1] == ["service2"]  # service2 后执行

    def test_build_reload_plan_complex_dependencies(self):
        """测试构建重载计划（复杂依赖）"""
        registry = ServiceRegistry()
        service1 = MockConfigReloadableService(
            config_deps=["key1"], service_deps=[]  # 无依赖
        )
        service2 = MockConfigReloadableService(
            config_deps=["key2"], service_deps=["service1"]  # 依赖 service1
        )
        service3 = MockConfigReloadableService(
            config_deps=["key3"], service_deps=["service1"]  # 依赖 service1
        )
        service4 = MockConfigReloadableService(
            config_deps=["key4"],
            service_deps=["service2", "service3"],  # 依赖 service2 和 service3
        )

        registry.register("service1", service1)
        registry.register("service2", service2)
        registry.register("service3", service3)
        registry.register("service4", service4)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"key1", "key2", "key3", "key4"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        plan = coordinator._build_reload_plan(
            ["service1", "service2", "service3", "service4"], diff
        )

        # 应该分成3个阶段
        assert len(plan.stages) == 3
        assert plan.stages[0] == ["service1"]  # service1 先执行
        assert set(plan.stages[1]) == {
            "service2",
            "service3",
        }  # service2 和 service3 并行
        assert plan.stages[2] == ["service4"]  # service4 最后执行

    def test_build_reload_plan_cyclic_dependency(self):
        """测试检测循环依赖"""
        registry = ServiceRegistry()
        service1 = MockConfigReloadableService(
            config_deps=["key1"], service_deps=["service2"]  # 依赖 service2
        )
        service2 = MockConfigReloadableService(
            config_deps=["key2"], service_deps=["service1"]  # 依赖 service1
        )

        registry.register("service1", service1)
        registry.register("service2", service2)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"key1", "key2"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        with pytest.raises(CyclicDependencyError):
            coordinator._build_reload_plan(["service1", "service2"], diff)

    def test_execute_reload_plan_success(self):
        """测试执行重载计划（成功）"""
        registry = ServiceRegistry()
        service = MockConfigReloadableService(
            config_deps=["key"],
            service_deps=[],
            prepare_success=True,
            commit_success=True,
        )

        registry.register("service1", service)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"key"}, old_config={}, new_config={}, timestamp=time.time()
        )

        plan = ReloadPlan(
            stages=[["service1"]],
            strategy_map={"service1": ReloadStrategy.PARAMETER_UPDATE},
            affected_services={"service1"},
        )

        success = coordinator._execute_reload_plan(plan, diff)

        assert success
        assert service.prepare_called
        assert service.commit_called
        assert not service.rollback_called

    def test_execute_reload_plan_prepare_failure(self):
        """测试准备阶段失败"""
        registry = ServiceRegistry()
        service = MockConfigReloadableService(
            config_deps=["key"], service_deps=[], prepare_success=False
        )

        registry.register("service1", service)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"key"}, old_config={}, new_config={}, timestamp=time.time()
        )

        plan = ReloadPlan(
            stages=[["service1"]],
            strategy_map={"service1": ReloadStrategy.PARAMETER_UPDATE},
            affected_services={"service1"},
        )

        success = coordinator._execute_reload_plan(plan, diff)

        assert not success
        assert service.prepare_called
        assert not service.commit_called

    def test_execute_reload_plan_commit_failure_rollback(self):
        """测试提交阶段失败并回滚"""
        registry = ServiceRegistry()
        service = MockConfigReloadableService(
            config_deps=["key"],
            service_deps=[],
            prepare_success=True,
            commit_success=False,
        )

        registry.register("service1", service)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"key"}, old_config={}, new_config={}, timestamp=time.time()
        )

        plan = ReloadPlan(
            stages=[["service1"]],
            strategy_map={"service1": ReloadStrategy.PARAMETER_UPDATE},
            affected_services={"service1"},
        )

        success = coordinator._execute_reload_plan(plan, diff)

        assert not success
        assert service.prepare_called
        assert service.commit_called
        # 注意：当服务提交失败时，它自己不会被回滚（因为它还没提交成功）
        # 只有已提交成功的服务才会被回滚
        assert not service.rollback_called

    def test_execute_reload_plan_multiple_services_partial_failure(self):
        """测试多服务提交部分失败并回滚"""
        registry = ServiceRegistry()
        service1 = MockConfigReloadableService(
            config_deps=["key1"],
            service_deps=[],
            prepare_success=True,
            commit_success=True,
        )
        service2 = MockConfigReloadableService(
            config_deps=["key2"],
            service_deps=[],
            prepare_success=True,
            commit_success=False,  # 第二个服务提交失败
        )

        registry.register("service1", service1)
        registry.register("service2", service2)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"key1", "key2"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        plan = ReloadPlan(
            stages=[["service1", "service2"]],
            strategy_map={
                "service1": ReloadStrategy.PARAMETER_UPDATE,
                "service2": ReloadStrategy.PARAMETER_UPDATE,
            },
            affected_services={"service1", "service2"},
        )

        success = coordinator._execute_reload_plan(plan, diff)

        assert not success
        # service1 应该被回滚（因为它提交成功了）
        assert service1.rollback_called
        # service2 不应该被回滚（因为它提交失败了，还没有完成提交）
        assert not service2.rollback_called

    def test_execute_reload_plan_recreate_strategy(self):
        """测试 RECREATE 策略执行"""
        registry = ServiceRegistry()
        service = MockConfigReloadableService(
            config_deps=["transcription.provider"],
            service_deps=[],
            prepare_success=True,
            commit_success=True,
        )
        factory = lambda: MockConfigReloadableService(
            config_deps=["transcription.provider"], service_deps=[]
        )

        registry.register("service1", service, factory=factory)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"transcription.provider"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        plan = ReloadPlan(
            stages=[["service1"]],
            strategy_map={"service1": ReloadStrategy.RECREATE},
            affected_services={"service1"},
        )

        success = coordinator._execute_reload_plan(plan, diff)

        assert success
        # RECREATE 策略会创建新实例并替换
        new_service = registry.get("service1")
        assert new_service is not service


# ========== 端到端集成测试 ==========


class TestConfigReloadE2E:
    """端到端集成测试"""

    def test_e2e_simple_reload(self):
        """测试简单的配置重载流程"""
        # 1. 设置
        registry = ServiceRegistry()
        service = MockConfigReloadableService(config_deps=["test.key"], service_deps=[])
        registry.register("test_service", service)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        # 2. 触发配置变更
        diff = ConfigDiff(
            changed_keys={"test.key"},
            old_config={"test": {"key": "old"}},
            new_config={"test": {"key": "new"}},
            timestamp=time.time(),
        )

        # 3. 执行重载
        success = coordinator.handle_config_change(diff)

        # 4. 验证
        assert success
        assert service.prepare_called
        assert service.commit_called

    def test_e2e_service_cannot_reload(self):
        """测试服务无法重载时提示重启"""
        registry = ServiceRegistry()
        service = MockConfigReloadableService(
            config_deps=["test.key"], service_deps=[], can_reload=False  # 无法重载
        )
        registry.register("test_service", service)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"test.key"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        success = coordinator.handle_config_change(diff)

        # 应该返回 False 并发出 restart_required 事件
        assert not success

        # 验证事件被发出
        event_manager.emit.assert_called()
        event_calls = [call[0][0] for call in event_manager.emit.call_args_list]
        assert "config.reload.restart_required" in event_calls

    def test_e2e_multiple_services_with_dependencies(self):
        """测试多个服务带依赖的配置重载"""
        registry = ServiceRegistry()

        # 创建依赖链：service1 <- service2 <- service3
        service1 = MockConfigReloadableService(
            config_deps=["key1"], service_deps=[]
        )
        service2 = MockConfigReloadableService(
            config_deps=["key2"], service_deps=["service1"]
        )
        service3 = MockConfigReloadableService(
            config_deps=["key3"], service_deps=["service2"]
        )

        registry.register("service1", service1)
        registry.register("service2", service2)
        registry.register("service3", service3)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"key1", "key2", "key3"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        success = coordinator.handle_config_change(diff)

        # 验证所有服务都被重载
        assert success
        assert service1.prepare_called and service1.commit_called
        assert service2.prepare_called and service2.commit_called
        assert service3.prepare_called and service3.commit_called

    def test_e2e_partial_failure_with_rollback(self):
        """测试部分失败并回滚的端到端流程"""
        registry = ServiceRegistry()

        # 创建依赖关系：service2 依赖 service1
        # 这样 service1 会先提交，service2 后提交
        service1 = MockConfigReloadableService(
            config_deps=["key1"],
            service_deps=[],
            prepare_success=True,
            commit_success=True,
        )
        service2 = MockConfigReloadableService(
            config_deps=["key2"],
            service_deps=["service1"],  # 依赖 service1
            prepare_success=True,
            commit_success=False,  # 第二个服务提交失败
        )

        registry.register("service1", service1)
        registry.register("service2", service2)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"key1", "key2"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        success = coordinator.handle_config_change(diff)

        # 应该失败并回滚已提交成功的服务
        assert not success
        assert service1.rollback_called  # service1 提交成功，需要回滚
        assert not service2.rollback_called  # service2 提交失败，不需要回滚


# ========== 边界条件测试 ==========


class TestConfigReloadBoundary:
    """边界条件测试"""

    def test_empty_config_change(self):
        """测试空的配置变更"""
        registry = ServiceRegistry()
        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys=set(),  # 空的变更
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        success = coordinator.handle_config_change(diff)
        assert success  # 空变更应该成功

    def test_unregistered_service_config_change(self):
        """测试影响未注册服务的配置变更"""
        registry = ServiceRegistry()
        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"nonexistent.key"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        success = coordinator.handle_config_change(diff)
        assert success  # 没有受影响的服务，应该成功

    def test_service_without_config_dependencies(self):
        """测试没有配置依赖的服务"""
        registry = ServiceRegistry()

        # 注册一个普通对象（不实现 IConfigReloadable）
        plain_service = object()
        registry.register("plain_service", plain_service)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"some.key"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        # 应该不会崩溃，只是跳过该服务
        success = coordinator.handle_config_change(diff)
        assert success

    def test_service_with_empty_dependencies(self):
        """测试空依赖列表的服务"""
        registry = ServiceRegistry()
        service = MockConfigReloadableService(
            config_deps=[],  # 空的配置依赖
            service_deps=[],  # 空的服务依赖
        )
        registry.register("service1", service)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        diff = ConfigDiff(
            changed_keys={"any.key"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        # 空依赖的服务不应该被影响
        success = coordinator.handle_config_change(diff)
        assert success
        assert not service.prepare_called
        assert not service.commit_called

    def test_very_large_dependency_chain(self):
        """测试超长依赖链"""
        registry = ServiceRegistry()

        # 创建一个10层的依赖链
        services = []
        for i in range(10):
            deps = [f"service{i-1}"] if i > 0 else []
            service = MockConfigReloadableService(
                config_deps=[f"key{i}"], service_deps=deps
            )
            services.append(service)
            registry.register(f"service{i}", service)

        event_manager = Mock()
        coordinator = ConfigReloadCoordinator(registry, event_manager)

        # 触发所有服务的配置变更
        changed_keys = {f"key{i}" for i in range(10)}
        diff = ConfigDiff(
            changed_keys=changed_keys,
            old_config={},
            new_config={},
            timestamp=time.time(),
        )

        success = coordinator.handle_config_change(diff)

        # 应该成功处理
        assert success
        # 所有服务都应该被重载
        for service in services:
            assert service.prepare_called
            assert service.commit_called

    def test_reload_strategy_determination(self):
        """测试重载策略判断逻辑"""
        service = MockConfigReloadableService(config_deps=[], service_deps=[])

        # 测试 RECREATE 策略（provider 变更）
        diff_recreate = ConfigDiff(
            changed_keys={"transcription.provider"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )
        assert service.get_reload_strategy(diff_recreate) == ReloadStrategy.RECREATE

        # 测试 REINITIALIZE 策略（api_key 变更）
        diff_reinit = ConfigDiff(
            changed_keys={"transcription.groq.api_key"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )
        assert service.get_reload_strategy(diff_reinit) == ReloadStrategy.REINITIALIZE

        # 测试 REINITIALIZE 策略（model 变更）
        diff_model = ConfigDiff(
            changed_keys={"transcription.local.model"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )
        assert service.get_reload_strategy(diff_model) == ReloadStrategy.REINITIALIZE

        # 测试 PARAMETER_UPDATE 策略（其他变更）
        diff_param = ConfigDiff(
            changed_keys={"transcription.local.streaming_mode"},
            old_config={},
            new_config={},
            timestamp=time.time(),
        )
        assert (
            service.get_reload_strategy(diff_param) == ReloadStrategy.PARAMETER_UPDATE
        )
