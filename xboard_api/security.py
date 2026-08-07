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
# NOTE 2026-08-07: sanitize_response 已删除——响应脱敏曾导致脱敏值回写覆盖真实密钥的事故
# （iDataRiver developer_secret 被 "sk_7fe...dbd9" 覆盖丢失）。错误信息脱敏（sanitize_error）保留。


def sanitize_error(message: str) -> str:
    """Strip internal paths and debug info from error messages."""
    for pattern, replacement in _SENSITIVE_PATTERNS:
        message = pattern.sub(replacement, message)
    return message
