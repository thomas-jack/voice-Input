"""Simplified lifecycle management base class

Provides minimal lifecycle management for components that need start/stop semantics.
Follows YAGNI principle - only includes actually needed features.
"""

from abc import ABC, abstractmethod
from enum import Enum

from ...utils import app_logger


class ComponentState(Enum):
    """Simple 3-state component lifecycle"""

    STOPPED = "stopped"  # Component is stopped (initial state)
    RUNNING = "running"  # Component is actively running
    ERROR = "error"  # Component encountered an error


class LifecycleComponent(ABC):
    """Simplified base class for lifecycle-managed components

    Provides basic start/stop lifecycle management without unnecessary complexity.

    Usage:
        class MyComponent(LifecycleComponent):
            def __init__(self):
                super().__init__("MyComponent")
                self._resource = None

            def _do_start(self) -> bool:
                self._resource = acquire_resource()
                return True

            def _do_stop(self) -> bool:
                release_resource(self._resource)
                return True

        # Use the component
        component = MyComponent()
        component.start()
        # ... use component ...
        component.stop()
    """

    def __init__(self, component_name: str):
        """Initialize lifecycle component

        Args:
            component_name: Name for logging and identification
        """
        self._component_name = component_name
        self._state = ComponentState.STOPPED

    def start(self) -> bool:
        """Start the component

        Returns:
            True if start successful, False otherwise
        """
        if self._state == ComponentState.RUNNING:
            return True  # Already running

        try:
            app_logger.log_audio_event(
                f"{self._component_name} starting", {"component": self._component_name}
            )

            success = self._do_start()

            if success:
                self._state = ComponentState.RUNNING
                app_logger.log_audio_event(
                    f"{self._component_name} started",
                    {"component": self._component_name},
                )
            else:
                self._state = ComponentState.ERROR

            return success

        except Exception as e:
            self._state = ComponentState.ERROR
            app_logger.log_error(e, f"{self._component_name}_start")
            return False

    def stop(self) -> bool:
        """Stop the component

        Returns:
            True if stop successful, False otherwise
        """
        if self._state == ComponentState.STOPPED:
            return True  # Already stopped

        try:
            app_logger.log_audio_event(
                f"{self._component_name} stopping", {"component": self._component_name}
            )

            success = self._do_stop()

            if success:
                self._state = ComponentState.STOPPED
                app_logger.log_audio_event(
                    f"{self._component_name} stopped",
                    {"component": self._component_name},
                )
            else:
                self._state = ComponentState.ERROR

            return success

        except Exception as e:
            self._state = ComponentState.ERROR
            app_logger.log_error(e, f"{self._component_name}_stop")
            return False

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

    @property
    def is_running(self) -> bool:
        """Check if component is currently running"""
        return self._state == ComponentState.RUNNING

    @property
    def state(self) -> ComponentState:
        """Get current component state"""
        return self._state

    @property
    def component_name(self) -> str:
        """Get component name"""
        return self._component_name
