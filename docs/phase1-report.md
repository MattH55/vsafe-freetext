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
| ingest | original r02-r12.xlsx (11 files) | 7,148,511 | 659 s |
| ingest | updated r02-r12.xlsx (11 files) | 7,148,511 | 1,170 s |
| ingest | call-center CSVs (CDC 23-00926, GDIT 23-00925) | 1,606,548 + 1,605,019 | 2 s + 5 s |
| link | call-center outcomes onto r01 entries | 395,010 entries | 15 s |
| qa | original vs updated, 13 releases (hashes only) | 7,948,511 x 2 | 28 s |

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
mild, none, vaccine, shot, today). Protocol owner decisions (2026-11-10): `cardiorespiratory`
becomes a ninth candidate PACVS domain; `taste_smell` stays a labelled acute theme, not a
domain; `upper_respiratory` is a criterion-3 exclusion. No file carries age, so no output is
stratified by age band (accepted).

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

## Call-center outcomes (task 3.8)

Two FOIA files, ingested 2026-11-10: 23-00926 (CDC; 1,606,548 rows, 2 s) and 23-00925 (GDIT;
1,605,019 rows, 5 s; cp1252-encoded, transcoded to UTF-8 at ingest). They describe the same
cases: 1,598,307 (registrant, survey form, reported date) keys appear in both. The CDC file
carries the trigger (health-impact answers) and care sought; the GDIT file carries call and
VAERS outcomes. Cases are merged on that key (`link_outcomes`).

| Cases in | Cases | People | VAERS filed (cases) | VAERS filed (people) |
|---|---|---|---|---|
| both files | 1,598,712 | 1,125,929 | 71,362 | 44,760 |
| GDIT only | 3,644 | 3,605 | 304 | 301 |
| CDC only | <10 people (suppressed) | | | |

VAERS filed = the report outcome says the report was completed by phone or had already been
filed. "Prefers to complete online" (about 77k people) is intent and is not counted, so this is
a lower bound on filing.

Release-1 entries with a call-center case within 90 days (`entry_outcomes`):

| Field | Entries | People | People with a case | People with VAERS filed | Share of entries with a case |
|---|---|---|---|---|---|
| SD | 41,470 | 40,322 | 20,481 | 836 | 0.52 |
| SRO | 345,957 | 242,609 | 77,319 | 2,666 | 0.34 |
| HCVO | 7,583 | 7,038 | 7,038 | 905 | 1.00 |
| all | 395,010 | 272,304 | 92,428 | 3,167 | 0.37 |

Every HCVO entry has a case, as expected: reporting a care visit triggers a call. Both files
also carry age at vaccination (`AGE_AT_VX`), but only for called registrants (about 2/3 of
cases), so it is not a usable age variable for the whole cohort; no output is stratified by
age (protocol owner, 2026-11-10). Link time: 15 s.

## QA: original vs updated (task 3.7)

Rows compared as a multiset over the shared columns (REGISTRANT_CODE and the three text
fields).

| Release | Rows (original) | Rows (updated) | People | Rows only in original | Rows only in updated |
|---|---|---|---|---|---|
| 1 | 390,000 | 390,000 | 272,544 | 0 | 0 |
| 2 | 390,000 | 390,000 | 298,471 | 0 | 0 |
| 3 | 390,000 | 390,000 | 296,200 | <10 | <10 |
| 4 | 650,000 | 650,000 | 468,307 | 0 | 0 |
| 5 | 650,000 | 650,000 | 459,022 | 0 | 0 |
| 6 | 650,000 | 650,000 | 453,851 | 0 | 0 |
| 7 | 780,000 | 780,000 | 536,169 | 0 | 0 |
| 8 | 780,000 | 780,000 | 532,779 | 0 | 0 |
| 9 | 780,000 | 780,000 | 611,767 | 0 | 0 |
| 10 | 780,000 | 780,000 | 524,042 | 0 | 0 |
| 11 | 780,000 | 780,000 | 662,093 | 0 | 0 |
| 12 | 518,511 | 518,511 | 377,718 | 0 | 0 |
| under-3 | 16,418 | 16,418 | 8,181 | 0 | 0 |

All 13 files, 7,948,511 rows each side. Columns in every release: updated = original +
`SURVEY_STATIC_ID`, `RESPONSE_ID`, `STARTED_ON`; no other column differences. Release 3 has
fewer than 10 rows on each side that differ (equal numbers, so cells edited in place, not rows
added or removed); the updated file is used. Zero cells here are exact zeros, checked locally
before suppression. Cross-check run time: 28 s.

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
