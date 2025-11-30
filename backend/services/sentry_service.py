"""
Sentry Error Tracking Service

Provides centralized error tracking and monitoring:
- Exception capture
- Performance monitoring
- User context
- Custom tags and breadcrumbs
"""

import logging
from typing import Optional, Dict, Any, Callable
from functools import wraps
import os

logger = logging.getLogger(__name__)

# Try to import Sentry
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.httpx import HttpxIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("sentry-sdk not installed. Error tracking will be limited.")


class SentryService:
    """
    Sentry error tracking service.
    """
    
    def __init__(self):
        self._initialized = False
        self._dsn: Optional[str] = None
        self._environment: str = "development"
    
    def initialize(
        self,
        dsn: Optional[str] = None,
        environment: str = "development",
        release: Optional[str] = None,
        sample_rate: float = 1.0,
        traces_sample_rate: float = 0.1,
        profiles_sample_rate: float = 0.1,
        enable_tracing: bool = True,
    ) -> bool:
        """
        Initialize Sentry SDK.
        
        Args:
            dsn: Sentry DSN (Data Source Name)
            environment: Environment name (development, staging, production)
            release: Release version
            sample_rate: Error sampling rate (0.0 to 1.0)
            traces_sample_rate: Performance tracing sample rate
            profiles_sample_rate: Profiling sample rate
            enable_tracing: Enable performance tracing
        """
        if not SENTRY_AVAILABLE:
            logger.warning("Sentry SDK not available")
            return False
        
        # Get DSN from parameter or environment
        self._dsn = dsn or os.getenv("SENTRY_DSN")
        
        if not self._dsn:
            logger.info("Sentry DSN not configured, skipping initialization")
            return False
        
        self._environment = environment
        
        try:
            sentry_sdk.init(
                dsn=self._dsn,
                environment=environment,
                release=release or os.getenv("APP_VERSION", "unknown"),
                sample_rate=sample_rate,
                traces_sample_rate=traces_sample_rate if enable_tracing else 0.0,
                profiles_sample_rate=profiles_sample_rate if enable_tracing else 0.0,
                integrations=[
                    FastApiIntegration(transaction_style="endpoint"),
                    SqlalchemyIntegration(),
                    RedisIntegration(),
                    HttpxIntegration(),
                    LoggingIntegration(
                        level=logging.INFO,
                        event_level=logging.ERROR,
                    ),
                ],
                # Filter sensitive data
                before_send=self._before_send,
                # Ignore certain exceptions
                ignore_errors=[
                    KeyboardInterrupt,
                    SystemExit,
                ],
                # Additional options
                attach_stacktrace=True,
                send_default_pii=False,  # Don't send PII by default
                max_breadcrumbs=50,
            )
            
            self._initialized = True
            logger.info(f"Sentry initialized for environment: {environment}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")
            return False
    
    def _before_send(self, event: dict, hint: dict) -> Optional[dict]:
        """Filter events before sending to Sentry."""
        # Remove sensitive data
        if "request" in event:
            request = event["request"]
            
            # Remove sensitive headers
            if "headers" in request:
                sensitive_headers = ["authorization", "cookie", "x-api-key"]
                request["headers"] = {
                    k: "[FILTERED]" if k.lower() in sensitive_headers else v
                    for k, v in request.get("headers", {}).items()
                }
            
            # Remove sensitive query params
            if "query_string" in request:
                request["query_string"] = "[FILTERED]"
        
        # Filter user data
        if "user" in event:
            user = event["user"]
            if "email" in user:
                user["email"] = "[FILTERED]"
        
        return event
    
    def capture_exception(
        self,
        exception: Exception,
        user_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
        level: str = "error",
    ) -> Optional[str]:
        """
        Capture an exception and send to Sentry.
        
        Returns the event ID if successful.
        """
        if not self._initialized or not SENTRY_AVAILABLE:
            logger.error(f"Exception (Sentry not initialized): {exception}")
            return None
        
        with sentry_sdk.push_scope() as scope:
            # Set user context
            if user_id:
                scope.set_user({"id": user_id})
            
            # Set tags
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)
            
            # Set extra context
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            
            # Set level
            scope.level = level
            
            # Capture exception
            event_id = sentry_sdk.capture_exception(exception)
            
            logger.info(f"Captured exception to Sentry: {event_id}")
            return event_id
    
    def capture_message(
        self,
        message: str,
        level: str = "info",
        user_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Capture a message and send to Sentry.
        """
        if not self._initialized or not SENTRY_AVAILABLE:
            logger.log(
                getattr(logging, level.upper(), logging.INFO),
                f"Message (Sentry not initialized): {message}"
            )
            return None
        
        with sentry_sdk.push_scope() as scope:
            if user_id:
                scope.set_user({"id": user_id})
            
            if tags:
                for key, value in tags.items():
                    scope.set_tag(key, value)
            
            if extra:
                for key, value in extra.items():
                    scope.set_extra(key, value)
            
            event_id = sentry_sdk.capture_message(message, level=level)
            return event_id
    
    def add_breadcrumb(
        self,
        message: str,
        category: str = "custom",
        level: str = "info",
        data: Optional[Dict[str, Any]] = None,
    ):
        """Add a breadcrumb for debugging context."""
        if not self._initialized or not SENTRY_AVAILABLE:
            return
        
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data,
        )
    
    def set_user(self, user_id: str, email: Optional[str] = None, username: Optional[str] = None):
        """Set user context for subsequent events."""
        if not self._initialized or not SENTRY_AVAILABLE:
            return
        
        user_data = {"id": user_id}
        if username:
            user_data["username"] = username
        # Note: email is filtered in before_send for privacy
        
        sentry_sdk.set_user(user_data)
    
    def set_tag(self, key: str, value: str):
        """Set a tag for subsequent events."""
        if not self._initialized or not SENTRY_AVAILABLE:
            return
        
        sentry_sdk.set_tag(key, value)
    
    def set_context(self, name: str, data: Dict[str, Any]):
        """Set additional context."""
        if not self._initialized or not SENTRY_AVAILABLE:
            return
        
        sentry_sdk.set_context(name, data)
    
    def start_transaction(
        self,
        name: str,
        op: str = "task",
        description: Optional[str] = None,
    ):
        """Start a performance transaction."""
        if not self._initialized or not SENTRY_AVAILABLE:
            return None
        
        return sentry_sdk.start_transaction(
            name=name,
            op=op,
            description=description,
        )
    
    def flush(self, timeout: float = 2.0):
        """Flush pending events to Sentry."""
        if not self._initialized or not SENTRY_AVAILABLE:
            return
        
        sentry_sdk.flush(timeout=timeout)
    
    @property
    def is_initialized(self) -> bool:
        """Check if Sentry is initialized."""
        return self._initialized


def track_errors(
    operation: str = "unknown",
    tags: Optional[Dict[str, str]] = None,
):
    """
    Decorator to automatically track errors in functions.
    
    Usage:
        @track_errors(operation="process_document")
        async def process_document(doc_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            service = get_sentry_service()
            service.add_breadcrumb(
                message=f"Starting {operation}",
                category="function",
                level="info",
            )
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                service.capture_exception(
                    e,
                    tags={**(tags or {}), "operation": operation},
                    extra={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            service = get_sentry_service()
            service.add_breadcrumb(
                message=f"Starting {operation}",
                category="function",
                level="info",
            )
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                service.capture_exception(
                    e,
                    tags={**(tags or {}), "operation": operation},
                    extra={"args": str(args)[:200], "kwargs": str(kwargs)[:200]},
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# Global instance
_sentry_service: Optional[SentryService] = None


def get_sentry_service() -> SentryService:
    """Get or create Sentry service instance."""
    global _sentry_service
    if _sentry_service is None:
        _sentry_service = SentryService()
    return _sentry_service


def initialize_sentry(
    dsn: Optional[str] = None,
    environment: str = "development",
    **kwargs,
) -> bool:
    """Initialize Sentry with configuration."""
    service = get_sentry_service()
    return service.initialize(dsn=dsn, environment=environment, **kwargs)
