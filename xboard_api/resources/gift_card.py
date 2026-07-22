"""GiftCard resource — gift card templates, codes, usages (12 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class GiftCardResource(BaseResource):
    resource_path = "gift-card"

    # ---------------------------------------------------------------
    # Templates
    # ---------------------------------------------------------------

    def templates(
        self,
        type: int | None = None,
        status: int | None = None,
        page: int = 1,
        per_page: int = 15,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if type is not None:
            params["type"] = type
        if status is not None:
            params["status"] = status
        return self._get("gift-card/templates", **params)

    def create_template(
        self,
        name: str,
        type: int,
        rewards: list,
        description: str | None = None,
        status: int = 1,
        conditions: list | None = None,
        limits: dict | None = None,
        special_config: dict | None = None,
        icon: str | None = None,
        background_image: str | None = None,
        theme_color: str | None = None,
        sort: int = 0,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": name,
            "type": type,
            "rewards": rewards,
            "status": status,
            "sort": sort,
        }
        if description:
            payload["description"] = description
        if conditions is not None:
            payload["conditions"] = conditions
        if limits is not None:
            payload["limits"] = limits
        if special_config is not None:
            payload["special_config"] = special_config
        if icon:
            payload["icon"] = icon
        if background_image:
            payload["background_image"] = background_image
        if theme_color:
            payload["theme_color"] = theme_color
        return self._post("gift-card/create-template", **payload)

    def update_template(
        self,
        id: int,
        **fields,
    ) -> dict[str, Any]:
        return self._post("gift-card/update-template", id=id, **fields)

    def delete_template(self, id: int) -> dict[str, Any]:
        return self._post("gift-card/delete-template", id=id)

    # ---------------------------------------------------------------
    # Codes
    # ---------------------------------------------------------------

    def generate_codes(
        self,
        template_id: int,
        count: int,
        prefix: str | None = None,
        expires_hours: int | None = None,
        max_usage: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "template_id": template_id,
            "count": count,
        }
        if prefix:
            payload["prefix"] = prefix
        if expires_hours is not None:
            payload["expires_hours"] = expires_hours
        if max_usage is not None:
            payload["max_usage"] = max_usage
        return self._post("gift-card/generate-codes", **payload)

    def codes(
        self,
        template_id: int | None = None,
        batch_id: str | None = None,
        status: int | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if template_id is not None:
            params["template_id"] = template_id
        if batch_id:
            params["batch_id"] = batch_id
        if status is not None:
            params["status"] = status
        return self._get("gift-card/codes", **params)

    def toggle_code(self, id: int, action: str) -> dict[str, Any]:
        return self._post("gift-card/toggle-code", id=id, action=action)

    def update_code(self, id: int, **fields) -> dict[str, Any]:
        return self._post("gift-card/update-code", id=id, **fields)

    def delete_code(self, id: int) -> dict[str, Any]:
        return self._post("gift-card/delete-code", id=id)

    def export_codes(self, batch_id: str) -> str:
        return self._get("gift-card/export-codes", batch_id=batch_id).get("data", "")

    # ---------------------------------------------------------------
    # Usages & Stats
    # ---------------------------------------------------------------

    def usages(
        self,
        template_id: int | None = None,
        user_id: int | None = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if template_id is not None:
            params["template_id"] = template_id
        if user_id is not None:
            params["user_id"] = user_id
        return self._get("gift-card/usages", **params)

    def statistics(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._get("gift-card/statistics", **params)

    def types(self) -> list[dict[str, Any]]:
        data = self._get("gift-card/types")
        return data if isinstance(data, list) else []
