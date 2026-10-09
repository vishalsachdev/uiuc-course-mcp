import sys
from pathlib import Path

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.memory import create_connected_server_and_client_session

from uiuc_course_mcp.client import CourseExplorerClient
from uiuc_course_mcp.server import create_server
from uiuc_course_mcp.service import CourseService


async def test_real_mcp():
    def handler(r):
        name = (
            "subject"
            if r.url.path.endswith("BADM.xml")
            else "course"
            if r.url.path.endswith("554.xml")
            else "section"
        )
        body = Path("tests/fixtures/" + name + ".xml").read_bytes()
        if name == "section":
            body = body.replace(
                b'id="68315"', ('id="' + r.url.path.rsplit("/", 1)[-1][:-4] + '"').encode(), 1
            )
        return httpx.Response(200, content=body)

    async with CourseExplorerClient(transport=httpx.MockTransport(handler)) as client:
        server = create_server(CourseService(client))
        async with create_connected_server_and_client_session(server) as session:
            tools = (await session.list_tools()).tools
            assert {t.name for t in tools} == {
                "search_courses",
                "get_course_details",
                "list_course_sections",
            }
            for t in tools:
                assert {"year", "term"} <= set(t.inputSchema["required"])
                assert t.annotations.readOnlyHint
            for name in ["search_courses", "get_course_details", "list_course_sections"]:
                args = {"subject": "BADM", "year": 2026, "term": "fall"}
                if name != "search_courses":
                    args["course_number"] = "554"
                result = await session.call_tool(name, args)
                assert (
                    not result.isError and result.structuredContent["coverage"]["subject"] == "BADM"
                )
            result = await session.call_tool(
                "search_courses", {"subject": "../BADM", "year": 2026, "term": "fall"}
            )
            assert result.isError


async def test_subprocess_stdio():
    async with (
        stdio_client(
            StdioServerParameters(command=sys.executable, args=["-m", "uiuc_course_mcp"])
        ) as (read, write),
        ClientSession(read, write) as session,
    ):
        result = await session.initialize()
        assert result.serverInfo.name == "UIUC Course MCP"
        assert len((await session.list_tools()).tools) == 3
