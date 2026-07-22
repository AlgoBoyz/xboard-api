"""Payment resource — payment methods (7 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class PaymentResource(BaseResource):
    resource_path = "payment"

    def fetch(self) -> list[dict[str, Any]]:
        return self.list()

    def get_payment_methods(self) -> list[str]:
        data = self._get("payment/getPaymentMethods")
        return data if isinstance(data, list) else []

    def get_payment_form(self, payment: str, id: int) -> dict[str, Any]:
        return self._post("payment/getPaymentForm", payment=payment, id=id)

    def save(
        self,
        name: str,
        payment: str,
        config: dict,
        id: int | None = None,
        icon: str | None = None,
        notify_domain: str | None = None,
        handling_fee_fixed: int | None = None,
        handling_fee_percent: float | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": name,
            "payment": payment,
            "config": config,
        }
        if id is not None:
            payload["id"] = id
        if icon:
            payload["icon"] = icon
        if notify_domain:
            payload["notify_domain"] = notify_domain
        if handling_fee_fixed is not None:
            payload["handling_fee_fixed"] = handling_fee_fixed
        if handling_fee_percent is not None:
            payload["handling_fee_percent"] = handling_fee_percent
        return self._post("payment/save", **payload)

    def drop(self, id: int) -> dict[str, Any]:
        return self._post("payment/drop", id=id)

    def show(self, id: int) -> dict[str, Any]:
        return self._post("payment/show", id=id)

    def sort(self, ids: list[int]) -> dict[str, Any]:
        return self._post("payment/sort", ids=ids)
