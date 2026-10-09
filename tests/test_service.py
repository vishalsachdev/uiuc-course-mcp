from pathlib import Path

import httpx
import pytest

from uiuc_course_mcp.client import CourseDataError, CourseExplorerClient
from uiuc_course_mcp.service import CourseService


@pytest.fixture
async def service():
    def handler(r):
        path = r.url.path
        if path.endswith("76559.xml"):
            return httpx.Response(503)
        name = (
            "section"
            if path.count("/") == 8
            else "course"
            if path.endswith("/554.xml")
            else "subject"
        )
        if path.endswith("81817.xml"):
            name = "section"
        return httpx.Response(200, content=Path("tests/fixtures/" + name + ".xml").read_bytes())

    async with CourseExplorerClient(transport=httpx.MockTransport(handler), backoff=0) as c:
        yield CourseService(c)


@pytest.mark.parametrize("q", ["badm 554", "BADM554", "554", "database", "enterprise"])
async def test_search(service, q):
    r = await service.search_courses("badm", 2026, "fall", q, 20)
    assert any(c["course_number"] == "554" for c in r["results"])
    assert r["coverage"]["year"] == 2026 and r["coverage"]["term"] == "fall"
    assert r["source_url"].startswith("https://courses.illinois.edu/")


async def test_no_match_and_page(service):
    r = await service.search_courses("BADM", 2026, "fall", "no such title")
    assert r["total_matches"] == 0 and r["results"] == []
    r = await service.search_courses("BADM", 2026, "fall", "", 1, 1)
    assert len(r["results"]) == 1 and r["next_offset"] == 2


@pytest.mark.parametrize("kwargs", [{"limit": 0}, {"limit": 51}, {"offset": -1}, {"limit": True}])
async def test_invalid_pagination(service, kwargs):
    with pytest.raises(CourseDataError):
        await service.search_courses("BADM", 2026, "fall", **kwargs)


async def test_details(service):
    r = await service.get_course_details("BADM", "554", 2026, "fall")
    assert r["title"] == "Enterprise Database Management"
    assert len(r["section_references"]) == 3


async def test_sections_partial(service):
    r = await service.list_course_sections("BADM", "554", 2026, "fall", 2)
    assert not r["complete"] and r["requested_count"] == 2 and r["returned_count"] == 1
    assert r["errors"] == [{"crn": "76559", "code": "upstream_unavailable"}]
    assert r["next_offset"] == 2
    assert r["sections"][0]["crn"] == "68315"


async def test_schema_failure_not_complete_empty_success():
    async with CourseExplorerClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, content=b"<course><label>Title</label><offerings/></course>"
            )
        )
    ) as c:
        with pytest.raises(CourseDataError) as e:
            await CourseService(c).list_course_sections("BADM", "554", 2026, "fall")
        assert e.value.code == "invalid_schema"


async def test_explicit_empty_sections_valid():
    async with CourseExplorerClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(
                200, content=b"<course><label>Title</label><sections/></course>"
            )
        )
    ) as c:
        result = await CourseService(c).list_course_sections("BADM", "554", 2026, "fall")
        assert result["complete"] and result["total_sections"] == 0
