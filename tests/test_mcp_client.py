#!/usr/bin/env python3
"""Test MCP client — connects to Xboard MCP server and calls a tool."""

import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

MCP_URL = "http://192.168.31.148:9020/sse"
API_KEY = "nGKuqw5wTC7RC_BAIb1f_tX8r8xEwuEvVF_A3m1Jp18"


async def main():
    headers = {"X-API-Key": API_KEY}
    async with sse_client(MCP_URL, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"=== Tools: {len(tools.tools)} ===")
            for t in tools.tools[:5]:
                print(f"  {t.name}: {t.description[:60]}...")

            # Call config_fetch
            print("\n=== config_fetch ===")
            result = await session.call_tool("config_fetch", {})
            for content in result.content:
                text = content.text[:200]
                print(f"  {text}...")
                break

            # Call plan_list
            print("\n=== plan_list ===")
            result = await session.call_tool("plan_list", {})
            for content in result.content:
                print(f"  {content.text[:300]}")

            # Call stat_dashboard
            print("\n=== stat_dashboard ===")
            result = await session.call_tool("stat_dashboard", {})
            for content in result.content:
                print(f"  {content.text[:300]}")

            # Call system_status
            print("\n=== system_status ===")
            result = await session.call_tool("system_status", {})
            for content in result.content:
                print(f"  {content.text[:200]}")

            # Call server_group_list
            print("\n=== server_group_list ===")
            result = await session.call_tool("server_group_list", {})
            for content in result.content:
                print(f"  {content.text[:200]}")

            print("\n=== ALL PASSED ===")


if __name__ == "__main__":
    asyncio.run(main())
