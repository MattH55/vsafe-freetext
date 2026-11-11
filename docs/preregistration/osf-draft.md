# OSF registration draft (Secondary Data Preregistration template)

**Status: DRAFT, not filed.** The protocol owner reviews, edits and files this on OSF
Registries. Items marked **[DECIDE]** need a decision before filing. After filing, set
`osf_registration` in `config/analysis.yaml` to the registration DOI. That unlocks long-term
text in code. Every change after filing is an OSF amendment, never an edit to the filed text.

---

## 1. Title

A persistent multi-system symptom entity after COVID-19 vaccination? Systematic classification
of 7.5 million v-safe free-text entries, with a pre-registered test of domain co-occurrence.

## 2. Authors

Matthew Halma (OpenSourceMed). **[DECIDE]** Add gold-set coders and other contributors.

## 3. Research questions and hypotheses

**Primary question.** Does v-safe's long-term follow-up (3-, 6- and 12-month surveys) contain
a persistent, multi-system symptom entity consistent with PACVS (post-acute COVID-19 vaccination
syndrome), and if so, why did it not surface in VAERS?

The nine candidate symptom domains are listed in `taxonomy/v1.0/themes.yaml` (`domain: pacvs`):

- fatigue / post-exertional malaise
- cognitive
- dysautonomia
- sensory / neuropathic
- sleep
- pain
- gastrointestinal
- menstrual change
- cardiorespiratory

| # | Hypothesis (H1) | Null (H0) | Tier |
|---|---|---|---|
| Q1 Coherence | In long-term free text, the PACVS domains co-occur within people more than a null that keeps each domain's frequency would predict. | Co-occurrence is no higher than the marginal-preserving permutation null. | Confirmatory |
| Q2 Natural history | Among people meeting the case definition, onset is concentrated in the first six weeks after a dose. They report PACVS domains at a later long-term survey more often than comparison group (c) does. | Onset is spread evenly over the follow-up surveys, and persistence is the same as in group (c). | Confirmatory |
| Q3 Detection failure | Cases have a lower VAERS-filing rate than the acute-event group (b). Matched VAERS reports for cases are coded to more different MedDRA PTs. | Same capture rate as group (b), and coding is no more dispersed. | Confirmatory |
| Q4 Burden | Cases report health impact, medical care and call-center contact more often than group (a). | Same as group (a). | Descriptive (no test) |

## 4. Data

| Source | Description | Access |
|---|---|---|
| v-safe free text, updated files (FOIA 24-01322; 12 releases + under-3) | Entries in the three free-text fields: symptom description, other systemic reaction, other healthcare visit. Each entry carries a registrant code, survey id, response id and start time. | Public; ICAN productions. URLs and sha256 in `data/raw/MANIFEST.tsv`. |
| v-safe free text, original files | Cross-check only | as above |
| Registrants, vaccinations, health check-ins | Denominators, dose anchor, survey answers | data.cdc.gov / ICAN |
| Call center (FOIA 23-00925 GDIT, 23-00926 CDC) | Cases, care sought, VAERS-filed dispositions | ICAN |
| CDC MedDRA coding of the free text (Nov 2024 file) | Validation | ICAN |
| VAERS public data (1990–2026, data dated 2026-06-03) | VAERS arm, Q3 | vaers.hhs.gov |

Each file has its sha256 recorded at download. All files were downloaded between 2026-11-08 and
2026-11-10. VAERS matching uses OpenVSafe's v-safe-to-VAERS matches (score ≥ 8 of 11 fields;
decided 2026-11-10). OpenVSafe publishes no bulk file. The matches were read from its public person pages on 2026-11-10 and 2026-11-11, keeping only VAERS ID, confidence, score and runner-up: 27,234 of 44,954 VAERS-filed people have a match, 24,067 of them high-confidence. A VAERS report describes one person, so the 559 reports matched to more than one person are ambiguous. Everyone matched to them (1,321 people) is dropped (decided 2026-11-11).

## 5. Prior knowledge of the data (disclosure)

The full log is in `docs/preregistration/prior-knowledge.md`, which is attached. In summary:

- **Free text read or classified before filing:** only week-1 and six-week entries. These are
  the whole of updated release 1 (395,010 entries; release 1 contains no long-term survey
  text). We ran layer 1 (the lexicon) on all of them. On samples of 2,000 random entries and
  1,000 lexicon-unlabelled entries, we ran layer 3, a large-language-model labeller restricted
  to a closed list of themes.
- **Whole-corpus processing before filing:** releases 2–12 were ingested to Parquet and checked
  row by row against the original files using hashes. No text from those releases was read or
  classified.
- **Seen in aggregate only:** join rates, theme coverage, frequent word sequences (n-grams)
  used by at least 10 people, and theme-to-MedDRA counts. For the call-center files, we also
  saw value frequencies of the coded answer lists. No individual entry has been quoted.
- **Taxonomy changes made after seeing week-1 / six-week aggregates:**
  - We added five acute-reaction themes and an upper-respiratory theme.
  - Cardiorespiratory became the ninth PACVS domain.
  - Upper-respiratory symptoms became an exclusion.
  - Taste and smell stayed an acute theme, not a domain.
  - The persistence theme was given a sharper description after the two LLMs disagreed on it.
  
  All of these changes were made before any long-term text was seen.
- **Not done before filing:** no gold-set result has been computed, and no long-term (3-, 6-
  or 12-month) free text has been opened, read or classified. The code enforces this:
  `themes.exploratory_filter_sql`, the `PermissionError` guards in `layer3`, `gold` and
  `themes`, and `osf_registration: null`.

## 6. Variables

**Unit:** a registrant × dose. The denominator is every registrant × dose with at least one
completed long-term survey (3, 6 or 12 months).

**Classified free text.** Each entry gets themes from three layers: lexicon, then embeddings,
then an LLM restricted to the closed theme list. Each entry also gets two flags:
`third_party` (the entry is about someone else) and `pre_vaccine` (it reports something
before vaccination). Entries flagged `pre_vaccine` do not count towards any criterion
(`phenotype.prepare` drops them). Entries about another person do count: a registrant often
reports for a dependant (decided 2026-11-10).

| Theme group | Themes | Role |
|---|---|---|
| PACVS domains | fatigue_pem, cognitive, dysautonomia, sensory_neuropathic, sleep, pain, gastrointestinal, menstrual, cardiorespiratory | Criterion 2; Q1 matrix |
| Exclusion | acute_diagnosis, unrelated_cause, upper_respiratory | Criterion 3; group (b) uses acute_diagnosis |
| Lay layer | persistence, care_sought, missed_work_school, pre_existing_worsened | Q2/Q4, descriptive |
| Acute profile | injection_site, lymphadenopathy, fever_chills, skin, taste_smell | Descriptive |

**Case definition (PACVS-like).** A case meets all three criteria (`src/vsafe_ft/phenotype.py`):

1. The person completed a 3-, 6- or 12-month survey S, and at S either their health now was
   worse than baseline, or they reported a health impact (unable to do normal activities,
   missed work or school, or needed care).
2. Free text at S covers at least 2 PACVS domains. Alternatively, free text across at least 2
   long-term surveys of that dose covers at least 2 domains between them.
3. No exclusion theme appears in the free text at S.

**Comparison groups.** The groups do not overlap. Where a person fits more than one, the
priority is case, then (b), then (c), then (a).

- **(a) No symptoms.** Completed a long-term survey; no long-term survey was worse or had an
  impact; no PACVS text at any long-term survey.
- **(b) Acute event.** Free text at any survey of that dose names an acute diagnosis.
- **(c) Severe week-1, recovered.** At week 1, reported an impact or at least 2 PACVS domains;
  completed at least one long-term survey; no long-term survey was worse or had an impact.

**Outcomes for Q3/Q4.** These come from the call center, counted within 90 days after an entry:
a case opened, a VAERS report filed (a call disposition), care sought, hospitalisation, and an
emergency visit. They also include VAERS reports matched to the person. Thresholds are fixed in
`config/analysis.yaml`.

**Strata for stability checks:** manufacturer, dose number and sex. The files have no age
column, so age is not a stratum (decided 2026-11-10).

## 7. Classifier validation and the confirmatory theme set

- **Gold set.** Entries are stratified by field × period × whether the lexicon labelled them.
  Half of the sample is allocated equally across strata and half in proportion to stratum
  size. Each entry carries an inverse-probability weight. Two coders code each entry blind to
  the classifiers, and disagreements are adjudicated (`src/vsafe_ft/gold.py`). 1,000
  week-1 / six-week entries are drawn before filing, and 1,000 long-term entries only after
  filing (2,000 in total, `analysis.yaml`).
- **Coder agreement.** Cohen's kappa for each theme.
- **Classifier performance.** Weighted precision and recall for each theme, computed for each
  layer and for the final union of layers.
- **Confirmatory gate.** A theme is confirmatory only if both precision and recall are at
  least 0.85 on the long-term part of the gold set. Themes that fail are reported as
  exploratory, with precision/recall bounds. If any PACVS domain fails, Q1–Q3 are run on the
  domains that pass (primary), and on all nine domains (sensitivity).
- **Model sensitivity.** A second LLM labels a fixed sample. A theme whose count shifts by more
  than 20% between the two models is flagged model-sensitive and reported as such.
  - Primary LLM: `z-ai/glm-5.3` via NanoGPT, on zero-data-retention routes only.
  - Second LLM: `claude-opus-5-5`.
- **Fixed before filing.** The prompt version, the theme list and the taxonomy are frozen as
  `taxonomy/v1.0`, with the sha256 written by `scripts/freeze_taxonomy.py`. The gold set is
  not used to tune anything before filing. After filing, any change to the taxonomy is an
  amendment that names the gold-set result that motivated it.

## 8. Analysis plan

**Q1 (primary confirmatory test)**

- **Data.** A people × domains boolean matrix. Rows are registrant × dose in the denominator
  with any long-term free text. A domain counts as present if any long-term entry of that dose
  is classified to it.
- **Statistic.** The sum, over all 36 domain pairs, of the number of people who have both
  domains.
- **Null.** 1,000 permutations. Each permutation shuffles every domain column independently,
  so each domain's marginal frequency is kept exactly. Seed 20261110.
- **Decision.** One-sided p = (1 + #{null ≥ observed}) / 1,001. We reject H0 at α = 0.05.
  - The per-pair p-values are secondary, with Holm adjustment across the 36 pairs
    (`stats.holm`).
  - The number of people with 2 or more domains is descriptive only.
- **Stability.** The test is repeated within each manufacturer and each dose. We call the
  pattern reproducible if the Q1 test rejects in every stratum with at least 1,000 people.
- **Replication.** The same classifier is run on VAERS `SYMPTOM_TEXT` for COVID-19 vaccines,
  and the same test is applied there.
- **Latent class analysis (LCA).** We fit models with 1–6 classes on the domain matrix and
  choose the number of classes by BIC. This is reported descriptively: a class with high
  probability on 2 or more domains is descriptive. LCA is **exploratory** (decided
  2026-11-10): it supports or weakens H1 but is not a test.

**Q2**

- **Onset.** For cases, onset is the first survey at which the case domains appear: week 1,
  six weeks, or a long-term survey. We compare the share with onset at or before six weeks
  against the share expected if onset were spread evenly over the surveys completed. Each
  case's null probability of early onset is the share of their completed surveys of that dose
  that are week-1 or six-week; the number of early-onset cases is compared with that
  Poisson-binomial null by an exact one-sided test (`stats.onset_test`).
- **Persistence.** We compare cases with group (c) on the share reporting at least one PACVS
  domain at a later long-term survey, among people who completed one. This uses a risk
  difference with a 95% Newcombe hybrid score interval and a one-sided pooled z-test at
  α = 0.05 (`stats.risk_difference`).
- **Cadence.** All counts over time are rates per 1,000 check-ins of that survey type.

**Q3**

- **Capture.** The rate ratio for any VAERS report (call-center VAERS-filed disposition or a
  matched VAERS report), cases vs group (b), with a 95% log-scale Wald CI. We reject H0 if
  the upper limit is below 1 (`stats.risk_ratio`).
- **Dispersion.** On matched reports, we compare the Shannon entropy of the MedDRA PTs for
  cases with that for group (b), using a one-sided permutation test of the group labels with
  1,000 permutations (`stats.dispersion_test`).
- **Match sets** (decided 2026-11-11; `openvsafe.analysis_set`). The main analysis uses every
  OpenVSafe match scoring at least 8 of 11, after dropping people whose report is shared
  (25,913 people). A sensitivity analysis repeats both Q3 tests on high-confidence matches
  only, meaning those at least 3 points ahead of the runner-up (23,925 people). Inference
  rests on the main analysis. Both are reported, and any difference in conclusion is stated.

**Q4.** Rates per 1,000 people for health-impact answers, medical care, and call-center cases,
for cases and each comparison group. Descriptive only.

**Attrition.** We bound case prevalence by assuming every eligible non-responder is well
(lower bound) or unwell (upper bound) (`stats.attrition_bounds`). Long-term response is also
reported by week-1 severity.

**Missing data.** Entries that cannot be linked to a dose or a survey are excluded and counted.
Redacted entries, marked (b)(6), are excluded and counted, with 12,543 expected. No imputation.

**Output and disclosure.** We publish only aggregates. Any cell with fewer than 10 distinct
people is suppressed. No output is broken down below the national level.

**Exploratory, labelled as such:** blind clustering of embeddings of all long-term free text,
taxonomy discovery, the menstrual, neurological and cardiac deep dives, and every theme that
fails the gate.

## 9. Attachments at filing

- `taxonomy/v1.0/` (frozen 2026-11-10; sha256 of `SHA256SUMS`:
  `7c3dad37944e6fb62839797daef1aba96d943106f22aad65353e397382c5307d`)
- the git commit hash of this repository at filing
- `config/analysis.yaml`
- `data/raw/MANIFEST.tsv`
- `docs/preregistration/prior-knowledge.md`
- `docs/protocol.md`

## 10. Open items before filing

Done 2026-11-10: taxonomy frozen as v1.0 (the pipeline now reads it). Decided 2026-11-11: Q3 drops VAERS reports matched to more than one person; high-confidence matches only as a sensitivity analysis. Decided 2026-11-10: gold-set split 1,000 / 1,000; LCA exploratory; the Q2 onset test as
above; OpenVSafe's VAERS matches; `pre_vaccine` entries dropped, third-party entries kept.

1. Done 2026-11-11: OpenVSafe's matches read from its person pages (see Data).
2. Add gold-set coders and other contributors as authors (section 2).
3. Rotate the NanoGPT and Anthropic API keys before any full-corpus labelling.
4. File on OSF, then set `osf_registration` in `config/analysis.yaml`.
