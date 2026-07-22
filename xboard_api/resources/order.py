"""Order resource (5 endpoints)."""

from __future__ import annotations

from typing import Any, Generator

from .base import BaseResource


class OrderResource(BaseResource):
    resource_path = "order"

    # ---------------------------------------------------------------
    # Read
    # ---------------------------------------------------------------

    def fetch(
        self,
        page: int = 1,
        page_size: int = 50,
        is_commission: bool | None = None,
        **filters,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"current": page, "pageSize": page_size}
        if is_commission is not None:
            params["is_commission"] = is_commission
        if filters:
            params["filter[]"] = filters
        return self._get("order/fetch", **params)

    def detail(self, id: int) -> dict[str, Any]:
        return self._post("order/detail", id=id)

    def paginate(
        self,
        page_size: int = 50,
        **filters,
    ) -> Generator[dict[str, Any], None, None]:
        yield from super().paginate(page_size=page_size, **filters)

    # ---------------------------------------------------------------
    # Write
    # ---------------------------------------------------------------

    def update(self, trade_no: str, commission_status: int) -> dict[str, Any]:
        return self._post("order/update", trade_no=trade_no, commission_status=commission_status)

    def assign(
        self,
        plan_id: int,
        email: str,
        period: str,
        total_amount: int,
    ) -> dict[str, Any]:
        return self._post(
            "order/assign",
            plan_id=plan_id,
            email=email,
            period=period,
            total_amount=total_amount,
        )

    def paid(self, trade_no: str) -> dict[str, Any]:
        return self._post("order/paid", trade_no=trade_no)

    def cancel(self, trade_no: str) -> dict[str, Any]:
        return self._post("order/cancel", trade_no=trade_no)
