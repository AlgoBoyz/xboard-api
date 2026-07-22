"""Security utilities for Xboard Admin API wrapper.

- sanitize_error: strip internal paths/structures from exception messages
- sanitize_response: redact sensitive fields from API responses
- audit_log: log all MCP tool calls
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger("xboard.security")

# Patterns that might leak internal info
_SENSITIVE_PATTERNS = [
    (re.compile(r"/var/www/[^\s)]+", re.IGNORECASE), "[redacted-path]"),
    (re.compile(r"/home/[^\s)]+", re.IGNORECASE), "[redacted-path]"),
    (re.compile(r"/www/[^\s)]+", re.IGNORECASE), "[redacted-path]"),
    (re.compile(r"SQLSTATE\[\w+\]:\s*\d+\s+", re.IGNORECASE), "DB error: "),
    (re.compile(r'"(password|token|secret|api_key|private_key|public_key)"\s*:\s*"[^"]+"', re.IGNORECASE), r'"\1":"***"'),
]

# Sensitive fields to redact from tool responses
_SENSITIVE_KEYS = {
    "token", "server_token", "private_key", "public_key",
    "password", "api_key", "secret", "key",
    "merchant_private_key", "alipay_public_key", "app_secret",
    "notify_url", "subscribe_url",
}


def sanitize_error(message: str) -> str:
    """Strip internal paths and debug info from error messages."""
    for pattern, replacement in _SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message


def sanitize_response(data: Any, depth: int = 0) -> Any:
    """Recursively redact sensitive fields from API response data.

    Redacts specific keys (token, password, api_key, etc.) and
    replaces their values with '***'. Also strips PEM content.
    """
    if depth > 10:
        return data

    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            if k in _SENSITIVE_KEYS or any(
                s in k.lower() for s in ("token", "password", "secret", "key")
            ):
                if isinstance(v, str) and len(v) > 3:
                    result[k] = "***"
                elif isinstance(v, (int, float)):
                    result[k] = v
                else:
                    result[k] = "***"
            elif k == "config" and isinstance(v, dict):
                # payment configs — redact all values
                result[k] = {ck: "***" for ck in v}
            elif k == "install_command" and isinstance(v, str):
                # machine install command contains token in URL
                result[k] = re.sub(r"--token '[^']+'", "--token '***'", v)
            else:
                result[k] = sanitize_response(v, depth + 1)
        return result
    elif isinstance(data, list):
        return [sanitize_response(item, depth + 1) for item in data]
    elif isinstance(data, str) and "-----BEGIN" in data:
        # PEM content redaction
        return "[PEM content redacted]"
    return data
