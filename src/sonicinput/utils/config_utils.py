"""Common configuration utilities

Provides shared configuration patterns to eliminate code duplication
across the codebase.
"""

from typing import Any, Dict, Optional
from pathlib import Path
import json


class ConfigMerger:
    """Utility for merging configuration dictionaries with consistent patterns"""

    @staticmethod
    def merge_recursive(
        base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively merge two configuration dictionaries

        Args:
            base: Base configuration dictionary
            override: Configuration to merge into base

        Returns:
            Merged configuration dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = ConfigMerger.merge_recursive(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def ensure_structure(
        config: Dict[str, Any], required_structure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ensure configuration has required structure, adding missing sections

        Args:
            config: Configuration to validate/repair
            required_structure: Required structure with default values

        Returns:
            Configuration with ensured structure
        """
        result = config.copy()

        for key, default_value in required_structure.items():
            if key not in result:
                result[key] = default_value
            elif isinstance(default_value, dict) and isinstance(result[key], dict):
                result[key] = ConfigMerger.ensure_structure(result[key], default_value)
            elif isinstance(default_value, dict) and not isinstance(result[key], dict):
                # Repair corrupted structure
                result[key] = default_value

        return result


class ConfigPathHelper:
    """Helper for working with configuration file paths"""

    @staticmethod
    def ensure_config_dir(config_path: Path) -> bool:
        """Ensure the configuration directory exists

        Args:
            config_path: Path to configuration file

        Returns:
            True if directory exists or was created successfully
        """
        try:
            config_dir = config_path.parent
            config_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception:
            return False

    @staticmethod
    def backup_config(config_path: Path, backup_suffix: str = ".backup") -> bool:
        """Create a backup of the configuration file

        Args:
            config_path: Path to configuration file
            backup_suffix: Suffix for backup file

        Returns:
            True if backup was created successfully
        """
        try:
            if config_path.exists():
                backup_path = config_path.with_suffix(
                    config_path.suffix + backup_suffix
                )
                import shutil

                shutil.copy2(config_path, backup_path)
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def load_json_config(
        config_path: Path,
    ) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Load JSON configuration from file

        Args:
            config_path: Path to configuration file

        Returns:
            Tuple of (config_dict, error_message)
        """
        try:
            if not config_path.exists():
                return None, "Configuration file does not exist"

            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            if not isinstance(config, dict):
                return None, "Configuration file must contain a JSON object"

            return config, None

        except json.JSONDecodeError as e:
            return None, f"Invalid JSON in configuration file: {e}"
        except Exception as e:
            return None, f"Error reading configuration file: {e}"

    @staticmethod
    def save_json_config(config: Dict[str, Any], config_path: Path) -> Optional[str]:
        """Save configuration to JSON file

        Args:
            config: Configuration dictionary to save
            config_path: Path to save configuration file

        Returns:
            Error message if save failed, None if successful
        """
        try:
            # Ensure directory exists
            if not ConfigPathHelper.ensure_config_dir(config_path):
                return "Failed to create configuration directory"

            # Create backup if file exists
            if config_path.exists():
                ConfigPathHelper.backup_config(config_path)

            # Save configuration
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            return None

        except Exception as e:
            return f"Error saving configuration file: {e}"


def get_nested_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Get a nested configuration value using dot notation

    Args:
        config: Configuration dictionary
        key_path: Dot-separated key path (e.g., 'ui.overlay.opacity')
        default: Default value if key not found

    Returns:
        Configuration value or default
    """
    try:
        keys = key_path.split(".")
        current = config

        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return default
            current = current[key]

        return current

    except (TypeError, KeyError):
        return default


def set_nested_value(config: Dict[str, Any], key_path: str, value: Any) -> bool:
    """Set a nested configuration value using dot notation

    Args:
        config: Configuration dictionary to modify
        key_path: Dot-separated key path (e.g., 'ui.overlay.opacity')
        value: Value to set

    Returns:
        True if value was set successfully
    """
    try:
        keys = key_path.split(".")
        current = config

        # Navigate to parent of final key, creating dicts as needed
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            elif not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]

        # Set the final value
        final_key = keys[-1]
        current[final_key] = value
        return True

    except Exception:
        return False
