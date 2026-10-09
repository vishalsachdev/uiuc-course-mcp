import asyncio

import httpx
import pytest

from uiuc_course_mcp.client import CourseDataError, CourseExplorerClient, validate_identifiers

PATH = "/cisapp/explorer/schedule/2026/fall/BADM.xml"


@pytest.mark.parametrize(
    "subject,year,term,number",
    [
        ("BADM/..", 2026, "fall", None),
        ("BADM", 2026, "../fall", None),
        ("BADM", 1999, "fall", None),
        ("BADM", 2026, "fall", "554%2f"),
        ("BA%44M", 2026, "fall", None),
    ],
)
def test_reject_identifiers(subject, year, term, number):
    with pytest.raises(CourseDataError):
        validate_identifiers(subject, year, term, number)


def test_normalize():
    assert validate_identifiers(" badm ", 2026, "FALL", "554") == ("BADM", 2026, "fall", "554")


async def test_cache_original_timestamp_expiry():
    calls = []
    clock = [0]

    def handler(request):
        calls.append(request)
        return httpx.Response(200, content=b"<subject/>")

    async with CourseExplorerClient(
        transport=httpx.MockTransport(handler), clock=lambda: clock[0]
    ) as c:
        a = await c.get(PATH, "subject")
        clock[0] = 299
        b = await c.get(PATH, "subject")
        assert b.retrieved_at == a.retrieved_at and b.cache_age_seconds == 299
        clock[0] = 300
        await c.get(PATH, "subject")
        assert len(calls) == 2
        assert c.http.timeout.read == 15


@pytest.mark.parametrize(
    "status,body,code",
    [
        (302, b"", "upstream_http"),
        (404, b"", "not_found"),
        (200, b"<html/>", "invalid_xml"),
        (200, b"<course/>", "invalid_xml"),
        (200, b"<!DOCTYPE subject><subject/>", "invalid_xml"),
        (200, b"x" * (2 * 1024 * 1024 + 1), "response_too_large"),
    ],
)
async def test_bad_response(status, body, code):
    async with CourseExplorerClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(status, content=body))
    ) as c:
        with pytest.raises(CourseDataError) as e:
            await c.get(PATH, "subject")
        assert e.value.code == code


async def test_retry_and_concurrency():
    active = peak = 0
    attempts = {}

    async def handler(r):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.001)
        active -= 1
        n = attempts.get(str(r.url), 0)
        attempts[str(r.url)] = n + 1
        return httpx.Response(503 if n < 2 else 200, content=b"<subject/>")

    async with CourseExplorerClient(transport=httpx.MockTransport(handler), backoff=0) as c:
        await asyncio.gather(
            *(
                c.get(PATH.replace("BADM", s), "subject")
                for s in ["BADM", "CS", "STAT", "MATH", "ECON", "FIN"]
            )
        )
    assert peak <= 4 and set(attempts.values()) == {3}


async def test_no_retry_404_and_no_arbitrary_paths():
    calls = []

    def handler(r):
        calls.append(r)
        return httpx.Response(404)

    async with CourseExplorerClient(transport=httpx.MockTransport(handler)) as c:
        for path in ["https://evil.test/a", "//evil.test/a", PATH + "/../x"]:
            with pytest.raises(CourseDataError):
                await c.get(path, "subject")
        with pytest.raises(CourseDataError):
            await c.get(PATH, "subject")
    assert len(calls) == 1


async def test_transport_exhaustion_and_errors_not_cached():
    calls = []

    def handler(request):
        calls.append(request)
        raise httpx.ReadTimeout("timeout")

    async with CourseExplorerClient(transport=httpx.MockTransport(handler), backoff=0) as c:
        for _ in range(2):
            with pytest.raises(CourseDataError) as e:
                await c.get(PATH, "subject")
            assert e.value.code == "upstream_unavailable"
    assert len(calls) == 6


async def test_cache_bounded_eviction():
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, content=b"<subject/>")

    async with CourseExplorerClient(transport=httpx.MockTransport(handler)) as c:
        for i in range(129):
            await c.get(
                PATH.replace("/2026/", "/2025/").replace(
                    "BADM", "AA" + chr(65 + i // 26) + chr(65 + i % 26)
                ),
                "subject",
            )
        assert len(c.cache) == 128
        await c.get(PATH.replace("/2026/", "/2025/").replace("BADM", "AAAA"), "subject")
    assert len(calls) == 130


async def test_upper_year_boundary_constructs_request():
    async with CourseExplorerClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, content=b"<subject><courses/></subject>")
        )
    ) as c:
        result = await c.get(PATH.replace("2026", "2100"), "subject")
        assert "/2100/" in result.source_url
