# v-safe free-text analysis

A reproducible whole-corpus classification of the 7,554,929 v-safe free-text entries,
validated against the CDC's own MedDRA coding. Every count is placed in time since dose
and linked to the person's survey answers, care-seeking and VAERS outcome.

**Lead question.** Is there a reproducible, persistent, multi-system symptom entity
consistent with PACVS in v-safe's long-term follow-up, and if so, why did it not surface
in VAERS-based surveillance? The study is designed so the null can win.
See [`docs/protocol.md`](docs/protocol.md).

> **No participant-level data is ever committed.** `data/` is gitignored except for
> placeholders. Only frozen aggregates that pass the minimum-cell rule (≥10 people)
> leave the analysis machine. See [`docs/data-use.md`](docs/data-use.md).

## Layout

```
config/            sources.yaml (files, hosts), columns.yaml (column mapping), analysis.yaml (fixed parameters)
docs/              protocol, data-use terms, open questions, pre-registration materials
taxonomy/v0/       draft themes + lexicon (frozen as v1.0 at the OSF registration)
src/vsafe_ft/
  ingest.py        1  .xlsx/.csv/.zip -> Parquet, with release, row index and content hash
  normalise.py     2  whitespace/encoding normalisation, (b)(6) redaction flag
  link.py          2-5,7  dedupe; ASOF join to most recent dose; survey join; join-rate gate
  classify/        6  layer 1 lexicon, layer 2 embeddings, layer 3 closed-list LLM
  themes.py        6  layer-1 entry_themes table, pre-registration guard
  explore.py          aggregate-only taxonomy discovery (n-grams, MedDRA theme map)
  aggregate.py     8  per-theme tables, rates per 1,000 check-ins, checksummed
  phenotype.py        PACVS-like case definition + comparison groups (SQL)
  stats.py            Q1 permutation test, attrition bounds
  suppress.py      minimum-cell rule and identifier guard on every output
  download.py      fetch + sha256 manifest
  cli.py           `vsafe-ft` command
scripts/           freeze_taxonomy.py (taxonomy/v0 -> v1.0 + SHA256SUMS)
tests/             unit tests (run without any real data)
data/              raw/, interim/, aggregates/  (gitignored)
```

## Quick start

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest
```

**Data directory.** Participant data must never sit in a cloud-synced folder (OneDrive,
Dropbox, iCloud): syncing would copy it off the machine. Set `VSAFE_DATA_DIR` to a local
path; `download`, `ingest`, `link` and the other data commands refuse to run when the data
directory is inside a OneDrive tree. It defaults to `./data`.

```bash
export VSAFE_DATA_DIR=/path/outside/any/synced/folder
vsafe-ft download                                   # resumable; writes $VSAFE_DATA_DIR/raw/MANIFEST.tsv
```

First contact with a release (phase 1):

```bash
vsafe-ft inspect $VSAFE_DATA_DIR/raw/freetext_updated/r01.xlsx   # header row only, never data rows
# fill the TODOs in config/columns.yaml
vsafe-ft ingest --part freetext_updated --only r01.xlsx           # .xlsx / .csv / .zip by file type
vsafe-ft ingest --part vaccinations
vsafe-ft ingest --part registrants
vsafe-ft ingest --part health_checkins
vsafe-ft link --release r01      # dedupe; registrant, dose, survey, MedDRA and outcome joins
vsafe-ft gate                    # gate 1: join rates >= 0.90
vsafe-ft classify                # layer-1 entry_themes; week-1/six-week only until OSF registration
vsafe-ft explore                 # n-grams used by >= 10 people, unlabelled entries only
vsafe-ft qa                      # duplicates, MedDRA coverage, original-vs-updated cross-check
```

Every table these commands print or write has been through `suppress` + `assert_safe`.

Optional extras: `pip install -e '.[embed]'` (layer 2), `pip install -e '.[llm]'` (layer 3).

## Phases and gates

| Phase | Work | Gate |
|---|---|---|
| 1 | Ingest + link one release; exploratory pass; draft taxonomy | Join rates ≥90% or documented reason |
| 2 | Freeze taxonomy v1.0; **OSF pre-registration** | Registered before any gold-set result tunes the classifier |
| 3 | Gold set (2,000 entries, double-coded); layer tuning | Per-theme precision and recall ≥0.85 for confirmatory themes |
| 4 | Full-corpus run; Q1–Q4; VAERS arm | Aggregates checksummed and tagged |
| 5 | Report, manuscript, website JSON from frozen aggregates | — |

## Status

Scaffold. Column names for every table are unconfirmed (`TODO` in `config/columns.yaml`);
the link steps refuse to run until they are set. Open items: [`docs/open-questions.md`](docs/open-questions.md).
