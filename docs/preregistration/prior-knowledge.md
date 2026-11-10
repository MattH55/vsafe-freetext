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
