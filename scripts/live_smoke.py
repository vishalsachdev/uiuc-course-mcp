"""Explicit read-only live verification: uv run python scripts/live_smoke.py 2026 fall."""

import asyncio
import json
import sys

from uiuc_course_mcp.client import CourseExplorerClient
from uiuc_course_mcp.service import CourseService


async def run(year, term):
    async with CourseExplorerClient() as client:
        service = CourseService(client)
        search = await service.search_courses("BADM", year, term, "BADM 554")
        details = await service.get_course_details("BADM", "554", year, term)
        sections = await service.list_course_sections("BADM", "554", year, term)
        assert any(c["course_number"] == "554" for c in search["results"])
        assert details["title"] == "Enterprise Database Management"
        assert sections["complete"] and sections["sections"]
        print(json.dumps({"search": search, "details": details, "sections": sections}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: live_smoke.py YEAR TERM")
    asyncio.run(run(int(sys.argv[1]), sys.argv[2]))
