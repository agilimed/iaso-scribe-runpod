"""
Production middleware for IASO Clinical AI Services
Implements request validation, logging, error handling, and monitoring
"""

import time
import json
import uuid
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import asyncio
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
tenant_id_var: ContextVar[str] = ContextVar("tenant_id", default="")

logger = logging.getLogger(__name__)

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests"""
    
    def __init__(self, app: ASGIApp, max_content_length: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_content_length = max_content_length
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Validate content length
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > self.max_content_length:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request body too large. Maximum size: {self.max_content_length} bytes"}
                )
        
        # Validate content type for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith(("application/json", "multipart/form-data")):
                return JSONResponse(
                    status_code=415,
                    content={"detail": "Unsupported media type. Use application/json"}
                )
        
        response = await call_next(request)
        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """Structured logging for all requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID if not present
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(request_id)
        
        # Extract tenant ID from token or headers
        tenant_id = request.headers.get("X-Tenant-ID", "unknown")
        if hasattr(request.state, "tenant_id"):
            tenant_id = request.state.tenant_id
        tenant_id_var.set(tenant_id)
        
        # Log request
        start_time = time.time()
        
        # Capture request body for debugging (be careful with sensitive data)
        body = None
        if request.method in ["POST", "PUT", "PATCH"] and request.headers.get("content-type", "").startswith("application/json"):
            body_bytes = await request.body()
            # Restore body for downstream processing
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive
            
            try:
                body = json.loads(body_bytes) if body_bytes else None
                # Mask sensitive fields
                if body:
                    body = self._mask_sensitive_data(body)
            except:
                body = "<invalid json>"
        
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "tenant_id": tenant_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get("user-agent"),
                "remote_addr": request.client.host if request.client else None,
                "body": body
            }
        )
        
        # Process request
        response = None
        error = None
        try:
            response = await call_next(request)
        except Exception as e:
            error = e
            raise
        finally:
            # Log response
            duration = time.time() - start_time
            status_code = response.status_code if response else 500
            
            log_data = {
                "request_id": request_id,
                "tenant_id": tenant_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": round(duration * 1000, 2),
                "remote_addr": request.client.host if request.client else None
            }
            
            if error:
                logger.error("Request failed", extra=log_data, exc_info=error)
            elif status_code >= 400:
                logger.warning("Request completed with error", extra=log_data)
            else:
                logger.info("Request completed", extra=log_data)
        
        # Add request ID to response headers
        if response:
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(duration, 3))
        
        return response
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive fields in logs"""
        sensitive_fields = ["password", "token", "api_key", "secret", "ssn", "dob"]
        
        if isinstance(data, dict):
            masked = {}
            for key, value in data.items():
                if any(field in key.lower() for field in sensitive_fields):
                    masked[key] = "***MASKED***"
                elif isinstance(value, dict):
                    masked[key] = self._mask_sensitive_data(value)
                elif isinstance(value, list):
                    masked[key] = [self._mask_sensitive_data(item) if isinstance(item, dict) else item for item in value]
                else:
                    masked[key] = value
            return masked
        return data

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling with proper error responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # FastAPI HTTPException - return as is
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": e.status_code,
                        "message": e.detail,
                        "request_id": request_id_var.get(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
        except asyncio.CancelledError:
            # Request cancelled
            return JSONResponse(
                status_code=499,
                content={
                    "error": {
                        "code": 499,
                        "message": "Request cancelled",
                        "request_id": request_id_var.get(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
        except Exception as e:
            # Unhandled exception
            logger.error(
                "Unhandled exception",
                extra={
                    "request_id": request_id_var.get(),
                    "error": str(e),
                    "type": type(e).__name__
                },
                exc_info=True
            )
            
            # Don't expose internal errors in production
            message = "Internal server error"
            if logger.level == logging.DEBUG:
                message = f"{type(e).__name__}: {str(e)}"
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": 500,
                        "message": message,
                        "request_id": request_id_var.get(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )

class TimeoutMiddleware(BaseHTTPMiddleware):
    """Request timeout middleware"""
    
    def __init__(self, app: ASGIApp, timeout: int = 30):
        super().__init__(app)
        self.timeout = timeout
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout)
        except asyncio.TimeoutError:
            logger.warning(
                "Request timeout",
                extra={
                    "request_id": request_id_var.get(),
                    "method": request.method,
                    "path": request.url.path,
                    "timeout": self.timeout
                }
            )
            return JSONResponse(
                status_code=504,
                content={
                    "error": {
                        "code": 504,
                        "message": f"Request timeout after {self.timeout} seconds",
                        "request_id": request_id_var.get(),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )

# Utility functions for structured responses
def success_response(data: Any, message: str = "Success", meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create standardized success response"""
    response = {
        "success": True,
        "message": message,
        "data": data,
        "request_id": request_id_var.get(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if meta:
        response["meta"] = meta
    
    return response

def error_response(code: int, message: str, details: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Create standardized error response"""
    content = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id_var.get(),
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    
    if details:
        content["error"]["details"] = details
    
    return JSONResponse(status_code=code, content=content)

def paginated_response(
    data: list,
    page: int,
    page_size: int,
    total: int,
    message: str = "Success"
) -> Dict[str, Any]:
    """Create standardized paginated response"""
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "success": True,
        "message": message,
        "data": data,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1
        },
        "request_id": request_id_var.get(),
        "timestamp": datetime.utcnow().isoformat()
    }