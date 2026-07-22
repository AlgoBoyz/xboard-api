"""Server resource — groups, routes, nodes, machines (24 endpoints)."""

from __future__ import annotations

import base64
import secrets
from typing import Any

from .base import BaseResource


# -- Reality key generation --

REALITY_DEST = "cdn-dynmedia-1.microsoft.com"
REALITY_DEST_PORT = "443"


def generate_reality_keys():
    """Generate X25519 Reality key pair with urlsafe base64.

    Returns (public_key, private_key, short_id).
    Keys use urlsafe base64 to avoid '+' '/' in subscription URLs.
    """
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey

    priv = X25519PrivateKey.generate()
    pub = base64.urlsafe_b64encode(
        priv.public_key().public_bytes_raw()
    ).rstrip(b"=").decode()
    prv = base64.urlsafe_b64encode(
        priv.private_bytes_raw()
    ).rstrip(b"=").decode()
    sid = secrets.token_hex(8)
    return pub, prv, sid


def build_reality_settings(public_key, private_key, short_id, dest=REALITY_DEST, dest_port=REALITY_DEST_PORT):
    """Build protocol_settings for VLESS+Reality."""
    return {
        "tls": 2,
        "tls_settings": {
            "server_name": None,
            "allow_insecure": False,
            "ech": {"enabled": False, "config": None, "query_server_name": None, "key": None, "key_path": None, "config_path": None},
        },
        "flow": "xtls-rprx-vision",
        "encryption": {"enabled": False, "encryption": None, "decryption": None},
        "network": "tcp",
        "network_settings": [],
        "reality_settings": {
            "server_name": dest,
            "server_port": dest_port,
            "public_key": public_key,
            "private_key": private_key,
            "short_id": short_id,
            "allow_insecure": False,
        },
        "multiplex": {
            "enabled": False, "protocol": "smux", "max_connections": 4,
            "padding": False,
            "brutal": {"enabled": False, "up_mbps": 100, "down_mbps": 100},
        },
        "utls": {"enabled": True, "fingerprint": "chrome"},
    }


class ServerGroupResource(BaseResource):
    resource_path = "server/group"

    def fetch(self) -> list[dict[str, Any]]:
        return self.list()

    def save(self, name: str, id: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name}
        if id is not None:
            payload["id"] = id
        return self._post("server/group/save", **payload)

    def drop(self, id: int) -> dict[str, Any]:
        return self._post("server/group/drop", id=id)


class ServerRouteResource(BaseResource):
    resource_path = "server/route"

    def fetch(self) -> list[dict[str, Any]]:
        return self.list()

    def save(
        self,
        remarks: str,
        match: list,
        action: str,
        action_value: str | None = None,
        id: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "remarks": remarks,
            "match": match,
            "action": action,
        }
        if action_value is not None:
            payload["action_value"] = action_value
        if id is not None:
            payload["id"] = id
        return self._post("server/route/save", **payload)

    def drop(self, id: int) -> dict[str, Any]:
        return self._post("server/route/drop", id=id)


class ServerNodeResource(BaseResource):
    resource_path = "server/manage"

    def get_nodes(self) -> list[dict[str, Any]]:
        data = self._get("server/manage/getNodes")
        return data if isinstance(data, list) else []

    def save(
        self,
        name: str,
        group_ids: list,
        host: str,
        port: int,
        id: int | None = None,
        type: str = "vless",
        server_port: int = 443,
        rate: float = 1.0,
        protocol_settings: dict | None = None,
        enabled: bool = True,
        show: int = 1,
        route_ids: list | None = None,
        parent_id: int | None = None,
        machine_id: int | None = None,
        tags: list | None = None,
        generate_keys: bool = False,
        **extra,
    ) -> dict[str, Any]:
        """Create or update a VLESS+Reality node.

        Required:
          - name: node display name
          - group_ids: server group IDs (e.g. [3])
          - host: server IP or relay IP
          - port: client connection port (for direct nodes, same as server_port)

        Defaults:
          - type: "vless", server_port: 443, rate: 1.0
          - protocol_settings: auto-generated VLESS+Reality if generate_keys=True

        Usage:
          # Create with auto-generated Reality keys
          api.save(name="SG-5", group_ids=[3], host="89.34.227.226",
                   port=443, machine_id=7, generate_keys=True)

          # Create with explicit protocol_settings (update existing)
          api.save(name="SG-3", group_ids=[3], host="89.34.227.226",
                   port=443, id=24, protocol_settings=existing_ps)
        """
        if generate_keys and (protocol_settings is None or id is None):
            pub, priv, sid = generate_reality_keys()
            dest_port = str(server_port)
            protocol_settings = build_reality_settings(pub, priv, sid, dest_port=dest_port)

        if protocol_settings is None:
            raise ValueError(
                "protocol_settings is required. "
                "Pass generate_keys=True to auto-generate Reality keys, "
                "or pass protocol_settings=build_reality_settings(...)."
            )

        payload: dict[str, Any] = {
            "type": type,
            "name": name,
            "host": host,
            "port": port,
            "server_port": str(server_port),
            "rate": rate,
            "enabled": enabled,
            "show": show,
            "group_ids": group_ids,
            "protocol_settings": protocol_settings,
        }
        if id is not None:
            payload["id"] = id
        if route_ids is not None:
            payload["route_ids"] = route_ids
        if parent_id is not None:
            payload["parent_id"] = parent_id
        if machine_id is not None:
            payload["machine_id"] = machine_id
        if tags is not None:
            payload["tags"] = tags
        payload.update(extra)
        return self._post("server/manage/save", **payload)

    def update(self, id: int, **fields) -> dict[str, Any]:
        payload = {"id": id, **fields}
        return self._post("server/manage/update", **payload)

    def drop(self, id: int, confirm: bool = False) -> dict[str, Any]:
        if not confirm:
            raise ValueError("server_node_drop requires confirm=True")
        return self._post("server/manage/drop", id=id)

    def copy(self, id: int) -> dict[str, Any]:
        return self._post("server/manage/copy", id=id)

    def batch_delete(self, ids: list[int]) -> dict[str, Any]:
        return self._post("server/manage/batchDelete", ids=ids)

    def batch_update(self, ids: list[int], **fields) -> dict[str, Any]:
        payload = {"ids": ids, **fields}
        return self._post("server/manage/batchUpdate", **payload)

    def reset_traffic(self, id: int) -> dict[str, Any]:
        return self._post("server/manage/resetTraffic", id=id)

    def batch_reset_traffic(self, ids: list[int]) -> dict[str, Any]:
        return self._post("server/manage/batchResetTraffic", ids=ids)

    def generate_ech_key(self, public_name: str = "ech.example.com") -> dict[str, Any]:
        return self._get("server/manage/generateEchKey", public_name=public_name)

    def sort(self, *args, **kwargs) -> dict[str, Any]:
        raise NotImplementedError("Use sort_with_order instead")

    def sort_nodes(self, items: list[dict]) -> dict[str, Any]:
        """Sort expects list of {id, order}."""
        return self._post("server/manage/sort", items=items)


class ServerMachineResource(BaseResource):
    resource_path = "server/machine"

    def fetch(self) -> list[dict[str, Any]]:
        return self.list()

    def save(
        self,
        name: str,
        notes: str | None = None,
        is_active: bool = True,
        id: int | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "is_active": is_active}
        if notes is not None:
            payload["notes"] = notes
        if id is not None:
            payload["id"] = id
        return self._post("server/machine/save", **payload)

    def drop(self, id: int, confirm: bool = False) -> dict[str, Any]:
        if not confirm:
            raise ValueError("server_machine_drop requires confirm=True")
        return self._post("server/machine/drop", id=id)

    def reset_token(self, id: int) -> dict[str, Any]:
        return self._post("server/machine/resetToken", id=id)

    def get_token(self, id: int) -> str | None:
        data = self._get("server/machine/getToken", id=id)
        return data.get("token") if isinstance(data, dict) else None

    def install_command(self, id: int) -> str | None:
        data = self._get("server/machine/installCommand", id=id)
        return data.get("install_command") if isinstance(data, dict) else None

    def nodes(self, machine_id: int) -> list[dict[str, Any]]:
        data = self._get("server/machine/nodes", machine_id=machine_id)
        return data if isinstance(data, list) else []

    def history(
        self,
        machine_id: int,
        limit: int = 60,
        range_hours: int = 1,
    ) -> list[dict[str, Any]]:
        data = self._get(
            "server/machine/history",
            machine_id=machine_id,
            limit=limit,
            range_hours=range_hours,
        )
        return data if isinstance(data, list) else []
