"""Stat resource — dashboard and analytics (8 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class StatResource(BaseResource):
    resource_path = "stat"

    def get_override(self) -> dict[str, Any]:
        return self._get("stat/getOverride")

    def get_stats(self) -> dict[str, Any]:
        return self._get("stat/getStats")

    def get_server_last_rank(self) -> list[dict[str, Any]]:
        data = self._get("stat/getServerLastRank")
        return data if isinstance(data, list) else []

    def get_server_yesterday_rank(self) -> list[dict[str, Any]]:
        data = self._get("stat/getServerYesterdayRank")
        return data if isinstance(data, list) else []

    def get_order(
        self,
        start_date: str,
        end_date: str,
        type: str = "paid_total",
    ) -> list[dict[str, Any]]:
        data = self._get(
            "stat/getOrder",
            start_date=start_date,
            end_date=end_date,
            type=type,
        )
        return data if isinstance(data, list) else []

    def get_stat_user(self, user_id: int, page_size: int = 50) -> dict[str, Any]:
        return self._get("stat/getStatUser", user_id=user_id, pageSize=page_size)

    def get_stat_record(self, type: str | None = None) -> list[dict[str, Any]]:
        params = {"type": type} if type else {}
        data = self._get("stat/getStatRecord", **params)
        return data if isinstance(data, list) else []

    def get_traffic_rank(
        self,
        type: str = "user",
        start_time: int | None = None,
        end_time: int | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"type": type}
        if start_time is not None:
            params["start_time"] = start_time
        if end_time is not None:
            params["end_time"] = end_time
        data = self._get("stat/getTrafficRank", **params)
        return data if isinstance(data, list) else []
