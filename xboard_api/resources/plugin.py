"""Plugin resource — plugin management (10 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class PluginResource(BaseResource):
    resource_path = "plugin"

    def types(self) -> dict[str, Any]:
        return self._get("plugin/types")

    def get_plugins(self, type: str | None = None) -> list[dict[str, Any]]:
        params = {"type": type} if type else {}
        data = self._get("plugin/getPlugins", **params)
        return data if isinstance(data, list) else []

    def install(self, code: str) -> dict[str, Any]:
        return self._post("plugin/install", code=code)

    def uninstall(self, code: str) -> dict[str, Any]:
        return self._post("plugin/uninstall", code=code)

    def enable(self, code: str) -> dict[str, Any]:
        return self._post("plugin/enable", code=code)

    def disable(self, code: str) -> dict[str, Any]:
        return self._post("plugin/disable", code=code)

    def get_config(self, code: str) -> dict[str, Any]:
        return self._get("plugin/config", code=code)

    def update_config(self, code: str, config: dict) -> dict[str, Any]:
        return self._post("plugin/config", code=code, config=config)

    def delete(self, code: str) -> dict[str, Any]:
        return self._post("plugin/delete", code=code)
