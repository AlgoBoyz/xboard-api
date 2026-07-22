"""User resource (9 endpoints)."""

from __future__ import annotations

from typing import Any, Generator

from .base import BaseResource


class UserResource(BaseResource):
    resource_path = "user"

    # ---------------------------------------------------------------
    # Read
    # ---------------------------------------------------------------

    def fetch(
        self,
        page: int = 1,
        page_size: int = 50,
        **filters,
    ) -> dict[str, Any]:
        """Paginated user list. Returns raw paginated response."""
        params = {"current": page, "pageSize": page_size}
        if filters:
            params["filter[]"] = filters
        return self._get("user/fetch", **params)

    def get_by_id(self, id: int) -> dict[str, Any]:
        return self._get("user/getUserInfoById", id=id)

    def paginate(
        self,
        page_size: int = 50,
        sort_field: str = "id",
        sort_order: str = "desc",
        **filters,
    ) -> Generator[dict[str, Any], None, None]:
        yield from super().paginate(
            page_size=page_size,
            sort_field=sort_field,
            sort_order=sort_order,
            **filters,
        )

    # ---------------------------------------------------------------
    # Write
    # ---------------------------------------------------------------

    def update(self, id: int, **fields) -> dict[str, Any]:
        payload = {"id": id, **fields}
        return self._post("user/update", **payload)

    def generate(
        self,
        email_suffix: str,
        plan_id: int | None = None,
        generate_count: int = 1,
        email_prefix: str | None = None,
        password: str | None = None,
        expired_at: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "email_suffix": email_suffix,
            "plan_id": plan_id,
            "generate_count": generate_count,
        }
        if email_prefix:
            payload["email_prefix"] = email_prefix
        if password:
            payload["password"] = password
        if expired_at:
            payload["expired_at"] = expired_at
        return self._post("user/generate", **payload)

    def dump_csv(
        self,
        scope: str = "all",
        user_ids: list[int] | None = None,
        filters: list | None = None,
    ) -> str:
        payload: dict[str, Any] = {"scope": scope}
        if user_ids:
            payload["user_ids"] = user_ids
        if filters:
            payload["filter"] = filters
        return self._post("user/dumpCSV", **payload)

    def send_mail(
        self,
        subject: str,
        content: str,
        scope: str = "all",
        user_ids: list[int] | None = None,
        filters: list | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "subject": subject,
            "content": content,
            "scope": scope,
        }
        if user_ids:
            payload["user_ids"] = user_ids
        if filters:
            payload["filter"] = filters
        return self._post("user/sendMail", **payload)

    def ban(
        self,
        scope: str = "all",
        user_ids: list[int] | None = None,
        filters: list | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"scope": scope}
        if user_ids:
            payload["user_ids"] = user_ids
        if filters:
            payload["filter"] = filters
        return self._post("user/ban", **payload)

    def reset_secret(self, id: int) -> dict[str, Any]:
        return self._post("user/resetSecret", id=id)

    def destroy(self, id: int) -> dict[str, Any]:
        return self._post("user/destroy", id=id)
