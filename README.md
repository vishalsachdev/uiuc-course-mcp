# UIUC Course MCP

Discover Illinois courses from a local MCP client. Search offered courses within a subject, read course descriptions and restrictions, and inspect section schedules using public [Illinois Course Explorer](https://courses.illinois.edu/) data.

Independent community project; not affiliated with or endorsed by the university. Read-only, no account or API key required.

## Quick start

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). Download this repository, then from its directory:

```sh
uv sync --locked
uv run uiuc-course-mcp
```

The server waits for an MCP client over stdio; it does not present an interactive terminal or open a web port. Use the following configuration to connect a local client.

## Claude Desktop

Run `pwd` in the project directory to find its absolute path. Add this to your Claude Desktop MCP configuration, replacing `/ABSOLUTE/PATH/uiuc-course-mcp` with that path:

```json
{
  "mcpServers": {
    "uiuc-courses": {
      "command": "/ABSOLUTE/PATH/uiuc-course-mcp/.venv/bin/uiuc-course-mcp"
    }
  }
}
```

On Windows, the executable is `.venv\\Scripts\\uiuc-course-mcp.exe`. Restart your client after configuration. Compatible local MCP clients can use the same executable and stdio transport.

For Codex CLI, after installation:

```sh
codex mcp add uiuc-courses -- /ABSOLUTE/PATH/uiuc-course-mcp/.venv/bin/uiuc-course-mcp
```

This release runs on your computer. The documentation website is not an MCP endpoint. Remote web/mobile custom connectors need a separately hosted server, which is outside this release.

## Tools

All tools require explicit `year` and `term`. Terms are `spring`, `summer`, `fall`, `winter`; availability depends on the official source. Subject codes are normalized to uppercase, and course numbers are three-digit strings.

| Tool | Purpose | Example arguments |
| --- | --- | --- |
| `search_courses` | Search number/title in a single subject | `{"subject":"BADM","year":2026,"term":"fall","query":"database"}` |
| `get_course_details` | Read full description, credits, restrictions and section references | `{"subject":"BADM","course_number":"554","year":2026,"term":"fall"}` |
| `list_course_sections` | Read all meetings/instructors for selected sections | `{"subject":"BADM","course_number":"554","year":2026,"term":"fall"}` |

Search and section tools accept `limit` (1–50, default 20) and `offset` (nonnegative, default 0). Follow `next_offset` until null. Search filters before pagination. Section results preserve source order, return individual errors, and set `complete` to indicate whether the **requested page** fetched successfully; a non-null `next_offset` still means more pages remain.

Try: “Find database courses in BADM for fall 2026, then show BADM 554's restrictions and all section meetings.”

## Data and privacy

- Fixed official HTTPS origin; no arbitrary URLs, redirects, or XML-provided links followed.
- Five-minute in-memory cache, at most 128 successful responses, cleared on restart. Original retrieval time and cache age appear in results. No disk cache or search-history storage.
- Up to four active requests, 15-second HTTP timeouts, two retries for transient errors, 2 MiB response limit, and DTD/entity rejection.
- No telemetry, student credentials, enrollment records, database, registration changes, or LLM API calls.
- Full prerequisite/restriction prose is preserved where supplied, including in descriptions. Eligibility is not assessed.
- Raw status codes are not seat availability. Missing capacity, seats and waitlist counts stay null. Verify consequential schedule decisions with Course Explorer/advising.
- Source text is data, not instructions. Missing terms and upstream/schema failures produce visible errors rather than silent fallback.

Campus-wide, semantic/description search, GenEd filters, conflict detection and degree audits are outside the initial scope.

## Development

```sh
uv sync --locked
uv run pytest -q
uv run ruff check .
uv build
uv run python scripts/live_smoke.py 2026 fall
```

Offline tests use dated public XML fixtures and synthetic edge cases. Live smoke is explicit and requires internet access. See [validation](docs/validation.md) and [fixture provenance](tests/fixtures/README.md).

## GitHub Pages

The `site/` directory contains a static, accessible setup site without trackers or remote scripts. The Pages workflow deploys it from `main`. In repository Settings → Pages, select **GitHub Actions** as the source, then run the Pages workflow. The separate CI workflow verifies tests, lint and package builds.

## Inspiration and license

Inspired by [Anteater-MCP](https://github.com/KKazuhaK/Anteater-MCP) by [Kazuha Mo / KKazuhaK](https://github.com/KKazuhaK), which demonstrates useful course-discovery workflows for UC Irvine. UIUC Course MCP is an independent implementation using Illinois Course Explorer data; it does not incorporate Anteater-MCP source code.

Original code is [MIT licensed](LICENSE). Official course data remains attributed to Illinois Course Explorer; the code license does not assert ownership of that data.
