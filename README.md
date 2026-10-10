# UIUC Course MCP

[![CI](https://github.com/vishalsachdev/uiuc-course-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/vishalsachdev/uiuc-course-mcp/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Illinois course search and section schedules for your local AI assistant.**

From [Vishal Sachdev](https://github.com/vishalsachdev), creator of [Canvas MCP](https://github.com/vishalsachdev/canvas-mcp).

[Setup website](https://vishalsachdev.github.io/uiuc-course-mcp/) · [Request a feature](https://github.com/vishalsachdev/uiuc-course-mcp/issues/new?template=feature_request.yml) · [Report a bug](https://github.com/vishalsachdev/uiuc-course-mcp/issues/new?template=bug_report.yml) · [Contribute](CONTRIBUTING.md)

Discover Illinois courses from a local MCP client. Search offered courses within a subject, read course descriptions and restrictions, and inspect section schedules using public [Illinois Course Explorer](https://courses.illinois.edu/) data.

Independent community project; not affiliated with or endorsed by the university. Read-only, no account or API key required.

## Try these questions

- “Find BADM courses with database in the title for fall 2026.”
- “What does BADM 554 cover, and what restrictions does the source list?”
- “Show every BADM 554 section meeting for fall 2026, including instructors.”

A verified BADM 554 example returns **Enterprise Database Management**, **4 hours.**, and source-provided section references. Results include official URLs and retrieval timestamps. This is a dated example, not a promise about future offerings.

## Run without cloning

With Python 3.11+, Git and uv installed, configure your local MCP client to run:

```sh
uvx --from git+https://github.com/vishalsachdev/uiuc-course-mcp@9778a866e6023bddfd41d6c8cf74e907f08ec106 uiuc-course-mcp
```

This pins the reviewed source revision. uv downloads the code and installs dependencies in an isolated cached environment. It starts a stdio server that waits for its client; it is not an interactive course-search CLI. Dependencies are resolved from the project's constraints; use the cloned, locked setup below if you need exact dependency reproducibility.

Claude Desktop configuration:

```json
{
  "mcpServers": {
    "uiuc-courses": {
      "command": "/ABSOLUTE/PATH/TO/uvx",
      "args": ["--from", "git+https://github.com/vishalsachdev/uiuc-course-mcp@9778a866e6023bddfd41d6c8cf74e907f08ec106", "uiuc-course-mcp"]
    }
  }
}
```

Find the executable with `which uvx` on macOS/Linux or `where uvx` on Windows. Use its absolute path; GUI clients may not inherit your terminal PATH. Merge the `uiuc-courses` entry into your existing `mcpServers` object rather than replacing other connectors.

## Quick start

Requires Python 3.11+, Git and [uv](https://docs.astral.sh/uv/). Clone this repository, then from its directory:

```sh
git clone https://github.com/vishalsachdev/uiuc-course-mcp.git
cd uiuc-course-mcp
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

## Verify your connection

After restarting your client, confirm it lists `search_courses`, `get_course_details` and `list_course_sections`. Ask: “Find BADM courses with database in the title for fall 2026.” On October 10, 2026, this returned BADM 352 and BADM 554; offerings can change. Then ask for BADM 554's description and section meetings, with source links.

If the connector does not appear, check the absolute executable path, JSON syntax and your client's MCP logs. Run `uv --version` and `git --version` in a terminal; first-time installation needs network access to GitHub and the Python package index. Course lookups need access to `courses.illinois.edu`. A terminal server that waits silently is normal; stop it with Ctrl-C and let the client start its own process. No API key is required.

For a repeatable protocol check from a checkout, run `uv run python scripts/mcp_smoke.py -- .venv/bin/uiuc-course-mcp`. Add `--live` before `--` to opt into the dated public course check. On Windows substitute `.venv\Scripts\uiuc-course-mcp.exe`. This checks the installed server with the official Python MCP client; it does not certify a particular desktop app. See [validation](docs/validation.md) for tested environments and remaining native checks.

## Update or roll back

**Git-source configuration:** the full commit after `@` deliberately stays fixed. Restarting, refreshing uv's cache or using `--upgrade` does **not** advance that source pin. When adopting a reviewed newer revision, save your old configuration, replace the commit in the `--from` argument with the new full commit from GitHub, and restart the client. Repeat the connection check above. To roll back the source, restore the previous commit and restart. Dependencies remain resolved within project constraints; use the locked checkout for exact dependency versions.

**Cloned checkout:** stop the client, save `git rev-parse HEAD`, and ensure `git status --short` is empty before updating:

```sh
git switch main
git pull --ff-only
uv sync --locked
```

Restart and repeat the connection check. If you have local edits, preserve them before updating; do not discard them to make these commands succeed. To roll back a clean checkout, stop the client, run `git switch --detach <saved-commit>` followed by `uv sync --locked`, and restart. A ZIP download has no Git update path: download the newer source, install it, and update the client's executable path if the folder moved. Keep the old folder until the new connection works.

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

## Companion to Canvas MCP

Use UIUC Course MCP to discover public Illinois offerings and section schedules. Use [Canvas MCP](https://github.com/vishalsachdev/canvas-mcp) for supported workflows inside your Canvas courses, such as assignments, deadlines and course content. Canvas MCP requires its own credentials and permissions. These are separate servers; no automatic linking or data exchange is built in.

## Contribute

Feature requests, bug reports, documentation fixes and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for local checks and scope. Describe your course-discovery workflow so contributors can prioritize useful improvements. There is no promise of a response time or feature delivery date.

## Inspiration and license

Inspired by [Anteater-MCP](https://github.com/KKazuhaK/Anteater-MCP) by [Kazuha Mo / KKazuhaK](https://github.com/KKazuhaK), which demonstrates useful course-discovery workflows for UC Irvine. UIUC Course MCP is an independent implementation using Illinois Course Explorer data; it does not incorporate Anteater-MCP source code.

Original code is [MIT licensed](LICENSE). Official course data remains attributed to Illinois Course Explorer; the code license does not assert ownership of that data.
