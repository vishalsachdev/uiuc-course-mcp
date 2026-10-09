# UIUC Course Discovery MCP Design

Build an independent, read-only MCP server that lets students and instructors discover University of Illinois Urbana-Champaign courses and inspect term-specific sections. The initial release uses public Illinois Course Explorer data, requires no student credentials, and acknowledges Anteater-MCP as inspiration. This is a design for review, not an implementation or deployment claim.

## Agreed direction

The user approved a separate UIUC project rather than a fork of Anteater-MCP, with course search, course details and listed prerequisites, and section schedules. They explicitly requested acknowledgment of Anteater-MCP. Implementation will be original; no Anteater code will be copied. Proposed project name: `uiuc-course-mcp`. Proposed license for original code: MIT. Neither university endorsement nor official advising status is implied.

## Approach

Use Python 3.11+ with the official MCP Python SDK and a small asynchronous HTTP client. Start with local stdio transport for Claude Desktop, Claude Code, Codex and other compatible clients. Keep three boundaries: a fixed-origin Illinois data client, XML-to-structured-data parsers, and thin MCP tool handlers. No database, accounts, credential store, LLM API, hosted service, or frontend is needed for this release.

Alternatives considered: forking Anteater introduces UCI-specific rules and AGPL obligations; wrapping a community UIUC API adds a service dependency. Direct official data access is the smallest independently maintained option. Public HTTP hosting can be considered separately after the local release works.

## Verified source behavior

Read-only requests on October 9, 2026 returned XML successfully for:

- `https://courses.illinois.edu/cisapp/explorer/schedule/2026/fall/BADM.xml`: subject metadata and offered course numbers/titles.
- `https://courses.illinois.edu/cisapp/explorer/schedule/2026/fall/BADM/554.xml`: BADM 554 Enterprise Database Management, description, credit hours, course restrictions and three section references.
- `https://courses.illinois.edu/cisapp/explorer/schedule/2026/fall/BADM/554/68315.xml`: section AN1, CRN 68315, dates, Tuesday/Thursday meetings at 12:30PM–01:50PM, building/room and instructor Sachdev, V.

The sampled section XML contains status codes but no numeric capacity, seats remaining or waitlist count. Do not interpret status code A as available seats. Missing fields are explicitly unknown. Catalog URL guesses returned errors; this release uses verified schedule endpoints rather than depending on an unverified catalog route.

Official access guidance: https://answers.uillinois.edu/illinois/page.php?id=88215. The public API requires no authentication. The API documentation URL currently returns the Course Explorer homepage when fetched, so actual XML fixtures are essential for validation.

## Tool contracts

All tools require an explicit year and term; never silently substitute another term. Supported term strings are spring, summer, fall and winter, with upstream availability determining validity. Validate subject codes, course numbers, year and limits before making requests. Do not accept arbitrary URLs or follow XML-provided links; construct paths on the fixed official origin.

| Tool | Inputs and behavior |
| --- | --- |
| `search_courses` | Required subject, year and term; optional query and result limit. Search course number/title within that subject's offered courses. Match ignoring case; normalize course-code searches such as BADM 554. Results explicitly state subject and term coverage. Description/semantic search and campus-wide crawling are deferred. |
| `get_course_details` | Required subject, course number, year and term. Return title, full description, credit text, source-provided prerequisite/restriction text and section references. Preserve requirements as prose; do not infer eligibility or build a prerequisite graph. |
| `list_course_sections` | Required subject, course number, year and term; bounded limit and offset. Fetch selected sections with limited concurrency. Return CRN, section number, source status, notes/restrictions, dates, all meetings/instructors and source links. Represent absent/TBA times explicitly; never invent seat availability. |

Each result includes its official source URL, retrieval timestamp, coverage and any continuation information. Search filtering happens before result pagination. Section pagination follows the upstream reference order. Partial section failures return a visible per-section error, not an apparently complete list. Tool descriptions identify returned course prose as data, not agent instructions.

## Operational behavior

Use HTTPS with a fixed allowed origin, redirect refusal, a 15-second request timeout, at most four concurrent requests, bounded response bodies and safe XML parsing that rejects DTD/entity expansion. Validate the expected XML root and distinguish HTML/error responses from empty data. Retry transient upstream failures at most twice with backoff; do not retry invalid input or not-found responses.

Use a bounded in-memory cache for successful public responses only, with a five-minute lifetime. Preserve the original retrieval timestamp on cache hits and expose cache age. Never convert network errors into empty search results. No persistent personal data or request query logs. Keep operational logs on stderr so stdout remains valid MCP protocol traffic.

## Validation and delivery

Create fixtures from official subject, course and section XML. Tests cover namespace handling, all meetings, missing/TBA fields, restrictions, invalid/path-shaped identifiers, missing course/term, HTML in place of XML, oversized/malformed/entity XML, timeout/rate-limit handling, pagination and partial failures. Use a real in-process MCP client to discover and call the three tools. Run a separate read-only live smoke check using BADM 554, with dated results; offline tests must not depend on live data.

Deliver an installable Python project, README with local client setup and examples, MIT license, tests and dated validation report. Keep package publication and hosted deployment separate from local implementation. Save a complete source archive if an external git repository is not yet established.

README acknowledgment wording:

> Inspired by [Anteater-MCP](https://github.com/KKazuhaK/Anteater-MCP) by [Kazuha Mo / KKazuhaK](https://github.com/KKazuhaK), which demonstrates useful course-discovery workflows for UC Irvine. UIUC Course MCP is an independent implementation using Illinois Course Explorer data; it does not incorporate Anteater-MCP source code.

## Later capabilities

Consider description search with a bounded local index, campus-wide discovery, schedule conflict checks, GenEd filters and independently sourced historical grades after the initial release. Registration actions, personalized degree audits, claims of eligibility, student credentials, enrollment monitoring and multi-user hosting are outside this design.
