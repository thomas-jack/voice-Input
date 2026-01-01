"""Input validation utilities

Provides comprehensive validation functions for configuration values,
user inputs, and data integrity checking.
"""

import re
from pathlib import Path
from typing import Any, Dict, Union

from ..core.services.config.audio_constants import Audio
from ..core.services.config.config_keys import ConfigKeys
from ..core.services.config.ui_constants import UI
from ..core.services.config.validation_constants import Limits, Patterns
from ..core.services.config.whisper_constants import Whisper


class ValidationError(Exception):
    """Base exception for validation errors"""

    pass


class ConfigValidationError(ValidationError):
    """Exception raised for configuration validation errors"""

    pass


class AudioValidationError(ValidationError):
    """Exception raised for audio-related validation errors"""

    pass


class NetworkValidationError(ValidationError):
    """Exception raised for network-related validation errors"""

    pass


class ValidationResult:
    """Validation result container"""

    def __init__(self, is_valid: bool, message: str = "", value: Any = None):
        self.is_valid = is_valid
        self.message = message
        self.value = value

    def __bool__(self) -> bool:
        return self.is_valid

    @classmethod
    def success(cls, value: Any = None, message: str = "Valid") -> "ValidationResult":
        """Create a successful validation result"""
        return cls(True, message, value)

    @classmethod
    def error(cls, message: str, value: Any = None) -> "ValidationResult":
        """Create a failed validation result"""
        return cls(False, message, value)


class ConfigValidator:
    """Configuration value validator"""

    @staticmethod
    def validate_hotkey(hotkey: str) -> ValidationResult:
        """Validate hotkey format

        Args:
            hotkey: Hotkey string to validate

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(hotkey, str):
            return ValidationResult.error("Hotkey must be a string")

        if not hotkey:
            return ValidationResult.error("Hotkey cannot be empty")

        # Normalize the hotkey
        normalized = hotkey.lower().replace(" ", "")

        if not re.match(Patterns.HOTKEY_PATTERN, normalized):
            return ValidationResult.error(
                f"Invalid hotkey format. Expected format: 'ctrl+shift+key' or similar. Got: {hotkey}"
            )

        return ValidationResult.success(normalized, "Valid hotkey format")

    @staticmethod
    def validate_whisper_model(model: str) -> ValidationResult:
        """Validate Whisper model name

        Args:
            model: Model name to validate

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(model, str):
            return ValidationResult.error("Model name must be a string")

        if model not in Whisper.AVAILABLE_MODELS:
            return ValidationResult.error(
                f"Invalid Whisper model. Available models: {', '.join(Whisper.AVAILABLE_MODELS)}"
            )

        return ValidationResult.success(model, "Valid Whisper model")

    @staticmethod
    def validate_language_code(language: str) -> ValidationResult:
        """Validate language code

        Args:
            language: Language code to validate

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(language, str):
            return ValidationResult.error("Language code must be a string")

        if language == "auto":
            return ValidationResult.success(language, "Auto-detection language")

        if language not in Whisper.LANGUAGE_CODES:
            available = ", ".join(Whisper.LANGUAGE_CODES.keys())
            return ValidationResult.error(
                f"Invalid language code. Available languages: {available}"
            )

        return ValidationResult.success(language, "Valid language code")

    @staticmethod
    def validate_sample_rate(sample_rate: int) -> ValidationResult:
        """Validate audio sample rate

        Args:
            sample_rate: Sample rate to validate

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(sample_rate, int):
            return ValidationResult.error("Sample rate must be an integer")

        if sample_rate < Limits.MIN_SAMPLE_RATE or sample_rate > Limits.MAX_SAMPLE_RATE:
            return ValidationResult.error(
                f"Sample rate must be between {Limits.MIN_SAMPLE_RATE} and {Limits.MAX_SAMPLE_RATE} Hz"
            )

        if sample_rate not in Audio.SAMPLE_RATES:
            available = ", ".join(map(str, Audio.SAMPLE_RATES))
            return ValidationResult.error(
                f"Sample rate not in recommended values. Available: {available} Hz"
            )

        return ValidationResult.success(sample_rate, "Valid sample rate")

    @staticmethod
    def validate_api_key(
        api_key: str, provider: str = "openrouter"
    ) -> ValidationResult:
        """Validate API key format

        Args:
            api_key: API key to validate
            provider: API provider name

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(api_key, str):
            return ValidationResult.error("API key must be a string")

        if not api_key:
            return ValidationResult.error("API key cannot be empty")

        # Check for common patterns
        if provider.lower() == "openrouter":
            if not re.match(Patterns.OPENROUTER_API_KEY_PATTERN, api_key):
                return ValidationResult.error(
                    "Invalid OpenRouter API key format. Should start with 'sk-' followed by alphanumeric characters"
                )

        return ValidationResult.success(api_key, f"Valid {provider} API key format")

    @staticmethod
    def validate_timeout(timeout: Union[int, float]) -> ValidationResult:
        """Validate timeout value

        Args:
            timeout: Timeout value in seconds

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(timeout, (int, float)):
            return ValidationResult.error("Timeout must be a number")

        if timeout < Limits.MIN_TIMEOUT or timeout > Limits.MAX_TIMEOUT:
            return ValidationResult.error(
                f"Timeout must be between {Limits.MIN_TIMEOUT} and {Limits.MAX_TIMEOUT} seconds"
            )

        return ValidationResult.success(timeout, "Valid timeout value")

    @staticmethod
    def validate_path(
        path: str,
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_dir: bool = False,
    ) -> ValidationResult:
        """Validate file/directory path

        Args:
            path: Path to validate
            must_exist: Whether path must exist
            must_be_file: Whether path must be a file
            must_be_dir: Whether path must be a directory

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(path, str):
            return ValidationResult.error("Path must be a string")

        if not path:
            return ValidationResult.error("Path cannot be empty")

        try:
            path_obj = Path(path)

            if must_exist and not path_obj.exists():
                return ValidationResult.error(f"Path does not exist: {path}")

            if must_be_file and path_obj.exists() and not path_obj.is_file():
                return ValidationResult.error(f"Path is not a file: {path}")

            if must_be_dir and path_obj.exists() and not path_obj.is_dir():
                return ValidationResult.error(f"Path is not a directory: {path}")

            return ValidationResult.success(str(path_obj), "Valid path")

        except (OSError, ValueError) as e:
            return ValidationResult.error(f"Invalid path format: {e}")

    @staticmethod
    def validate_percentage(
        value: Union[int, float], allow_zero: bool = True, allow_hundred: bool = True
    ) -> ValidationResult:
        """Validate percentage value (0-100)

        Args:
            value: Percentage value to validate
            allow_zero: Whether 0% is allowed
            allow_hundred: Whether 100% is allowed

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(value, (int, float)):
            return ValidationResult.error("Percentage must be a number")

        min_val = 0 if allow_zero else 0.01
        max_val = 100 if allow_hundred else 99.99

        if value < min_val or value > max_val:
            return ValidationResult.error(
                f"Percentage must be between {min_val}% and {max_val}%"
            )

        return ValidationResult.success(value, "Valid percentage")

    @staticmethod
    def validate_opacity(opacity: Union[int, float]) -> ValidationResult:
        """Validate opacity value (0.0-1.0)

        Args:
            opacity: Opacity value to validate

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(opacity, (int, float)):
            return ValidationResult.error("Opacity must be a number")

        if opacity < 0.0 or opacity > 1.0:
            return ValidationResult.error("Opacity must be between 0.0 and 1.0")

        return ValidationResult.success(float(opacity), "Valid opacity value")


class AudioValidator:
    """Audio-related validator"""

    @staticmethod
    def validate_audio_device_id(device_id: Union[int, str, None]) -> ValidationResult:
        """Validate audio device ID

        Args:
            device_id: Device ID to validate

        Returns:
            ValidationResult with validation status
        """
        if device_id is None:
            return ValidationResult.success(None, "Default device")

        if isinstance(device_id, str):
            if device_id.lower() in ["default", "auto"]:
                return ValidationResult.success(device_id, "Default device selection")

        if isinstance(device_id, int):
            if device_id < 0:
                return ValidationResult.error("Device ID cannot be negative")
            return ValidationResult.success(device_id, "Valid device ID")

        return ValidationResult.error(
            "Device ID must be an integer, 'default', or None"
        )

    @staticmethod
    def validate_channels(channels: int) -> ValidationResult:
        """Validate audio channels

        Args:
            channels: Number of channels

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(channels, int):
            return ValidationResult.error("Channels must be an integer")

        if channels < 1 or channels > 2:
            return ValidationResult.error("Channels must be 1 (mono) or 2 (stereo)")

        return ValidationResult.success(channels, "Valid channel count")

    @staticmethod
    def validate_chunk_size(chunk_size: int) -> ValidationResult:
        """Validate audio chunk size

        Args:
            chunk_size: Chunk size to validate

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(chunk_size, int):
            return ValidationResult.error("Chunk size must be an integer")

        if chunk_size < Limits.MIN_CHUNK_SIZE or chunk_size > Limits.MAX_CHUNK_SIZE:
            return ValidationResult.error(
                f"Chunk size must be between {Limits.MIN_CHUNK_SIZE} and {Limits.MAX_CHUNK_SIZE}"
            )

        # Check if it's a power of 2
        if chunk_size & (chunk_size - 1) != 0:
            return ValidationResult.error(
                "Chunk size should be a power of 2 for optimal performance"
            )

        return ValidationResult.success(chunk_size, "Valid chunk size")


class UIValidator:
    """UI-related validator"""

    @staticmethod
    def validate_position_preset(preset: str) -> ValidationResult:
        """Validate overlay position preset

        Args:
            preset: Position preset name

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(preset, str):
            return ValidationResult.error("Position preset must be a string")

        if preset not in UI.POSITION_PRESETS:
            available = ", ".join(UI.POSITION_PRESETS.keys())
            return ValidationResult.error(
                f"Invalid position preset. Available: {available}"
            )

        return ValidationResult.success(preset, "Valid position preset")

    @staticmethod
    def validate_coordinates(x: int, y: int) -> ValidationResult:
        """Validate screen coordinates

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(x, int) or not isinstance(y, int):
            return ValidationResult.error("Coordinates must be integers")

        # Allow negative values for relative positioning
        if abs(x) > 10000 or abs(y) > 10000:
            return ValidationResult.error("Coordinates are out of reasonable range")

        return ValidationResult.success((x, y), "Valid coordinates")

    @staticmethod
    def validate_theme(theme: str) -> ValidationResult:
        """Validate UI theme

        Args:
            theme: Theme name

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(theme, str):
            return ValidationResult.error("Theme must be a string")

        valid_themes = ["light", "dark", "auto"]
        if theme not in valid_themes:
            return ValidationResult.error(
                f"Invalid theme. Available: {', '.join(valid_themes)}"
            )

        return ValidationResult.success(theme, "Valid theme")


class NetworkValidator:
    """Network-related validator"""

    @staticmethod
    def validate_url(url: str) -> ValidationResult:
        """Validate URL format

        Args:
            url: URL to validate

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(url, str):
            return ValidationResult.error("URL must be a string")

        if not url:
            return ValidationResult.error("URL cannot be empty")

        # Basic URL validation
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
            r"localhost|"  # localhost...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(url):
            return ValidationResult.error("Invalid URL format")

        return ValidationResult.success(url, "Valid URL format")

    @staticmethod
    def validate_port(port: int) -> ValidationResult:
        """Validate port number

        Args:
            port: Port number

        Returns:
            ValidationResult with validation status
        """
        if not isinstance(port, int):
            return ValidationResult.error("Port must be an integer")

        if port < 1 or port > 65535:
            return ValidationResult.error("Port must be between 1 and 65535")

        return ValidationResult.success(port, "Valid port number")


class CompleteConfigValidator:
    """Complete configuration validator"""

    def __init__(self):
        self.config_validator = ConfigValidator()
        self.audio_validator = AudioValidator()
        self.ui_validator = UIValidator()
        self.network_validator = NetworkValidator()

    def validate_configuration(
        self, config: Dict[str, Any]
    ) -> Dict[str, ValidationResult]:
        """Validate complete configuration

        Args:
            config: Configuration dictionary

        Returns:
            Dictionary of validation results for each key
        """
        results = {}

        # Define validation rules
        validation_rules = {
            ConfigKeys.RECORDING_HOTKEY: self.config_validator.validate_hotkey,
            ConfigKeys.WHISPER_MODEL: self.config_validator.validate_whisper_model,
            ConfigKeys.SPEECH_LANGUAGE: self.config_validator.validate_language_code,
            ConfigKeys.AUDIO_SAMPLE_RATE: self.config_validator.validate_sample_rate,
            ConfigKeys.OPENROUTER_API_KEY: lambda key: self.config_validator.validate_api_key(
                key, "openrouter"
            ),
            ConfigKeys.AUDIO_INPUT_DEVICE: self.audio_validator.validate_audio_device_id,
            ConfigKeys.AUDIO_CHANNELS: self.audio_validator.validate_channels,
            ConfigKeys.OVERLAY_POSITION: self.ui_validator.validate_position_preset,
            ConfigKeys.OVERLAY_OPACITY: self.config_validator.validate_opacity,
            ConfigKeys.UI_THEME: self.ui_validator.validate_theme,
        }

        # Validate each configured key
        for key, value in config.items():
            if key in validation_rules:
                try:
                    results[key] = validation_rules[key](value)
                except Exception as e:
                    results[key] = ValidationResult.error(f"Validation error: {str(e)}")

        return results

    def get_validation_summary(
        self, results: Dict[str, ValidationResult]
    ) -> Dict[str, Any]:
        """Get validation summary

        Args:
            results: Validation results

        Returns:
            Summary dictionary
        """
        valid_count = sum(1 for result in results.values() if result.is_valid)
        total_count = len(results)

        errors = [
            f"{key}: {result.message}"
            for key, result in results.items()
            if not result.is_valid
        ]

        return {
            "valid": valid_count == total_count,
            "valid_count": valid_count,
            "total_count": total_count,
            "errors": errors,
            "error_count": len(errors),
        }
