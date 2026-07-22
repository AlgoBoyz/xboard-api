"""Base resource class providing common CRUD operations.

All resource modules inherit from BaseResource which itself wraps XboardClient.
"""

from __future__ import annotations

import logging
from typing import Any, Generator

logger = logging.getLogger(__name__)


class BaseResource:
    """Base class for API resource wrappers.

    Each subclass defines `resource_path` (e.g. "plan", "user", "server/manage")
    and inherits standard CRUD helpers.

    Usage:
        class PlanResource(BaseResource):
            resource_path = "plan"
    """

    resource_path: str = ""

    def __init__(self, client):
        self.client = client

    # ---------------------------------------------------------------
    # Generic helpers
    # ---------------------------------------------------------------

    def _get(self, path: str, **params) -> dict[str, Any]:
        return self.client.get(path, params=params)

    def _post(self, path: str, **body) -> dict[str, Any]:
        return self.client.post(path, **body)

    def _delete(self, path: str, **body) -> dict[str, Any]:
        return self.client.delete(path, **body)

    # ---------------------------------------------------------------
    # List
    # ---------------------------------------------------------------

    def list(self, **filters) -> list[dict[str, Any]]:
        """Fetch all records for this resource."""
        data = self._get(f"{self.resource_path}/fetch", **filters)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("data", data.get("items", []))
        return []

    def paginate(
        self,
        page_size: int = 50,
        sort_field: str = "id",
        sort_order: str = "desc",
        **filters,
    ) -> Generator[dict[str, Any], None, None]:
        """Paginate through all records for endpoints using current/pageSize convention.

        Only call this for endpoints that support pagination (user/fetch, order/fetch, etc.).
        """
        page = 1
        base_params = {
            "pageSize": page_size,
            "sort[]": {sort_field: sort_order},
            **filters,
        }
        while True:
            params = {**base_params, "current": page}
            result = self._get(f"{self.resource_path}/fetch", **params)
            items = result if isinstance(result, list) else result.get("data", [])
            if not items:
                break
            yield from items
            if len(items) < page_size:
                break
            page += 1

    # ---------------------------------------------------------------
    # Get by ID
    # ---------------------------------------------------------------

    def get(self, id: int) -> dict[str, Any] | None:
        """Get a single resource by ID. Not all endpoints support this."""
        data = self._get(f"{self.resource_path}/fetch", id=id)
        if isinstance(data, (list, dict)):
            return data
        return None

    # ---------------------------------------------------------------
    # Save (create or update)
    # ---------------------------------------------------------------

    def save(self, **fields) -> dict[str, Any]:
        """Create or update a resource (POST to /save)."""
        return self._post(f"{self.resource_path}/save", **fields)

    # ---------------------------------------------------------------
    # Drop (delete)
    # ---------------------------------------------------------------

    def drop(self, id: int) -> dict[str, Any]:
        """Delete a resource (POST to /drop)."""
        return self._post(f"{self.resource_path}/drop", id=id)

    # ---------------------------------------------------------------
    # Sort
    # ---------------------------------------------------------------

    def sort(self, ids: list[int]) -> dict[str, Any]:
        """Sort resources (POST to /sort)."""
        return self._post(f"{self.resource_path}/sort", ids=ids)
