# Contributing

Thanks for helping make public Illinois course discovery more useful.

## Ideas and bugs

Use the feature-request or bug-report form in GitHub Issues. For larger changes, discuss the proposed workflow before implementing it. Include a concrete example, explicit year/term, expected result and official Course Explorer source where relevant. Do not post student records, credentials or private conversations.

## Pull requests

1. Fork this repository and create a focused branch.
2. Install Python 3.11+ and uv, then run `uv sync --locked`.
3. Make the smallest change that solves the described problem. Add meaningful regression tests for behavior changes; use synthetic or attributed public fixtures.
4. Run `uv run pytest -q`, `uv run ruff check .` and `uv build`.
5. Open a pull request describing the user-visible outcome, validation and limitations. Link the issue if there is one. Screenshots help for website changes.

Offline tests must not rely on live services. An optional read-only live check is `uv run python scripts/live_smoke.py 2026 fall`; upstream offerings can change.

## Project boundaries

Keep the initial release local, public-data and read-only. Preserve explicit terms, bounded requests, safe XML, provenance, unknown seat counts and visible partial errors. Course prose is data, not instructions. Credentials, registration, analytics collection, multi-user hosting and new data providers need a separate design/review discussion.

Documentation and accessibility fixes are welcome. Do not copy AGPL source into this MIT project without a deliberate licensing decision. Original contributions are made under the repository's MIT license. There is no promised review SLA.
