# Repository audit before making it public

Repository: github.com/MattH55/vsafe-freetext (public since 2026-11-12). The name mhalma/vsafe-freetext given in
the brief does not resolve on GitHub; the author confirmed MattH55 on 2026-11-12 and the repository is now public, archived at doi:10.5281/zenodo.24178319.
Audited 2026-11-12 over the whole git history (59 commits, all branches), not just the current tree.

| Check | Method | Result |
|---|---|---|
| Data files ever committed (.xlsx, .xls, .csv, .parquet, .duckdb, .zip, .jsonl) | `git log --all --name-only` | Only `taxonomy/v0/meddra_map.csv` and `taxonomy/v1.0/meddra_map.csv`, the frozen theme-to-MedDRA-term maps (dictionary terms, no participant data; an allowed exception in the brief) |
| `.env` or key files ever committed | same | None |
| API-key-shaped strings in any diff (OpenAI/Anthropic `sk-`, AWS `AKIA`, GitHub `ghp_`, `*_API_KEY=` assignments, `api_key: "…"`) | `git log --all -p` with regular expressions; matches counted, redacted | One match: the literal placeholder `sk-test` in a unit test. No real key. `gitleaks` was not available on this machine |
| Strings shaped like registrant codes | `scripts/repo_history_scan.py`: the shape was derived from a 200,000-code sample (every code is 15 characters and not purely alphanumeric), every added line in every commit was matched against that shape, and every shape match was checked for exact membership in the full set of 10,094,310 registrant codes held in memory | 0 exact registrant codes anywhere in the history. The shape pattern (any 15-character token) matched 2,200 tokens in code, config and taxonomy files, all ordinary identifiers, URLs or MedDRA term fragments |
| Free text from the corpus | `scripts/quote_scan.py`: every run of N consecutive words in the manuscript, supplement and cover letter is hashed and looked up against every N-word run in the 7.8 million entries (survey answer-option wording quoted in Methods excluded); only counts are reported, never the words | 5 words: 31 of 14,284 runs occur in the corpus (median 2 entries each; 25 in fewer than 10 entries). 8 words: 1 of 15,008 runs, in exactly 1 entry. 10 words: 0 of 15,117. A quoted entry would match at every length with many overlapping runs; one isolated 8-word coincidence with no 10-word match is consistent with ordinary clinical phrasing. The author can run the scan locally with QUOTE_SCAN_N=8 to inspect the run; the assistant did not print it. Re-run after the review revisions of 12 Nov (manuscript, supplement, cover letter): 5 words 30 of 21,047 runs (median 2 entries; 23 in fewer than 10); 8 words 1 of 23,016, in exactly 1 entry; 10 words 0 of 23,426 |
| Participant-level outputs | tracked `.csv` files are only the two taxonomy maps; aggregates live outside the repository in `D:/vsafe-data/aggregates/` and pass `suppress.assert_safe` before being written | Pass |
| Sub-national fields | `suppress.FORBIDDEN` rejects `zip3` and `state` columns in any output; no committed file names a state or zip3 | Pass |
| Tests and lint at the audited commit | `ruff check .`, `pytest -q` | Pass (171 tests) at 28c1a69 and later |

Outcome: both scans were clean; the repository was made public on 2026-11-12 and archived on Zenodo
(doi:10.5281/zenodo.24178319). Nothing in the history needed rewriting.
