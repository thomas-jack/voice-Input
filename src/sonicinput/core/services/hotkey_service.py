"""热键服务 - 支持配置热重载

此服务封装热键管理器（Win32 或 Pynput），提供配置热重载能力。

核心功能：
- 管理热键注册和监听
- 支持后端切换（win32/pynput）
- 实现配置热重载（IConfigReloadable）
- 处理热键变更和后端变更

设计理念：
- 服务层封装：隐藏底层管理器实现细节
- 配置驱动：根据配置自动选择和切换后端
- 热重载友好：支持无缝切换热键和后端
"""

from typing import List, Tuple, Dict, Any, Callable, Optional
from ..base.lifecycle_component import LifecycleComponent
from ..interfaces.config_reload import (
    IConfigReloadable,
    ConfigDiff,
    ReloadResult,
    ReloadStrategy,
)
from ..interfaces.config import IConfigService
from ..interfaces.hotkey import IHotkeyService
from ...utils import app_logger


class HotkeyService(LifecycleComponent, IConfigReloadable):
    """热键服务（支持配置热重载）

    封装热键管理器，提供配置热重载能力。
    """

    def __init__(
        self,
        config_service: IConfigService,
        callback: Callable[[str], None],
    ):
        """初始化热键服务

        Args:
            config_service: 配置服务
            callback: 热键触发回调函数
        """
        super().__init__("HotkeyService", config_service)

        self._callback = callback
        self._manager: Optional[IHotkeyService] = None
        self._current_backend: str = ""
        self._current_keys: List[str] = []

    def _on_initialize(self) -> None:
        """初始化服务：创建热键管理器"""
        try:
            # 读取配置
            if not self._config_service:
                raise RuntimeError("Config service is not initialized")

            # 使用 get_setting 获取配置
            backend: str = self._config_service.get_setting("hotkeys.backend", "pynput")
            keys: List[str] = self._config_service.get_setting("hotkeys.keys", [])

            # 创建管理器
            self._create_manager(backend)

            # 注册热键
            if keys and self._manager:
                for key in keys:
                    try:
                        self._manager.register_hotkey(key, "toggle_recording")
                    except Exception as e:
                        app_logger.log_error(
                            e,
                            f"HotkeyService.initialize: Failed to register {key}"
                        )

            # 保存当前状态
            self._current_backend = backend
            self._current_keys = keys

            app_logger.log_audio_event(
                "HotkeyService initialized",
                {
                    "backend": backend,
                    "keys": keys,
                    "manager_type": type(self._manager).__name__,
                }
            )

        except Exception as e:
            app_logger.log_error(e, "HotkeyService._on_initialize")
            raise

    def _on_start(self) -> None:
        """启动服务：开始监听热键"""
        try:
            if self._manager:
                success = self._manager.start_listening()
                if success:
                    app_logger.log_audio_event(
                        "HotkeyService started listening",
                        {"backend": self._current_backend}
                    )
                else:
                    app_logger.log_audio_event(
                        "HotkeyService failed to start listening",
                        {"backend": self._current_backend}
                    )
        except Exception as e:
            app_logger.log_error(e, "HotkeyService._on_start")
            raise

    def _on_stop(self) -> None:
        """停止服务：停止监听热键"""
        try:
            if self._manager:
                self._manager.stop_listening()
                app_logger.log_audio_event(
                    "HotkeyService stopped listening",
                    {"backend": self._current_backend}
                )
        except Exception as e:
            app_logger.log_error(e, "HotkeyService._on_stop")

    def _on_cleanup(self) -> None:
        """清理服务：清理热键管理器"""
        try:
            if self._manager:
                # 注销所有热键
                if hasattr(self._manager, "unregister_all_hotkeys"):
                    self._manager.unregister_all_hotkeys()

                self._manager = None

                app_logger.log_audio_event(
                    "HotkeyService cleaned up",
                    {"backend": self._current_backend}
                )
        except Exception as e:
            app_logger.log_error(e, "HotkeyService._on_cleanup")

    def _create_manager(self, backend: str) -> None:
        """创建热键管理器

        Args:
            backend: 后端类型（"win32" 或 "pynput"）
        """
        if backend == "win32":
            from ..hotkey_manager_win32 import Win32HotkeyManager
            self._manager = Win32HotkeyManager(self._callback)
            app_logger.log_audio_event(
                "Created Win32 hotkey manager",
                {"backend": "win32"}
            )
        elif backend == "pynput":
            from ..hotkey_manager_pynput import PynputHotkeyManager
            self._manager = PynputHotkeyManager(self._callback)
            app_logger.log_audio_event(
                "Created Pynput hotkey manager",
                {"backend": "pynput"}
            )
        else:
            raise ValueError(f"Unsupported hotkey backend: {backend}")

    # ========== IConfigReloadable 接口实现 ==========

    def get_config_dependencies(self) -> List[str]:
        """声明此服务依赖的配置键

        Returns:
            配置键列表
        """
        return [
            "hotkeys.keys",
            "hotkeys.backend",
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
        # 检查是否切换后端
        if "hotkeys.backend" in diff.changed_keys:
            return ReloadStrategy.RECREATE

        # 仅热键变更，重新初始化即可
        return ReloadStrategy.REINITIALIZE

    def can_reload_now(self) -> Tuple[bool, str]:
        """检查当前是否可以执行重载

        热键服务可以随时重载，不影响其他功能。

        Returns:
            (是否可以重载, 原因说明)
        """
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
            new_keys = new_config.get("hotkeys", {}).get("keys", [])
            new_backend = new_config.get("hotkeys", {}).get("backend", "pynput")

            # 验证新配置
            if not new_keys:
                return ReloadResult(
                    success=False,
                    message="Hotkeys cannot be empty"
                )

            if new_backend not in ["pynput", "win32"]:
                return ReloadResult(
                    success=False,
                    message=f"Unsupported hotkey backend: {new_backend}"
                )

            # 保存回滚数据
            rollback_data = {
                "backend": self._current_backend,
                "keys": self._current_keys.copy(),
                "manager": self._manager,  # 保存当前管理器实例
            }

            app_logger.log_audio_event(
                "HotkeyService prepare_reload success",
                {
                    "old_backend": self._current_backend,
                    "new_backend": new_backend,
                    "old_keys": self._current_keys,
                    "new_keys": new_keys,
                }
            )

            return ReloadResult(
                success=True,
                message="Preparation successful",
                rollback_data=rollback_data
            )

        except Exception as e:
            app_logger.log_error(e, "HotkeyService.prepare_reload")
            return ReloadResult(
                success=False,
                message=f"Preparation failed: {str(e)}"
            )

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
            new_keys = new_config.get("hotkeys", {}).get("keys", [])
            new_backend = new_config.get("hotkeys", {}).get("backend", "pynput")

            if strategy == ReloadStrategy.REINITIALIZE:
                # 仅热键变更，调用管理器的 reload()
                app_logger.log_audio_event(
                    "Reloading hotkeys (same backend)",
                    {"backend": self._current_backend, "new_keys": new_keys}
                )

                if self._manager and hasattr(self._manager, "reload"):
                    self._manager.reload(new_keys)
                    self._current_keys = new_keys
                else:
                    return ReloadResult(
                        success=False,
                        message=f"Manager {self._current_backend} doesn't support reload"
                    )

                return ReloadResult(success=True, message="Hotkeys reloaded")

            elif strategy == ReloadStrategy.RECREATE:
                # RECREATE 策略由 Coordinator 处理
                # 但为了完整性，也实现一下后端切换逻辑
                app_logger.log_audio_event(
                    "Switching hotkey backend",
                    {"old": self._current_backend, "new": new_backend}
                )

                # 1. 停止旧管理器
                if self._manager:
                    try:
                        if hasattr(self._manager, "unregister_all_hotkeys"):
                            self._manager.unregister_all_hotkeys()
                        if hasattr(self._manager, "stop_listening"):
                            self._manager.stop_listening()
                    except Exception as e:
                        app_logger.log_error(e, "Failed to cleanup old hotkey manager")

                # 2. 创建新管理器
                self._create_manager(new_backend)

                # 3. 注册新热键
                if self._manager:
                    for key in new_keys:
                        try:
                            self._manager.register_hotkey(key, "toggle_recording")
                        except Exception as e:
                            app_logger.log_error(
                                e,
                                f"Failed to register hotkey: {key}"
                            )

                    # 4. 启动新管理器
                    if hasattr(self._manager, "start_listening"):
                        self._manager.start_listening()

                # 5. 更新状态
                self._current_backend = new_backend
                self._current_keys = new_keys

                app_logger.log_audio_event(
                    "Hotkey backend switched",
                    {"backend": new_backend, "keys": new_keys}
                )

                return ReloadResult(success=True, message="Backend switched")

            else:
                return ReloadResult(
                    success=False,
                    message=f"Unknown strategy: {strategy}"
                )

        except Exception as e:
            app_logger.log_error(e, "HotkeyService.commit_reload")
            return ReloadResult(
                success=False,
                message=f"Commit failed: {str(e)}"
            )

    def rollback_reload(self, rollback_data: Dict[str, Any]) -> bool:
        """回滚到之前的配置状态

        Args:
            rollback_data: prepare_reload 返回的回滚数据

        Returns:
            是否回滚成功
        """
        try:
            # 恢复管理器状态
            if "manager" in rollback_data:
                # 停止当前管理器
                if self._manager:
                    try:
                        if hasattr(self._manager, "unregister_all_hotkeys"):
                            self._manager.unregister_all_hotkeys()
                        if hasattr(self._manager, "stop_listening"):
                            self._manager.stop_listening()
                    except Exception as e:
                        app_logger.log_error(e, "Failed to cleanup during rollback")

                # 恢复旧管理器
                self._manager = rollback_data["manager"]

            if "backend" in rollback_data:
                self._current_backend = rollback_data["backend"]

            if "keys" in rollback_data:
                self._current_keys = rollback_data["keys"]

            app_logger.log_audio_event(
                "HotkeyService rollback successful",
                {
                    "backend": self._current_backend,
                    "keys": self._current_keys,
                }
            )

            return True

        except Exception as e:
            app_logger.log_error(e, "HotkeyService.rollback_reload")
            return False

    # ========== 公共接口 ==========

    @property
    def is_listening(self) -> bool:
        """是否正在监听热键"""
        if self._manager:
            return self._manager.is_listening
        return False

    def get_registered_hotkeys(self) -> Dict[str, str]:
        """获取已注册的热键

        Returns:
            热键映射字典
        """
        if self._manager:
            return self._manager.get_registered_hotkeys()
        return {}

    @property
    def current_backend(self) -> str:
        """当前使用的后端"""
        return self._current_backend
