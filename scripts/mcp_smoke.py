"""Check an installed stdio server; live Course Explorer calls are explicit opt-in.

uv run python scripts/mcp_smoke.py -- .venv/bin/uiuc-course-mcp
uv run python scripts/mcp_smoke.py --live -- uvx --from git+https://... uiuc-course-mcp
"""

import argparse
import asyncio
import json
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def check(command, live):
    async with (
        stdio_client(
            StdioServerParameters(command=command[0], args=command[1:], env=dict(os.environ))
        ) as (r, w),
        ClientSession(r, w) as session,
    ):
        info = await session.initialize()
        assert info.serverInfo.name == "UIUC Course MCP", info.serverInfo
        tools = (await session.list_tools()).tools
        assert {t.name for t in tools} == {
            "search_courses", "get_course_details", "list_course_sections"
        }
        for tool in tools:
            assert {"year", "term"} <= set(tool.inputSchema["required"])
            assert tool.annotations and tool.annotations.readOnlyHint
        print(json.dumps({"server": info.serverInfo.name, "tools": sorted(t.name for t in tools)}))
        if live:
            for name in ["search_courses", "get_course_details", "list_course_sections"]:
                args = {"subject": "BADM", "year": 2026, "term": "fall"}
                if name == "search_courses":
                    args["query"] = "database"
                else:
                    args["course_number"] = "554"
                result = await session.call_tool(name, args)
                assert not result.isError, result
                data = result.structuredContent
                assert data is not None
                if name == "search_courses":
                    assert any(c["course_number"] == "554" for c in data["results"])
                elif name == "get_course_details":
                    assert data["title"] == "Enterprise Database Management"
                else:
                    assert data["complete"] and data["sections"] and not data["errors"]
                print(json.dumps({"tool": name, "result": data}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Query public BADM 554 fall 2026 data")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    options = parser.parse_args()
    command = options.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("supply the installed server command after --")
    asyncio.run(check(command, options.live))
