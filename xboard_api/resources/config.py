"""Config resource — site settings (6 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


class ConfigResource(BaseResource):
    resource_path = "config"

    # ---------------------------------------------------------------
    # Read
    # ---------------------------------------------------------------

    def fetch(self, key: str | None = None) -> dict[str, Any]:
        """Get all config or a specific key's config."""
        params = {"key": key} if key else {}
        return self._get("config/fetch", **params)

    def get_email_template(self) -> list[str]:
        """List available email template files."""
        data = self._get("config/getEmailTemplate")
        return data if isinstance(data, list) else []

    def get_theme_template(self) -> list[str]:
        """List available theme directories."""
        data = self._get("config/getThemeTemplate")
        return data if isinstance(data, list) else []

    # ---------------------------------------------------------------
    # Write
    # ---------------------------------------------------------------

    def save(self, **values) -> dict[str, Any]:
        """Save one or more config keys. Accepts arbitrary key=value pairs.

        Keys that match email template fields (start with subscribe_template_)
        will be saved to the subscribe_templates table instead.
        """
        return self._post("config/save", **values)

    # ---------------------------------------------------------------
    # Telegram
    # ---------------------------------------------------------------

    def set_telegram_webhook(self, bot_token: str) -> dict[str, Any]:
        return self._post("config/setTelegramWebhook", telegram_bot_token=bot_token)

    # ---------------------------------------------------------------
    # Test
    # ---------------------------------------------------------------

    def test_send_mail(self) -> dict[str, Any]:
        """Send a test email to the logged-in admin."""
        return self._post("config/testSendMail")
