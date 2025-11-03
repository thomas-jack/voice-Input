"""重构后的配置服务 - 门面模式协调各专职服务

使用门面模式（Facade Pattern）协调多个专职服务，保持向后兼容的API。
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, TypeVar, List
from datetime import datetime

from ...interfaces.config import IConfigService
from ...interfaces.event import IEventService, EventPriority
from ....utils import ConfigurationError, app_logger

from .config_reader import ConfigReader
from .config_writer import ConfigWriter
from .config_validator import ConfigValidator
from .config_migrator import ConfigMigrator
from .config_backup import ConfigBackupService

T = TypeVar("T")


class RefactoredConfigService(IConfigService):
    """重构后的配置服务 - 门面模式

    协调多个专职服务提供统一的配置管理接口，保持与原ConfigService完全兼容。
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        event_service: Optional[IEventService] = None,
    ):
        """初始化配置服务

        Args:
            config_path: 配置文件路径，None 表示使用默认路径
            event_service: 事件服务实例，用于发送配置变更事件
        """
        self._event_service = event_service

        # 设置配置文件路径
        if config_path:
            self.config_path = Path(config_path)
        else:
            config_dir = Path(os.getenv("APPDATA", ".")) / "SonicInput"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "config.json"

        # 初始化各专职服务
        self._reader = ConfigReader(self.config_path)
        self._writer = ConfigWriter(self.config_path)
        self._validator = ConfigValidator()
        self._migrator = ConfigMigrator(self.config_path)
        self._backup = ConfigBackupService(self.config_path)

        # 检查并迁移旧配置文件
        self._migrator.migrate_from_old_app_name()

        # 加载配置
        self.load_config()

        # 验证和修复配置结构完整性
        self._validate_and_repair_config_structure()

        app_logger.log_audio_event(
            "ConfigService initialized",
            {
                "config_path": str(self.config_path),
                "config_exists": self.config_path.exists(),
                "structure_validated": True,
                "event_service_enabled": self._event_service is not None,
            },
        )

    def get_setting(self, key: str, default: Optional[T] = None) -> T:
        """获取配置项

        Args:
            key: 配置项键名，支持嵌套路径 (例如: "whisper.model")
            default: 默认值

        Returns:
            配置项的值，如果不存在则返回默认值
        """
        return self._reader.get_setting(key, default)

    def set_setting(self, key: str, value: Any, immediate: bool = False) -> None:
        """设置配置项

        Args:
            key: 配置项键名，支持嵌套路径
            value: 要设置的值
            immediate: 是否立即保存（默认False，使用防抖机制）

        Raises:
            ConfigurationError: 配置项无效或类型不匹配时
        """
        old_value = self.get_setting(key)

        # 更新配置
        self._writer.set_setting(key, value)

        # 同步到读取器
        self._reader._config = self._writer._config

        # 发送配置变更事件
        if self._event_service:
            self._event_service.emit(
                "config_changed",
                {
                    "key": key,
                    "old_value": old_value,
                    "new_value": value,
                    "timestamp": datetime.now().isoformat(),
                },
                EventPriority.NORMAL,
            )

        # 保存配置
        if immediate:
            if not self._writer.save_config():
                raise ConfigurationError(
                    f"Failed to save configuration after setting '{key}'"
                )
            self._send_config_saved_event()
        else:
            self._writer.schedule_save()

    def save_config(self) -> bool:
        """保存配置到文件

        Returns:
            是否保存成功
        """
        success = self._writer.save_config()

        if success:
            self._send_config_saved_event()

        return success

    def load_config(self) -> bool:
        """从文件加载配置

        Returns:
            是否加载成功
        """
        success = self._reader.load_config()

        if success:
            # 执行配置迁移
            config, migrated = self._migrator.migrate_config_structure(
                self._reader._config
            )
            self._reader._config = config
            self._writer.set_config(config)

            if migrated:
                self._writer.save_config()

            # 发送配置加载事件
            if self._event_service:
                self._event_service.emit(
                    "config_loaded",
                    {
                        "config_path": str(self.config_path),
                        "timestamp": datetime.now().isoformat(),
                    },
                    EventPriority.NORMAL,
                )

        return success

    def reset_to_default(self, key: Optional[str] = None) -> None:
        """重置配置到默认值

        Args:
            key: 要重置的配置项键名，None 表示重置所有配置
        """
        if key is None:
            # 重置所有配置
            from .config_defaults import get_default_config

            config = get_default_config()
            self._reader._config = config
            self._writer.set_config(config)
            self.save_config()

            if self._event_service:
                self._event_service.emit(
                    "config_reset",
                    {"type": "full", "timestamp": datetime.now().isoformat()},
                    EventPriority.HIGH,
                )

            app_logger.log_audio_event("Configuration reset to defaults", {})
        else:
            # 重置特定配置项
            old_value = self.get_setting(key)
            default_value = self._reader._get_default_value(key)
            if default_value is not None:
                self.set_setting(key, default_value)

                if self._event_service:
                    self._event_service.emit(
                        "config_reset",
                        {
                            "type": "single",
                            "key": key,
                            "old_value": old_value,
                            "new_value": default_value,
                            "timestamp": datetime.now().isoformat(),
                        },
                        EventPriority.NORMAL,
                    )

    def validate_config(self) -> Dict[str, Any]:
        """验证配置完整性

        Returns:
            验证结果，包含错误信息和修复建议
        """
        return self._validator.validate_config(self._reader._config)

    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有配置的副本

        Returns:
            配置字典的深拷贝
        """
        return self._reader.get_all_settings()

    def get_config_path(self) -> Path:
        """获取配置文件路径

        Returns:
            配置文件的路径
        """
        return self.config_path

    def export_config(self, target_path: Union[str, Path]) -> bool:
        """导出配置到指定路径

        Args:
            target_path: 目标文件路径

        Returns:
            是否导出成功
        """
        return self._backup.export_config(self._reader._config, target_path)

    def import_config(self, source_path: Union[str, Path]) -> bool:
        """从指定路径导入配置

        Args:
            source_path: 源文件路径

        Returns:
            是否导入成功
        """
        imported_config = self._backup.import_config(source_path)

        if imported_config is not None:
            # 合并配置
            old_config = self._reader._config.copy()
            merged_config = self._reader._merge_configs(
                self._reader._config, imported_config
            )

            self._reader._config = merged_config
            self._writer.set_config(merged_config)

            if self.save_config():
                if self._event_service:
                    self._event_service.emit(
                        "config_imported",
                        {
                            "source_path": str(source_path),
                            "timestamp": datetime.now().isoformat(),
                        },
                        EventPriority.HIGH,
                    )
                return True
            else:
                # 恢复原配置
                self._reader._config = old_config
                self._writer.set_config(old_config)
                return False

        return False

    def backup_config(self) -> Optional[str]:
        """创建配置备份

        Returns:
            备份文件路径，失败时返回None
        """
        return self._backup.backup_config(self._reader._config)

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出配置备份

        Returns:
            备份文件信息列表
        """
        return self._backup.list_backups()

    def flush(self) -> bool:
        """立即保存所有待处理的配置更改

        Returns:
            是否保存成功
        """
        success = self._writer.flush()

        if success:
            self._send_config_saved_event()

        return success

    def cleanup(self) -> None:
        """清理资源"""
        self._writer.cleanup()
        app_logger.log_audio_event("ConfigService cleaned up", {})

    def _validate_and_repair_config_structure(self) -> bool:
        """验证和修复整个配置结构完整性

        Returns:
            是否修复成功
        """
        config, repaired = self._validator.validate_and_repair_structure(
            self._reader._config
        )

        if repaired:
            self._reader._config = config
            self._writer.set_config(config)
            self._writer.save_config()

        return True

    def _send_config_saved_event(self) -> None:
        """发送配置保存事件"""
        if self._event_service:
            self._event_service.emit(
                "config_saved",
                {
                    "config_path": str(self.config_path),
                    "timestamp": datetime.now().isoformat(),
                },
                EventPriority.NORMAL,
            )

            # 发送配置变更事件（用于热重载）
            self._event_service.emit(
                "config.changed",
                {
                    "config": self._reader._config.copy(),
                    "timestamp": datetime.now().isoformat(),
                },
                EventPriority.HIGH,
            )
