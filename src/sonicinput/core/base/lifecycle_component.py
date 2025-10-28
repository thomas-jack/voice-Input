"""Base class for lifecycle-managed components

Provides common lifecycle management functionality to eliminate code duplication
across controllers and services.
"""

import threading
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject

from ..interfaces.lifecycle import ILifecycleManaged, ComponentState
from ..interfaces.config import IConfigService
from ..interfaces.event import IEventService
from ..interfaces.state import IStateManager
from ...utils import app_logger


# Create a compatible metaclass for QObject + ABC
class QObjectABCMeta(type(QObject), type(ABC)):
    """Metaclass that combines QObject and ABC metaclasses"""
    pass


class LifecycleComponent(QObject, ILifecycleManaged, ABC, metaclass=QObjectABCMeta):
    """Base class for all lifecycle-managed components

    Provides common functionality for:
    - Component state management
    - Thread-safe operations
    - Standardized initialization/start/stop/cleanup flow
    - Health checking
    - Error handling and logging
    """

    def __init__(self,
                 component_name: str,
                 config_service: Optional[IConfigService] = None,
                 event_service: Optional[IEventService] = None,
                 state_manager: Optional[IStateManager] = None,
                 parent: Optional[QObject] = None):
        """Initialize base lifecycle component

        Args:
            component_name: Unique name for this component
            config_service: Configuration service instance
            event_service: Event service instance
            state_manager: State manager instance
            parent: Qt parent object
        """
        super().__init__(parent)

        # Core properties
        self._component_name = component_name
        self._component_state = ComponentState.UNINITIALIZED

        # Services
        self._config_service = config_service
        self._event_service = event_service
        self._state_manager = state_manager

        # Thread safety and timing
        self._lock = threading.RLock()
        self._initialized_at: Optional[float] = None
        self._started_at: Optional[float] = None
        self._stopped_at: Optional[float] = None

        # Error tracking
        self._error_count = 0
        self._last_error: Optional[str] = None
        self._last_error_time: Optional[float] = None

        self._log_event("created", {"component_name": component_name})

    # ==================== ILifecycleManaged Implementation ====================

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the component with standardized flow"""
        try:
            with self._lock:
                if self._component_state != ComponentState.UNINITIALIZED:
                    return True

                self._component_state = ComponentState.INITIALIZING
                self._log_event("initializing")

                # Call subclass-specific initialization
                success = self._do_initialize(config)

                if success:
                    self._component_state = ComponentState.INITIALIZED
                    self._initialized_at = time.time()
                    self._log_event("initialized")
                else:
                    self._component_state = ComponentState.ERROR
                    self._record_error("Initialization failed")

                return success

        except Exception as e:
            self._component_state = ComponentState.ERROR
            self._handle_exception(e, "initialize")
            return False

    def start(self) -> bool:
        """Start the component with standardized flow"""
        try:
            with self._lock:
                if self._component_state != ComponentState.INITIALIZED:
                    return False

                self._component_state = ComponentState.STARTING
                self._log_event("starting")

                # Call subclass-specific start logic
                success = self._do_start()

                if success:
                    self._component_state = ComponentState.RUNNING
                    self._started_at = time.time()
                    self._log_event("started")
                else:
                    self._component_state = ComponentState.ERROR
                    self._record_error("Start failed")

                return success

        except Exception as e:
            self._component_state = ComponentState.ERROR
            self._handle_exception(e, "start")
            return False

    def stop(self) -> bool:
        """Stop the component with standardized flow"""
        try:
            with self._lock:
                if self._component_state != ComponentState.RUNNING:
                    return True

                self._component_state = ComponentState.STOPPING
                self._log_event("stopping")

                # Call subclass-specific stop logic
                success = self._do_stop()

                if success:
                    self._component_state = ComponentState.STOPPED
                    self._stopped_at = time.time()
                    self._log_event("stopped")
                else:
                    self._component_state = ComponentState.ERROR
                    self._record_error("Stop failed")

                return success

        except Exception as e:
            self._component_state = ComponentState.ERROR
            self._handle_exception(e, "stop")
            return False

    def cleanup(self) -> None:
        """Clean up component resources with standardized flow"""
        try:
            with self._lock:
                self._log_event("cleaning_up")

                # Call subclass-specific cleanup
                self._do_cleanup()

                self._component_state = ComponentState.DESTROYED
                self._log_event("cleaned_up")

        except Exception as e:
            self._handle_exception(e, "cleanup")

    def get_state(self) -> ComponentState:
        """Get current component state"""
        return self._component_state

    def get_component_name(self) -> str:
        """Get component name"""
        return self._component_name

    def health_check(self) -> Dict[str, Any]:
        """Perform health check with standardized information"""
        try:
            # Base health information
            uptime_seconds = 0
            if self._started_at:
                uptime_seconds = time.time() - self._started_at

            base_health = {
                "healthy": self._component_state in [
                    ComponentState.INITIALIZED,
                    ComponentState.RUNNING
                ],
                "state": self._component_state.value,
                "component_state": self._component_state.value,
                "error_count": self._error_count,
                "last_error": self._last_error,
                "uptime_seconds": uptime_seconds
            }

            # Add subclass-specific health information
            component_health = self._get_component_health()
            base_health.update(component_health)

            return base_health

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "state": self._component_state.value
            }

    # ==================== Abstract Methods for Subclasses ====================

    @abstractmethod
    def _do_initialize(self, config: Dict[str, Any]) -> bool:
        """Subclass-specific initialization logic

        Args:
            config: Initialization configuration

        Returns:
            True if initialization successful
        """
        pass

    @abstractmethod
    def _do_start(self) -> bool:
        """Subclass-specific start logic

        Returns:
            True if start successful
        """
        pass

    @abstractmethod
    def _do_stop(self) -> bool:
        """Subclass-specific stop logic

        Returns:
            True if stop successful
        """
        pass

    @abstractmethod
    def _do_cleanup(self) -> None:
        """Subclass-specific cleanup logic"""
        pass

    def _get_component_health(self) -> Dict[str, Any]:
        """Get component-specific health information

        Override this method to add component-specific health data.

        Returns:
            Dictionary of component-specific health data
        """
        return {}

    # ==================== Protected Helper Methods ====================

    def _log_event(self, event: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
        """Log component event with standardized format

        Args:
            event: Event name
            extra_data: Additional event data
        """
        data = {"component_name": self._component_name, "event": event}
        if extra_data:
            data.update(extra_data)
        app_logger.log_audio_event(f"{self._component_name}_{event}", data)

    def _handle_exception(self, exception: Exception, operation: str) -> None:
        """Handle exception with standardized logging and error tracking

        Args:
            exception: The exception that occurred
            operation: Name of the operation that failed
        """
        self._record_error(f"{operation}: {str(exception)}")
        app_logger.log_error(exception, f"{self._component_name}_{operation}")

    def _record_error(self, error_message: str) -> None:
        """Record error for tracking

        Args:
            error_message: Description of the error
        """
        with self._lock:
            self._error_count += 1
            self._last_error = error_message
            self._last_error_time = time.time()

    def _load_config_setting(self, key: str, default: Any = None) -> Any:
        """Helper to load configuration setting safely

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if self._config_service:
            return self._config_service.get_setting(key, default)
        return default

    def _emit_event(self, event_name: str, data: Any = None) -> None:
        """Helper to emit event safely

        Args:
            event_name: Name of event to emit
            data: Event data
        """
        if self._event_service:
            self._event_service.emit(event_name, data)

    def _subscribe_to_event(self, event_name: str, handler) -> Optional[str]:
        """Helper to subscribe to event safely

        Args:
            event_name: Name of event to subscribe to
            handler: Event handler function

        Returns:
            Subscription ID if successful, None otherwise
        """
        if self._event_service:
            return self._event_service.subscribe(event_name, handler)
        return None

    # ==================== Properties ====================

    @property
    def is_initialized(self) -> bool:
        """Check if component is initialized"""
        return self._component_state != ComponentState.UNINITIALIZED

    @property
    def is_running(self) -> bool:
        """Check if component is running"""
        return self._component_state == ComponentState.RUNNING

    @property
    def is_healthy(self) -> bool:
        """Check if component is healthy"""
        return self._component_state in [
            ComponentState.INITIALIZED,
            ComponentState.RUNNING
        ] and self._error_count == 0

    @property
    def uptime_seconds(self) -> float:
        """Get component uptime in seconds"""
        if self._started_at:
            return time.time() - self._started_at
        return 0.0