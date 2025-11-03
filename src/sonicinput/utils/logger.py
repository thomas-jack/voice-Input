"""Deprecated logging module - kept for backwards compatibility

This module is deprecated. Use unified_logger instead:
    from sonicinput.utils import logger
"""

# Re-export from unified_logger for backwards compatibility
try:
    from .unified_logger import app_logger_compat as app_logger
except ImportError:
    # Fallback if unified_logger is not available
    app_logger = None

__all__ = ["app_logger"]
