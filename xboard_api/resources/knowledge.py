"""Knowledge resource — knowledge base articles (5 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class KnowledgeResource(BaseResource):
    resource_path = "knowledge"

    def fetch(self, id: int | None = None) -> list[dict[str, Any]] | dict[str, Any]:
        params = {"id": id} if id is not None else {}
        data = self._get("knowledge/fetch", **params)
        return data

    def get_category(self) -> list[dict[str, Any]]:
        data = self._get("knowledge/getCategory")
        return data if isinstance(data, list) else []

    def save(
        self,
        title: str,
        content: str,
        id: int | None = None,
        category_id: int | None = None,
        show: int = 0,
        sort: int = 0,
        **extra,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": title,
            "content": content,
            "show": show,
            "sort": sort,
        }
        if id is not None:
            payload["id"] = id
        if category_id is not None:
            payload["category_id"] = category_id
        payload.update(extra)
        return self._post("knowledge/save", **payload)

    def show(self, id: int) -> dict[str, Any]:
        return self._post("knowledge/show", id=id)

    def drop(self, id: int) -> dict[str, Any]:
        return self._post("knowledge/drop", id=id)

    def sort(self, ids: list[int]) -> dict[str, Any]:
        return self._post("knowledge/sort", ids=ids)
