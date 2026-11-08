# Phase 1 report: one-release exploratory pass

Aggregates only. Every table below passed `suppress.suppress` + `suppress.assert_safe`
(cells with fewer than 10 people are blank). No entry is quoted.

## Environment and timings

| Item | Value |
|---|---|
| Machine | Windows 11 workstation; data in `VSAFE_DATA_DIR` outside OneDrive |
| Python / duckdb / polars | 3.13 / 2.0.0 / see `pip freeze` |
| Download link | ~50-170 KB/s observed on 2026-11-08 (8.52 GB in total) |

| Step | File(s) | Rows | Duration |
|---|---|---|---|
| download | updated r01 (31.8 MB) | | 400 s |
| download | original r01 (16.8 MB) | | 99 s |
| download | vaccinations zip (157.8 MB) | | 1,444 s (incl. a DNS outage, resumed) |
| ingest | updated r01.xlsx | 390,000 | 63 s |
| ingest | updated r12_under3.xlsx | 16,418 | 3 s |
| ingest | original r01.xlsx | 390,000 | 27 s |
| ingest | original r12_under3.xlsx | 16,418 | 2 s |
| ingest | vaccinations CSV (909 MB unzipped) | 20,140,862 | 49 s |

## Gate 1: join rates

_Pending: needs vaccinations, registrants and check-ins ingested._

## Layer-1 lexicon coverage (week-1 and six-week entries only)

_Pending._

## Candidate themes from n-grams (>= 10 people)

_Pending._

## QA: original vs updated (task 3.7)

Rows compared as a multiset over the shared columns (REGISTRANT_CODE and the three text
fields).

| Release | Rows (original) | Rows (updated) | People | Rows only in original | Rows only in updated |
|---|---|---|---|---|---|
| 1 | 390,000 | 390,000 | 272,544 | 0 | 0 |
| under-3 | 16,418 | 16,418 | 8,181 | 0 | 0 |

Columns: updated = original + `SURVEY_STATIC_ID`, `RESPONSE_ID`, `STARTED_ON`; no other
differences. Releases 2-12 to follow as they download.

## QA: duplicates, MedDRA coverage

_Pending._
