"""Custom exceptions raised by the Procore SDK."""

from __future__ import annotations

from typing import Any


class ProcoreError(Exception):
    """Base exception for all SDK-specific errors."""


class ConfigurationError(ProcoreError):
    """Raised when SDK configuration is missing or invalid."""


class AuthenticationError(ProcoreError):
    """Raised when OAuth authentication or token refresh fails."""


class AuthorizationError(ProcoreError):
    """Raised when Procore denies access to an authenticated request."""


class ValidationError(ProcoreError):
    """Raised when input or response validation fails."""


class ProcoreAPIError(ProcoreError):
    """Raised when the Procore API returns an unsuccessful response."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: Any | None = None,
    ) -> None:
        """Initialize an API error.

        Args:
            message: Human-readable error summary.
            status_code: Optional HTTP status code returned by Procore.
            response_body: Optional parsed or raw response body.
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class ResourceNotFoundError(ProcoreAPIError):
    """Raised when a requested Procore resource cannot be found."""


class NotFoundError(ResourceNotFoundError):
    """Raised when a resolver cannot find a matching Procore resource."""


class DuplicateMatchError(ProcoreError):
    """Raised when multiple exact resolver matches are found."""


class MultipleResultsError(ProcoreError):
    """Raised when a resolver search is ambiguous."""


class RateLimitError(ProcoreAPIError):
    """Raised when Procore rate-limits a request."""


class TransientAPIError(ProcoreAPIError):
    """Raised for transient Procore API failures that may succeed later."""
