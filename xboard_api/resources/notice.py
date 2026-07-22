"""Notice resource — announcements (4 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class NoticeResource(BaseResource):
    resource_path = "notice"

    def fetch(self) -> list[dict[str, Any]]:
        return self.list()

    def save(
        self,
        title: str,
        content: str,
        id: int | None = None,
        img_url: str | None = None,
        tags: list | None = None,
        show: int = 0,
        popup: int = 0,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "title": title,
            "content": content,
            "show": show,
            "popup": popup,
        }
        if id is not None:
            payload["id"] = id
        if img_url is not None:
            payload["img_url"] = img_url
        if tags is not None:
            payload["tags"] = tags
        return self._post("notice/save", **payload)

    def drop(self, id: int) -> dict[str, Any]:
        return self._post("notice/drop", id=id)

    def show(self, id: int) -> dict[str, Any]:
        return self._post("notice/show", id=id)

    def sort(self, ids: list[int]) -> dict[str, Any]:
        return self._post("notice/sort", ids=ids)
