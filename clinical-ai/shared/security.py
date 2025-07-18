"""
Production-ready security module for IASO Clinical AI Services
Implements authentication, authorization, rate limiting, and security headers
"""

import os
import time
import jwt
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from functools import wraps

from fastapi import HTTPException, Request, status, Header, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import redis
from circuitbreaker import circuit

# Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "true").lower() == "true"
API_KEY_HEADER = "X-API-Key"

# Logger
logger = logging.getLogger(__name__)

# Redis client for distributed rate limiting
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30
    )
    redis_client.ping()
    logger.info("Redis connection established for rate limiting")
except Exception as e:
    logger.warning(f"Redis connection failed, using in-memory rate limiting: {e}")
    redis_client = None

# Rate limiter with Redis backend for distributed rate limiting
def get_redis_url():
    if redis_client:
        return f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}" if REDIS_PASSWORD else f"redis://{REDIS_HOST}:{REDIS_PORT}"
    return None

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri=get_redis_url(),
    headers_enabled=True  # Add rate limit headers to responses
)

# Security schemes
security = HTTPBearer(auto_error=False)

class TokenPayload:
    """Token payload structure"""
    def __init__(self, sub: str, tenant_id: str, roles: List[str], exp: int):
        self.sub = sub
        self.tenant_id = tenant_id
        self.roles = roles
        self.exp = exp

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def verify_token(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    api_key: Optional[str] = Header(None, alias=API_KEY_HEADER)
) -> Dict[str, Any]:
    """Verify JWT token or API key"""
    if not ENABLE_AUTH:
        # Return mock token payload for development
        return {
            "sub": "dev-user",
            "tenant_id": "dev-tenant",
            "roles": ["admin"],
            "user_id": "dev-user-id"
        }
    
    # Check API key first
    if api_key:
        # Validate API key (implement your API key validation logic)
        if validate_api_key(api_key):
            return {
                "sub": "api-key-user",
                "tenant_id": extract_tenant_from_api_key(api_key),
                "roles": ["api_user"],
                "user_id": "api-key-user"
            }
    
    # Check JWT token
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    # Add request context
    request.state.user_id = payload.get("sub")
    request.state.tenant_id = payload.get("tenant_id")
    
    return payload

def validate_api_key(api_key: str) -> bool:
    """Validate API key against database or cache"""
    # TODO: Implement actual API key validation
    # This is a placeholder - store API keys in database or cache
    valid_keys = os.getenv("VALID_API_KEYS", "").split(",")
    return api_key in valid_keys

def extract_tenant_from_api_key(api_key: str) -> str:
    """Extract tenant ID from API key"""
    # TODO: Implement actual tenant extraction logic
    return "default-tenant"

def require_roles(required_roles: List[str]):
    """Decorator to require specific roles"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract token_payload from kwargs
            token_payload = kwargs.get("token_payload", {})
            user_roles = token_payload.get("roles", [])
            
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def setup_security(app, allowed_origins: List[str] = None):
    """Setup security middleware and headers for FastAPI app"""
    
    # CORS middleware
    if allowed_origins is None:
        allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time", "X-RateLimit-*"]
    )
    
    # Trusted host middleware
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "*").split(",")
    if "*" not in allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
    
    # Rate limiting middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
    
    # Security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        start_time = time.time()
        
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", f"{int(time.time() * 1000)}")
        request.state.request_id = request_id
        
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(time.time() - start_time, 3))
        
        # Add CSP header for production
        if os.getenv("ENVIRONMENT", "dev") == "prod":
            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
        
        return response
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": getattr(request.state, "request_id", "unknown")
            }
        )
    
    return app

# Circuit breaker for external service calls
class CircuitBreakerError(Exception):
    """Custom exception for circuit breaker"""
    pass

@circuit(failure_threshold=5, recovery_timeout=30, expected_exception=CircuitBreakerError)
def call_external_service(service_name: str, func, *args, **kwargs):
    """
    Wrapper for external service calls with circuit breaker
    
    Usage:
        result = call_external_service("service_name", requests.get, url, timeout=5)
    """
    try:
        result = func(*args, **kwargs)
        return result
    except Exception as e:
        logger.error(f"External service {service_name} failed: {e}")
        raise CircuitBreakerError(f"Service {service_name} is unavailable")

# Health check helper
async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connectivity for health endpoint"""
    try:
        if redis_client:
            redis_client.ping()
            return {"redis": "healthy"}
        else:
            return {"redis": "not configured"}
    except Exception as e:
        return {"redis": f"unhealthy: {str(e)}"}

# Metrics collection (basic implementation)
class MetricsCollector:
    """Basic metrics collector for Prometheus"""
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.request_duration = []
    
    def record_request(self, duration: float, status_code: int):
        self.request_count += 1
        self.request_duration.append(duration)
        if status_code >= 400:
            self.error_count += 1
    
    def get_metrics(self) -> str:
        """Return metrics in Prometheus format"""
        avg_duration = sum(self.request_duration) / len(self.request_duration) if self.request_duration else 0
        return f"""# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total {self.request_count}

# HELP http_errors_total Total HTTP errors
# TYPE http_errors_total counter
http_errors_total {self.error_count}

# HELP http_request_duration_seconds HTTP request duration
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_sum {sum(self.request_duration)}
http_request_duration_seconds_count {len(self.request_duration)}
"""

metrics_collector = MetricsCollector()

# Middleware to collect metrics
async def metrics_middleware(request: Request, call_next):
    """Middleware to collect request metrics"""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    metrics_collector.record_request(duration, response.status_code)
    return response