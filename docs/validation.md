# Validation — 2026-10-09 UTC

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
