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
| ingest | registrants CSV | 10,094,310 | 28 s |
| download | MedDRA 2024-11 zip (383 MB) | | 11,498 s (6 connection resets, resumed) |
| ingest | MedDRA 2024-11 (3 CSVs, 2.0 GB unzipped) | 14,134,779 | 95 s |
| download | adult check-in zip (5.76 GB) | | 48,116 s (2 timeouts, resumed) |
| ingest | adult check-in CSV (25.0 GB unzipped, Deflate64) | 144,856,043 | 13,269 s |

Adult check-ins: 9,552,127 people, 117 survey ids, every `DAYS_SINCE` value numeric. By the
derived survey-type bins: 0-7 days 82.6M, 8-42 days 44.7M, 43-135 days 7.8M, 136-270 days
6.5M, 271-450 days 3.2M, over 450 days 7 rows. Modes after day 7 are days 14, 21, 28, 35
and 42 (weekly) and 91, 182 and 365 (3, 6 and 12 months), as in the under-3 file, so the
bins in `link.survey_type_from_days` hold for adults too.

## Gate 1: join rates

Updated release 1 (`vsafe-ft link --release r01 --skip-outcomes`, 1,485 s; `vsafe-ft gate`):
**PASS**.

| Metric | Rate | Entries not linked |
|---|---|---|
| Dose linked (a vaccination on or before the check-in) | 1.000 | 0 of 395,010 |
| Survey matched (check-in found on response id + registrant) | 1.000 | 0 |
| Registrant matched (in the registrants file) | 1.000 | 0 |
| Beyond the dose window | | 0 |

- 395,010 entries (SRO 345,957, SD 41,470, HCVO 7,583) from 390,000 rows.
- Cross-check: the dose-linked days since vaccination equal the check-in's own `DAYS_SINCE`
  for 394,959 entries (99.99%); 14 differ by 1 day, 16 by 2-7 days, 21 by more than 7.
- Release 1 holds only week-1 (342,103 entries, 237,568 people) and weeks 2-6 (52,907
  entries, 48,808 people) check-ins: no long-term survey text, so the whole release is
  inside the exploratory scope.
- Doses: dose 1 351,730 entries, dose 2 43,280.
- Redaction marker present: HCVO 151, SRO 177, SD 29 entries.
- Two bugs found on the way, both fixed before this run: check-ins had been keyed on the
  survey form id, and `MM/DD/YYYY` dates were not parsed (see `docs/open-questions.md`).

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

MedDRA 2024-11 release, whole file (all survey types; codes only, no text read):

| Field file | Code rows | People | Responses |
|---|---|---|---|
| SD | 7,923,602 | 2,191,402 | 3,612,159 |
| SRO | 5,844,757 | 2,180,183 | 4,094,478 |
| HCVO | 366,420 | 263,253 | 318,968 |

- `ACTIVE`: 13,911,745 YES, 223,034 NO (1.6%). Inactive codes are dropped in `link_meddra`.
- `MEDDRA_VERSION`: 25.1 (44%), 27.0, 26.0, 26.1, 27.1 (<0.1%): the dictionary version
  changed during coding; check for PT renames across versions when building
  `taxonomy/v0/meddra_map.csv`.
- No row lacks `RESPONSE_ID` or `PT_NAME`: codes join to entries on response id + field.

Coverage of release-1 entries: _pending (needs the check-in file for the survey link)._
