"""Ticket resource — support tickets (3 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class TicketResource(BaseResource):
    resource_path = "ticket"

    def fetch(
        self,
        id: int | None = None,
        status: int | None = None,
        reply_status: int | None = None,
        email: str | None = None,
        page: int = 1,
        page_size: int = 50,
        **filters,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"current": page, "pageSize": page_size}
        if id is not None:
            params["id"] = id
        if status is not None:
            params["status"] = status
        if reply_status is not None:
            params["reply_status"] = reply_status
        if email is not None:
            params["email"] = email
        if filters:
            params["filter[]"] = filters
        return self._get("ticket/fetch", **params)

    def reply(self, id: int, message: str) -> dict[str, Any]:
        return self._post("ticket/reply", id=id, message=message)

    def close(self, id: int) -> dict[str, Any]:
        return self._post("ticket/close", id=id)
