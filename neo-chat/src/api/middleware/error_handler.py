"""Global error handling middleware."""

from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError

from ...utils.logger import logger


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware for global error handling."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors globally.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler
            
        Returns:
            HTTP response or error response
        """
        try:
            return await call_next(request)
            
        except ValidationError as e:
            # Pydantic validation errors
            logger.warning(
                f"Validation error: {str(e)}",
                extra={
                    "event_type": "validation_error",
                    "metadata": {
                        "request_id": getattr(request.state, "request_id", None),
                        "path": request.url.path,
                        "errors": e.errors(),
                    }
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "error": "Validation Error",
                    "message": "Invalid request data",
                    "details": e.errors(),
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            
        except ValueError as e:
            # Value errors (e.g., invalid phone number)
            logger.warning(
                f"Value error: {str(e)}",
                extra={
                    "event_type": "value_error",
                    "metadata": {
                        "request_id": getattr(request.state, "request_id", None),
                        "path": request.url.path,
                        "error": str(e),
                    }
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "Bad Request",
                    "message": str(e),
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            
        except PermissionError as e:
            # Permission errors
            logger.warning(
                f"Permission error: {str(e)}",
                extra={
                    "event_type": "permission_error",
                    "metadata": {
                        "request_id": getattr(request.state, "request_id", None),
                        "path": request.url.path,
                    }
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Forbidden",
                    "message": "You don't have permission to access this resource",
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            
        except FileNotFoundError as e:
            # Not found errors
            logger.warning(
                f"Not found: {str(e)}",
                extra={
                    "event_type": "not_found",
                    "metadata": {
                        "request_id": getattr(request.state, "request_id", None),
                        "path": request.url.path,
                    }
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Not Found",
                    "message": str(e),
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            
        except TimeoutError as e:
            # Timeout errors
            logger.error(
                f"Timeout error: {str(e)}",
                extra={
                    "event_type": "timeout_error",
                    "metadata": {
                        "request_id": getattr(request.state, "request_id", None),
                        "path": request.url.path,
                    }
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": "Timeout",
                    "message": "The request took too long to process. Please try again.",
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
            
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(
                f"Unexpected error: {str(e)}",
                extra={
                    "event_type": "unexpected_error",
                    "metadata": {
                        "request_id": getattr(request.state, "request_id", None),
                        "path": request.url.path,
                        "error_type": type(e).__name__,
                        "error": str(e),
                    }
                },
                exc_info=True
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "request_id": getattr(request.state, "request_id", None),
                }
            )
