# Amendment 1: CDC MedDRA coding as the reference standard

**Registration:** https://osf.io/gnfpd (filed 2026-11-11)
**Amendment drafted:** 2026-11-11
**Status:** filed on OSF 2026-11-11 as an update to https://osf.io/gnfpd, before any result it governs was computed.
**Replaces:** section 7 of the registration ("Classifier validation and the confirmatory theme
set"), the parts about human coders.

## What changes and why

The registration validated the classifier against a gold set of 1,000 long-term entries, each
coded by two independent human coders, with adjudication. We cannot recruit or fund two
coders. Without them the confirmatory gate (precision and recall ≥ 0.85 per theme) cannot be
applied as registered.

We replace the human gold set with an existing human reference: the MedDRA coding that CDC
applied to v-safe free text. CDC staff coded each entry to MedDRA Preferred Terms (PTs). The
coding is independent of our classifier, was done before this study existed, and covers
99.9% of entries (7,814,740 of 7,819,251 entries have at least one active code in the
2024-11 release).

No confirmatory analysis (Q1–Q3) has been run. No precision or recall has been computed on
long-term entries against any reference. The 1,000-entry long-term gold sample was drawn on
2026-11-11, but no one has opened or coded it.

## New validation procedure

**Reference label.** An entry has theme T in the reference if CDC coded the entry to at least
one PT listed for T in the frozen map `taxonomy/v1.0/meddra_map.csv` (sha256 in
`taxonomy/v1.0/SHA256SUMS`). Only active codes from the 2024-11 MedDRA release are used. The
map is used exactly as frozen at registration and is not edited after this amendment.

**Entries evaluated.** All long-term entries (3-, 6- and 12-month surveys) that have at least
one CDC code. Pre-vaccine entries are excluded, as in the case definition. Redacted entries
are excluded. Using every eligible entry, not a sample, removes sampling error and the need
for weights.

**Measures, per theme.**
- **Precision:** of entries the classifier labels T, the share whose CDC codes include a
  T-mapped PT.
- **Recall:** of entries whose CDC codes include a T-mapped PT, the share the classifier
  labels T.
- Both are reported with 95% Wilson intervals.
- Both are computed for layer 1 (the lexicon) and for the final classifier: layer 1 plus
  layer 3, where layer 3 has labelled the entry.

**Gate (unchanged threshold).**
- A theme is confirmatory if both its precision and its recall are ≥ 0.85 for the final
  classifier.
- A theme that fails is reported as exploratory, with its precision and recall.
- As registered, if any PACVS domain fails, Q1–Q3 are run on the domains that pass (primary)
  and on all nine domains (sensitivity).

**Themes with no MedDRA equivalent.** Themes with no PTs in the frozen map cannot be
validated this way and are exploratory: `persistence`, `care_sought`, `missed_work_school`.
Every PACVS domain has mapped PTs.

## Known limitations (stated in advance)

1. **The reference is coding, not ground truth.** CDC coded entries for adverse-event
   reporting, which is not the same as our theme definitions. Where CDC used a vaguer or
   different term, the classifier will look less accurate than it is.
   - Phase 1 found such a case. Entries the lexicon labelled `cognitive` were mostly coded
     "Feeling abnormal" rather than a cognitive PT (`docs/phase1-report.md`, early entries
     only).
   - A theme can therefore fail the gate because of reference mismatch. We report it as
     exploratory either way, and do not change the map to rescue it.
2. **The map depends on the lexicon.** The map was built from the PT and LLT names that the
   lexicon's patterns match, so PTs describing a theme in words the lexicon does not know may
   be missing. That can inflate recall.
   - To show the size of this, we also report, per theme, the share of the theme's entries
     that carry a PT outside the map. This is descriptive only.
3. **CDC codes per response.** CDC may code several PTs for one entry, or code only the most
   prominent symptom. Missing secondary codes lower measured precision.
4. **No coder-agreement measure.** With no second human coder, Cohen's kappa is not reported.

## What is unchanged

- The taxonomy (v1.0), the prompts (v0.1), the models, the case definition and the Q1–Q4
  analysis plan.
- The 0.85 threshold.
- The model-sensitivity check, in which a second LLM labels a fixed sample.
- The rule that only aggregates with at least 10 people per cell are published.

## Gold sheets already produced

The two-coder sheets (`gold_set/`) are kept but not used for the confirmatory decision. If a
coder later codes any of them, the result is reported as a descriptive check only.
