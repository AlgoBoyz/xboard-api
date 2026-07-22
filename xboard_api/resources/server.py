"""Server resource — groups, routes, nodes, machines (24 endpoints)."""

from __future__ import annotations

from typing import Any

from .base import BaseResource


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
        type: str,
        name: str,
        host: str,
        port: int,
        server_port: int,
        rate: float,
        protocol_settings: dict,
        id: int | None = None,
        enabled: bool = True,
        show: int = 1,
        group_ids: list | None = None,
        route_ids: list | None = None,
        parent_id: int | None = None,
        machine_id: int | None = None,
        tags: list | None = None,
        **extra,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": type,
            "name": name,
            "host": host,
            "port": port,
            "server_port": str(server_port),
            "rate": rate,
            "enabled": enabled,
            "show": show,
            "protocol_settings": protocol_settings,
        }
        if id is not None:
            payload["id"] = id
        if group_ids is not None:
            payload["group_ids"] = group_ids
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
