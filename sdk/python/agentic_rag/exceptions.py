"""Exceptions for Agentic RAG SDK."""


class AgenticRAGError(Exception):
    """Base exception for Agentic RAG SDK."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class AuthenticationError(AgenticRAGError):
    """Authentication failed."""
    pass


class RateLimitError(AgenticRAGError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ResourceNotFoundError(AgenticRAGError):
    """Resource not found."""
    pass


class ValidationError(AgenticRAGError):
    """Validation error."""
    pass


class InsufficientCreditsError(AgenticRAGError):
    """Insufficient credits."""
    pass
