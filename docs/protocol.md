# V-safe Free-Text Analysis — Scoping Protocol

Nov 8, 2026 · Matthew Halma

## Purpose

Turn the 7.55 million v-safe free-text entries into a dated, person-linked, systematically
classified corpus, and report what people wrote that the check-box survey could not capture.
Existing work stops at keyword search with four hand-curated topics (OpenVSafe), qualitative
reading (*Cries for Help*), undated MedDRA codes without aggregation (CDC), or single-condition
LLM screens. The APPC/Penn position that the free text is not suited to systematic analysis is
the claim the manuscript tests directly.

The decisive fact: ICAN's updated free-text files carry `SURVEY_STATIC_ID`, `RESPONSE_ID` and
`STARTED_ON`, so each entry can be dated and tied to a check-in. The temporal dimension is unexplored.

## Data and join paths

| Part | Size | Role |
|---|---|---|
| Free text, updated (24-01322-FOIA), 12 releases + under-3 | ~635 MB | Primary corpus, 7,554,929 entries |
| Free text, original | ~330 MB | Cross-check |
| MedDRA codes (Jun 2023, Oct 2023, Nov 2024) | 845 MB | Validation; 30,987,860 codes |
| Registrants (+ race_ethnicity) | 218 MB | Denominators; 10,147,001 people |
| Vaccinations | 151 MB | Dose anchor |
| Health check-ins | 5 GB | Survey context; 151,847,152 check-ins |
| Call center (FOIA 23-00925, 23-00926) | 526 MB | Care-seeking, VAERS filing |
| Pregnancy registry survey | 4.7 MB | Pregnancy sub-analysis |

1. Free text → registrant → vaccinations: dose number, manufacturer, days since most recent dose.
2. Free text → `SURVEY_STATIC_ID` → check-ins: boxes ticked, severity, medical-care answer.
3. Free text → (registrant, date, field) → MedDRA: CDC coding of the same entry.
4. Registrant → call center → VAERS filing.
5. OpenVSafe's VAERS matches (score ≥8 of 11): used for Q3 (decided 2026-11-10); read from OpenVSafe's person pages 2026-11-11: 27,234 of 44,954 VAERS-filed people matched (`docs/phase1-report.md`). Reports matched to more than one person are dropped; Q3 is repeated on high-confidence matches as a sensitivity analysis (decided 2026-11-11).

## Research questions

**Primary.** Is there a reproducible, persistent, multi-system symptom entity consistent with
PACVS in v-safe's long-term follow-up, and if so, why did it not surface in VAERS?

**Null.** Free text at 3–12 months is an unstructured mix of background complaints: co-occurrence
no greater than expected from domain marginals; no onset-time or persistence pattern tied to dose.

| # | Sub-question | Evidence | Null-consistent result |
|---|---|---|---|
| Q1 Coherence | Do domains cluster in the same people beyond chance, reproducibly? | Co-occurrence network + LCA vs permutation null; stable across manufacturer, dose, age; replicated in VAERS narratives | Chance co-occurrence; unstable clusters |
| Q2 Natural history | Onset and persistence? | Time-to-onset from dated surveys; share reporting at 6 and 12 months; acute-onset vs de novo | Flat onset; persistence ≈ comparison groups |
| Q3 Detection failure | Did VAERS see these people, and as what? | Capture rate vs acute-event controls; MedDRA PT dispersion on matched reports | Similar capture; concentrated coding |
| Q4 Burden | What did it cost them? | Health-impact, medical-care, call-center cases vs comparisons | Impact ≈ comparison groups |

## Case definition (PACVS-like phenotype)

All of:
1. A completed 3-, 6- or 12-month survey with "health now" worse than baseline or a health-impact
   answer (unable to do normal activities, missed work/school, needed care).
2. Free text at that survey, or at ≥2 surveys, classified to ≥2 candidate symptom domains.
3. No free text or check-box at the same survey attributing symptoms to a named acute diagnosis
   or an unrelated cause (injury, pregnancy, infection).

Entries about something before vaccination do not count; entries about another person (a
dependant) do (decided 2026-11-10).

**Domains:** fatigue/PEM; cognitive; dysautonomia; sensory/neuropathic; sleep; pain;
gastrointestinal; menstrual change; cardiorespiratory (dyspnoea, chest tightness; added
2026-11-10). Implemented as themes in `taxonomy/`. Altered taste/smell is labelled but is not a
domain. Upper-respiratory symptoms (sore throat, congestion, cough) count as a criterion-3
exclusion (likely intercurrent infection).

| Element | Choice |
|---|---|
| Denominator | Registrants completing ≥1 long-term survey for a given dose |
| Comparison groups | (a) long-term completers with no symptoms; (b) acute diagnosed event; (c) severe week-1 text, reported recovery |
| Trajectory | Week-1 and six-week themes per case (immediate vs delayed onset) |
| Attrition | Long-term response by week-1 severity; prevalence bounded under all-well / all-unwell non-responders |
| Discovery arm | Blind clustering of embeddings of all long-term free text |
| Care-seeking | Medical-care answers and call-center cases |

**VAERS arm.** Share of cases with any VAERS report vs acute-event group; PT scatter on matched
reports; the same classifier applied to VAERS `SYMPTOM_TEXT` for COVID-19 vaccines (can start now).

## Pipeline

1. Ingest .xlsx → Parquet (release, row index, content hash). 2. Dedupe, normalise, flag (b)(6).
3. Link to dose (`days_since_dose`; flag pre-dose and >400 days). 4. Link to survey. 5. Link to MedDRA.
6. Classify (three layers). 7. Link to outcomes within 90 days. 8. Aggregate with minimum-cell rule
(<10 people suppressed). 9. Validate, checksum, tag. Downstream outputs read only frozen aggregates.

## Classification

| Layer | Method | Target coverage |
|---|---|---|
| 1 | Lexicon: MedDRA LLT strings, lay synonyms, negation | 50–70% |
| 2 | Sentence embeddings, nearest-centroid, clustering | 30–50% |
| 3 | Closed-list LLM on low-confidence residue and validation samples | 5–15% |

Taxonomy backbone: MedDRA SOC → HLGT, plus a lay layer (severity, duration/persistence, care sought,
work/school missed, pre-existing worsened, third-party events). Frozen and versioned before the full run.

**Validation:** 2,000-entry stratified gold set, double-coded, kappa and per-theme P/R per layer;
agreement with CDC coding; negation/attribution test set; second embedding model and second LLM
(themes shifting >20% flagged model-sensitive); OSF pre-registration.

## Gates

- Join rates for registrant and survey keys ≥90% or documented reason.
- Taxonomy v1.0 frozen and confirmatory analysis registered before gold-set results tune anything.
- Per-theme precision and recall ≥0.85 for every confirmatory theme (others exploratory).
- Aggregates checksummed and tagged. No full-corpus run before these pass.

## Limitations

Self-reported, unverified, self-selected smartphone population; descriptive only, no incidence or
causation. Survey cadence bias (report per 1,000 check-ins of that type); denominators from check-ins;
free text prompted by "other" boxes; 12,543 redacted entries; partial MedDRA coverage; classifier
error carried as P/R bounds; check-in and call-center records end mid-2023. No unvaccinated baseline;
SARS-CoV-2 infection only partly captured; imperfect 12-month recall.

## Outputs

Technical report (Quarto), manuscript (RECORD + TRIPOD-style NLP items; Drug Safety, Vaccine, JAMIA
or Open Research Europe), and a website theme explorer serving aggregate JSON only, linking to
OpenVSafe for entry-level search.
