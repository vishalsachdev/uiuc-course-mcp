"""Preserve source prose as public data, never as instructions."""

from .client import CourseDataError, xml_root


def parsed_root(body, expected, container):
    root = xml_root(body, expected)
    for node in root.iter():
        node.tag = node.tag.rsplit("}", 1)[-1]
    if root.find(container) is None:
        raise CourseDataError("invalid_schema")
    return root


def text(node, path):
    child = node.find(path)
    if child is None:
        return None
    return "".join(child.itertext()).strip() or None


def required(value):
    if not value:
        raise CourseDataError("invalid_schema")
    return value


def parse_subject(body: bytes) -> dict:
    root = parsed_root(body, "subject", "courses")
    return {
        "subject": root.get("id"),
        "courses": [
            {
                "course_number": required(c.get("id")),
                "title": required("".join(c.itertext()).strip()),
            }
            for c in root.findall("courses/course")
        ],
    }


def parse_course(body: bytes) -> dict:
    root = parsed_root(body, "course", "sections")
    return {
        "course_code": root.get("id"),
        "title": required(text(root, "label")),
        "description": text(root, "description"),
        "credits": text(root, "creditHours"),
        "prerequisites": text(root, "prerequisites"),
        "restrictions": text(root, "courseSectionInformation"),
        "section_references": [
            {"crn": required(s.get("id")), "section_number": "".join(s.itertext()).strip() or None}
            for s in root.findall("sections/section")
        ],
    }


def parse_section(body: bytes) -> dict:
    root = parsed_root(body, "section", "meetings")
    meetings = []
    for m in root.findall("meetings/meeting"):
        meetings.append(
            {
                "days": text(m, "daysOfTheWeek"),
                "start": text(m, "start"),
                "end": text(m, "end"),
                "room": text(m, "roomNumber"),
                "building": text(m, "buildingName"),
                "type": text(m, "type"),
                "type_code": m.find("type").get("code") if m.find("type") is not None else None,
                "instructors": [
                    {
                        "name": "".join(i.itertext()).strip() or None,
                        "first_name": i.get("firstName"),
                        "last_name": i.get("lastName"),
                    }
                    for i in m.findall("instructors/instructor")
                ],
            }
        )
    return {
        "crn": required(root.get("id")),
        "section_number": text(root, "sectionNumber"),
        "status_code": text(root, "statusCode"),
        "section_status_code": text(root, "sectionStatusCode"),
        "notes": text(root, "sectionNotes"),
        "part_of_term": text(root, "partOfTerm"),
        "start_date": text(root, "startDate"),
        "end_date": text(root, "endDate"),
        "meetings": meetings,
        "capacity": None,
        "seats_remaining": None,
        "waitlist_count": None,
    }
