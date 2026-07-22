"""System resource — system status and audit logs (5 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class SystemResource(BaseResource):
    resource_path = "system"

    def get_system_status(self) -> dict[str, Any]:
        return self._get("system/getSystemStatus")

    def get_queue_stats(self) -> dict[str, Any]:
        return self._get("system/getQueueStats")

    def get_queue_workload(self) -> dict[str, Any]:
        return self._get("system/getQueueWorkload")

    def get_horizon_failed_jobs(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        return self._get(
            "system/getHorizonFailedJobs",
            current=page,
            page_size=page_size,
        )

    def get_audit_log(
        self,
        page: int = 1,
        page_size: int = 50,
        action: str | None = None,
        admin_id: int | None = None,
        keyword: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"current": page, "page_size": page_size}
        if action:
            params["action"] = action
        if admin_id is not None:
            params["admin_id"] = admin_id
        if keyword:
            params["keyword"] = keyword
        return self._get("system/getAuditLog", **params)
