"""
Error handling - Linus style: Fail fast, fail clearly, recover gracefully.
"The only thing worse than an error is a hidden error."
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging
import traceback

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base error - all our errors inherit from this"""
    def __init__(self, message: str, code: str = "error", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found - clear and simple"""
    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", "not_found", 404)


class ValidationError(AppError):
    """Invalid input - tell them what's wrong"""
    def __init__(self, field: str, reason: str):
        super().__init__(f"Invalid {field}: {reason}", "validation_error", 400)


class AuthError(AppError):
    """Authentication failed - no details for security"""
    def __init__(self):
        super().__init__("Authentication required", "auth_error", 401)


async def handle_app_error(request: Request, exc: AppError):
    """Handle our errors - clean and consistent"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.code,
            "message": exc.message
        }
    )


async def handle_unexpected_error(request: Request, exc: Exception):
    """Handle unexpected errors - log everything, show nothing sensitive"""
    # Log the full error for debugging
    logger.error(
        f"Unexpected error: {exc.__class__.__name__}: {exc}\n"
        f"Path: {request.url.path}\n"
        f"Traceback:\n{traceback.format_exc()}"
    )
    
    # Return generic error to client
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred"
        }
    )


def setup_error_handlers(app):
    """Setup error handlers - one place, consistent behavior"""
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(Exception, handle_unexpected_error)