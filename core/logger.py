"""Centralized structured logging utilities for the Procore SDK."""

from __future__ import annotations

import json
import logging
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOGGER_NAME = "procore_sdk"
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
SDK_LOG_FILE = LOG_DIR / "sdk.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

SENSITIVE_KEYS = {
    "authorization",
    "access_token",
    "refresh_token",
    "client_secret",
}


def ensure_log_directory() -> Path:
    """Create and return the SDK log directory."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a configured SDK logger.

    Args:
        name: Optional child logger name.

    Returns:
        A configured SDK ``logging.Logger`` instance.
    """
    ensure_log_directory()
    logger_name = LOGGER_NAME if name is None else f"{LOGGER_NAME}.{name}"
    logger = logging.getLogger(logger_name)

    if not any(
        getattr(handler, "_procore_sdk_handler", False) for handler in logger.handlers
    ):
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler._procore_sdk_handler = True  # type: ignore[attr-defined]

        sdk_file_handler = logging.FileHandler(SDK_LOG_FILE, encoding="utf-8")
        sdk_file_handler.setFormatter(formatter)
        sdk_file_handler._procore_sdk_handler = True  # type: ignore[attr-defined]

        error_file_handler = logging.FileHandler(ERROR_LOG_FILE, encoding="utf-8")
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(formatter)
        error_file_handler._procore_sdk_handler = True  # type: ignore[attr-defined]

        logger.addHandler(stream_handler)
        logger.addHandler(sdk_file_handler)
        logger.addHandler(error_file_handler)

    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def sanitize_log_value(value: Any) -> Any:
    """Return a log-safe version of a value."""
    if isinstance(value, dict):
        return {
            key: (
                "[REDACTED]"
                if key.lower() in SENSITIVE_KEYS
                else sanitize_log_value(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_log_value(item) for item in value]
    return value


def structured_message(event: str, **fields: Any) -> str:
    """Return a compact JSON log message."""
    payload = {
        "event": event,
        "timestamp": datetime.now(tz=UTC).isoformat(),
        **sanitize_log_value(fields),
    }
    return json.dumps(payload, default=str, sort_keys=True)


def log_api_request(
    logger: logging.Logger,
    *,
    method: str,
    endpoint: str,
    status_code: int | None,
    elapsed_ms: float,
    retry_count: int = 0,
) -> None:
    """Log structured metadata for an API request."""
    logger.info(
        structured_message(
            "api_request",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            elapsed_ms=round(elapsed_ms, 2),
            retry_count=retry_count,
        )
    )


def log_exception(
    logger: logging.Logger,
    *,
    exc: BaseException,
    request_url: str | None = None,
    http_status: int | None = None,
    response_body: Any | None = None,
) -> None:
    """Log a structured exception record with stack trace."""
    logger.error(
        structured_message(
            "exception",
            exception_type=type(exc).__name__,
            request_url=request_url,
            http_status=http_status,
            response_body=response_body,
            stack_trace="".join(traceback.format_exception(exc)),
        )
    )


logger = get_logger()
