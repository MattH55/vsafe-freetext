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
| 2026-11-10 | r01 week-1 / six-week entries | Layer-3 pilot: a 2,000-entry random sample (z-ai/glm-5.3 on NanoGPT ZDR routes and claude-opus-5-5 on the Anthropic API, 30-day retention) and a 1,000-entry layer-1 residue sample (GLM only), text only (docs/data-use.md). The assistant did not read the texts or the model replies, only the aggregate tables | Coverage, agreement and model-shift aggregates (phase1-report.md) |
| 2026-11-10 | original + updated r02-r12 (xlsx -> Parquet) | Ingest; row-level cross-check on hashes of all shared columns; column-name comparison | Row and people counts and which release has differing rows; no text read, no long-term text classified |
| 2026-11-10 | r01 week-1 / six-week entries | Layer-3 re-run of the same 2,000-entry random sample with prompt v0.1 (sharpened `persistence` description), both models | Model-shift counts per theme only (phase1-report.md); no text read |
| 2026-11-10 | r01 week-1 / six-week entries | Gold-set draw (1,000 entries, 6 strata) and blind coder sheets written to the data dir | Stratum counts and weights only; sheets not opened by the assistant |
| 2026-11-10 | openvsafe.org /registrant/<code> pages for people with a VAERS-filed call-center case | OpenVSafe's v-safe-to-VAERS match table (no bulk file exists). One page fetched with every text node masked to learn the layout; then each page parsed in memory and discarded, keeping only VAERS ID, confidence, score and runner-up score (`vsafe_ft.openvsafe`). The pages also show the person's free text, which may include long-term entries: it is never stored, logged or shown | Match-table column headers (site labels); counts by match status and confidence only |

## After registration

Registered 2026-11-11 as https://osf.io/gnfpd (embargoed; project osf.io/7wpgy). Everything below
happened after filing and follows the registered plan.

| Date | What was opened or run | Data |
|---|---|---|
| 2026-11-11 | `vsafe-ft link` on all 12 updated releases and the under-3 file, into `interim/vsafe_full.duckdb` | all survey types, including 3-, 6- and 12-month |
| 2026-11-11 | `vsafe-ft classify --long-term`: layer 1 (taxonomy v1.0) on all 7,819,251 entries | aggregates only (`docs/phase2-report.md`) |
| 2026-11-11 | `vsafe-ft gold draw --period long_term --seed 1`, sheets A and B written | texts not opened |
| 2026-11-11 | `vsafe-ft llm-label --long-term --residue --all` (layer 3, `z-ai/glm-5.3`, NanoGPT ZDR, prompt v0.1): every long-term entry layer 1 left unthemed, 649,516 entries, 386,870 unique texts | labels stored in `llm_labels`; no text read by the analyst |
| 2026-11-11 | Layer-3 long-term run paused after 1,800 texts (NanoGPT quota) | labels stored; not analysed |
| 2026-11-11 | Amendment 1 drafted (CDC MedDRA coding as the reference standard). No precision, recall or Q1–Q3 result computed on long-term entries | none |
| 2026-11-11 | Layer-1 validation vs CDC MedDRA coding computed (amendment 1) | aggregates in `docs/phase2-report.md` |
| 2026-11-11 | DeepSeek V4.1 Flash pilot on the phase-1 sample (2,000 week-1 / six-week entries) and model-shift tables vs Claude and GLM | aggregates only |
| 2026-11-11 | Amendment 2 drafted (layer-3 model change) | none |
| 2026-11-11 to 12 | Amendment 2 filed; `llm-label --long-term --residue --all --model deepseek/deepseek-v4.1-flash --workers 8`: all 386,862 residue texts labelled (NanoGPT ZDR, reasoning off) | labels stored; no text read by the analyst |
| 2026-11-12 | `validate --layer final`: final-classifier precision/recall vs CDC coding. Only fatigue_pem passes. Post-hoc counts of CDC PTs on exclusion-theme false positives (PT names and counts only) | aggregates (`docs/phase2-report.md`) |
| 2026-11-12 | Protocol owner decided: report as registered, no amendment 3; run Q1–Q3 as the nine-domain sensitivity analysis | none |
| 2026-11-12 | `vsafe-ft analyse`: final classifier, case definition on all check-ins, Q1 (all, strata, VAERS replication on 1,057,077 COVID-19 report texts, layer 1 only), Q2, Q3 (both OpenVSafe sets), Q4, attrition, Table 1 | aggregates `analysis_sens9_*`; no text read |
| 2026-11-12 | Registered model-sensitivity check: `llm-label --long-term --residue --sample 2000 --seed 1 --model claude-opus-5-5` (Anthropic API, 30-day retention, 1,687 texts) and `llm-report --long-term` | model-shift aggregates only |
| 2026-11-12 | Exploratory (unregistered, specified after seeing the registered results): text-matched Q1 null; exclusion-criterion variants; `llm-label` (DeepSeek) on cases' week-1 / six-week residue (26,889 texts); week-1 structured symptom fields read from the raw check-in Parquet for cases and a 1-in-20 sample (checkbox values only) | aggregates `analysis_expl_*`; no text read |
| 2026-11-12 | Manuscript drafted as a Claude Doc from the aggregate tables; figures drawn from aggregates | aggregates only |
| 2026-11-12 | Levi & Lu cohorts rebuilt from structured check-in answers only (`vsafe_ft.cohorts`; no age field exists, so the adult check-in file stands in for "16 or older"); overlap with the text-defined case at person level | aggregates `sub_levilu_*`; no text read |

## Published analyses read

| Date | Item | What was learned |
|---|---|---|
| 2026-11-08 | OpenVSafe search and topic counts (suicide 420, pregnancy loss 4,705, vision loss 1,861, aneurysm/dissection 1,197; 1,762-person death floor) | Topic-level counts; no dates |
| 2026-11-08 | *Cries for Help* (OpenVAERS) | Qualitative selection of entries |
| 2026-11-08 | Independent LLM screens (e.g. Vaccine Data Science) | Single-condition screens over MedDRA-selected subsets |
| 2026-11-12 | Levi R, Lu N, *Reporting on prolonged adverse health impact among V-SAFE enrollees*, Research Square, posted 25 Aug 2026, doi:10.21203/rs.3.rs-10768889/v1 (full text and appendices) | See below |

### Levi & Lu (2026): what we now know about long-term-survey data

Read on 2026-11-12, after registration (2026-11-11) and after the registered analyses had been
run. It did not change the registered plan; no amendment was filed.

This paper reports results from **3-, 6- and 12-month survey data**. We have read:

- The size of the attribution-defined cohort (185,285; 1.87% of people aged 16+), its split by
  sex, age, race, dose count and manufacturer, and the two comparison cohorts (9,529,657 and
  189,982).
- The CDC MedDRA PT and SOC rates in that cohort across all surveys and on the qualifying
  survey. Leading PTs: fatigue, headache, arthralgia, dizziness, dyspnoea, nausea, myalgia,
  diarrhoea, chest pain, rash, lymphadenopathy, palpitations, tinnitus.
- Rates of disability, care and hospitalisation on the qualifying survey (~50% reporting at
  least one of: unable to work, unable to do daily activities, hospitalised, severe event).
- Median distinct symptoms per person (8, 11 and 13 for one, two and three or more doses).
- Rechallenge rates from dose 1 to dose 2, and transitions from the qualifying survey to the
  next monthly survey.

What this does **not** reveal: whether symptom domains co-occur beyond chance (Q1); onset by
survey (Q2); VAERS filing or coding (Q3); and the size or profile of a phenotype defined from the
free text without attribution. All of these had been computed under the registered plan before
the paper was read.

The PACVS domain list was set from the PACVS, long-COVID and ME/CFS literature (protocol,
8 Nov 2026) and frozen as taxonomy v1.0 on 2026-11-10, before this paper was read. It is not
revised in light of the paper.
