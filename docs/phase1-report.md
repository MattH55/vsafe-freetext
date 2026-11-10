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

Release 1, all 395,010 entries in scope (no long-term check-ins in this release).
`vsafe-ft classify`: 94 s. Share of entries matched by at least one theme:

| Field | Entries | Taxonomy as drafted | After n-gram additions (`a9810ec`) |
|---|---|---|---|
| SD | 41,470 | 52.0% | 85.0% |
| SRO | 345,957 | 24.6% | 68.3% |
| HCVO | 7,583 | 8.6% | 13.5% |
| All | 395,010 | 27.2% | 69.0% |

HCVO stays low: the field mostly records the kind of care visit, not symptoms.

Entries per theme after the additions (all fields; every cell >= 10 people):

| Theme | Domain | Entries |
|---|---|---|
| upper_respiratory | acute | 67,311 |
| pain | pacvs | 40,572 |
| injection_site | acute | 39,851 |
| dysautonomia | pacvs | 32,067 |
| lymphadenopathy | acute | 28,093 |
| fever_chills | acute | 22,366 |
| fatigue_pem | pacvs | 17,278 |
| sensory_neuropathic | pacvs | 16,156 |
| skin | acute | 16,020 |
| gastrointestinal | pacvs | 12,207 |
| unrelated_cause | exclusion | 10,060 |
| taste_smell | acute | 7,885 |
| cardiorespiratory | acute | 5,751 |
| sleep | pacvs | 3,586 |
| cognitive | pacvs | 2,715 |
| persistence | lay | 2,453 |
| menstrual | pacvs | 1,430 |
| acute_diagnosis | exclusion | 1,399 |
| pre_existing_worsened | lay | 798 |
| care_sought | lay | 592 |
| missed_work_school | lay | 143 |

Attribution flags (drafted taxonomy): third-party wording in 464 SRO and 103 SD entries;
pre-vaccine wording in 243 SRO and 14 SD entries; HCVO cells suppressed (< 10 people).

Text length (characters): SRO 41% under 20, 36% 20-49, 22% 50-199, 1% 200+; SD 24% under
20, 36% 20-49, 35% 50-199, 4% 200+; HCVO 34% under 20, 43% 20-49, 23% 50-199, 1% 200+.

Caveat for the protocol: at week 1, the PACVS-domain themes mostly capture the acute
reaction (dizziness, headache, muscle aches, tingling at the arm). Domain hits at week 1
are not evidence of PACVS; the case definition uses long-term surveys only.

## Candidate themes from n-grams (>= 10 people)

`vsafe-ft explore` (178 s): the 300 most frequent 1-3-grams in entries no theme matched,
stop words removed, each used by >= 10 people. Clusters among them, with the people count
of the largest n-gram in each (drafted taxonomy):

| Cluster | Largest n-gram people | Action |
|---|---|---|
| injection site: soreness, swelling, redness, itch, bruising | 20,129 | new theme `injection_site` |
| upper respiratory: sore throat, runny/stuffy nose, congestion, cough, sneezing | 17,519 | new theme `upper_respiratory` |
| lymph nodes: swollen nodes, armpit, axilla | 11,563 | new theme `lymphadenopathy` |
| fever, chills, hot flashes, flushing, sweating | 4,635 | new theme `fever_chills` |
| rash, hives, itching | 4,393 | new theme `skin` |
| taste/smell: metallic taste, loss of taste or smell, dry mouth | 2,132 | new theme `taste_smell` |
| shortness of breath, chest tightness or pressure | 2,075 | new theme `cardiorespiratory` |
| "light headed" (two words), heart rate | 2,365 | added to `dysautonomia` |
| back, neck, jaw pain; aches | 2,422 | added to `pain` |
| appetite | 1,670 | added to `gastrointestinal` |
| positive test, seasonal allergies | 1,689 | added to `unrelated_cause` |

After the additions the most frequent leftovers are non-specific words (pain, arm, sore,
mild, none, vaccine, shot, today). Open for the protocol owner: whether `taste_smell` or
`cardiorespiratory` belong among the PACVS domains (both are long-COVID features), and
whether `upper_respiratory` should be a criterion-3 exclusion (a likely cold).

## MedDRA map and theme precision

`vsafe-ft meddra-map` writes `taxonomy/v0/meddra_map.csv`: theme -> MedDRA PT, where the
lexicon matches the PT name or an LLT CDC coded under it, using only codes on in-scope
(week-1 / six-week) entries and only PTs coded for >= 10 people. Current draft: 248 rows,
229 PTs. Inputs and outputs are MedDRA dictionary terms, not participant text.

Precision check (`phase1_theme_pt_cooccurrence`): the PTs CDC coded on the same entries as
each theme. The top PT is the expected one for most themes, e.g. `fatigue_pem` -> Fatigue
(90% of its entries), `dysautonomia` -> Dizziness (78%), `lymphadenopathy` ->
Lymphadenopathy (66%), `cardiorespiratory` -> Dyspnoea (70%), `fever_chills` -> Pyrexia /
Chills, `taste_smell` -> Dysgeusia / Ageusia / Anosmia, `unrelated_cause` -> SARS-CoV-2 test
positive / COVID-19 (60%), `sleep` -> Insomnia / Night sweats.

Issues found and their status:

| Theme | Signal | Status |
|---|---|---|
| sensory_neuropathic | bare "burning" mapped to dysuria, dyspepsia, throat/eye irritation | fixed: neuropathic phrasing only (35 -> 24 PTs) |
| menstrual | top co-coded PT is "Unevaluable event" (21% of its entries) | open: likely "period" as a time span; needs gold-set review |
| cognitive | 84% co-coded "Feeling abnormal", only 8% "Confusional state" | open: vague wording; check in gold set |
| acute_diagnosis | "Pre-existing disease" on 11% of its entries | open: history mentions, not new diagnoses |
| fatigue_pem, pain | headache / fatigue co-coded | expected: entries list several symptoms |

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

Coverage of release-1 entries: **100%** in every field (SD 41,470, SRO 345,957, HCVO
7,583 entries all have at least one active code from the 2024-11 release).

Duplicates in release 1: 395,010 entries before and after dedupe; within-release copies,
cross-release keys and under-3/main overlaps are all below 10 people (suppressed), as
expected for a single release.
