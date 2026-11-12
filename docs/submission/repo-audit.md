# Repository audit before making it public

Repository: github.com/MattH55/vsafe-freetext (private). The name mhalma/vsafe-freetext given in
the brief does not resolve on GitHub; [[HUMAN: confirm the name or rename the repository]].
Audited 2026-11-12 over the whole git history (59 commits, all branches), not just the current tree.

| Check | Method | Result |
|---|---|---|
| Data files ever committed (.xlsx, .xls, .csv, .parquet, .duckdb, .zip, .jsonl) | `git log --all --name-only` | Only `taxonomy/v0/meddra_map.csv` and `taxonomy/v1.0/meddra_map.csv`, the frozen theme-to-MedDRA-term maps (dictionary terms, no participant data; an allowed exception in the brief) |
| `.env` or key files ever committed | same | None |
| API-key-shaped strings in any diff (OpenAI/Anthropic `sk-`, AWS `AKIA`, GitHub `ghp_`, `*_API_KEY=` assignments, `api_key: "…"`) | `git log --all -p` with regular expressions; matches counted, redacted | One match: the literal placeholder `sk-test` in a unit test. No real key. `gitleaks` is not installed on this machine; [[HUMAN: optionally run gitleaks before publishing]] |
| Strings shaped like registrant codes | pending: the code shape is derived from the database (length and character classes, no codes printed) and the history is then scanned for that pattern | [[pending: database in use by the analysis run]] |
| Free text from the corpus | pending: every run of 5 or more consecutive words in any committed file is checked against the corpus; only the count of matches is reported | [[pending: database in use]] |
| Participant-level outputs | tracked `.csv` files are only the two taxonomy maps; aggregates live outside the repository in `D:/vsafe-data/aggregates/` and pass `suppress.assert_safe` before being written | Pass |
| Sub-national fields | `suppress.FORBIDDEN` rejects `zip3` and `state` columns in any output; no committed file names a state or zip3 | Pass |
| Tests and lint at the audited commit | `ruff check .`, `pytest -q` | Pass (168 tests) at 9a17cc4 |

Decision for Matthew: if the two pending scans are clean, the repository can be made public at tag
`v1.0-submission` and archived on Zenodo for a DOI. Nothing in the history needs rewriting on the
evidence so far; if a pending scan finds something, the assistant will say so and will not rewrite
history without a go-ahead.
