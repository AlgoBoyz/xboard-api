"""Plan resource — subscription plans (5 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class PlanResource(BaseResource):
    resource_path = "plan"

    # ---------------------------------------------------------------
    # Read
    # ---------------------------------------------------------------

    def fetch(self) -> list[dict[str, Any]]:
        """List all plans."""
        data = self._get("plan/fetch")
        if isinstance(data, list):
            return data
        return []

    # ---------------------------------------------------------------
    # Write
    # ---------------------------------------------------------------

    def save(
        self,
        name: str,
        transfer_enable: int,
        id: int | None = None,
        content: str = "",
        reset_traffic_method: int = 0,
        prices: dict | None = None,
        group_id: int | None = None,
        speed_limit: int | None = None,
        device_limit: int | None = None,
        capacity_limit: int | None = None,
        tags: list | None = None,
        force_update: bool = False,
        **extra,
    ) -> dict[str, Any]:
        """Create or update a plan. `transfer_enable` is in GB."""
        payload: dict[str, Any] = {
            "name": name,
            "transfer_enable": transfer_enable,
        }
        if id is not None:
            payload["id"] = id
        if content is not None:
            payload["content"] = content
        if reset_traffic_method is not None:
            payload["reset_traffic_method"] = reset_traffic_method
        if prices is not None:
            payload["prices"] = prices
        if group_id is not None:
            payload["group_id"] = group_id
        if speed_limit is not None:
            payload["speed_limit"] = speed_limit
        if device_limit is not None:
            payload["device_limit"] = device_limit
        if capacity_limit is not None:
            payload["capacity_limit"] = capacity_limit
        if tags is not None:
            payload["tags"] = tags
        if force_update:
            payload["force_update"] = force_update
        payload.update(extra)
        return self._post("plan/save", **payload)

    def drop(self, id: int) -> dict[str, Any]:
        return self._post("plan/drop", id=id)

    def update(
        self,
        id: int,
        show: bool | None = None,
        renew: bool | None = None,
        sell: bool | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"id": id}
        if show is not None:
            payload["show"] = show
        if renew is not None:
            payload["renew"] = renew
        if sell is not None:
            payload["sell"] = sell
        return self._post("plan/update", **payload)

    def sort(self, ids: list[int]) -> dict[str, Any]:
        return self._post("plan/sort", ids=ids)
