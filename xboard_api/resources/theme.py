"""Theme resource — theme management (5 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class ThemeResource(BaseResource):
    resource_path = "theme"

    def get_themes(self) -> dict[str, Any]:
        return self._get("theme/getThemes")

    def save_theme_config(self, name: str, config: dict) -> dict[str, Any]:
        return self._post("theme/saveThemeConfig", name=name, config=config)

    def get_theme_config(self, name: str) -> dict[str, Any]:
        return self._post("theme/getThemeConfig", name=name)

    def delete(self, name: str) -> dict[str, Any]:
        return self._post("theme/delete", name=name)
