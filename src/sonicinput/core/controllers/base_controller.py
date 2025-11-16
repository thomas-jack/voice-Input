"""Base controller class for all controllers

Provides common initialization, event handling, and logging patterns
to eliminate code duplication across controllers.
"""

from typing import Optional, Dict, Any
from abc import ABC
from ..interfaces import (
    IConfigService,
    IEventService,
    IStateManager,
)
from ...utils import app_logger
from .logging_helper import ControllerLogging


class BaseController(ABC):
    """Abstract base class for all controllers

    Provides:
    - Common initialization with required services
    - Standard instance variable setup
    - Event listener registration pattern
    - Standardized logging and error handling
    - Template methods for subclass customization

    All controllers should inherit from this class to ensure
    consistent patterns and reduce code duplication.
    """

    def __init__(
        self,
        config_service: IConfigService,
        event_service: IEventService,
        state_manager: IStateManager,
    ):
        """Initialize base controller with required services

        Args:
            config_service: Configuration management service
            event_service: Event bus for pub/sub communication
            state_manager: Application state management

        Example:
            class MyController(BaseController):
                def __init__(self, config, events, state, other_service):
                    super().__init__(config, events, state)
                    self._other_service = other_service
                    self._register_event_listeners()
                    self._log_initialization()
        """
        # Required services (all controllers use these)
        self._config = config_service
        self._events = event_service
        self._state = state_manager

        # Component name (for logging)
        self._component_name = self.__class__.__name__

    # ========== Template Methods (for subclass override) ==========

    def _register_event_listeners(self) -> None:
        """Register event listeners for this controller

        Override in subclass to register event listeners.
        This is called from subclass __init__ after all setup is complete.

        Example:
            def _register_event_listeners(self):
                self._events.on("transcription_request", self._on_transcription_request)
                self._events.on(Events.CUSTOM_EVENT, self._on_custom_event)
        """
        pass

    def _get_component_context(self) -> Dict[str, Any]:
        """Provide component-specific logging context

        Override in subclass to add component-specific context.
        This context is included in initialization and error logs.

        Returns:
            Dictionary with component-specific context for logging

        Example:
            def _get_component_context(self):
                return {
                    "ai_enabled": self._config.get_setting("ai.enabled"),
                    "provider": self._config.get_setting("ai.provider"),
                    "version": "1.0"
                }
        """
        return {}

    # ========== Protected Helper Methods ==========

    def _log_initialization(self) -> None:
        """Log component initialization with standard format

        Call this at the end of your __init__ method after all setup is complete.
        This logs the component initialization with any context provided by
        _get_component_context().

        Example:
            def __init__(self, config, events, state, service):
                super().__init__(config, events, state)
                self._service = service
                self._register_event_listeners()
                self._log_initialization()  # Always call this last
        """
        context = self._get_component_context()
        ControllerLogging.log_initialization(self._component_name, context)

    def _emit_event(self, event_name: str, data: Optional[Any] = None) -> None:
        """Safely emit event through event service

        Wraps event emission with error handling to ensure
        event bus errors don't crash the controller.

        Args:
            event_name: Name of event to emit
            data: Optional event data payload

        Example:
            self._emit_event("custom_event", {"status": "completed"})
            self._emit_event(Events.RECORDING_STARTED)
        """
        try:
            self._events.emit(event_name, data)
        except Exception as e:
            app_logger.log_error(
                e,
                f"emit_event_{event_name}",
                context={"event": event_name, "has_data": data is not None},
            )

    def _get_config_setting(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration setting with error handling

        Retrieves a configuration setting with automatic fallback
        to default value if retrieval fails.

        Args:
            key: Configuration key (e.g., "audio.device_id")
            default: Default value if key not found or error occurs

        Returns:
            Configuration value or default

        Example:
            sample_rate = self._get_config_setting("audio.sample_rate", 16000)
            device_id = self._get_config_setting("audio.device_id")
        """
        try:
            return self._config.get_setting(key, default)
        except Exception as e:
            app_logger.log_error(
                e,
                "get_config_setting",
                context={"key": key, "has_default": default is not None},
            )
            return default

    def _set_config_setting(self, key: str, value: Any) -> bool:
        """Set configuration setting with error handling

        Updates a configuration setting with error handling.
        Returns success/failure status.

        Args:
            key: Configuration key to set
            value: Value to set

        Returns:
            True if successful, False on error

        Example:
            success = self._set_config_setting("ai.enabled", True)
            if not success:
                # Handle error
        """
        try:
            self._config.set_setting(key, value)
            return True
        except Exception as e:
            app_logger.log_error(e, "set_config_setting", context={"key": key})
            return False
