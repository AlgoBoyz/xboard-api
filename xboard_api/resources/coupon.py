"""Coupon resource — discount coupons (5 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class CouponResource(BaseResource):
    resource_path = "coupon"

    def fetch(
        self,
        page: int = 1,
        page_size: int = 50,
        **filters,
    ) -> dict[str, Any]:
        return self._get(
            "coupon/fetch", current=page, pageSize=page_size, **filters
        )

    def generate(
        self,
        name: str,
        type: int,
        value: int,
        started_at: int,
        ended_at: int,
        generate_count: int = 1,
        limit_use: int | None = None,
        limit_use_with_user: int | None = None,
        limit_plan_ids: list | None = None,
        limit_period: list | None = None,
        code: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": name,
            "type": type,
            "value": value,
            "started_at": started_at,
            "ended_at": ended_at,
            "generate_count": generate_count,
        }
        if limit_use is not None:
            payload["limit_use"] = limit_use
        if limit_use_with_user is not None:
            payload["limit_use_with_user"] = limit_use_with_user
        if limit_plan_ids is not None:
            payload["limit_plan_ids"] = limit_plan_ids
        if limit_period is not None:
            payload["limit_period"] = limit_period
        if code is not None:
            payload["code"] = code
        return self._post("coupon/generate", **payload)

    def drop(self, id: int) -> dict[str, Any]:
        return self._post("coupon/drop", id=id)

    def show(self, id: int) -> dict[str, Any]:
        return self._post("coupon/show", id=id)

    def update(self, id: int, show: bool) -> dict[str, Any]:
        return self._post("coupon/update", id=id, show=show)
