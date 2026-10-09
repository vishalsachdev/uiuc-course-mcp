# UIUC Course Discovery MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task if native execution is selected; use superpowers:subagent-driven-development if delegated execution is selected. Steps use checkbox syntax for tracking.

**Goal:** Deliver an installable, read-only local MCP for Illinois course search, course details and section schedules, with Anteater-MCP credited as inspiration.

**Architecture:** A fixed-origin asynchronous Course Explorer client retrieves bounded XML responses. Safe parsers produce structured public data; three thin MCP handlers validate inputs and return results with source, timestamp, coverage and pagination metadata.

**Tech Stack:** Python 3.11+, official `mcp` Python SDK, `httpx`, `defusedxml`, pytest, pytest-asyncio and Ruff. Use a src-layout package and a console entry point; resolve and lock compatible dependency versions during implementation.

**Spec:** `docs/superpowers/specs/2026-10-09-uiuc-course-mcp-design.md` (approved by the user).

## Global Constraints

- Independent original implementation; no Anteater source copying. MIT license and exact acknowledgment from the specification.
- Local stdio only; no hosted service, publication, accounts, credentials, writes, database or LLM calls.
- Explicit year and term. Terms: spring, summer, fall, winter; upstream availability decides whether a requested term exists.
- Fixed HTTPS origin `https://courses.illinois.edu`; construct schedule paths, never follow upstream links or redirects.
- 15-second timeout, at most four simultaneous requests, at most two retries with backoff, successful-response cache lifetime five minutes.
- Preserve source prose and all meetings. Missing data stays unknown; status A does not mean seats are available.
- Search course numbers/titles within one specified subject and term. Campus-wide and semantic/description search are deferred.
- Each result includes official source, retrieval timestamp, coverage, continuation information and cache age where applicable.
- Protocol traffic only on stdout; operational logs on stderr. No personal data or query logging.

## Review Focus

- Incomplete section responses: report each failed section and partial coverage; never present failures as an empty complete list (Task 3).
- Async/TBA and multiple meetings: retain raw time/day strings and all instructors; do not fabricate schedule times (Task 2).
- Case/spacing and path-shaped inputs: normalize valid course-code queries and reject identifiers capable of changing URL structure before HTTP (Task 1).
- Upstream HTML or schema changes: report a data error rather than treating non-XML or unexpected roots as valid empty data (Tasks 1 and 2).
- Stale cache provenance and concurrent requests: preserve original fetch time, expire at 300 seconds, and enforce concurrency through retries and streaming (Task 1).

## Files

| Path | Responsibility |
| --- | --- |
| `pyproject.toml`, `uv.lock`, `.gitignore` | Packaging, dependency lock, test configuration and excluded local state |
| `src/uiuc_course_mcp/client.py` | Validated fixed-origin requests, bounded streaming, cache and error types |
| `src/uiuc_course_mcp/parsers.py` | Safe XML parsing and subject/course/section normalization |
| `src/uiuc_course_mcp/service.py` | Search, details, section pagination and aggregation |
| `src/uiuc_course_mcp/server.py`, `__init__.py`, `__main__.py` | Three registered tools and local stdio startup |
| `tests/fixtures/*.xml`, `tests/test_client.py`, `tests/test_parsers.py`, `tests/test_service.py`, `tests/test_mcp.py` | Offline public XML fixtures and behavioral checks |
| `scripts/live_smoke.py` | Explicit read-only BADM 554 smoke check |
| `README.md`, `LICENSE`, `docs/validation.md` | Installation, boundaries, acknowledgment and dated evidence |

### Task 1: Validated public data client

**Interfaces:** `validate_identifiers(subject: str, year: int, term: str, course_number: str | None = None) -> tuple[str, int, str, str | None]`; `CourseExplorerClient.get(path: str, expected_root: str) -> FetchResult` (async); `FetchResult` contains `body: bytes`, `source_url: str`, `retrieved_at: str`, `cache_age_seconds: float`. Raise `CourseDataError` with safe reason codes.

- [ ] Write `tests/test_client.py` for accepted identifiers, rejected traversal/encoded paths, 15-second timeout configuration, no redirects, HTML/incorrect root rejection, response size cap, cache expiry/original timestamps, at most four active HTTP calls, transient retries and no retry on 404.
- [ ] Run the tests before implementation and confirm failure due to the absent package/client.
- [ ] Add packaging and implement the client with injectable httpx transport and monotonic clock. Use 2 MiB maximum XML body, 128 cached entries, case-normalized subject regex `[A-Z]{2,8}`, three-digit course numbers, years 2000–2100, and fixed path construction. Retry only timeout/transport failures, 429 and 500/502/503/504, with bounded backoff; surface exhaustion.
- [ ] Run `uv run pytest tests/test_client.py -q`; expect zero failures. Run Ruff on the task files.
- [ ] Commit `feat: add bounded Illinois Course Explorer client`.

### Task 2: Safe XML normalization

**Interfaces:** `parse_subject(body: bytes) -> dict`, `parse_course(body: bytes) -> dict`, `parse_section(body: bytes) -> dict`. Parsers validate the expected local root name using defusedxml with DTD/entities/external references forbidden. Dictionaries preserve source field text without asserting eligibility.

- [ ] Save fresh public BADM subject, BADM 554 course and AN1 section responses as fixtures, with source URLs and retrieval dates recorded. Add synthetic fixtures for multiple meetings, TBA and optional fields.
- [ ] Write `tests/test_parsers.py`: namespaced roots work; BADM 554 title/credits/description/restrictions survive; section AN1 has CRN 68315 and raw TR/12:30PM/01:50PM fields; all meetings/instructors survive; missing times and seats are null; malformed XML, DTD/entities and wrong roots raise safe errors.
- [ ] Run parser tests before implementation and confirm the missing parser failures.
- [ ] Implement the three parsers. Preserve source prerequisite text when supplied, including text embedded in descriptions, without inventing structured dependencies. Return only parsed public fields; ignore upstream href destinations.
- [ ] Run `uv run pytest tests/test_parsers.py -q`; expect zero failures. Run Ruff.
- [ ] Commit `feat: normalize public course and section XML`.

### Task 3: Search and section services

**Interfaces:** `CourseService.search_courses(subject: str, year: int, term: str, query: str = '', limit: int = 20, offset: int = 0) -> dict`; `get_course_details(subject: str, course_number: str, year: int, term: str) -> dict`; `list_course_sections(subject: str, course_number: str, year: int, term: str, limit: int = 20, offset: int = 0) -> dict` (all async). The service consumes Task 1's client and Task 2's parsers.

- [ ] Write `tests/test_service.py` for empty/no-match searches, lowercase/title/number/full-code queries, filtering before slicing, required term coverage, limits 1–50, offsets >=0, unsupported identifiers rejected before HTTP, section order, all meetings and explicit per-section failures.
- [ ] Run service tests and confirm the service is absent.
- [ ] Implement the service. Normalize whitespace/case for queries; recognize subject+number without stripping subject text from ordinary title queries. Return `results`, `total_matches`, `offset`, `next_offset`, `coverage` and provenance for search; details include section references. Section responses include `sections`, `errors`, `complete`, requested/returned counts and next offset. No silent cross-term fallback. Section fetch failures keep their CRN and safe error reason; return partial coverage.
- [ ] Run `uv run pytest tests/test_service.py -q`; expect zero failures. Run Ruff.
- [ ] Commit `feat: add subject search and section discovery`.

### Task 4: MCP and delivery

**Interfaces:** `create_server(service: CourseService) -> FastMCP` using the official SDK; `main() -> None` runs stdio with client lifecycle cleanup. Console command `uiuc-course-mcp`. Tool names and arguments match Task 3 exactly.

- [ ] Write `tests/test_mcp.py` using a real MCP client connected to the server: discover exactly three tools, check required year/term schema, call each with fixture-backed HTTP, inspect structured results and verify invalid inputs/errors. Add a subprocess stdio initialization smoke test to catch stdout contamination and entry-point problems.
- [ ] Run MCP tests before implementing handlers and confirm failure.
- [ ] Implement server lifecycle and tools with read-only annotations and descriptions marking course text as data. Add README installation and client configs using absolute executable paths; preserve the specification's acknowledgment verbatim and explicitly distinguish local setup from remote web/mobile connector support.
- [ ] Add MIT license, fixture provenance, and `scripts/live_smoke.py` that reads BADM 554 for an explicitly supplied year/term, records results and never mutates upstream state.
- [ ] Run `uv run pytest -q`, `uv run ruff check .`, and build/install a wheel in a fresh environment. Run installed entry-point stdio smoke and the live BADM 554 check. Record exact counts, versions, date and material limits in `docs/validation.md`.
- [ ] Review the entire diff against the specification and fix supported findings. Commit `feat: expose UIUC course discovery through MCP`.
- [ ] Package the source, fixtures, lockfile and docs into `uiuc-course-mcp-source.zip`, excluding virtual environments, caches, secrets and git internals. Save the source archive and validation report. Do not publish or deploy.

## Execution recommendation

Native execution is recommended: four tightly connected tasks share small client/parser/service interfaces and operate only on public read-only data. The implementation receives a whole-project review after tests pass. Delegated execution remains an option if the user prefers separate task reviews.

Plan self-review: every approved tool, source boundary, operational limit, provenance requirement and delivery requirement maps to a task above. This plan adds only reversible implementation defaults for bounds and packaging; it does not expand the feature scope.
