"""Term-specific public discovery with explicit provenance and partial coverage."""

import asyncio
import re

from .client import CourseDataError, validate_identifiers
from .parsers import parse_course, parse_section, parse_subject


def pagination(limit, offset):
    if type(limit) is not int or not 1 <= limit <= 50 or type(offset) is not int or offset < 0:
        raise CourseDataError("invalid_input")


def provenance(fetch):
    return {
        "source_url": fetch.source_url,
        "retrieved_at": fetch.retrieved_at,
        "cache_age_seconds": fetch.cache_age_seconds,
    }


class CourseService:
    def __init__(self, client):
        self.client = client

    def base(self, subject, year, term, course_number=None):
        subject, year, term, course_number = validate_identifiers(
            subject, year, term, course_number
        )
        path = f"/cisapp/explorer/schedule/{year}/{term}/{subject}"
        if course_number is not None:
            path += "/" + course_number
        return path, {
            "subject": subject,
            "year": year,
            "term": term,
            "course_number": course_number,
        }

    async def search_courses(
        self, subject: str, year: int, term: str, query: str = "", limit: int = 20, offset: int = 0
    ) -> dict:
        pagination(limit, offset)
        path, coverage = self.base(subject, year, term)
        if not isinstance(query, str) or len(query) > 500:
            raise CourseDataError("invalid_input")
        q = " ".join(query.lower().split())
        code = re.fullmatch(r"([a-z]{2,8})\s*([0-9]{3})", q)
        if code:
            q = code[2] if code[1].upper() == coverage["subject"] else "__different_subject__"
        fetch = await self.client.get(path + ".xml", "subject")
        courses = parse_subject(fetch.body)["courses"]
        matches = [c for c in courses if q in c["course_number"].lower() or q in c["title"].lower()]
        return {
            "results": matches[offset : offset + limit],
            "total_matches": len(matches),
            "offset": offset,
            "next_offset": offset + limit if offset + limit < len(matches) else None,
            "coverage": coverage,
            **provenance(fetch),
        }

    async def get_course_details(
        self, subject: str, course_number: str, year: int, term: str
    ) -> dict:
        path, coverage = self.base(subject, year, term, course_number)
        fetch = await self.client.get(path + ".xml", "course")
        return {
            **parse_course(fetch.body),
            "coverage": coverage,
            "next_offset": None,
            **provenance(fetch),
        }

    async def list_course_sections(
        self,
        subject: str,
        course_number: str,
        year: int,
        term: str,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        pagination(limit, offset)
        path, coverage = self.base(subject, year, term, course_number)
        fetch = await self.client.get(path + ".xml", "course")
        references = parse_course(fetch.body)["section_references"]
        selected = references[offset : offset + limit]

        async def section(ref):
            crn = ref["crn"]
            try:
                if not re.fullmatch(r"[0-9]{5}", crn):
                    raise CourseDataError("invalid_schema")
                result = await self.client.get(path + "/" + crn + ".xml", "section")
                data = parse_section(result.body)
                if data["crn"] != crn:
                    raise CourseDataError("invalid_schema")
                return {**data, **provenance(result)}, None
            except CourseDataError as exc:
                return None, {"crn": crn, "code": exc.code}

        values = await asyncio.gather(*(section(r) for r in selected))
        sections = [s for s, e in values if s is not None]
        errors = [e for s, e in values if e is not None]
        next_offset = offset + limit if offset + limit < len(references) else None
        return {
            "sections": sections,
            "errors": errors,
            "complete": not errors,
            "requested_count": len(selected),
            "returned_count": len(sections),
            "total_sections": len(references),
            "offset": offset,
            "next_offset": next_offset,
            "coverage": coverage,
            **provenance(fetch),
        }
