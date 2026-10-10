# Validation

## Independent first-user check — 2026-10-10 UTC

Environment: Linux, Python 3.12.14, official Python MCP SDK client over stdio.
Reviewed repository head: `df82f97990e371537ff13d7ee2982997c7668cc2`.
Documented source pin: `9778a866e6023bddfd41d6c8cf74e907f08ec106`.

| Check | Observed result |
| --- | --- |
| Exact documented `uvx --from git+https://github.com/vishalsachdev/uiuc-course-mcp@9778a866e6023bddfd41d6c8cf74e907f08ec106 uiuc-course-mcp` command | Installed from GitHub with an empty dedicated uv cache; initialized and discovered exactly the three documented tools. Server launched outside the source checkout. |
| Live calls through that installed server | `search_courses` returned BADM 352 and 554 for `database`, fall 2026; `get_course_details` returned Enterprise Database Management; `list_course_sections` returned three sections, no errors, `next_offset: null`. All calls included official source URLs and retrieval times. |
| Source update and rollback | Changed the source pin to the reviewed head above, reinitialized and repeated all three live calls successfully; restored the documented pin and repeated successfully. These revisions have identical server source and dependency files, so this validates the installation/configuration mechanics, not a behavioral upgrade. |
| Locked checkout path | Fresh public Git clone and `uv sync --locked` succeeded. Switching from the documented revision to `main`, `git pull --ff-only`, syncing, and restoring the saved revision all succeeded; the installed entry point initialized and discovered three tools after rollback. |
| Built distribution | Wheel and sdist built; wheel installed in a separate empty virtual environment; installed console entry point initialized and discovered three tools. |
| Existing regression suite | 47 passed; Ruff passed. No runtime compatibility defect reproduced. |
| Public Pages deployment | HTTP 200 and HTML byte-for-byte equal to reviewed `site/index.html` on October 10. All local fragment targets resolved. All 14 distinct external links returned HTTP 200, including feature/bug forms, contribution guide, PR comparison, and Canvas MCP. |

Installation checks require network access; live source checks are dated samples rather than a campus-wide guarantee. The test harness explicitly inherits its environment so network proxy settings are preserved. A first attempt to test the newer pin without those settings failed at GitHub DNS resolution before server startup; passing the environment resolved it. This is a harness/network limitation, not evidence of a server defect.

Onboarding improvements from this review: explicit clone commands; configuration-merge guidance; tool discovery and example acceptance checks; setup troubleshooting; source-pin and locked-checkout update/rollback instructions on the README and website. `scripts/mcp_smoke.py` checks any installed stdio command; `--live` explicitly opts into public Course Explorer calls. CI now starts the exact documented Git-source command in a fresh cache and checks MCP initialization, tool names, required term arguments and read-only annotations, rather than only installing the package. Live upstream calls remain outside ordinary CI.

### Native checks still unverified

- Claude Desktop on the maintainer's Mac: edit/merge configuration, fully restart, see three tools, and ask the dated BADM search/details/sections questions. Check app logs and absolute executable paths if unavailable.
- Codex CLI registration and an assistant-driven tool call: CLI is unavailable in this review environment.
- Native Windows executable paths and GUI environment inheritance: documented but not tested here.
- Visual browser and screen-reader accessibility: HTTP, source links and fragment checks passed; no rendered-browser or assistive-technology audit was completed in this environment.

This supports a tested local stdio release, with explicit desktop coverage limits. No native app installation, public package-index publication, promotional posting or university endorsement is claimed.

## Initial build checks — 2026-10-09 UTC

Initial local release 0.1.0, Python 3.12.14. Checks performed in the build workspace; client installation on the user's own machine has not been performed.

- Offline suite: 47 tests passed, including fixed-origin input checks, unsafe XML, body limits, original cache timestamps/expiry, concurrency/retries, source normalization, pagination, partial sections and actual MCP discovery/calls.
- Ruff: all checks passed.
- Wheel and source distribution built successfully. Wheel installed into a separate clean environment; installed console entry point initialized over stdio and discovered exactly three tools.
- Explicit live check: BADM 554, fall 2026, returned Enterprise Database Management and three sections with zero section errors. Live result retrieval timestamps are available in the smoke output. This is a sample, not a comprehensive campus/term validation.
- Dependencies locked: mcp 1.30.0 (official Python SDK), httpx 0.28.1 with SOCKS support, defusedxml 0.7.1. Test tools: pytest 9.1.1, Ruff 0.16.10.
- Static Pages site has no external scripts, tracking, credential entry or MCP endpoint. Repository creation, Pages settings and public deployment depend on GitHub access; do not interpret the prepared deployment workflow as evidence of a live website.

HTTP timeouts apply per network phase, not as a single wall-clock deadline across retries. Cache is process-local memory, successful responses only, max 128 entries, TTL 300 seconds. Section `complete` covers the requested page; inspect `next_offset` for further pages. Missing seats and waitlists remain null. No telemetry/events are implemented.

Initial tests are not an independent security audit. Read-only public-data scope avoids credential custody, student records, registration and account infrastructure.

Final independent code review identified absent-container schema errors and default-namespaced field loss. Six reproducing parser tests failed before fixes and then passed; service checks distinguish schema errors from explicitly empty section collections. The year-2100 boundary was aligned after a failing regression test. Final offline suite: 47 passed. Final Ruff and live BADM 554 checks passed.
