"""Common validation utilities

Provides shared validation patterns to eliminate code duplication
across the codebase.
"""

from typing import Any, Type, Union, List, Callable
from .validators import ValidationResult


def validate_type(value: Any, expected_type: Type, field_name: str = "Value") -> ValidationResult:
    """Validate that a value is of the expected type

    Args:
        value: Value to validate
        expected_type: Expected type or tuple of types
        field_name: Name of the field for error messages

    Returns:
        ValidationResult indicating if validation passed
    """
    if not isinstance(value, expected_type):
        type_name = expected_type.__name__ if hasattr(expected_type, '__name__') else str(expected_type)
        actual_type = type(value).__name__
        return ValidationResult.error(f"{field_name} must be {type_name}, got {actual_type}")

    return ValidationResult.success(value, f"{field_name} type is valid")


def validate_not_empty(value: Any, field_name: str = "Value") -> ValidationResult:
    """Validate that a value is not empty

    Args:
        value: Value to validate
        field_name: Name of the field for error messages

    Returns:
        ValidationResult indicating if validation passed
    """
    if not value:
        return ValidationResult.error(f"{field_name} cannot be empty")

    return ValidationResult.success(value, f"{field_name} is not empty")


def validate_dict_structure(value: Any, field_name: str = "Value") -> ValidationResult:
    """Validate that a value is a dictionary

    Args:
        value: Value to validate
        field_name: Name of the field for error messages

    Returns:
        ValidationResult indicating if validation passed
    """
    type_result = validate_type(value, dict, field_name)
    if not type_result.is_valid:
        return type_result

    return ValidationResult.success(value, f"{field_name} is a valid dictionary")


def validate_range(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float],
                  field_name: str = "Value") -> ValidationResult:
    """Validate that a numeric value is within a specified range

    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Name of the field for error messages

    Returns:
        ValidationResult indicating if validation passed
    """
    # First validate type
    type_result = validate_type(value, (int, float), field_name)
    if not type_result.is_valid:
        return type_result

    if value < min_val or value > max_val:
        return ValidationResult.error(f"{field_name} must be between {min_val} and {max_val}, got {value}")

    return ValidationResult.success(value, f"{field_name} is within valid range")


def validate_in_choices(value: Any, choices: List[Any], field_name: str = "Value") -> ValidationResult:
    """Validate that a value is in a list of allowed choices

    Args:
        value: Value to validate
        choices: List of allowed values
        field_name: Name of the field for error messages

    Returns:
        ValidationResult indicating if validation passed
    """
    if value not in choices:
        choices_str = ", ".join(str(c) for c in choices)
        return ValidationResult.error(f"{field_name} must be one of: {choices_str}, got {value}")

    return ValidationResult.success(value, f"{field_name} is a valid choice")


def validate_chain(*validators: Callable[[], ValidationResult]) -> ValidationResult:
    """Chain multiple validators together, stopping at first failure

    Args:
        *validators: Functions that return ValidationResult

    Returns:
        ValidationResult indicating if all validations passed
    """
    for validator in validators:
        result = validator()
        if not result.is_valid:
            return result

    return ValidationResult.success(None, "All validations passed")


def validate_config_structure(config: Any, required_keys: List[str],
                            field_name: str = "Configuration") -> ValidationResult:
    """Validate that a configuration has required keys and proper structure

    Args:
        config: Configuration to validate
        required_keys: List of required keys (supports dot notation)
        field_name: Name of the field for error messages

    Returns:
        ValidationResult indicating if validation passed
    """
    # First validate it's a dict
    type_result = validate_dict_structure(config, field_name)
    if not type_result.is_valid:
        return type_result

    missing_keys = []
    for key in required_keys:
        if '.' in key:
            # Handle nested keys
            keys = key.split('.')
            current = config
            try:
                for k in keys:
                    if not isinstance(current, dict) or k not in current:
                        missing_keys.append(key)
                        break
                    current = current[k]
            except (TypeError, KeyError):
                missing_keys.append(key)
        else:
            # Handle simple keys
            if key not in config:
                missing_keys.append(key)

    if missing_keys:
        return ValidationResult.error(f"{field_name} missing required keys: {missing_keys}")

    return ValidationResult.success(config, f"{field_name} structure is valid")


class ConfigValidator:
    """Helper class for validating configuration sections with consistent patterns"""

    def __init__(self, config: dict, section_name: str):
        self.config = config
        self.section_name = section_name
        self.errors = []

    def require_key(self, key: str, expected_type: Type = None) -> 'ConfigValidator':
        """Require a key to exist, optionally with a specific type"""
        if key not in self.config:
            self.errors.append(f"Missing required key: {key}")
            return self

        if expected_type and not isinstance(self.config[key], expected_type):
            type_name = expected_type.__name__ if hasattr(expected_type, '__name__') else str(expected_type)
            actual_type = type(self.config[key]).__name__
            self.errors.append(f"Key '{key}' must be {type_name}, got {actual_type}")

        return self

    def validate_range_key(self, key: str, min_val: Union[int, float], max_val: Union[int, float]) -> 'ConfigValidator':
        """Validate that a key's value is within a range"""
        if key not in self.config:
            return self

        value = self.config[key]
        if not isinstance(value, (int, float)):
            self.errors.append(f"Key '{key}' must be numeric")
            return self

        if value < min_val or value > max_val:
            self.errors.append(f"Key '{key}' must be between {min_val} and {max_val}, got {value}")

        return self

    def validate_choices_key(self, key: str, choices: List[Any]) -> 'ConfigValidator':
        """Validate that a key's value is in allowed choices"""
        if key not in self.config:
            return self

        value = self.config[key]
        if value not in choices:
            choices_str = ", ".join(str(c) for c in choices)
            self.errors.append(f"Key '{key}' must be one of: {choices_str}, got {value}")

        return self

    def get_result(self) -> ValidationResult:
        """Get the final validation result"""
        if self.errors:
            error_message = f"{self.section_name} validation failed: " + "; ".join(self.errors)
            return ValidationResult.error(error_message)

        return ValidationResult.success(self.config, f"{self.section_name} validation passed")