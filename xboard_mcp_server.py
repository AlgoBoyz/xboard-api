"""Xboard Admin API MCP Server.

Run on the Xboard server. Exposes all xboard_api wrapper functions
as MCP tools over SSE transport with API key authentication.

Usage:
    XBOARD_API_KEY=secret python server.py --port 9020
"""

from __future__ import annotations

import os
import sys
import logging
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import Response

# Load env file if present
load_dotenv("/etc/xboard-mcp.env", override=False)
load_dotenv(os.path.expanduser("~/.xboard-mcp.env"), override=False)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("XBOARD_BASE_URL", "http://127.0.0.1")
SECURE_PATH = os.environ.get("XBOARD_SECURE_PATH", "4ec3c529")
API_KEY = os.environ.get("XBOARD_API_KEY", "")
ALLOWED_IPS = os.environ.get("XBOARD_ALLOWED_IPS", "")
BIND_HOST = os.environ.get("XBOARD_MCP_HOST", "127.0.0.1")
BIND_PORT = int(os.environ.get("XBOARD_MCP_PORT", "9020"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("xboard-mcp")

# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

AUTH_HEADER = "X-API-Key"


async def auth_middleware(request: Request, call_next):
    if request.url.path in ("/health", "/ping"):
        return await call_next(request)

    # IP allowlist check
    if ALLOWED_IPS:
        client_ip = request.client.host if request.client else "unknown"
        allowed = [ip.strip() for ip in ALLOWED_IPS.split(",") if ip.strip()]
        if client_ip not in allowed and "0.0.0.0/0" not in allowed:
            logger.warning(f"Blocked IP: {client_ip}")
            return Response("Forbidden", status_code=403)

    # API key check
    key = request.headers.get(AUTH_HEADER, "")
    if not API_KEY:
        return await call_next(request)
    if key != API_KEY:
        return Response("Unauthorized", status_code=401)

    # Patch Host header to avoid Starlette 421 Misdirected Request
    # when accessed from external IPs
    if request.headers.get("host", "").split(":")[0] not in ("127.0.0.1", "localhost"):
        request.scope["headers"] = [
            (k, v) for k, v in request.scope.get("headers", [])
            if k != b"host"
        ] + [(b"host", b"localhost")]

    return await call_next(request)


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="xboard-admin-mcp",
    instructions="Xboard Admin API — manage plans, users, nodes, orders, config, etc.",
)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

from xboard_api import XboardClient, load_token

_client: XboardClient | None = None


def get_client() -> XboardClient:
    global _client
    if _client is None:
        _client = XboardClient(base_url=BASE_URL, secure_path=SECURE_PATH)
    return _client


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

# -- Config --
@mcp.tool(name="config_fetch", description="获取站点全部配置或指定 key")
def config_fetch(key: str | None = None) -> dict[str, Any]:
    from xboard_api.resources.config import ConfigResource
    return ConfigResource(get_client()).fetch(key=key)


@mcp.tool(name="config_save", description="保存站点配置，传入 key=value 对")
def config_save(**values) -> dict[str, Any]:
    from xboard_api.resources.config import ConfigResource
    return ConfigResource(get_client()).save(**values)


# -- Plan --
@mcp.tool(name="plan_list", description="获取所有套餐列表")
def plan_list() -> list[dict[str, Any]]:
    from xboard_api.resources.plan import PlanResource
    return PlanResource(get_client()).fetch()


@mcp.tool(name="plan_save", description="创建或更新套餐")
def plan_save(
    name: str,
    transfer_enable: int,
    group_id: int,
    prices: dict,
    id: int | None = None,
    content: str | None = None,
    speed_limit: int = 20,
    device_limit: int = 10,
    capacity_limit: int = 100,
    tags: list | None = None,
    **extra,
) -> dict[str, Any]:
    from xboard_api.resources.plan import PlanResource
    return PlanResource(get_client()).save(
        name=name, transfer_enable=transfer_enable, group_id=group_id,
        prices=prices, id=id, content=content,
        speed_limit=speed_limit, device_limit=device_limit,
        capacity_limit=capacity_limit, tags=tags, **extra,
    )


@mcp.tool(name="plan_drop", description="删除套餐")
def plan_drop(id: int) -> dict[str, Any]:
    from xboard_api.resources.plan import PlanResource
    return PlanResource(get_client()).drop(id=id)


# -- User --
@mcp.tool(name="user_get_by_id", description="根据 ID 获取用户信息")
def user_get_by_id(id: int) -> dict[str, Any]:
    from xboard_api.resources.user import UserResource
    return UserResource(get_client()).get_by_id(id=id)


@mcp.tool(name="user_generate", description="批量生成用户")
def user_generate(
    email_suffix: str,
    plan_id: int | None = None,
    generate_count: int = 1,
    email_prefix: str | None = None,
    password: str | None = None,
    expired_at: int | None = None,
) -> dict[str, Any]:
    from xboard_api.resources.user import UserResource
    return UserResource(get_client()).generate(
        email_suffix=email_suffix, plan_id=plan_id,
        generate_count=generate_count, email_prefix=email_prefix,
        password=password, expired_at=expired_at,
    )


@mcp.tool(name="user_update", description="更新用户信息")
def user_update(id: int, **fields) -> dict[str, Any]:
    from xboard_api.resources.user import UserResource
    return UserResource(get_client()).update(id=id, **fields)


@mcp.tool(name="user_destroy", description="删除用户")
def user_destroy(id: int) -> dict[str, Any]:
    from xboard_api.resources.user import UserResource
    return UserResource(get_client()).destroy(id=id)


@mcp.tool(name="user_reset_secret", description="重置用户订阅密钥")
def user_reset_secret(id: int) -> dict[str, Any]:
    from xboard_api.resources.user import UserResource
    return UserResource(get_client()).reset_secret(id=id)


# -- Server Nodes --
@mcp.tool(name="server_node_list", description="获取所有节点列表")
def server_node_list() -> list[dict[str, Any]]:
    from xboard_api.resources.server import ServerNodeResource
    return ServerNodeResource(get_client()).get_nodes()


@mcp.tool(name="server_node_save", description="创建或更新节点 (VLESS/VMess/Trojan 等)")
def server_node_save(
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
    machine_id: int | None = None,
    tags: list | None = None,
    **extra,
) -> dict[str, Any]:
    from xboard_api.resources.server import ServerNodeResource
    return ServerNodeResource(get_client()).save(
        type=type, name=name, host=host, port=port,
        server_port=server_port, rate=rate,
        protocol_settings=protocol_settings, id=id,
        enabled=enabled, show=show, group_ids=group_ids,
        route_ids=route_ids, machine_id=machine_id, tags=tags, **extra,
    )


@mcp.tool(name="server_node_drop", description="删除节点")
def server_node_drop(id: int) -> dict[str, Any]:
    from xboard_api.resources.server import ServerNodeResource
    return ServerNodeResource(get_client()).drop(id=id)


@mcp.tool(name="server_node_generate_ech", description="生成 ECH 通讯密钥")
def server_node_generate_ech(public_name: str = "ech.example.com") -> dict[str, Any]:
    from xboard_api.resources.server import ServerNodeResource
    return ServerNodeResource(get_client()).generate_ech_key(public_name=public_name)


# -- Server Machines --
@mcp.tool(name="server_machine_list", description="获取宿主机列表")
def server_machine_list() -> list[dict[str, Any]]:
    from xboard_api.resources.server import ServerMachineResource
    return ServerMachineResource(get_client()).fetch()


@mcp.tool(name="server_machine_save", description="创建或更新宿主机")
def server_machine_save(name: str, notes: str | None = None, is_active: bool = True, id: int | None = None) -> dict[str, Any]:
    from xboard_api.resources.server import ServerMachineResource
    return ServerMachineResource(get_client()).save(name=name, notes=notes, is_active=is_active, id=id)


@mcp.tool(name="server_machine_drop", description="删除宿主机")
def server_machine_drop(id: int) -> dict[str, Any]:
    from xboard_api.resources.server import ServerMachineResource
    return ServerMachineResource(get_client()).drop(id=id)


# -- Server Groups --
@mcp.tool(name="server_group_list", description="获取权限组列表")
def server_group_list() -> list[dict[str, Any]]:
    from xboard_api.resources.server import ServerGroupResource
    return ServerGroupResource(get_client()).fetch()


@mcp.tool(name="server_group_save", description="创建或更新权限组")
def server_group_save(name: str, id: int | None = None) -> dict[str, Any]:
    from xboard_api.resources.server import ServerGroupResource
    return ServerGroupResource(get_client()).save(name=name, id=id)


@mcp.tool(name="server_group_drop", description="删除权限组")
def server_group_drop(id: int) -> dict[str, Any]:
    from xboard_api.resources.server import ServerGroupResource
    return ServerGroupResource(get_client()).drop(id=id)


# -- Server Routes --
@mcp.tool(name="server_route_list", description="获取路由规则列表")
def server_route_list() -> list[dict[str, Any]]:
    from xboard_api.resources.server import ServerRouteResource
    return ServerRouteResource(get_client()).fetch()


@mcp.tool(name="server_route_save", description="创建或更新路由规则")
def server_route_save(remarks: str, match: list, action: str, action_value: str | None = None, id: int | None = None) -> dict[str, Any]:
    from xboard_api.resources.server import ServerRouteResource
    return ServerRouteResource(get_client()).save(remarks=remarks, match=match, action=action, action_value=action_value, id=id)


@mcp.tool(name="server_route_drop", description="删除路由规则")
def server_route_drop(id: int) -> dict[str, Any]:
    from xboard_api.resources.server import ServerRouteResource
    return ServerRouteResource(get_client()).drop(id=id)


# -- Order --
@mcp.tool(name="order_assign", description="手动为用户分配订单")
def order_assign(plan_id: int, email: str, period: str, total_amount: int) -> dict[str, Any]:
    from xboard_api.resources.order import OrderResource
    return OrderResource(get_client()).assign(plan_id=plan_id, email=email, period=period, total_amount=total_amount)


@mcp.tool(name="order_paid", description="手动标记订单已支付")
def order_paid(trade_no: str) -> dict[str, Any]:
    from xboard_api.resources.order import OrderResource
    return OrderResource(get_client()).paid(trade_no=trade_no)


@mcp.tool(name="order_cancel", description="取消订单")
def order_cancel(trade_no: str) -> dict[str, Any]:
    from xboard_api.resources.order import OrderResource
    return OrderResource(get_client()).cancel(trade_no=trade_no)


@mcp.tool(name="order_detail", description="获取订单详情")
def order_detail(id: int) -> dict[str, Any]:
    from xboard_api.resources.order import OrderResource
    return OrderResource(get_client()).detail(id=id)


# -- Stat --
@mcp.tool(name="stat_dashboard", description="获取仪表盘概览")
def stat_dashboard() -> dict[str, Any]:
    from xboard_api.resources.stat import StatResource
    return StatResource(get_client()).get_override()


@mcp.tool(name="stat_traffic_rank", description="获取流量排行")
def stat_traffic_rank(type: str = "user", start_time: int | None = None, end_time: int | None = None) -> list[dict[str, Any]]:
    from xboard_api.resources.stat import StatResource
    return StatResource(get_client()).get_traffic_rank(type=type, start_time=start_time, end_time=end_time)


# -- Notice --
@mcp.tool(name="notice_list", description="获取公告列表")
def notice_list() -> list[dict[str, Any]]:
    from xboard_api.resources.notice import NoticeResource
    return NoticeResource(get_client()).fetch()


@mcp.tool(name="notice_save", description="创建或更新公告")
def notice_save(title: str, content: str, id: int | None = None, img_url: str | None = None, tags: list | None = None, show: int = 0) -> dict[str, Any]:
    from xboard_api.resources.notice import NoticeResource
    return NoticeResource(get_client()).save(title=title, content=content, id=id, img_url=img_url, tags=tags, show=show)


@mcp.tool(name="notice_drop", description="删除公告")
def notice_drop(id: int) -> dict[str, Any]:
    from xboard_api.resources.notice import NoticeResource
    return NoticeResource(get_client()).drop(id=id)


# -- Ticket --
@mcp.tool(name="ticket_reply", description="回复工单")
def ticket_reply(id: int, message: str) -> dict[str, Any]:
    from xboard_api.resources.ticket import TicketResource
    return TicketResource(get_client()).reply(id=id, message=message)


@mcp.tool(name="ticket_close", description="关闭工单")
def ticket_close(id: int) -> dict[str, Any]:
    from xboard_api.resources.ticket import TicketResource
    return TicketResource(get_client()).close(id=id)


# -- Coupon --
@mcp.tool(name="coupon_generate", description="创建优惠券")
def coupon_generate(
    name: str, type: int, value: int, started_at: int, ended_at: int,
    generate_count: int = 1, limit_use: int | None = None,
) -> dict[str, Any]:
    from xboard_api.resources.coupon import CouponResource
    return CouponResource(get_client()).generate(
        name=name, type=type, value=value, started_at=started_at,
        ended_at=ended_at, generate_count=generate_count, limit_use=limit_use,
    )


@mcp.tool(name="coupon_drop", description="删除优惠券")
def coupon_drop(id: int) -> dict[str, Any]:
    from xboard_api.resources.coupon import CouponResource
    return CouponResource(get_client()).drop(id=id)


# -- GiftCard --
@mcp.tool(name="giftcard_create_template", description="创建礼品卡模板")
def giftcard_create_template(name: str, type: int, rewards: list, description: str | None = None) -> dict[str, Any]:
    from xboard_api.resources.gift_card import GiftCardResource
    return GiftCardResource(get_client()).create_template(name=name, type=type, rewards=rewards, description=description)


@mcp.tool(name="giftcard_generate_codes", description="生成礼品卡兑换码")
def giftcard_generate_codes(template_id: int, count: int) -> dict[str, Any]:
    from xboard_api.resources.gift_card import GiftCardResource
    return GiftCardResource(get_client()).generate_codes(template_id=template_id, count=count)


# -- Knowledge --
@mcp.tool(name="knowledge_save", description="创建或更新知识库文章")
def knowledge_save(title: str, body: str, category: str, language: str = "zh-CN", id: int | None = None, show: int = 0) -> dict[str, Any]:
    from xboard_api.resources.knowledge import KnowledgeResource
    return KnowledgeResource(get_client()).save(title=title, body=body, category=category, language=language, id=id, show=show)


# -- Payment --
@mcp.tool(name="payment_list", description="获取支付方式列表")
def payment_list() -> list[dict[str, Any]]:
    from xboard_api.resources.payment import PaymentResource
    return PaymentResource(get_client()).fetch()


@mcp.tool(name="payment_save", description="创建或更新支付方式")
def payment_save(name: str, payment: str, config: dict, id: int | None = None) -> dict[str, Any]:
    from xboard_api.resources.payment import PaymentResource
    return PaymentResource(get_client()).save(name=name, payment=payment, config=config, id=id)


# -- System --
@mcp.tool(name="system_status", description="获取系统运行状态")
def system_status() -> dict[str, Any]:
    from xboard_api.resources.system import SystemResource
    return SystemResource(get_client()).get_system_status()


@mcp.tool(name="system_audit_log", description="获取管理员审计日志")
def system_audit_log(page: int = 1, page_size: int = 50) -> dict[str, Any]:
    from xboard_api.resources.system import SystemResource
    return SystemResource(get_client()).get_audit_log(page=page, page_size=page_size)


# -- Traffic Reset --
@mcp.tool(name="traffic_reset_user", description="手动重置用户流量")
def traffic_reset_user(user_id: int, reason: str | None = None) -> dict[str, Any]:
    from xboard_api.resources.traffic_reset import TrafficResetResource
    return TrafficResetResource(get_client()).reset_user(user_id=user_id, reason=reason)


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    from starlette.middleware.base import BaseHTTPMiddleware

    if not API_KEY:
        logger.warning("XBOARD_API_KEY not set — authentication disabled!")

    sse = mcp.sse_app()
    sse.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

    logger.info(f"Xboard MCP server starting on {BIND_HOST}:{BIND_PORT}")
    logger.info(f"Auth: {'enabled' if API_KEY else 'DISABLED'}, Allowed IPs: {ALLOWED_IPS or 'any'}")
    uvicorn.run(sse, host=BIND_HOST, port=BIND_PORT)
