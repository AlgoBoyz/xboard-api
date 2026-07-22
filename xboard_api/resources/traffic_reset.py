"""Traffic reset resource — logs, stats, manual reset (4 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class TrafficResetResource(BaseResource):
    resource_path = "traffic-reset"

    def logs(
        self,
        user_id: int | None = None,
        user_email: str | None = None,
        reset_type: str | None = None,
        trigger_source: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if user_id is not None:
            params["user_id"] = user_id
        if user_email:
            params["user_email"] = user_email
        if reset_type:
            params["reset_type"] = reset_type
        if trigger_source:
            params["trigger_source"] = trigger_source
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._get("traffic-reset/logs", **params)

    def stats(self, days: int = 30) -> dict[str, Any]:
        return self._get("traffic-reset/stats", days=days)

    def user_history(self, user_id: int, limit: int = 10) -> list[dict[str, Any]]:
        data = self._get(f"traffic-reset/user/{user_id}/history", limit=limit)
        return data if isinstance(data, list) else []

    def reset_user(self, user_id: int, reason: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"user_id": user_id}
        if reason:
            payload["reason"] = reason
        return self._post("traffic-reset/reset-user", **payload)
