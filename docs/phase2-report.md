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

**Status.** Layer 1 only. The final-classifier validation is below.

## Layer 3 on the long-term residue (amendment 2, 2026-11-11 to 12)

`vsafe-ft llm-label --long-term --residue --all --model deepseek/deepseek-v4.1-flash --workers 8`
labelled every unique long-term residue text: 649,516 entries, 386,862 texts. About 10 h
wall time over two runs (one dropped connection, resumed), 0 failed after retry, 0 refusals,
about US$0.02. 83% of texts received at least one theme. The 1,800 GLM-5.3 labels are unused.

## Validation of the final classifier (2026-11-12)

`vsafe-ft validate --layer final --model deepseek/deepseek-v4.1-flash` took 23 s
(`validate_meddra_final_deepseek-v4_1-flash.csv`). Layer 3 raised recall in every PACVS domain
and lowered precision in every one.

| Domain | Precision (lexicon → final) | Recall (lexicon → final) | Gate |
|---|---|---|---|
| fatigue_pem | 0.984 → 0.961 | 0.842 → 0.859 | **pass** |
| dysautonomia | 0.978 → 0.774 | 0.872 → 0.946 | fail (precision) |
| gastrointestinal | 0.989 → 0.747 | 0.821 → 0.901 | fail (precision) |
| pain | 0.991 → 0.903 | 0.724 → 0.827 | fail (recall) |
| cognitive | 0.889 → 0.762 | 0.692 → 0.741 | fail |
| cardiorespiratory | 0.956 → 0.690 | 0.626 → 0.762 | fail |
| sleep | 0.973 → 0.738 | 0.621 → 0.718 | fail |
| menstrual | 0.927 → 0.849 | 0.575 → 0.659 | fail |
| sensory_neuropathic | 0.966 → 0.661 | 0.206 → 0.246 | fail |

Exclusion themes: unrelated_cause precision 0.144, acute_diagnosis 0.311. A post-hoc look at
the CDC PTs on those entries (counts only) shows most are map gaps (COVID-19, SARS-CoV-2 test
positive, nasopharyngitis, cerebrovascular accident, thrombosis are not in the frozen map) and
two real errors: negative COVID tests tagged unrelated_cause, chronic conditions tagged
acute_diagnosis.

**Decision (protocol owner, 2026-11-12):** only one PACVS domain passes, so the registered
primary analysis (Q1–Q3 on passing domains) is infeasible. Report as-is, no amendment. All
results below are the registered nine-domain sensitivity analysis.

## Confirmatory analysis, nine-domain sensitivity (2026-11-12)

`vsafe-ft analyse` (`analysis_sens9_*`). Setup (final classifier, case definition on 145M
check-ins) 63 min; helper tables 3 min; Q1–Q4 9 min after the permutation null was
re-implemented (positives drawn per domain instead of permuting the matrix: same null, ~16×
faster; `stats.cooccurrence_test`); VAERS replication 90 min.

| Group | Person-doses | People |
|---|---|---|
| case | 87,229 (1.01% of 8.62M with a long-term survey) | 86,323 |
| (a) no_symptoms | 5,877,624 | 4,760,357 |
| (b) acute_event | 104,736 | 102,616 |
| (c) severe_w1_recovered | 1,602,523 | 1,518,229 |
| other | 2,267,821 | 2,036,216 |

- **Q1:** 1,267,509 person-doses with long-term text; observed pairs 235,184 vs 188,776
  (ratio 1.25, p = 0.001); rejects in every dose and manufacturer stratum (1.21–1.39);
  23/36 pairs above null after Holm; strongest cognitive–sleep 4.1×, cognitive–fatigue 3.0×.
  VAERS replication (1,057,077 COVID-19 reports, layer 1): ratio 1.85, same core.
- **Q2 onset:** 27.9% early vs 71.3% expected (p = 1.0). H0 not rejected.
  **Q2 persistence:** 60.3% of cases vs 1.5% of group (c); RD 58.9 points (58.4–59.3).
- **Q3 capture:** rate ratio 0.94 (0.90–0.98), same on the high-confidence set; H0 rejected
  but the rates are 4.6% vs 4.9%. **Q3 dispersion:** cases' PT entropy lower (8.31 vs 8.59),
  p = 1.0.
- **Q4 / attrition:** `analysis_sens9_q4.csv`, `analysis_sens9_attrition.csv`. 49.4% of
  person-doses with a check-in completed a long-term survey (60.1% after a week-1 impact,
  42.4% without).
- **Table 1** (`analysis_sens9_table1.csv`): cases 77.5% women vs 58.1% in group (a); no age
  field exists in the linked release.

## Model sensitivity (registered check, 2026-11-12)

`llm-label --long-term --residue --sample 2000 --seed 1 --model claude-opus-5-5`: 1,687 texts,
0 failed, US$1.96, 593 s. `llm-report ... --long-term`
(`phase1_llm_model_shift_deepseek_v4_1_flash_residue2000_s1_longterm.csv`). Model-sensitive
(> 20%): fatigue_pem (20 vs 46 entries, 0.57), menstrual (0.44), cardiorespiratory (0.40),
cognitive (0.23); unrelated_cause (0.31), persistence (0.49), care_sought (0.27). Stable:
dysautonomia, gastrointestinal, pain, sensory_neuropathic. Sleep suppressed.

## Exploratory checks (not registered, 2026-11-12; `analysis_expl_*`)

Specified after the registered results were seen; `vsafe-ft analyse --steps exploratory`.

1. **Text-matched Q1 null** (`stats.cooccurrence_test(strata=...)`, 484 s): ratio 1.25 →
   1.06 (character deciles) → 1.04 (entries × deciles); pairs above null 23 → 19 → 16.
   Core survives: cognitive–sleep 2.5×, cognitive–fatigue 2.3×, fatigue–sleep 1.6×,
   cognitive–dysautonomia 1.6×. Mean domains per person-dose rise 0.26 → 1.07 across
   character deciles.
2. **Exclusion variants** (1,299 s): keyword-only exclusions → 89,198 cases, group (b)
   64,629, Q3 RR 0.82 (0.79–0.86); no criterion 3 → 135,252 cases, RR 0.78 (0.75–0.81).
   Q2 unchanged in direction.
3. **Onset** (402 s): layer 3 on cases' early residue (26,889 texts, US$0.0005, 32 min)
   raises the early share 27.9% → 32.7%; survey-type null expects 42.2%; p = 1.0.
   Structured week-1 fields: 80.9% of cases with a week-1 check-in ticked a same-domain
   symptom, vs 35–40% of group (a) and 89–92% of group (c) (1-in-20 sample of non-cases).

## Analyses not in the pre-registration, addendum 2 (2026-11-12; `sub_*`)

`vsafe-ft submission`. Full tables are in `docs/submission/supplement.md`; the headline check is
`docs/submission/headline-check.md`.

- **B2 curveball null** (row and column margins fixed; 1,000 samples each, 30 burn-in rounds,
  3 rounds between samples; 24 min per run): total pairs invariant (235,184 in every sample, so
  the aggregate test is empty by construction). Core pairs, unstratified / within entries /
  within text-length tertiles: cognitive–sleep 2.70 / 2.44 / 2.30; cognitive–fatigue 2.27 / 2.29
  / 2.06; cognitive–dysautonomia 1.55 / 1.42 / 1.53; fatigue–sleep 1.60 / 1.62 / 1.47;
  fatigue–pain 1.45 / 1.48 / 1.39. Pairs above null after Holm 15 / 13 / 15; below 18 / 19 / 17.
- **B3 persistence** (69 s): 69,816 cases (80.0%) met criterion 2 at one survey, 17,413 only
  across surveys. Persistence 47.1% for same-survey cases vs 60.3% for all; group (d) (worse or
  impacted, < 2 domains) 10.5%; risk difference 58.9 → 36.6 points at the strictest.
- **B4 structured week-1 answers** (286 s): cases with fatigue 78.9% ticked week-1 fatigue (64.4%
  moderate or severe) vs 35.5% (14.6%) in group (a); pain 80.2 / 63.1 vs 40.0 / 16.0; GI 47.8 /
  29.3 vs 10.2 / 2.7. Group (a) has no week-1 impact by construction.
- **B5 audit sheet** (315 s): 306 disagreements (17 per domain per side) written to
  `gold_set/vsafe_full/audit_layer3_vs_cdc_{sheet,key}.csv`; pool 223,652 CDC-only and 111,523
  layer-3-only entry-domain pairs. Coding by the protocol owner pending.
- **B6 dispersion** (448 s): Miller-Madow 8.38 vs 8.67; rarefied to 18,072 codes 8.31 vs 8.59;
  two-sided p = 0.001. Cases' coding is less dispersed on every measure.
- **B7** (625 s): Q1 with redacted entries included 1.247 (p = 0.001; 1,269,337 person-doses);
  case count unchanged; criterion 3 off 135,252 cases.
- **B8 reconciliation** (2,206 s, three raw-file scans): early entries 5,791,000 (the report's
  the earlier 5,790,999 was an off-by-one; corrected throughout); check-ins 144,972,101 = 144,856,043 adult +
  116,294 under-3 rows de-duplicated by response ID (Levi & Lu: 151,581,805 adult rows; file
  version); 17,459,757 person-doses with a check-in, 8,623,658 with a long-term survey,
  9,939,933 in a group; 7,554,929 (release description) vs 7,819,275 raw rows unexplained.
- **B9 cost**: `llm_runs` holds the Claude sample (232,706 tokens, US$1.96) and two DeepSeek runs
  (27,451 texts, 2,152,942 tokens, US$0.0005); the main DeepSeek run's row was lost with its
  dropped connection, so its cost is the run log's per-request total (US$0.022) and its tokens
  are unlogged. To be confirmed against the NanoGPT usage page.
- **Task 3.9, Levi & Lu cohorts** (structured answers only; no age field exists, so the adult
  check-in file stands in for "16+"):

| Group | Ours | Levi & Lu | Difference | % |
|---|---|---|---|---|
| Enrollees | 9,552,127 | 9,904,924 | -352,797 | -3.56 |
| Prolonged-AE | 167,335 | 185,285 | -17,950 | -9.69 |
| Prolonged-AE, dose 1 | 32,732 | 32,838 | -106 | -0.32 |
| Prolonged-AE, dose 2 | 101,064 | 100,564 | +500 | +0.50 |
| Prolonged-AE, dose 3+ | 33,539 | 51,883 | -18,344 | -35.36 |
| Prolonged-NoAttr | 167,930 | 189,982 | -22,052 | -11.61 |
| Prolonged-NoAttr, dose 1 | 20,389 | 18,710 | +1,679 | +8.97 |
| Prolonged-NoAttr, dose 2 | 89,862 | 81,462 | +8,400 | +10.31 |
| Prolonged-NoAttr, dose 3+ | 57,679 | 89,810 | -32,131 | -35.78 |
| Control | 9,216,862 | 9,529,657 | -312,795 | -3.28 |
| Women in Prolonged-AE | 124,376 | 137,430 | -13,054 | -9.50 |
| Women | 5,941,118 | 6,141,800 | -200,682 | -3.27 |

  Explanation of differences over 0.5%: every shortfall concentrates in the dose-3+ sub-cohorts
  (-35% in both), and our check-in file has 6.7 million fewer rows than theirs, so it holds fewer
  later surveys (file version or date window). The missing 16+ filter would raise our counts, not
  lower them. NoAttr dose 1 and 2 are higher than theirs (+9 to +10%), which may reflect how they
  treated an attribution answer of null (we treat null as not "Yes"); unexplained. The joins were
  not adjusted. Overlap at person level, among 6,754,831 people in both denominators: both
  29,593; text-defined only 56,730; Prolonged-AE only 137,742; neither 6,530,766. 34.3% of
  text-defined cases are in Prolonged-AE; 17.7% of Prolonged-AE meet the text definition;
  Cohen's kappa 0.22 (`sub_levilu_overlap.csv`).

## Decisions where the registration was silent

Survey-type mapping (day 0–7 = w1, week 2–6 = 6w); impact = any non-'N/A' answer;
pre-vaccine entries dropped if either layer flags them; layer 2 never built; layer 3 on
long-term text only; persistence reference = first worse/impact long-term survey; Q3 at
person level; model-sensitivity sample 2,000 (pilot size); permutation re-implemented.
