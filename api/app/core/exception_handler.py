"""
Robust exception handling following the kernel principle:
"Handle errors explicitly, fail fast, provide context"
"""

import sys
import traceback
import logging
from typing import Any, Optional, Dict, Callable
from functools import wraps
from contextlib import contextmanager
import time

logger = logging.getLogger(__name__)


class SecurityException(Exception):
    """Security-related exceptions - always log and alert"""
    pass


class ValidationException(Exception):
    """Input validation exceptions - user error, not system error"""
    pass


class ResourceException(Exception):
    """Resource-related exceptions - timeout, memory, etc."""
    pass


class ExceptionHandler:
    """
    Centralized exception handling.
    No bare except, no silent failures, always provide context.
    """
    
    @staticmethod
    def handle_with_context(
        func: Callable,
        context: str,
        default_return: Any = None,
        reraise: bool = False,
        log_level: str = "error"
    ):
        """
        Decorator for handling exceptions with context.
        Every exception gets logged with full context.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SecurityException as e:
                # Security exceptions always get logged as critical
                logger.critical(
                    f"SECURITY EXCEPTION in {context}: {str(e)}",
                    exc_info=True,
                    extra={"function": func.__name__, "args": str(args)[:200]}
                )
                if reraise:
                    raise
                return default_return
            except ValidationException as e:
                # Validation errors are user errors, log as warning
                logger.warning(
                    f"Validation error in {context}: {str(e)}",
                    extra={"function": func.__name__}
                )
                if reraise:
                    raise
                return default_return
            except ResourceException as e:
                # Resource errors might be temporary
                logger.error(
                    f"Resource error in {context}: {str(e)}",
                    extra={"function": func.__name__}
                )
                if reraise:
                    raise
                return default_return
            except Exception as e:
                # Unexpected exceptions get full traceback
                log_method = getattr(logger, log_level)
                log_method(
                    f"Unexpected error in {context}: {str(e)}",
                    exc_info=True,
                    extra={
                        "function": func.__name__,
                        "exception_type": type(e).__name__,
                        "traceback": traceback.format_exc()
                    }
                )
                if reraise:
                    raise
                return default_return
        return wrapper
    
    @staticmethod
    @contextmanager
    def safe_execution(
        operation: str,
        timeout: Optional[float] = None,
        cleanup: Optional[Callable] = None
    ):
        """
        Context manager for safe execution with timeout and cleanup.
        Always runs cleanup, even on exception.
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Starting operation: {operation}")
            yield
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise ResourceException(f"Operation '{operation}' timed out after {timeout}s")
                
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"Operation '{operation}' failed after {elapsed:.2f}s: {str(e)}",
                exc_info=True
            )
            raise
        finally:
            # Always run cleanup
            if cleanup:
                try:
                    cleanup()
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed for '{operation}': {cleanup_error}")
    
    @staticmethod
    def validate_input(
        value: Any,
        validator: Callable[[Any], bool],
        error_message: str
    ) -> Any:
        """
        Validate input with clear error messages.
        Fail fast with context.
        """
        if not validator(value):
            raise ValidationException(f"{error_message}. Got: {repr(value)[:100]}")
        return value
    
    @staticmethod
    def assert_not_none(
        value: Any,
        name: str,
        context: str = ""
    ) -> Any:
        """
        Assert value is not None with context.
        Common pattern in kernel code: explicit null checks.
        """
        if value is None:
            error_msg = f"'{name}' cannot be None"
            if context:
                error_msg += f" in {context}"
            raise ValidationException(error_msg)
        return value
    
    @staticmethod
    def safe_import(module_name: str, feature: str = "") -> Optional[Any]:
        """
        Safely import a module with fallback.
        Log but don't crash on missing optional dependencies.
        """
        try:
            import importlib
            return importlib.import_module(module_name)
        except ImportError as e:
            if feature:
                logger.info(f"Optional feature '{feature}' not available: {module_name}")
            else:
                logger.warning(f"Failed to import {module_name}: {e}")
            return None
    
    @staticmethod
    def log_exception_chain(e: Exception, context: str = ""):
        """
        Log the full exception chain for debugging.
        Shows the complete error context.
        """
        current = e
        chain = []
        
        while current is not None:
            chain.append({
                "type": type(current).__name__,
                "message": str(current),
                "traceback": traceback.format_exception(
                    type(current), current, current.__traceback__
                )
            })
            current = current.__cause__ or current.__context__
        
        logger.error(
            f"Exception chain in {context}",
            extra={"exception_chain": chain}
        )


# Global handler instance
exception_handler = ExceptionHandler()


# Convenience decorators
def safe_api_endpoint(func):
    """Decorator for API endpoints with standard error handling"""
    return exception_handler.handle_with_context(
        func,
        context=f"API endpoint {func.__name__}",
        reraise=True
    )


def safe_background_task(func):
    """Decorator for background tasks that shouldn't crash the system"""
    return exception_handler.handle_with_context(
        func,
        context=f"Background task {func.__name__}",
        reraise=False,
        log_level="error"
    )
