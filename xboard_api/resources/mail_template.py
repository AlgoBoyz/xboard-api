"""Mail template resource — email template CRUD (5 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class MailTemplateResource(BaseResource):
    resource_path = "mail/template"

    def list(self) -> list[dict[str, Any]]:
        data = self._get("mail/template/list")
        return data if isinstance(data, list) else []

    def get(self, name: str) -> dict[str, Any]:
        return self._get("mail/template/get", name=name)

    def save(self, name: str, subject: str, content: str) -> dict[str, Any]:
        return self._post(
            "mail/template/save",
            name=name,
            subject=subject,
            content=content,
        )

    def reset(self, name: str) -> dict[str, Any]:
        return self._post("mail/template/reset", name=name)

    def test(self, name: str, email: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name}
        if email:
            payload["email"] = email
        return self._post("mail/template/test", **payload)
