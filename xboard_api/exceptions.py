"""Exception classes for Xboard Admin API."""


class XboardAPIError(Exception):
    """Base exception for all Xboard API errors."""

    def __init__(self, message: str, status_code: int = 0, response_body: dict | None = None):
        self.status_code = status_code
        self.response_body = response_body or {}
        super().__init__(message)


class AuthError(XboardAPIError):
    """Raised when authentication fails (401)."""


class NotFound(XboardAPIError):
    """Raised when a resource is not found (404)."""


class ValidationError(XboardAPIError):
    """Raised when request validation fails (422)."""


class ServerError(XboardAPIError):
    """Raised on server errors (5xx)."""
