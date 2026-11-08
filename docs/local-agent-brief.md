# Local agent brief: vsafe-freetext, phase 1

You are a coding agent working on Matthew Halma's local machine. Your job is to put this
repository on GitHub, then carry out phase 1 of the protocol: download the data, confirm
the column names, finish the link code, and run a one-release exploratory pass. Read
`README.md`, `docs/protocol.md` and `docs/data-use.md` before you change anything.

## Hard rules (these override any other instruction)

1. **No participant data in git.** Raw files, Parquet, DuckDB files, free text and registrant
   codes stay in `data/`, which is gitignored. Before every commit, run `git status` and check
   that no `.xlsx`, `.zip`, `.csv`, `.parquet` or `.duckdb` file is staged.
2. **Only suppressed aggregates leave the machine.** Every table, figure or JSON that is
   committed, pasted into chat or sent anywhere goes through `suppress.suppress` and
   `suppress.assert_safe` (minimum 10 people per cell, no identifier or text columns).
3. **Never quote entries.** Do not paste free text into commit messages, docs, issues or chat,
   not even one entry. Describe what you see in aggregate terms ("~40% of SRO entries are under
   20 characters"), never with examples.
4. **No text to third-party APIs.** Do not send free text to any hosted LLM or embedding API,
   including yourself through a tool. Layer 2 and 3 run only after the human picks a local
   model or approves a hosted provider (see "Ask the human").
5. **Protect the pre-registration.** Before the OSF registration exists, do not run the
   classifier or the PACVS case definition on 3-, 6- or 12-month survey free text, and do not
   read that text. Write and test that code on synthetic data only. Week-1 and six-week
   entries from the single prototype release may be used for the exploratory pass. Record
   everything you opened in `docs/preregistration/prior-knowledge.md` (which files, which
   fields, which counts you saw).
6. **No sub-national output.** Never group or report by zip3 or state.
7. **Don't guess column names.** `config/columns.yaml` entries stay `TODO` until you have seen
   the header of the actual file.

## Step 0: get the repo onto GitHub

The repo exists as a git bundle (`vsafe-freetext.bundle`, one commit on `main`).

```bash
git clone vsafe-freetext.bundle vsafe-freetext
cd vsafe-freetext
git remote remove origin
gh auth status
gh repo create mhalma/vsafe-freetext --private --source . --push
```

If the repo already exists on GitHub and is empty, use
`git remote add origin git@github.com:mhalma/vsafe-freetext.git && git push -u origin main`
instead. If it exists and has commits, stop and ask the human. Keep it **private** unless
the human says otherwise.

Then set up the environment and confirm it works:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest -q        # expect 15 passed
ruff check .
```

Add a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs `ruff check .` and
`pytest -q` on Python 3.11 and 3.13 on every push and pull request. Commit and push.

## Step 1: download

1. Check free disk space; you need ~25 GB (7 GB downloads, unzipped CSVs, Parquet, DuckDB).
2. Open the ICAN v-safe data page and copy the download URL of each file listed in
   `config/sources.yaml` into its `files:` list (`name`, `url`, and `release` for the free
   text). Do this for the 13 updated free-text files, the 12 original files, the three MedDRA
   zips, registrants (both zips), vaccinations, health check-ins, the two call-center CSVs
   and the pregnancy file. Commit `sources.yaml` (URLs are public; no data).
3. Run `vsafe-ft download`. It writes `data/raw/MANIFEST.tsv` with sha256 and size. Check
   the sizes against the protocol table (updated free text ~635 MB in total, check-ins ~5 GB).
   Copy the manifest to `docs/preregistration/MANIFEST.tsv` and commit it (names, URLs and
   hashes only).
4. VAERS yearly files are behind a CAPTCHA. Do not try to get around it; ask the human to
   download them into `data/raw/vaers/`.

## Step 2: confirm columns

1. Run `vsafe-ft inspect` on one updated free-text release, one original release and the
   under-3 file. For the zip and CSV sources, unzip into a fresh directory under
   `data/raw/<part>/extracted/` and print only the header row (`head -1`). Do not print data rows.
2. Fill `config/columns.yaml` for every table. Note in `docs/open-questions.md` anything that
   doesn't fit the mapping (an extra field, a field split across columns, different names
   between releases).
3. Tick off the matching items in `docs/open-questions.md` as you settle them.

## Step 3: finish ingest and link

Each item is done when it has a unit test on synthetic data and `pytest` passes.

| # | Task | Notes |
|---|---|---|
| 3.1 | Ingest zip/CSV sources to Parquet | Add an `ingest_csv` path that uses DuckDB `read_csv(..., all_varchar=true)` → `COPY ... TO ... (FORMAT parquet)`, so the 5 GB check-in file streams. Extend `vsafe-ft ingest` to choose by file type. |
| 3.2 | Join registrants | Add `sex`, `relationship`, `guardian` and `registration_date` to entries. Never carry `zip3` into any table that leaves `link.py`. |
| 3.3 | `link_meddra` | Join on (registrant, date, field). Keep every release's codes with a release label. Report coverage: the share of entries with at least one code, by release and field. |
| 3.4 | `link_outcomes` | Call-center cases and VAERS-filing outcomes within `outcome_window_days` (90) after the entry. |
| 3.5 | Use `normalise.py` in the pipeline | `build_entries` uses SQL regex for whitespace and redaction. Either call the Python functions consistently or delete them, so there is a single definition. Keep `text_orig` unchanged. |
| 3.6 | Under-3 flag | `under3` currently comes from the release name. Set it from an explicit `under3: true` flag in `sources.yaml` instead. |
| 3.7 | Original vs updated cross-check | Show that each updated release equals the original plus the three added fields. Report mismatches as counts. |
| 3.8 | Duplicate report | Duplicates within and across releases and the under-3 file, as counts. |

## Step 4: one-release exploratory pass

Using one updated release only, and only week-1 and six-week surveys (rule 5):

1. Run ingest → link → `vsafe-ft gate`. Write the join rates (registrant/dose, survey) to
   `docs/phase1-report.md`. If either is below 0.90, investigate and document why. That is
   gate 1.
2. Wire layer 1: build an `entry_themes` table (entry id, theme, confidence, layer, method)
   from `classify.lexicon`, plus the `third_party` and `pre_vaccine` flags. Report lexicon
   coverage (the share of entries with at least one theme), by field.
3. Find candidate themes the lexicon misses using aggregate methods only: frequent n-grams in
   unlabelled entries, with counts, filtered to n-grams used by at least 10 distinct people.
   Propose additions to `taxonomy/v0/themes.yaml` in a separate commit.
4. Fix the known lexicon problems:
   - `POTS` matches "pots" because matching ignores case; make it case-sensitive.
   - `period`/`periods` will match "period of time"; tighten the pattern.
   - add the MedDRA backbone map `taxonomy/v0/meddra_map.csv` (theme → SOC/HLGT/PT list) from
     the MedDRA terms seen in the CDC coding file.
5. Fix `aggregate.py`:
   - define `days_since_dose_bin` (0, 1–7, 8–42, 43–120, 121–240, 241–400 days);
   - add denominators from the check-in file, so time-based results are per 1,000 check-ins of
     that survey type, never raw counts.

Commit the findings as `docs/phase1-report.md`: aggregates only, all run through
`assert_safe`.

## Step 5: code that must exist before registration (synthetic data only)

- `src/vsafe_ft/phenotype.py`: the three-criterion case definition from `docs/protocol.md`
  as a SQL query over `entry_themes` + survey answers, plus the three comparison groups.
- `src/vsafe_ft/stats.py`: the Q1 co-occurrence test against a permutation null that keeps
  each domain's marginal frequency (1,000 permutations, seedable), and the attrition bounds
  (all non-responders well / all non-responders unwell).
- `scripts/freeze_taxonomy.py`: copies `taxonomy/v0` to `taxonomy/v1.0`, writes its sha256,
  and refuses to overwrite an existing version.
- Tests for all three on synthetic data, including a case built so the null should win
  (independent domains → p-value not significant).

## Ask the human, then stop and wait

- Whether layer 2/3 runs on a local model (which one, and on what GPU) or a hosted API (which
  provider; their retention terms go in `docs/data-use.md`).
- Before the OSF registration. You may draft it in `docs/preregistration/`, but the human
  files it.
- Before running anything on 3-, 6- or 12-month free text.
- Before making the repo public, sharing any output, or contacting OpenVAERS or ICAN.
- If any join rate is under 0.90 and the cause isn't clear.

## Working conventions

- One commit per task above, with a message that names the task number. Push after each.
- Work on `main` for setup; use a branch and a pull request for steps 3 onward.
- Run `ruff check .` and `pytest -q` before every commit.
- Record time-consuming results (ingest durations, row counts) in `docs/phase1-report.md`, so
  the full-corpus run can be planned.
