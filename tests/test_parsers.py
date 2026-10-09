from pathlib import Path

import pytest

from uiuc_course_mcp.client import CourseDataError
from uiuc_course_mcp.parsers import parse_course, parse_section, parse_subject


def fixture(name):
    return Path("tests/fixtures/" + name + ".xml").read_bytes()


def test_subject():
    assert any(c["course_number"] == "554" for c in parse_subject(fixture("subject"))["courses"])


def test_course():
    c = parse_course(fixture("course"))
    assert c["title"] == "Enterprise Database Management"
    assert c["credits"] == "4 hours."
    assert "BADM 352" in c["description"] and "BADM 352" in c["restrictions"]
    assert c["section_references"][0]["crn"] == "68315"


def test_section():
    s = parse_section(fixture("section"))
    assert s["crn"] == "68315" and s["section_number"] == "AN1"
    m = s["meetings"][0]
    assert (m["days"], m["start"], m["end"]) == ("TR", "12:30PM", "01:50PM")
    assert m["instructors"][0]["name"] == "Sachdev, V"
    assert s["seats_remaining"] is None


def test_all_meetings_and_unknowns():
    s = parse_section(
        b'<section id="12345"><meetings><meeting><start>TBA</start><instructors><instructor>A</instructor><instructor>B</instructor></instructors></meeting><meeting/></meetings></section>'
    )
    assert len(s["meetings"]) == 2
    assert s["meetings"][0]["start"] == "TBA"
    assert len(s["meetings"][0]["instructors"]) == 2
    assert s["meetings"][1]["start"] is None


@pytest.mark.parametrize(
    "body", [b"<html/>", b"<course>", b'<!DOCTYPE course [<!ENTITY x "x">]><course>&x;</course>']
)
def test_unsafe_xml(body):
    with pytest.raises(CourseDataError):
        parse_course(body)


@pytest.mark.parametrize("body", [b"<subject/>", b"<subject><offeredCourses/></subject>"])
def test_subject_schema_change_is_error(body):
    with pytest.raises(CourseDataError):
        parse_subject(body)


@pytest.mark.parametrize(
    "body",
    [
        b"<course><label>Title</label></course>",
        b"<course><label>Title</label><newSections/></course>",
    ],
)
def test_course_schema_change_is_error(body):
    with pytest.raises(CourseDataError):
        parse_course(body)


def test_default_namespace_preserves_descendants():
    body = b'<section xmlns="urn:illinois" id="12345"><sectionNumber>A</sectionNumber><meetings><meeting><start>TBA</start><instructors><instructor>A</instructor></instructors></meeting></meetings></section>'
    s = parse_section(body)
    assert s["section_number"] == "A"
    assert s["meetings"][0]["start"] == "TBA"
    assert s["meetings"][0]["instructors"][0]["name"] == "A"


def test_section_missing_meetings_is_schema_error():
    with pytest.raises(CourseDataError):
        parse_section(b'<section id="12345"><newMeetings/></section>')
