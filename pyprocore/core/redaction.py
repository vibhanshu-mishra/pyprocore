"""Central redaction helpers for logs, CLI output, reports, and errors."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

REDACTED = "[REDACTED]"

_SENSITIVE_EXACT_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "client_id",
    "client_secret",
    "password",
    "refresh_token",
    "secret",
    "token",
}
_SENSITIVE_KEY_PARTS = (
    "app_version_key",
    "access_token",
    "api_key",
    "authorization",
    "bearer",
    "client_secret",
    "password",
    "refresh_token",
)
_SAFE_METADATA_KEYS = {
    "access_token_present",
    "client_id_env_var",
    "client_secret_env_var",
    "refresh_token_present",
    "secret_echoed",
    "contains_token",
    "token_count",
    "token_store",
    "token_status",
    "token_store_backend",
    "token_store_exists",
    "token_store_path",
    "token_type",
}
_SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "client_id",
    "client_secret",
    "code",
    "refresh_token",
    "sig",
    "signature",
    "token",
    "x-amz-credential",
    "x-amz-security-token",
    "x-amz-signature",
    "x-goog-credential",
    "x-goog-signature",
}
_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)(\b(?:access[_ -]?token|api[_ -]?key|authorization|client[_ -]?id|"
    r"client[_ -]?secret|password|refresh[_ -]?token|secret|token)\b"
    r"[\"']?\s*[:=]\s*[\"']?)([^\"'\s,;}&]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)(\b(?:authorization\s*:\s*)?bearer\s+)[A-Za-z0-9._~+/=-]+")
_API_KEY_PATTERN = re.compile(r"\bsk_(?:test|live)_[A-Za-z0-9_-]{4,}\b", re.IGNORECASE)
_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
_ENV_VAR_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def is_sensitive_key(key: object) -> bool:
    """Return whether a mapping key conventionally contains a credential."""
    normalized = str(key).strip().casefold().replace("-", "_").replace(" ", "_")
    if normalized in _SAFE_METADATA_KEYS or normalized.endswith("_env_var"):
        return False
    segments = set(normalized.split("_"))
    return (
        normalized in _SENSITIVE_EXACT_KEYS
        or bool(segments & {"password", "secret", "token"})
        or any(part in normalized for part in _SENSITIVE_KEY_PARTS)
    )


def redact_sensitive_value(value: Any) -> Any:
    """Return a recursively redacted value suitable for external output."""
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            normalized_key = key_text.strip().casefold().replace("-", "_").replace(" ", "_")
            if normalized_key.endswith("_env_var"):
                output[key_text] = _safe_env_var_value(item)
            elif normalized_key == "secret" and isinstance(item, bool):
                output[key_text] = item
            elif is_sensitive_key(key):
                output[key_text] = REDACTED
            else:
                output[key_text] = redact_sensitive_value(item)
        return output
    if isinstance(value, (list, tuple, set, frozenset)):
        return [redact_sensitive_value(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


def redact_sensitive_mapping(values: Mapping[str, Any]) -> dict[str, Any]:
    """Return a redacted dictionary while preserving its safe metadata."""
    redacted = redact_sensitive_value(values)
    return redacted if isinstance(redacted, dict) else {}


def redact_sensitive_text(text: str) -> str:
    """Redact embedded credentials and sensitive URL query parameters."""
    stripped = text.lstrip()
    if stripped.startswith(("{", "[", '"')):
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass
        else:
            indent = 2 if "\n" in text else None
            return json.dumps(redact_sensitive_value(parsed), indent=indent)
    redacted = _BEARER_PATTERN.sub(rf"\1{REDACTED}", text)
    redacted = _ASSIGNMENT_PATTERN.sub(rf"\1{REDACTED}", redacted)
    redacted = _API_KEY_PATTERN.sub(REDACTED, redacted)
    return _URL_PATTERN.sub(lambda match: _redact_embedded_url(match.group(0)), redacted)


def safe_for_logging(value: Any) -> Any:
    """Return a log/report/CLI-safe representation of ``value``."""
    return redact_sensitive_value(value)


def safe_validation_summary(errors: Iterable[Mapping[str, Any]]) -> str:
    """Format structured validation errors without echoing rejected inputs."""
    summaries = []
    for error in errors:
        location = error.get("loc", ())
        field = (
            ".".join(str(part) for part in location)
            if isinstance(location, tuple)
            else str(location)
        )
        message = redact_sensitive_text(str(error.get("msg", "Invalid value")))
        summaries.append(f"{field}: {message}" if field else message)
    return "; ".join(summaries)


def _safe_env_var_value(value: Any) -> Any:
    """Preserve only conventional environment-variable references."""
    if value is None:
        return None
    if isinstance(value, str) and _ENV_VAR_PATTERN.fullmatch(value):
        return value
    return REDACTED


def _redact_embedded_url(value: str) -> str:
    """Redact sensitive query parameters inside an arbitrary text string."""
    trailing = ""
    while value and value[-1] in ".,;)]}":
        trailing = value[-1] + trailing
        value = value[:-1]
    if "?" not in value:
        return value + trailing
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value + trailing
    if not parsed.query:
        return value + trailing
    safe_query = urlencode(
        [
            (key, REDACTED if key.casefold() in _SENSITIVE_QUERY_KEYS else value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        ],
        doseq=True,
    )
    return (
        urlunsplit((parsed.scheme, parsed.netloc, parsed.path, safe_query, parsed.fragment))
        + trailing
    )
