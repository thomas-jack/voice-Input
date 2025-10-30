"""增强的配置服务

基于现有 ConfigManager 的重构版本，实现完整的 IConfigService 接口。
提供类型安全的配置管理、自动修复、验证和备份功能。
"""

import json
import os
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Union, TypeVar, List
from datetime import datetime

from ..interfaces.config import IConfigService
from ..interfaces.event import IEventService, EventPriority
from ...utils import ConfigurationError, app_logger

T = TypeVar('T')


class ConfigService(IConfigService):
    """增强的配置服务

    提供类型安全的配置管理、自动修复、验证和备份功能。
    继承原有ConfigManager的所有功能，并添加事件通知。
    """

    def __init__(self, config_path: Optional[str] = None, event_service: Optional[IEventService] = None):
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
            config_dir = Path(os.getenv('APPDATA', '.')) / 'SonicInput'
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / 'config.json'

        self._config = {}
        self._default_config = self._get_default_config()

        # 防抖保存机制
        self._dirty = False
        self._save_timer: Optional[threading.Timer] = None
        self._save_delay = 0.5  # 500ms 防抖延迟
        self._timer_lock = threading.Lock()

        # 检查并迁移旧配置文件（VoiceInputSoftware → SonicInput）
        self._migrate_from_old_app_name()

        # 加载配置
        self.load_config()

        # 验证和修复配置结构完整性
        self._validate_and_repair_config_structure()

        app_logger.log_audio_event("ConfigService initialized", {
            "config_path": str(self.config_path),
            "config_exists": self.config_path.exists(),
            "structure_validated": True,
            "event_service_enabled": self._event_service is not None
        })

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "hotkeys": ["ctrl+shift+v"],
            "whisper": {
                "model": "large-v3-turbo",
                "language": "auto",
                "use_gpu": True,
                "auto_load": True,
                "temperature": 0.0,
                "device": "auto",
                "compute_type": "auto"
            },
            "ai": {
                "provider": "openrouter",
                "enabled": True,
                "filter_thinking": True,
                "prompt": "You are a professional transcription refinement specialist. Your task is to correct and improve text that has been transcribed by an automatic speech recognition (ASR) system.\n\nYour responsibilities:\n1. Remove filler words (um, uh, like, you know, etc.) and disfluencies\n2. Correct homophones and misrecognized words to their contextually appropriate forms\n3. Fix grammatical errors and improve sentence structure\n4. Preserve the original meaning and intent of the speaker\n5. Maintain natural language flow\n\nImportant constraints:\n- Output ONLY the corrected text, nothing else\n- Do NOT add explanations, comments, or metadata\n- Do NOT change the core message or add information not present in the original\n- Maintain the speaker's tone and style",
                "timeout": 30,
                "retries": 3,
                "openrouter": {
                    "api_key": "",
                    "model_id": "anthropic/claude-3-sonnet"
                },
                "groq": {
                    "api_key": "",
                    "model_id": "llama-3.3-70b-versatile"
                },
                "nvidia": {
                    "api_key": "",
                    "model_id": "meta/llama-3.1-8b-instruct"
                },
                "openai_compatible": {
                    "api_key": "",
                    "base_url": "http://localhost:1234/v1",
                    "model_id": "local-model"
                }
            },
            "audio": {
                "sample_rate": 16000,
                "channels": 1,
                "device_id": None,
                "chunk_size": 1024
            },
            "ui": {
                "show_overlay": True,
                "overlay_position": {
                    "mode": "preset",  # "preset" | "custom"
                    "preset": "center",  # 预设位置作为fallback
                    "custom": {
                        "x": 0,
                        "y": 0
                    },
                    "last_screen": {
                        "index": 0,
                        "name": "",
                        "geometry": "",
                        "device_pixel_ratio": 1.0
                    },
                    "auto_save": True
                },
                "overlay_always_on_top": True,
                "tray_notifications": False,
                "start_minimized": True,
                "theme_color": "cyan"
            },
            "input": {
                "preferred_method": "clipboard",
                "fallback_enabled": True,
                "auto_detect_terminal": True,
                "clipboard_restore_delay": 2.0,
                "typing_delay": 0.01
            },
            "logging": {
                "level": "INFO",
                "console_output": True,
                "max_log_size_mb": 10,
                "keep_logs_days": 7,
                "enabled_categories": ["audio", "api", "ui", "model", "hotkey", "gpu", "startup", "error", "performance"]
            },
            "advanced": {
                "gpu_memory_fraction": 0.8,
                "audio_processing": {
                    "normalize_audio": True,
                    "remove_silence": True,
                    "noise_reduction": True
                },
                "performance": {
                    "preload_model": True,
                    "cache_audio": False,
                    "parallel_processing": False
                }
            }
        }

    def get_setting(self, key: str, default: Optional[T] = None) -> T:
        """获取配置项

        Args:
            key: 配置项键名，支持嵌套路径 (例如: "whisper.model")
            default: 默认值

        Returns:
            配置项的值，如果不存在则返回默认值
        """
        try:
            keys = key.split('.')
            value = self._config

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value

        except Exception as e:
            app_logger.log_error(e, f"get_setting_{key}")
            return default

    def set_setting(self, key: str, value: Any, immediate: bool = False) -> None:
        """设置配置项

        Args:
            key: 配置项键名，支持嵌套路径
            value: 要设置的值
            immediate: 是否立即保存（默认False，使用防抖机制）

        Raises:
            ConfigurationError: 配置项无效或类型不匹配时
        """
        try:
            keys = key.split('.')
            config = self._config
            old_value = self.get_setting(key)

            # 导航到正确的嵌套位置，包含类型验证和自修复
            for i, k in enumerate(keys[:-1]):
                if k not in config:
                    config[k] = {}
                    app_logger.log_audio_event("Config auto-created missing key", {
                        "key": k,
                        "path": ".".join(keys[:i+1])
                    })
                elif not isinstance(config[k], dict):
                    # 关键修复：检测到非字典类型时自动修复
                    old_type = type(config[k]).__name__
                    config[k] = {}
                    app_logger.log_audio_event("Config auto-repaired type conflict", {
                        "key": k,
                        "path": ".".join(keys[:i+1]),
                        "old_type": old_type,
                        "new_type": "dict"
                    })
                config = config[k]

            # 设置值
            config[keys[-1]] = value

            # 发送配置变更事件（即使未立即保存）
            if self._event_service:
                self._event_service.emit("config_changed", {
                    "key": key,
                    "old_value": old_value,
                    "new_value": value,
                    "timestamp": datetime.now().isoformat()
                }, EventPriority.NORMAL)

            app_logger.log_audio_event("Setting updated", {
                "key": key,
                "value_type": type(value).__name__,
                "immediate_save": immediate
            })

            # 保存配置（使用防抖或立即保存）
            if immediate:
                if not self.save_config():
                    raise ConfigurationError(f"Failed to save configuration after setting '{key}'")
            else:
                self._schedule_save()

        except Exception as e:
            app_logger.log_error(e, f"set_setting_{key}")
            # 尝试修复损坏的配置路径
            try:
                self._repair_config_path(key)
                app_logger.log_audio_event("Config repair attempted", {
                    "key": key,
                    "error": str(e)
                })
            except Exception as repair_error:
                app_logger.log_error(repair_error, f"config_repair_{key}")

            raise ConfigurationError(f"Failed to set setting '{key}': {e}")

    def save_config(self) -> bool:
        """保存配置到文件

        Returns:
            是否保存成功
        """
        try:
            # 取消待处理的定时器
            with self._timer_lock:
                if self._save_timer is not None:
                    self._save_timer.cancel()
                    self._save_timer = None
                self._dirty = False

            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

            # 发送配置保存事件
            if self._event_service:
                self._event_service.emit("config_saved", {
                    "config_path": str(self.config_path),
                    "timestamp": datetime.now().isoformat()
                }, EventPriority.NORMAL)

                # 发送配置变更事件（用于热重载）
                self._event_service.emit("config.changed", {
                    "config": self._config.copy(),
                    "timestamp": datetime.now().isoformat()
                }, EventPriority.HIGH)

            app_logger.log_audio_event("Configuration saved", {
                "config_path": str(self.config_path),
                "keys_saved": len(self._config)
            })

            return True

        except Exception as e:
            app_logger.log_error(e, "save_config")
            return False

    def load_config(self) -> bool:
        """从文件加载配置

        Returns:
            是否加载成功
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)

                # 合并默认配置和加载的配置
                self._config = self._merge_configs(self._default_config, loaded_config)

                # 执行配置迁移（清理旧字段结构）
                self._migrate_config()

                # 发送配置加载事件
                if self._event_service:
                    self._event_service.emit("config_loaded", {
                        "config_path": str(self.config_path),
                        "timestamp": datetime.now().isoformat()
                    }, EventPriority.NORMAL)

                app_logger.log_audio_event("Configuration loaded", {
                    "config_path": str(self.config_path),
                    "keys_loaded": len(loaded_config)
                })
            else:
                # 使用默认配置
                self._config = self._default_config.copy()
                self.save_config()

                app_logger.log_audio_event("Default configuration created", {
                    "config_path": str(self.config_path)
                })

            return True

        except Exception as e:
            app_logger.log_error(e, "load_config")
            self._config = self._default_config.copy()
            return False

    def reset_to_default(self, key: Optional[str] = None) -> None:
        """重置配置到默认值

        Args:
            key: 要重置的配置项键名，None 表示重置所有配置
        """
        try:
            if key is None:
                # 重置所有配置
                self._config = self._default_config.copy()
                self.save_config()

                if self._event_service:
                    self._event_service.emit("config_reset", {
                        "type": "full",
                        "timestamp": datetime.now().isoformat()
                    }, EventPriority.HIGH)

                app_logger.log_audio_event("Configuration reset to defaults", {})
            else:
                # 重置特定配置项
                old_value = self.get_setting(key)
                default_value = self._get_default_value(key)
                if default_value is not None:
                    self.set_setting(key, default_value)

                    if self._event_service:
                        self._event_service.emit("config_reset", {
                            "type": "single",
                            "key": key,
                            "old_value": old_value,
                            "new_value": default_value,
                            "timestamp": datetime.now().isoformat()
                        }, EventPriority.NORMAL)

        except Exception as e:
            app_logger.log_error(e, "reset_to_default")
            raise ConfigurationError(f"Failed to reset configuration: {e}")

    def validate_config(self) -> Dict[str, Any]:
        """验证配置完整性

        Returns:
            验证结果，包含错误信息和修复建议
        """
        issues = []
        warnings = []

        try:
            # 验证快捷键
            hotkey = self.get_setting("hotkey", "")
            if not hotkey:
                issues.append("Hotkey is not set")

            # 验证Whisper配置
            whisper_model = self.get_setting("whisper.model", "")
            valid_models = ["tiny", "base", "small", "medium", "large-v3", "large-v3-turbo", "turbo"]
            if whisper_model not in valid_models:
                warnings.append(f"Unknown Whisper model: {whisper_model}")

            # 验证AI配置
            if self.get_setting("ai.enabled", False):
                provider = self.get_setting("ai.provider", "openrouter")
                api_key_path = f"ai.{provider}.api_key"
                api_key = self.get_setting(api_key_path, "")
                if not api_key:
                    warnings.append(f"AI is enabled (provider: {provider}) but API key is not set")

            # 验证音频配置
            sample_rate = self.get_setting("audio.sample_rate", 16000)
            if sample_rate not in [8000, 16000, 22050, 44100, 48000]:
                warnings.append(f"Unusual sample rate: {sample_rate}")

            # 验证UI配置
            theme = self.get_setting("ui.theme", "dark")
            if theme not in ["light", "dark", "auto"]:
                warnings.append(f"Unknown theme: {theme}")

            # 验证配置文件结构完整性
            structure_valid = self._validate_structure()
            if not structure_valid:
                issues.append("Configuration structure is incomplete")

        except Exception as e:
            issues.append(f"Validation error: {e}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }

    def get_all_settings(self) -> Dict[str, Any]:
        """获取所有配置的副本

        Returns:
            配置字典的深拷贝，用于读取完整配置而不暴露内部状态
        """
        return self._config.copy()

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
        try:
            target_path = Path(target_path)
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "config": self._config
            }

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            app_logger.log_audio_event("Configuration exported", {
                "file_path": str(target_path)
            })

            return True

        except Exception as e:
            app_logger.log_error(e, "export_config")
            return False

    def import_config(self, source_path: Union[str, Path]) -> bool:
        """从指定路径导入配置

        Args:
            source_path: 源文件路径

        Returns:
            是否导入成功
        """
        try:
            source_path = Path(source_path)
            with open(source_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            imported_config = import_data.get("config", {})

            # 合并配置（保留现有配置的完整性）
            old_config = self._config.copy()
            self._config = self._merge_configs(self._config, imported_config)

            if self.save_config():
                if self._event_service:
                    self._event_service.emit("config_imported", {
                        "source_path": str(source_path),
                        "timestamp": datetime.now().isoformat()
                    }, EventPriority.HIGH)

                app_logger.log_audio_event("Configuration imported", {
                    "file_path": str(source_path)
                })
                return True
            else:
                # 恢复原配置
                self._config = old_config
                return False

        except Exception as e:
            app_logger.log_error(e, "import_config")
            return False

    def backup_config(self) -> Optional[str]:
        """创建配置备份

        Returns:
            备份文件路径，失败时返回None
        """
        try:
            backup_dir = self.config_path.parent / 'backups'
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"config_backup_{timestamp}.json"

            if self.export_config(backup_path):
                app_logger.log_audio_event("Configuration backed up", {
                    "backup_path": str(backup_path)
                })
                return str(backup_path)
            else:
                return None

        except Exception as e:
            app_logger.log_error(e, "backup_config")
            return None

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出配置备份

        Returns:
            备份文件信息列表
        """
        try:
            backup_dir = self.config_path.parent / 'backups'
            if not backup_dir.exists():
                return []

            # 性能优化：使用列表推导式 + 缓存 stat() 结果（避免重复系统调用）
            backups = []
            for backup_file in backup_dir.glob("config_backup_*.json"):
                stat_info = backup_file.stat()  # 只调用一次 stat()
                backups.append({
                    "path": str(backup_file),
                    "name": backup_file.name,
                    "size": stat_info.st_size,
                    "modified": stat_info.st_mtime,
                    "modified_iso": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
                })

            # 按修改时间排序（最新的在前）
            backups.sort(key=lambda x: x["modified"], reverse=True)
            return backups

        except Exception as e:
            app_logger.log_error(e, "list_backups")
            return []

    def _get_default_value(self, key: str) -> Any:
        """获取配置项的默认值"""
        try:
            keys = key.split('.')
            value = self._default_config

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return None

            return value

        except Exception:
            return None

    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和加载的配置"""
        result = default.copy()

        def merge_recursive(base: Dict[str, Any], update: Dict[str, Any]) -> None:
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_recursive(base[key], value)
                else:
                    base[key] = value

        merge_recursive(result, loaded)
        return result

    def _migrate_from_old_app_name(self) -> None:
        """从旧应用名称 'VoiceInputSoftware' 迁移配置到 'SonicInput'

        如果新配置不存在但旧配置存在，则：
        1. 复制旧配置文件到新位置
        2. 复制日志目录（如果存在）
        3. 记录迁移操作
        """
        # 只在使用默认路径时才迁移（不是自定义配置路径）
        if str(self.config_path).find('SonicInput') == -1:
            return

        try:
            old_config_dir = Path(os.getenv('APPDATA', '.')) / 'VoiceInputSoftware'
            old_config_path = old_config_dir / 'config.json'

            # 如果新配置已存在，跳过迁移
            if self.config_path.exists():
                return

            # 如果旧配置不存在，跳过迁移
            if not old_config_path.exists():
                return

            app_logger.info("Migrating config from VoiceInputSoftware to SonicInput...")
            app_logger.info(f"  Old path: {old_config_path}")
            app_logger.info(f"  New path: {self.config_path}")

            # 复制配置文件
            import shutil
            shutil.copy2(old_config_path, self.config_path)
            app_logger.info("  Config file copied successfully")

            # 复制日志目录（如果存在）
            old_logs_dir = old_config_dir / 'logs'
            new_logs_dir = self.config_path.parent / 'logs'

            if old_logs_dir.exists() and old_logs_dir.is_dir():
                if new_logs_dir.exists():
                    app_logger.info("  New logs directory already exists, skipping logs migration")
                else:
                    shutil.copytree(old_logs_dir, new_logs_dir)
                    app_logger.info("  Logs directory copied successfully")

            app_logger.info("Config migration from VoiceInputSoftware to SonicInput completed successfully!")
            app_logger.info(f"Note: Old config directory still exists at {old_config_dir}")
            app_logger.info("      You can manually delete it if migration was successful.")

        except Exception as e:
            app_logger.log_error(e, "config_migration_from_old_app_name")
            app_logger.warning("Failed to migrate config from VoiceInputSoftware. Using default config.")

    def _migrate_config(self) -> None:
        """迁移配置结构，清理旧字段，统一为标准结构

        标准AI配置结构：
        ai:
          enabled: bool
          provider: str  (openrouter | groq)
          timeout: int
          retries: int
          prompt: str  (通用prompt，所有provider共用)
          openrouter:
            api_key: str
            model_id: str  (唯一字段名)
          groq:
            api_key: str
            model_id: str  (唯一字段名)
        """
        migrated = False

        try:
            # 1. 删除根级别的旧 openrouter 配置
            if "openrouter" in self._config:
                app_logger.info("Migrating: Removing root-level 'openrouter' config")
                del self._config["openrouter"]
                migrated = True

            # 2. 统一 AI provider 配置字段
            if "ai" in self._config:
                ai_config = self._config["ai"]

                for provider in ["openrouter", "groq"]:
                    if provider in ai_config:
                        provider_config = ai_config[provider]

                        # 迁移 model_id：优先级 model_id > simple_model_id > model
                        if "model_id" not in provider_config:
                            if "simple_model_id" in provider_config:
                                provider_config["model_id"] = provider_config["simple_model_id"]
                                app_logger.info(f"Migrating: {provider}.simple_model_id -> model_id")
                                migrated = True
                            elif "model" in provider_config:
                                provider_config["model_id"] = provider_config["model"]
                                app_logger.info(f"Migrating: {provider}.model -> model_id")
                                migrated = True

                        # 删除旧字段
                        if "simple_model_id" in provider_config:
                            del provider_config["simple_model_id"]
                            migrated = True
                        if "model" in provider_config:
                            del provider_config["model"]
                            migrated = True

                        # 删除所有 provider 级别的 prompt 字段（只用通用 ai.prompt）
                        for prompt_field in ["simple_prompt", "prompt"]:
                            if prompt_field in provider_config:
                                del provider_config[prompt_field]
                                migrated = True

                        # 删除旧的 enabled 字段（provider级别的enabled已废弃）
                        if "enabled" in provider_config:
                            del provider_config["enabled"]
                            migrated = True

                        # 删除冗余字段
                        for old_field in ["timeout", "max_retries", "custom_prompt"]:
                            if old_field in provider_config:
                                del provider_config[old_field]
                                migrated = True

            # 3. 迁移单个 hotkey 到 hotkeys 数组
            if "hotkey" in self._config and "hotkeys" not in self._config:
                old_hotkey = self._config["hotkey"]
                if isinstance(old_hotkey, str) and old_hotkey.strip():
                    self._config["hotkeys"] = [old_hotkey]
                    app_logger.info(f"Migrating: hotkey '{old_hotkey}' -> hotkeys array")
                    migrated = True
                del self._config["hotkey"]
                migrated = True
            elif "hotkey" in self._config:
                # 如果两者都存在，删除旧的
                del self._config["hotkey"]
                app_logger.info("Migrating: Removing redundant 'hotkey' field")
                migrated = True

            # 4. 保存迁移后的配置
            if migrated:
                self.save_config()
                app_logger.info("Configuration migration completed and saved")

        except Exception as e:
            app_logger.log_error(e, "migrate_config")

    def _repair_config_path(self, key: str) -> None:
        """修复损坏的配置路径"""
        keys = key.split('.')
        config = self._config

        # 重建整个路径，确保每个中间节点都是字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            elif not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        app_logger.log_audio_event("Config path repaired", {
            "key": key,
            "rebuilt_path": ".".join(keys[:-1])
        })

    def _schedule_save(self) -> None:
        """调度延迟保存（防抖）- 修复：线程安全的防抖实现"""
        with self._timer_lock:
            # 取消之前的定时器
            if self._save_timer is not None:
                self._save_timer.cancel()
                self._save_timer = None

            # 标记为脏数据（在取消定时器后，避免竞态）
            self._dirty = True

            # 创建新的定时器
            self._save_timer = threading.Timer(self._save_delay, self._perform_save)
            self._save_timer.daemon = True
            self._save_timer.start()

    def _perform_save(self) -> None:
        """执行实际保存（由定时器调用）- 修复：避免竞态条件"""
        # 读取 dirty 标志需要加锁
        with self._timer_lock:
            should_save = self._dirty

        if should_save:
            try:
                self.save_config()
            except Exception as e:
                app_logger.log_error(e, "scheduled_save")

    def flush(self) -> bool:
        """立即保存所有待处理的配置更改

        Returns:
            是否保存成功
        """
        with self._timer_lock:
            if self._save_timer is not None:
                self._save_timer.cancel()
                self._save_timer = None

        if self._dirty:
            return self.save_config()
        return True

    def _validate_and_repair_config_structure(self) -> bool:
        """验证和修复整个配置结构完整性"""
        try:
            repaired = False

            # 确保ui节点存在且为字典
            if "ui" not in self._config or not isinstance(self._config["ui"], dict):
                self._config["ui"] = {}
                repaired = True

            # 确保ui.overlay_position存在且为字典
            if ("overlay_position" not in self._config["ui"] or
                not isinstance(self._config["ui"]["overlay_position"], dict)):
                self._config["ui"]["overlay_position"] = {
                    "mode": "preset",
                    "preset": "center",
                    "custom": {"x": 0, "y": 0},
                    "auto_save": True
                }
                repaired = True

            # 确保ui.overlay_position.custom存在且为字典
            overlay_pos = self._config["ui"]["overlay_position"]
            if ("custom" not in overlay_pos or not isinstance(overlay_pos["custom"], dict)):
                overlay_pos["custom"] = {"x": 0, "y": 0}
                repaired = True

            # 检查其他关键结构
            required_structures = {
                "audio": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "device_id": None,
                    "chunk_size": 1024
                },
                "whisper": {
                    "model": "large-v3-turbo",
                    "language": "auto",
                    "device": "auto",
                    "compute_type": "auto"
                },
                "ui": {
                    "show_overlay": True,
                    "start_minimized": True
                }
            }

            for section, defaults in required_structures.items():
                if section not in self._config or not isinstance(self._config[section], dict):
                    self._config[section] = defaults
                    repaired = True
                else:
                    # 确保所有必需的键都存在
                    for key, default_value in defaults.items():
                        if key not in self._config[section]:
                            self._config[section][key] = default_value
                            repaired = True

            if repaired:
                self.save_config()

            return True

        except Exception as e:
            app_logger.log_error(e, "validate_and_repair_config_structure")
            return False

    def _validate_structure(self) -> bool:
        """验证配置结构完整性"""
        try:
            required_keys = [
                "hotkey",
                "whisper.model",
                "audio.sample_rate",
                "ui.show_overlay",
                "input.preferred_method"
            ]

            for key in required_keys:
                if self.get_setting(key) is None:
                    return False

            return True
        except Exception:
            return False

    def cleanup(self) -> None:
        """清理资源 - 取消所有待处理的定时器"""
        with self._timer_lock:
            if self._save_timer:
                self._save_timer.cancel()
                self._save_timer = None

        app_logger.log_audio_event("ConfigService cleaned up", {})