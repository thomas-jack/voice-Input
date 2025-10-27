"""生命周期管理器

负责管理所有组件的生命周期，确保正确的初始化、启动、停止和清理。
解决悬浮窗等组件的生命周期管理问题，防止资源泄漏和闪退。
"""

import threading
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from ..interfaces.lifecycle import ILifecycleManager, ILifecycleManaged, ComponentState
from ..interfaces.event import IEventService, EventPriority
from ..interfaces.state import IStateManager
from ...utils import app_logger


@dataclass
class ComponentInfo:
    """组件信息"""
    component: ILifecycleManaged
    priority: int
    state: ComponentState = ComponentState.UNINITIALIZED
    registered_at: float = field(default_factory=time.time)
    initialized_at: Optional[float] = None
    started_at: Optional[float] = None
    stopped_at: Optional[float] = None
    error_count: int = 0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None


class LifecycleManager(ILifecycleManager):
    """生命周期管理器

    负责管理所有组件的生命周期。
    确保组件正确的初始化、启动、停止和清理，防止悬浮窗闪退问题。
    """

    def __init__(self, event_service: Optional[IEventService] = None, state_manager: Optional[IStateManager] = None):
        """初始化生命周期管理器

        Args:
            event_service: 事件服务实例
            state_manager: 状态管理器实例
        """
        self._event_service = event_service
        self._state_manager = state_manager
        self._components: Dict[str, ComponentInfo] = {}
        self._lock = threading.RLock()
        self._state_change_callback: Optional[Callable[[str, ComponentState, ComponentState], None]] = None
        self._shutdown_in_progress = False

        app_logger.log_audio_event("LifecycleManager initialized", {
            "event_service_enabled": self._event_service is not None,
            "state_manager_enabled": self._state_manager is not None
        })

    def register_component(self, component: ILifecycleManaged, priority: int = 0) -> bool:
        """注册组件

        Args:
            component: 要注册的组件
            priority: 优先级，数字越大优先级越高

        Returns:
            是否注册成功
        """
        try:
            component_name = component.get_component_name()

            with self._lock:
                if component_name in self._components:
                    app_logger.log_audio_event("Component already registered", {
                        "component_name": component_name
                    })
                    return False

                self._components[component_name] = ComponentInfo(
                    component=component,
                    priority=priority,
                    state=ComponentState.UNINITIALIZED
                )

            # 发送组件注册事件
            if self._event_service:
                self._event_service.emit("component_registered", {
                    "component_name": component_name,
                    "priority": priority,
                    "timestamp": datetime.now().isoformat()
                }, EventPriority.NORMAL)

            app_logger.log_audio_event("Component registered", {
                "component_name": component_name,
                "priority": priority,
                "total_components": len(self._components)
            })

            return True

        except Exception as e:
            app_logger.log_error(e, "register_component")
            return False

    def unregister_component(self, component_name: str) -> bool:
        """注销组件

        Args:
            component_name: 组件名称

        Returns:
            是否注销成功
        """
        try:
            with self._lock:
                if component_name not in self._components:
                    return False

                component_info = self._components[component_name]

                # 如果组件正在运行，先停止它
                if component_info.state == ComponentState.RUNNING:
                    self._stop_component(component_name)

                # 清理组件资源
                try:
                    component_info.component.cleanup()
                except Exception as e:
                    app_logger.log_error(e, f"cleanup_component_{component_name}")

                # 从注册表中移除
                del self._components[component_name]

            # 发送组件注销事件
            if self._event_service:
                self._event_service.emit("component_unregistered", {
                    "component_name": component_name,
                    "timestamp": datetime.now().isoformat()
                }, EventPriority.NORMAL)

            app_logger.log_audio_event("Component unregistered", {
                "component_name": component_name,
                "remaining_components": len(self._components)
            })

            return True

        except Exception as e:
            app_logger.log_error(e, f"unregister_component_{component_name}")
            return False

    def initialize_all(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """初始化所有组件

        Args:
            config: 初始化配置

        Returns:
            各组件初始化结果
        """
        results = {}

        try:
            # 按优先级排序（高优先级先初始化）
            sorted_components = self._get_sorted_components()

            for component_name, component_info in sorted_components:
                try:
                    self._set_component_state(component_name, ComponentState.INITIALIZING)

                    # 获取组件特定的配置
                    component_config = config.get(component_name, {})

                    # 初始化组件
                    success = component_info.component.initialize(component_config)
                    results[component_name] = success

                    if success:
                        self._set_component_state(component_name, ComponentState.INITIALIZED)
                        component_info.initialized_at = time.time()

                        app_logger.log_audio_event("Component initialized", {
                            "component_name": component_name
                        })
                    else:
                        self._set_component_state(component_name, ComponentState.ERROR)
                        self._record_component_error(component_name, "Initialization failed")

                        app_logger.log_audio_event("Component initialization failed", {
                            "component_name": component_name
                        })

                except Exception as e:
                    results[component_name] = False
                    self._set_component_state(component_name, ComponentState.ERROR)
                    self._record_component_error(component_name, str(e))
                    app_logger.log_error(e, f"initialize_component_{component_name}")

            app_logger.log_audio_event("All components initialization completed", {
                "successful": sum(1 for success in results.values() if success),
                "failed": sum(1 for success in results.values() if not success),
                "total": len(results)
            })

        except Exception as e:
            app_logger.log_error(e, "initialize_all")

        return results

    def start_all(self) -> Dict[str, bool]:
        """启动所有组件

        Returns:
            各组件启动结果
        """
        results = {}

        try:
            # 按优先级排序（高优先级先启动）
            sorted_components = self._get_sorted_components()

            for component_name, component_info in sorted_components:
                # 只启动已初始化的组件
                if component_info.state != ComponentState.INITIALIZED:
                    results[component_name] = False
                    continue

                try:
                    self._set_component_state(component_name, ComponentState.STARTING)

                    # 启动组件
                    success = component_info.component.start()
                    results[component_name] = success

                    if success:
                        self._set_component_state(component_name, ComponentState.RUNNING)
                        component_info.started_at = time.time()

                        app_logger.log_audio_event("Component started", {
                            "component_name": component_name
                        })
                    else:
                        self._set_component_state(component_name, ComponentState.ERROR)
                        self._record_component_error(component_name, "Start failed")

                        app_logger.log_audio_event("Component start failed", {
                            "component_name": component_name
                        })

                except Exception as e:
                    results[component_name] = False
                    self._set_component_state(component_name, ComponentState.ERROR)
                    self._record_component_error(component_name, str(e))
                    app_logger.log_error(e, f"start_component_{component_name}")

            app_logger.log_audio_event("All components start completed", {
                "successful": sum(1 for success in results.values() if success),
                "failed": sum(1 for success in results.values() if not success),
                "total": len(results)
            })

        except Exception as e:
            app_logger.log_error(e, "start_all")

        return results

    def stop_all(self) -> Dict[str, bool]:
        """停止所有组件

        Returns:
            各组件停止结果
        """
        results = {}
        self._shutdown_in_progress = True

        try:
            # 按优先级倒序停止（低优先级先停止）
            sorted_components = self._get_sorted_components(reverse=True)

            for component_name, component_info in sorted_components:
                results[component_name] = self._stop_component(component_name)

            app_logger.log_audio_event("All components stop completed", {
                "successful": sum(1 for success in results.values() if success),
                "failed": sum(1 for success in results.values() if not success),
                "total": len(results)
            })

        except Exception as e:
            app_logger.log_error(e, "stop_all")
        finally:
            self._shutdown_in_progress = False

        return results

    def cleanup_all(self) -> None:
        """清理所有组件资源"""
        try:
            # 按优先级倒序清理（低优先级先清理）
            sorted_components = self._get_sorted_components(reverse=True)

            for component_name, component_info in sorted_components:
                try:
                    component_info.component.cleanup()
                    self._set_component_state(component_name, ComponentState.DESTROYED)

                    app_logger.log_audio_event("Component cleaned up", {
                        "component_name": component_name
                    })

                except Exception as e:
                    app_logger.log_error(e, f"cleanup_component_{component_name}")

            with self._lock:
                self._components.clear()

            app_logger.log_audio_event("All components cleaned up", {})

        except Exception as e:
            app_logger.log_error(e, "cleanup_all")

    def get_component(self, component_name: str) -> Optional[ILifecycleManaged]:
        """获取组件实例

        Args:
            component_name: 组件名称

        Returns:
            组件实例，不存在时返回None
        """
        with self._lock:
            component_info = self._components.get(component_name)
            return component_info.component if component_info else None

    def get_component_state(self, component_name: str) -> Optional[ComponentState]:
        """获取组件状态

        Args:
            component_name: 组件名称

        Returns:
            组件状态，不存在时返回None
        """
        with self._lock:
            component_info = self._components.get(component_name)
            return component_info.state if component_info else None

    def get_all_components(self) -> List[str]:
        """获取所有已注册的组件名称

        Returns:
            组件名称列表
        """
        with self._lock:
            return list(self._components.keys())

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """对所有组件进行健康检查

        Returns:
            各组件健康状态
        """
        health_results = {}

        with self._lock:
            components = list(self._components.items())

        for component_name, component_info in components:
            try:
                health_result = component_info.component.health_check()
                health_result.update({
                    "component_state": component_info.state.value,
                    "error_count": component_info.error_count,
                    "last_error": component_info.last_error,
                    "uptime_seconds": (
                        time.time() - component_info.started_at
                        if component_info.started_at else 0
                    )
                })
                health_results[component_name] = health_result

            except Exception as e:
                health_results[component_name] = {
                    "healthy": False,
                    "error": str(e),
                    "component_state": component_info.state.value
                }
                app_logger.log_error(e, f"health_check_{component_name}")

        return health_results

    def set_state_change_callback(self, callback: Callable[[str, ComponentState, ComponentState], None]) -> None:
        """设置状态变更回调

        Args:
            callback: 回调函数，参数为 (组件名称, 旧状态, 新状态)
        """
        self._state_change_callback = callback

    def restart_component(self, component_name: str) -> bool:
        """重启组件

        Args:
            component_name: 组件名称

        Returns:
            是否重启成功
        """
        try:
            # 先停止组件
            if not self._stop_component(component_name):
                return False

            # 等待一小段时间确保清理完成
            time.sleep(0.1)

            # 重新启动组件
            with self._lock:
                component_info = self._components.get(component_name)
                if not component_info:
                    return False

                # 重新初始化（如果需要）
                if component_info.state == ComponentState.STOPPED:
                    self._set_component_state(component_name, ComponentState.INITIALIZING)
                    if component_info.component.initialize({}):
                        self._set_component_state(component_name, ComponentState.INITIALIZED)
                        component_info.initialized_at = time.time()
                    else:
                        self._set_component_state(component_name, ComponentState.ERROR)
                        return False

                # 启动组件
                self._set_component_state(component_name, ComponentState.STARTING)
                if component_info.component.start():
                    self._set_component_state(component_name, ComponentState.RUNNING)
                    component_info.started_at = time.time()

                    app_logger.log_audio_event("Component restarted", {
                        "component_name": component_name
                    })
                    return True
                else:
                    self._set_component_state(component_name, ComponentState.ERROR)
                    return False

        except Exception as e:
            app_logger.log_error(e, f"restart_component_{component_name}")
            return False

    @property
    def total_components(self) -> int:
        """已注册的组件总数"""
        with self._lock:
            return len(self._components)

    @property
    def running_components(self) -> int:
        """正在运行的组件数量"""
        with self._lock:
            return sum(1 for info in self._components.values()
                      if info.state == ComponentState.RUNNING)

    def _get_sorted_components(self, reverse: bool = False) -> List[tuple]:
        """获取按优先级排序的组件列表

        Args:
            reverse: 是否倒序

        Returns:
            排序后的组件列表
        """
        with self._lock:
            components = list(self._components.items())
            return sorted(components, key=lambda x: x[1].priority, reverse=not reverse)

    def _stop_component(self, component_name: str) -> bool:
        """停止单个组件

        Args:
            component_name: 组件名称

        Returns:
            是否停止成功
        """
        try:
            with self._lock:
                component_info = self._components.get(component_name)
                if not component_info:
                    return False

                # 只停止正在运行的组件
                if component_info.state != ComponentState.RUNNING:
                    return True

                self._set_component_state(component_name, ComponentState.STOPPING)

            # 停止组件
            success = component_info.component.stop()

            with self._lock:
                if success:
                    self._set_component_state(component_name, ComponentState.STOPPED)
                    component_info.stopped_at = time.time()
                else:
                    self._set_component_state(component_name, ComponentState.ERROR)
                    self._record_component_error(component_name, "Stop failed")

            app_logger.log_audio_event("Component stopped", {
                "component_name": component_name,
                "success": success
            })

            return success

        except Exception as e:
            with self._lock:
                self._set_component_state(component_name, ComponentState.ERROR)
                self._record_component_error(component_name, str(e))
            app_logger.log_error(e, f"stop_component_{component_name}")
            return False

    def _set_component_state(self, component_name: str, new_state: ComponentState) -> None:
        """设置组件状态

        Args:
            component_name: 组件名称
            new_state: 新状态
        """
        with self._lock:
            component_info = self._components.get(component_name)
            if not component_info:
                return

            old_state = component_info.state
            component_info.state = new_state

        # 调用状态变更回调
        if self._state_change_callback:
            try:
                self._state_change_callback(component_name, old_state, new_state)
            except Exception as e:
                app_logger.log_error(e, "state_change_callback")

        # 发送组件状态变更事件
        if self._event_service:
            self._event_service.emit("component_state_changed", {
                "component_name": component_name,
                "old_state": old_state.value,
                "new_state": new_state.value,
                "timestamp": datetime.now().isoformat()
            }, EventPriority.NORMAL)

        # 更新状态管理器
        if self._state_manager:
            self._state_manager.set_state(f"component_{component_name}_state", new_state.value)

    def _record_component_error(self, component_name: str, error_message: str) -> None:
        """记录组件错误

        Args:
            component_name: 组件名称
            error_message: 错误消息
        """
        with self._lock:
            component_info = self._components.get(component_name)
            if component_info:
                component_info.error_count += 1
                component_info.last_error = error_message
                component_info.last_error_time = time.time()

        # 发送组件错误事件
        if self._event_service:
            self._event_service.emit("component_error", {
                "component_name": component_name,
                "error_message": error_message,
                "error_count": component_info.error_count if component_info else 0,
                "timestamp": datetime.now().isoformat()
            }, EventPriority.HIGH)