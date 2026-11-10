# Prior-knowledge log (phase 1)

Everything opened before the OSF registration, kept so the registration can disclose it.
Rule: no 3-, 6- or 12-month free text is read or classified before registration; only
week-1 and six-week entries of one updated release are used for the exploratory pass.

| Date (UTC) | File | Fields / what was done | What was seen (aggregate only) |
|---|---|---|---|
| 2026-11-08 | (none) | Source URLs checked with HTTP HEAD | File names and sizes only (see `MANIFEST.tsv`) |
| 2026-11-08 | updated r01.xlsx, r12_under3.xlsx; original r01.xlsx, r12_under3.xlsx | Header row only (`vsafe-ft inspect`) | Column names; no data rows |
| 2026-11-08 | updated + original r01, r12_under3 (Parquet) | Row-level cross-check, hashes of all columns | Row and people counts only (phase1-report.md) |
| 2026-11-08 | consolidated_registrants, consolidated_vaccinations, health check-in (u3 and adult) | Header rows; under-3 `DAYS_SINCE` value distribution | Column names; counts by day since vaccination (no text) |
| 2026-11-09 | vsafe-MedDRA-110124.zip (covid_meddra_sd/sro/hcvo.csv) | Header row only | Column names; no data rows |
| 2026-11-09 | consolidated_health_checkin (adult, Parquet) | `DAYS_SINCE` value counts; distinct people and survey ids | Counts by day since vaccination only (phase1-report.md); no text |
| 2026-11-09 | check-ins (adult + u3), updated r01 (Parquet) | Key checks: counts of rows, non-null and distinct `RESPONSE_ID`, distinct `SURVEY_STATIC_ID`; per form id the count and min/median/max `DAYS_SINCE` | Counts and day summaries only; no text |
| 2026-11-09 | linked r01 entries (DuckDB) | Join rates; counts by field, survey type, dose, redaction flag; dose-day vs `DAYS_SINCE` agreement | Counts only; no text. r01 has no long-term check-ins |
| 2026-11-09 | r01 entries (week-1 and weeks 2-6 only) | Layer-1 classification; theme, flag, length and MedDRA-coverage counts; top 300 candidate n-grams (>= 10 people each) before and after taxonomy additions | Suppressed aggregate tables only; no entry read |
| 2026-11-09 | MedDRA codes on r01 in-scope entries | Theme -> PT map (dictionary terms, PTs >= 10 people); theme x PT co-occurrence counts (top 5 per theme) | Dictionary terms and counts only; no long-term codes used |
| 2026-11-10 | call-center 23-00926 (CDC) and 23-00925 (GDIT) CSVs | Header rows. Incident: the first header attempt on 23-00925 failed on a non-UTF-8 byte, and DuckDB's error message quoted one data row (a registrant code and a standard call-disposition picklist value; no participant free text, no survey text). The row was not copied anywhere; `header_row` now reads only the first line and CSV errors are truncated before printing | Column names; one disposition row as described |
| 2026-11-10 | call-center Parquet (both files) | Per column: distinct and non-null counts, MM/DD/YYYY parse share; value frequencies of the picklist columns (final outcome, call outcomes, report outcomes, health impact, healthcare visits), values with < 10 people suppressed; overlap of case keys between the two files | Picklist labels and counts only; no free text, no zip code |
| 2026-11-10 | r01 week-1 / six-week entries | Layer-3 pilot: a 2,000-entry random sample (two LLMs) and a 1,000-entry sample of layer-1 residue sent as text only to NanoGPT on zero-data-retention routes (docs/data-use.md). The assistant did not read the texts or the model replies, only the aggregate tables | Coverage, agreement and model-shift aggregates (phase1-report.md) |
