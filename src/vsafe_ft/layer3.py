"""Layer-3 wiring: sample entries, label unique texts with the LLM, store and compare labels.

Labels are cached per (md5 of normalised text, model, prompt version) in `llm_labels`, so an
identical text is sent once and a re-link does not resend anything. Only week-1 / six-week
entries are eligible until the OSF registration exists (brief rule 5). Nothing here prints
or returns text; outputs are counts, and every aggregate goes through suppress.safe.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import polars as pl

from . import config
from .classify.llm import PROMPT_VERSION, has_pii
from .db import frame, one
from .suppress import safe
from .themes import LONG_TERM_PATTERN, exploratory_filter_sql, registration_filed

LABELS_DDL = """CREATE TABLE IF NOT EXISTS llm_labels (
    text_hash VARCHAR, model VARCHAR, prompt_version VARCHAR, themes VARCHAR[],
    third_party BOOLEAN, pre_vaccine BOOLEAN, ok BOOLEAN, labelled_at TIMESTAMP)"""
AMENDMENT_2_MODELS = {"deepseek/deepseek-v4.1-flash"}
RUNS_DDL = """CREATE TABLE IF NOT EXISTS llm_runs (
    started_at TIMESTAMP, model VARCHAR, prompt_version VARCHAR, texts INTEGER,
    skipped_pii INTEGER, failed INTEGER, requests INTEGER, tokens BIGINT, cost_usd DOUBLE,
    seconds DOUBLE)"""


def candidate_sql(*, sample: int | None, seed: int, residue_only: bool, long_term: bool = False,
                  source: str = "entries_survey") -> str:
    """Entries in the sample (stable hash order on response id + field), with text hash.

    long_term=False: week-1 / six-week entries; long_term=True: 3-, 6- and 12-month entries
    only (after registration). sample=None takes every eligible entry."""
    where = (f"e.survey_matched AND regexp_matches(coalesce(e.survey_type, ''), "
             f"'{LONG_TERM_PATTERN}')" if long_term else exploratory_filter_sql("e"))
    residue = ("AND NOT EXISTS (SELECT 1 FROM entry_themes t WHERE t.entry_id = e.entry_id)"
               if residue_only else "")
    return f"""
        SELECT e.entry_id, e.registrant, e.field, md5(e.text) AS text_hash, e.text
        FROM {source} e
        WHERE ({where}) AND NOT coalesce(e.redacted, false)
          AND length(trim(coalesce(e.text, ''))) > 0 {residue}
        ORDER BY hash(concat_ws('|', e.response_id, e.field, '{int(seed)}'))
        {"" if sample is None else f"LIMIT {int(sample)}"}"""


def label_entries(con, labeller, *, sample: int | None, seed: int = 1, residue_only: bool = False,
                  batch: int = 20, max_usd: float = 5.0, long_term: bool = False,
                  source: str = "entries_survey", log=print, workers: int = 1) -> dict:
    """Label the unique texts of a sample of entries; returns run counts (no text)."""
    if long_term and not registration_filed():
        raise PermissionError("Long-term free text may not be labelled before the OSF "
                              "registration exists (osf_registration in config/analysis.yaml).")
    if long_term and labeller.model in AMENDMENT_2_MODELS and not config.analysis().get("amendment_2"):
        raise PermissionError(f"{labeller.model} labels long-term text only after amendment 2 is "
                              "filed (amendment_2 in config/analysis.yaml).")
    con.execute(LABELS_DDL)
    con.execute(RUNS_DDL)
    model = labeller.model
    con.execute(f"CREATE OR REPLACE TEMP TABLE llm_sample AS "
                f"{candidate_sql(sample=sample, seed=seed, residue_only=residue_only, long_term=long_term, source=source)}")
    todo = frame(con, f"""
        SELECT text_hash, any_value(text) AS text FROM llm_sample s
        WHERE NOT EXISTS (SELECT 1 FROM llm_labels l WHERE l.text_hash = s.text_hash
                          AND l.model = '{model}' AND l.prompt_version = '{PROMPT_VERSION}'
                          AND l.ok)
        GROUP BY text_hash ORDER BY text_hash""")
    hashes, texts = todo["text_hash"].to_list(), todo["text"].to_list()
    del todo
    pii = [has_pii(t) for t in texts]
    send = [(h, t) for h, t, p in zip(hashes, texts, pii) if not p]
    t0, failed, done = time.time(), 0, 0
    started = time.strftime("%Y-%m-%d %H:%M:%S")
    chunks = [send[k:k + batch] for k in range(0, len(send), batch)]
    pool = ThreadPoolExecutor(max_workers=max(1, workers))
    try:
        for w in range(0, len(chunks), max(1, workers)):   # one wave of parallel requests
            if labeller.cost_usd >= max_usd:
                log(f"stopping: cost cap ${max_usd:.2f} reached")
                break
            wave = chunks[w:w + max(1, workers)]
            results = list(pool.map(lambda c: labeller.label([t for _, t in c]), wave))
            for chunk, res in zip(wave, results):
                rows = [(h, model, PROMPT_VERSION, r["themes"] if r else [],
                         bool(r and r["third_party"]), bool(r and r["pre_vaccine"]), r is not None)
                        for (h, _), r in zip(chunk, res)]
                failed += sum(1 for r in res if r is None)
                con.executemany("INSERT INTO llm_labels VALUES (?, ?, ?, ?, ?, ?, ?, now())", rows)
                done += len(chunk)
                if (done // batch) % 25 == 0:
                    log(f"{done}/{len(send)} texts, ${labeller.cost_usd:.3f}, {time.time() - t0:.0f}s")
    finally:
        pool.shutdown(wait=True)
    run = {"model": model, "prompt_version": PROMPT_VERSION,
           "sample_entries": one(con, "SELECT count(*) FROM llm_sample")[0],
           "unique_texts_to_label": len(hashes), "texts_sent": done,
           "skipped_pii": sum(pii), "failed": failed, "requests": labeller.requests,
           "tokens": labeller.tokens, "cost_usd": round(labeller.cost_usd, 4),
           "refusals": getattr(labeller, "refusals", 0),
           "seconds": round(time.time() - t0)}
    con.execute("INSERT INTO llm_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [started, model, PROMPT_VERSION, done, run["skipped_pii"], failed,
                 labeller.requests, labeller.tokens, labeller.cost_usd, run["seconds"]])
    return run


def _labelled_entries(model: str, source: str, sample: dict | None = None) -> str:
    """Exploratory entries whose text has an ok label from `model`.

    With `sample` (the candidate_sql arguments of a run: sample, seed, residue_only), only the
    entries of that run's sample; otherwise every entry sharing a labelled text, which weights
    the result towards frequent short texts.
    """
    in_sample = ""
    where = exploratory_filter_sql("e")
    if sample:
        in_sample = f"AND e.entry_id IN (SELECT entry_id FROM ({candidate_sql(source=source, **sample)}))"
        if sample.get("long_term"):     # a registered long-term sample (after registration)
            where = (f"e.survey_matched AND regexp_matches(coalesce(e.survey_type, ''), "
                     f"'{LONG_TERM_PATTERN}')")
    return f"""
        SELECT e.entry_id, e.registrant, e.field, l.themes AS llm_themes
        FROM {source} e
        JOIN llm_labels l ON l.text_hash = md5(e.text) AND l.model = '{model}'
             AND l.prompt_version = '{PROMPT_VERSION}' AND l.ok
        WHERE {where} {in_sample}"""


def agreement(con, model: str, source: str = "entries_survey",
              sample: dict | None = None) -> pl.DataFrame:
    """Per theme, layer 1 vs layer 3 on the labelled entries: both / lexicon only / LLM only.

    Counts are entries and distinct people; all *_people cells are suppressed below k.
    """
    df = frame(con, f"""
        WITH s AS ({_labelled_entries(model, source, sample)}),
        llm AS (SELECT entry_id, registrant, unnest(llm_themes) AS theme FROM s),
        lex AS (SELECT t.entry_id, s.registrant, t.theme FROM entry_themes t
                JOIN s USING (entry_id)),
        j AS (SELECT coalesce(a.theme, b.theme) AS theme,
                     coalesce(a.entry_id, b.entry_id) AS entry_id,
                     coalesce(a.registrant, b.registrant) AS registrant,
                     a.entry_id IS NOT NULL AS in_lex, b.entry_id IS NOT NULL AS in_llm
              FROM lex a FULL JOIN llm b ON a.entry_id = b.entry_id AND a.theme = b.theme)
        SELECT theme,
               count(*) FILTER (WHERE in_lex AND in_llm) AS both_entries,
               count(DISTINCT registrant) FILTER (WHERE in_lex AND in_llm) AS both_people,
               count(*) FILTER (WHERE in_lex AND NOT in_llm) AS lex_only_entries,
               count(DISTINCT registrant) FILTER (WHERE in_lex AND NOT in_llm) AS lex_only_people,
               count(*) FILTER (WHERE in_llm AND NOT in_lex) AS llm_only_entries,
               count(DISTINCT registrant) FILTER (WHERE in_llm AND NOT in_lex) AS llm_only_people,
               round(count(*) FILTER (WHERE in_lex AND in_llm)
                     / nullif(count(*) FILTER (WHERE in_lex), 0), 3) AS share_lex_confirmed
        FROM j GROUP BY theme ORDER BY theme""")
    return safe(df)


def coverage(con, model: str, source: str = "entries_survey",
              sample: dict | None = None) -> pl.DataFrame:
    """Share of labelled entries with >= 1 theme from layer 1, layer 3, and either, by field."""
    df = frame(con, f"""
        WITH s AS ({_labelled_entries(model, source, sample)}),
        lx AS (SELECT DISTINCT entry_id FROM entry_themes)
        SELECT s.field, count(*) AS entries, count(DISTINCT s.registrant) AS people,
               round(avg((lx.entry_id IS NOT NULL)::INT), 3) AS share_layer1,
               round(avg((len(s.llm_themes) > 0)::INT), 3) AS share_layer3,
               round(avg((lx.entry_id IS NOT NULL OR len(s.llm_themes) > 0)::INT), 3)
                   AS share_either
        FROM s LEFT JOIN lx USING (entry_id)
        GROUP BY ROLLUP (s.field) ORDER BY s.field NULLS LAST""").with_columns(
        pl.col("field").fill_null("all"))
    return safe(df)


def model_shift(con, m1: str, m2: str, source: str = "entries_survey",
                sample: dict | None = None) -> pl.DataFrame:
    """Per theme, entries labelled by each model on texts both labelled; flags shifts above
    analysis.yaml model_shift_flag (relative to the larger count)."""
    flag = float(config.analysis()["model_shift_flag"])
    df = frame(con, f"""
        WITH a AS ({_labelled_entries(m1, source, sample)}),
             b AS ({_labelled_entries(m2, source, sample)}),
        both_ AS (SELECT a.entry_id, a.registrant, a.llm_themes AS t1, b.llm_themes AS t2
                  FROM a JOIN b USING (entry_id)),
        x AS (SELECT entry_id, registrant, unnest(t1) AS theme, 1 AS m FROM both_
              UNION ALL SELECT entry_id, registrant, unnest(t2), 2 FROM both_)
        SELECT theme,
               count(*) FILTER (WHERE m = 1) AS model1_entries,
               count(DISTINCT registrant) FILTER (WHERE m = 1) AS model1_people,
               count(*) FILTER (WHERE m = 2) AS model2_entries,
               count(DISTINCT registrant) FILTER (WHERE m = 2) AS model2_people
        FROM x GROUP BY theme ORDER BY theme""")
    if df.height:
        hi = pl.max_horizontal("model1_entries", "model2_entries")
        df = df.with_columns(
            (abs(pl.col("model1_entries") - pl.col("model2_entries")) / hi).round(3).alias("shift"),
        ).with_columns((pl.col("shift") > flag).alias("model_sensitive"))
    out = safe(df)
    if "model_sensitive" in out.columns:    # suppress() nulls numbers only: null the flag too
        out = out.with_columns(pl.when(pl.col("suppressed")).then(None)
                               .otherwise(pl.col("model_sensitive")).alias("model_sensitive"))
    return out
