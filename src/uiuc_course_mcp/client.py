"""Bounded public XML access; no credentials or persistent storage."""

import asyncio
import re
import time
from collections import OrderedDict
from dataclasses import dataclass, replace
from datetime import UTC, datetime

import httpx
from defusedxml import ElementTree

ORIGIN = "https://courses.illinois.edu"


class CourseDataError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def validate_identifiers(subject, year, term, course_number=None):
    if not isinstance(subject, str) or not isinstance(term, str):
        raise CourseDataError("invalid_input")
    subject, term = subject.strip().upper(), term.strip().lower()
    if not re.fullmatch(r"[A-Z]{2,8}", subject):
        raise CourseDataError("invalid_input")
    if type(year) is not int or not 2000 <= year <= 2100:
        raise CourseDataError("invalid_input")
    if term not in {"spring", "summer", "fall", "winter"}:
        raise CourseDataError("invalid_input")
    if course_number is not None and (
        not isinstance(course_number, str) or not re.fullmatch(r"[0-9]{3}", course_number)
    ):
        raise CourseDataError("invalid_input")
    return subject, year, term, course_number


def xml_root(body, expected):
    try:
        root = ElementTree.fromstring(
            body, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
        if root.tag.rsplit("}", 1)[-1] != expected:
            raise ValueError()
        return root
    except Exception as exc:
        raise CourseDataError("invalid_xml") from exc


@dataclass(frozen=True)
class FetchResult:
    body: bytes
    source_url: str
    retrieved_at: str
    cache_age_seconds: float = 0


class CourseExplorerClient:
    def __init__(self, *, transport=None, clock=time.monotonic, backoff=0.25):
        self.http = httpx.AsyncClient(timeout=15, follow_redirects=False, transport=transport)
        self.clock, self.backoff = clock, backoff
        self.semaphore = asyncio.Semaphore(4)
        self.cache = OrderedDict()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.http.aclose()
        self.cache.clear()

    async def get(self, path: str, expected_root: str) -> FetchResult:
        if not re.fullmatch(
            r"/cisapp/explorer/schedule/(?:20[0-9]{2}|2100)/(?:spring|summer|fall|winter)/[A-Z]{2,8}(?:/[0-9]{3}(?:/[0-9]{5})?)?\.xml",
            path,
        ):
            raise CourseDataError("invalid_input")
        key = (path, expected_root)
        now = self.clock()
        if key in self.cache:
            fetched, result = self.cache[key]
            if now - fetched < 300:
                self.cache.move_to_end(key)
                return replace(result, cache_age_seconds=max(0, now - fetched))
            del self.cache[key]
        for attempt in range(3):
            try:
                async with self.semaphore, self.http.stream("GET", ORIGIN + path) as response:
                    if response.status_code == 404:
                        raise CourseDataError("not_found")
                    if response.status_code in {429, 500, 502, 503, 504}:
                        raise CourseDataError("upstream_unavailable")
                    if response.status_code != 200:
                        raise CourseDataError("upstream_http")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(body) + len(chunk) > 2 * 1024 * 1024:
                            raise CourseDataError("response_too_large")
                        body.extend(chunk)
                    xml_root(bytes(body), expected_root)
                result = FetchResult(bytes(body), ORIGIN + path, datetime.now(UTC).isoformat())
                self.cache[key] = (self.clock(), result)
                self.cache.move_to_end(key)
                while len(self.cache) > 128:
                    self.cache.popitem(last=False)
                return result
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt == 2:
                    raise CourseDataError("upstream_unavailable") from exc
            except CourseDataError as exc:
                if exc.code != "upstream_unavailable" or attempt == 2:
                    raise
            await asyncio.sleep(self.backoff * (2**attempt))
        raise CourseDataError("upstream_unavailable")
