"""HTTP client for Xboard Admin API.

Unified request handling, authentication, error parsing.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import requests

from .auth import load_token
from .exceptions import (
    AuthError,
    NotFound,
    ServerError,
    ValidationError,
    XboardAPIError,
)

logger = logging.getLogger(__name__)


class XboardClient:
    """Low-level HTTP client for Xboard Admin API.

    Handles:
    - Token authentication (Bearer)
    - Base URL construction
    - Unified error handling
    - Request logging

    Usage:
        client = XboardClient(
            base_url="http://192.168.31.148",
            secure_path="4ec3c529",
            token="1|xxxx...",
        )
        data = client.get("config/fetch")
        client.post("plan/save", name="VIP", transfer_enable=1000)
    """

    def __init__(
        self,
        base_url: str,
        secure_path: str,
        token: str | None = None,
        token_file: str | Path | None = None,
        timeout: int = 30,
        redact_sensitive: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.secure_path = secure_path.strip("/")
        self.api_base = f"{self.base_url}/api/v2/{self.secure_path}"
        self.timeout = timeout
        self.redact_sensitive = redact_sensitive
        self.session = requests.Session()

        if token:
            self.token = token
        elif token_file:
            self.token = load_token(token_file)
        else:
            self.token = load_token()

        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"

    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Issue an HTTP request and return parsed JSON response data.

        Path is relative to API base (e.g. "config/fetch", "user/fetch").
        Extra kwargs are passed to requests (json, params, files, etc.).
        """
        url = f"{self.api_base}/{path.lstrip('/')}"
        kwargs.setdefault("timeout", self.timeout)

        logger.info("Request: %s %s", method.upper(), url)
        resp = self.session.request(method, url, **kwargs)

        # Parse JSON
        try:
            body = resp.json()
        except (json.JSONDecodeError, ValueError):
            body = {"_raw": resp.text}

        # Success
        if 200 <= resp.status_code < 300:
            data = body.get("data", body)
            if isinstance(data, bool):
                return {"success": data}
            return data

        # Error handling
        self._handle_error(resp.status_code, body)
        return body

    def _handle_error(self, status_code: int, body: dict[str, Any]):
        from .security import sanitize_error

        msg = body.get("message", body.get("error", str(body)))
        msg = sanitize_error(str(msg))

        if status_code in (401, 403):
            raise AuthError(msg, status_code=status_code, response_body=body)
        elif status_code == 404:
            raise NotFound(msg, status_code=status_code, response_body=body)
        elif status_code == 422:
            raise ValidationError(msg, status_code=status_code, response_body=body)
        elif status_code >= 500:
            raise ServerError(msg, status_code=status_code, response_body=body)
        else:
            raise XboardAPIError(msg, status_code=status_code, response_body=body)

    def get(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> dict[str, Any]:
        # If raw dict is passed, wrap in json=
        if kwargs and "json" not in kwargs and "files" not in kwargs and "data" not in kwargs and "params" not in kwargs:
            kwargs = {"json": kwargs}
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> dict[str, Any]:
        if kwargs and "json" not in kwargs and "files" not in kwargs and "data" not in kwargs and "params" not in kwargs:
            kwargs = {"json": kwargs}
        return self._request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> dict[str, Any]:
        return self._request("DELETE", path, **kwargs)
