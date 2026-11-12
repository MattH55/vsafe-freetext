# Local agent brief, addendum 1 (12 Nov 2026): Levi & Lu preprint

This adds to `docs/local-agent-brief.md`. Where the two conflict, this addendum wins. The hard
rules in the brief are unchanged.

## Why

Levi R, Lu N. *Reporting on Prolonged Adverse Health Impact Among V-SAFE Enrollees*, Research
Square, 25 Aug 2026, doi:10.21203/rs.3.rs-10768889/v1. They defined a cohort from check-box
answers only: health "Worse" **and** attributed to vaccination at any 3-, 6- or 12-month survey.
They reported CDC MedDRA rates and an unvalidated gpt-4o-mini severity rating for that cohort.
The protocol now cites it, makes Q3 (VAERS) the lead question, and uses their cohort both as a
**linkage check** and as a **sensitivity case definition**. See `docs/protocol.md`, section
"Closest prior work".

## A. Merge the document changes

This addendum comes with a patch (`levi-lu-revisions.patch`) made against commit `75bb495`.
It changes `docs/protocol.md` and `docs/preregistration/README.md`, and adds
`docs/preregistration/prior-knowledge.md` and this file.

1. On a new branch `docs/levi-lu`, try `git am levi-lu-revisions.patch`.
2. If it conflicts (you may already have edited these files, and step 2 of the brief told you
   to create `prior-knowledge.md`), run `git am --abort` and merge by hand. Keep every entry
   you already logged. Prior-knowledge entries are append-only, so nothing in that file is
   removed in the merge.
3. Open a pull request. Do not merge it yourself; the human reviews protocol changes.

## B. New task 3.9: reproduce the Levi & Lu cohorts (linkage check)

Implement after 3.1–3.4. Build it from **structured check-in answers only**. This touches
long-term surveys, but not their free text, so it is allowed before registration (hard rule 5
concerns long-term **free text**).

Inclusion rules, from their Section 2.3:
- **Population:** registrants aged 16 or older at the first dose (use the vaccination age
  band; record how you handle a band that straddles 16).
  Exclude the under-3 check-in file.
- **Prolonged-AE:** in at least one 3-, 6- or 12-month survey, health compared with before the
  last dose = "Worse" **and** attribution = "Yes". The qualifying survey is the earliest such
  survey, ordered by dose and then by month.
- **Prolonged-NoAttr:** "Worse" in at least one monthly survey, and attribution never "Yes".
  The qualifying survey is the first "Worse".
- **Control:** everyone else aged 16+, **including people who never completed a monthly
  survey**.
- **Sub-cohorts:** highest reported dose 1, 2, 3 or more.

Their published targets:

| Group | n |
|---|---|
| Enrollees 16+ | 9,904,924 |
| Prolonged-AE | 185,285 (D1 32,838 / D2 100,564 / D3+ 51,883) |
| Prolonged-NoAttr | 189,982 (D1 18,710 / D2 81,462 / D3+ 89,810) |
| Control | 9,529,657 |
| Women in Prolonged-AE | 137,430 of 6,141,800 women 16+ |

Their three groups sum to 9,904,924, so a person who has "Worse" with attribution "Yes" at one
survey and "No" at another is in Prolonged-AE. Implement it that way.

Done when:
- `src/vsafe_ft/cohorts.py` builds the three cohorts plus sub-cohorts in DuckDB, with a unit
  test on synthetic check-ins covering the edge cases (mixed Yes/No across surveys; a person with
  no monthly survey; the qualifying survey falling at dose 2 when the person had 3 doses).
- `docs/phase1-report.md` has a table of our counts against theirs, with the difference and
  percentage difference for every row above. These are aggregate counts, so they pass
  `assert_safe`.
- Any difference over 0.5% is explained (age-band rule, deduplication, file version, the
  check-in date window ending 30 Jun 2023), or listed as unexplained. Do not tune the joins to
  hit their numbers; report the difference.

## C. New task 5.4: sensitivity case definition (synthetic data only, before registration)

In `phenotype.py`, add `levi_lu_case` next to the text-defined case definition, plus a function
that cross-tabulates the two (text-defined only, Levi & Lu only, both, neither) and reports
agreement (Cohen's kappa). Test it on synthetic data. It is **not** run on real long-term free
text until the human confirms the registration is filed.

## D. Column hints (confirm against the real headers; do not fill `columns.yaml` from these)

Their appendix names:
- the MedDRA files `Covid_meddra_sd.csv`, `Covid_meddra_sro.csv` and `Covid_meddra_hcvo.csv`;
- the adult check-in file `Consolidated_health_checkin.csv`, 151,581,805 rows;
- the under-3 check-in file `consolidated_health_checkin_u3.csv`, 265,347 rows;
- `Consolidated_vaccinations.csv` (21.1M rows) and `Consolidated_race_ethnicity.csv` (8.9M rows).

They also report two monthly-survey fields in the check-ins: health compared with before the
last dose (Better / About the same / Worse), and attribution (Yes / No). Add these to the
`health_checkins` mapping as `health_vs_before` and `attributed_to_vaccine`, and add the
positive-COVID-test answer as `covid_positive`. Row counts that differ from theirs go in the
phase-1 report.

## E. Unchanged

- No free text from 3-, 6- or 12-month surveys is read or classified before registration.
- Do not contact the authors; the human decides whether to do that.
