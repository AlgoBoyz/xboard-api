"""Plan resource — subscription plans (5 endpoints).

Business rules:
  - group_id is mandatory
  - speed_limit defaults to 20 (Mbps)
  - device_limit defaults to 10
  - capacity_limit defaults to 100 (GB)
  - prices must include: monthly, quarterly, half_yearly, yearly
"""

from __future__ import annotations

from typing import Any

from .base import BaseResource

REQUIRED_PERIODS = ["monthly", "quarterly", "half_yearly", "yearly"]


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
        group_id: int,
        prices: dict,
        id: int | None = None,
        content: str | None = None,
        reset_traffic_method: int | None = None,
        speed_limit: int = 20,
        device_limit: int = 10,
        capacity_limit: int = 100,
        tags: list | None = None,
        force_update: bool = False,
        **extra,
    ) -> dict[str, Any]:
        """Create or update a plan.

        Required:
          - name: plan display name
          - transfer_enable: traffic quota in GB
          - group_id: server group this plan belongs to
          - prices: dict with keys monthly/quarterly/half_yearly/yearly
              e.g. {'monthly': 19.9, 'quarterly': 49, 'half_yearly': 89, 'yearly': 159}

        Defaults (can override):
          - speed_limit: 20 Mbps
          - device_limit: 10
          - capacity_limit: 100 GB
        """
        missing = [k for k in REQUIRED_PERIODS if k not in prices]
        if missing:
            raise ValueError(
                f"prices must include: {', '.join(REQUIRED_PERIODS)}. "
                f"Missing: {', '.join(missing)}"
            )

        payload: dict[str, Any] = {
            "name": name,
            "transfer_enable": transfer_enable,
            "group_id": group_id,
            "prices": prices,
            "speed_limit": speed_limit,
            "device_limit": device_limit,
            "capacity_limit": capacity_limit,
        }
        if id is not None:
            payload["id"] = id
        if content is not None:
            payload["content"] = content
        if reset_traffic_method is not None:
            payload["reset_traffic_method"] = reset_traffic_method
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
