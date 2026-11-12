# Phase 2 report: full corpus, after registration

Registered 2026-11-11 as https://osf.io/gnfpd (embargoed). Everything here was run after
filing. Aggregates only: every cell has at least 10 people, and smaller cells are suppressed.
Data are in `D:/vsafe-data` (external drive), database `interim/vsafe_full.duckdb`
(`VSAFE_DB=vsafe_full`). The release-1 database `interim/vsafe.duckdb`, with the early gold set
and the LLM pilot labels, is unchanged.

## Link: 12 updated releases and the under-3 file (2026-11-11)

`vsafe-ft link` took 15,434 s (4 h 17 min). It was restarted once, after drive C filled up, and
moved to D:.

| Join | Rate |
|---|---|
| Entry to registrant | 0.998 |
| Entry to dose | 0.998 |
| Entry to check-in survey | 0.945 |

All three rates pass gate 1 (≥ 0.90).

There are 7,819,251 entries after de-duplication. The OSF abstract says 7.55 million entries.
The cause of the difference has not been checked yet.

| Period | Field | Entries | People | Share themed (layer 1) |
|---|---|---|---|---|
| week 1 / six weeks | SD | 1,679,313 | 1,180,793 | 0.767 |
| week 1 / six weeks | SRO | 3,968,173 | 2,142,765 | 0.598 |
| week 1 / six weeks | HCVO | 143,513 | 120,751 | 0.078 |
| long-term | SD | 1,458,795 | 1,207,417 | 0.644 |
| long-term | HCVO | 136,317 | 126,763 | 0.030 |
| long-term | SRO | suppressed (< 10 people) | | |
| survey not matched | SD | 315,973 | 270,666 | 0.665 |
| survey not matched | SRO | 94,608 | 57,021 | 0.650 |
| survey not matched | HCVO | 22,550 | 21,444 | 0.037 |

- **Long-term entries by survey:** 3 months 565,626; 6 months 586,468; 12 months 443,027. In
  total 1,595,121 entries from 1,207,426 people.
- **SRO at long-term surveys:** the long-term surveys have almost no SRO entries.
- **HCVO coverage:** HCVO is the lexicon's weakest field at every period (3–8%). Its recall on
  the gold set decides whether layer 3 is needed there.

## Layer 1 on every entry (2026-11-11)

`vsafe-ft classify --long-term` used the frozen taxonomy v1.0 and took about 84 minutes.

| Flag | SD people | SRO people | HCVO people |
|---|---|---|---|
| third party (kept) | 9,402 | 4,461 | 487 |
| pre-vaccine (dropped) | 2,142 | 2,773 | 35 |

## Gold set, long-term period (drawn 2026-11-11)

`vsafe-ft gold draw --size 1000 --period long_term --seed 1` took 31 s. It drew 1,000 entries,
which are 940 distinct texts. The sheets are `D:/vsafe-data/gold_set/vsafe_full/sheet_A.csv`
and `sheet_B.csv`; I have not opened them.

| Stratum | Entries | Texts | Weight |
|---|---|---|---|
| HCVO, themed | 124 | 119 | 32.44 |
| HCVO, unthemed | 164 | 146 | 800.29 |
| SD, themed | 418 | 402 | 2,242.99 |
| SD, unthemed | 285 | 266 | 1,818.47 |
| SRO, themed and unthemed | suppressed (< 10 people) | | |

The confirmatory theme set is decided by this part of the gold set (precision and recall
≥ 0.85, OSF section 7). Q1–Q3 run only after both coders finish and disagreements are
adjudicated.

## Validation against CDC MedDRA coding, layer 1 (amendment 1, 2026-11-11)

`vsafe-ft validate --layer lexicon` took 31 s. It covered 1,590,177 long-term entries with a
2024-11 code, from 1,205,307 people. Redacted and pre-vaccine entries were excluded.

An entry counts as having a theme in the reference if CDC coded it to a PT that the frozen
v1.0 map lists for that theme. 95% Wilson intervals are in
`aggregates/vsafe_full/validate_meddra_lexicon.csv`; every interval is narrower than ±0.01.

| Theme | Domain | Lexicon entries | Reference entries | Precision | Recall | Gate (≥ 0.85 both) |
|---|---|---|---|---|---|---|
| dysautonomia | PACVS | 55,039 | 61,701 | 0.978 | 0.872 | pass |
| fatigue_pem | PACVS | 169,299 | 197,809 | 0.984 | 0.842 | fail (recall) |
| gastrointestinal | PACVS | 74,645 | 89,894 | 0.989 | 0.821 | fail (recall) |
| pain | PACVS | 251,945 | 345,148 | 0.991 | 0.724 | fail (recall) |
| cognitive | PACVS | 13,674 | 17,565 | 0.889 | 0.692 | fail (recall) |
| cardiorespiratory | PACVS | 30,737 | 46,936 | 0.956 | 0.626 | fail (recall) |
| sleep | PACVS | 5,786 | 9,067 | 0.973 | 0.621 | fail (recall) |
| menstrual | PACVS | 24,707 | 39,807 | 0.927 | 0.575 | fail (recall) |
| sensory_neuropathic | PACVS | 26,035 | 122,015 | 0.966 | 0.206 | fail (recall) |
| fever_chills | acute | 120,443 | 122,347 | 0.970 | 0.955 | pass |
| upper_respiratory | exclusion | 352,196 | 367,587 | 0.993 | 0.952 | pass |
| skin | acute | 34,764 | 48,210 | 0.964 | 0.695 | fail |
| taste_smell | acute | 19,638 | 29,463 | 0.932 | 0.622 | fail |
| lymphadenopathy | acute | 14,073 | 19,250 | 0.866 | 0.633 | fail |
| injection_site | acute | 17,751 | 78,113 | 0.927 | 0.211 | fail |
| acute_diagnosis | exclusion | 36,429 | 28,139 | 0.660 | 0.854 | fail (precision) |
| unrelated_cause | exclusion | 189,889 | 57,851 | 0.245 | 0.803 | fail |
| pre_existing_worsened | lay | 6,209 | 11,667 | 0.210 | 0.112 | fail |

**What the lexicon gets wrong.** Precision is high for every PACVS domain (0.89–0.99).
Recall is what fails: the lexicon misses entries that CDC coded.

**Where the misses are** (`validate_missed_lexicon.csv`). 18–77% of the missed entries, by
theme, are in the residue, meaning entries the lexicon gave no theme at all. Layer 3 as
registered labels only the residue. Even a perfect layer 3 on the residue would leave recall
below the gate for cognitive, cardiorespiratory, sleep, menstrual and sensory_neuropathic. The
other misses are in entries that have some other theme.

**Status.** This is layer 1 only. The registered gate applies to the final classifier
(layer 1 plus layer 3), and layer 3 has labelled 1,800 of 386,862 residue texts.
