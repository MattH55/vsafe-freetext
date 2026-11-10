"""Gold set: stratified draw, blind coder sheets, inter-coder agreement, adjudication, and
precision/recall of each classifier layer against the adjudicated codes.

Design (docs/protocol.md, Validation):
- Entries are drawn per stratum (field x period x layer-1 themed/unthemed) in a stable hash
  order; half the target goes equally to every stratum, half in proportion to its size. Each
  entry carries a weight (stratum entries / entries drawn) so P/R estimate the population.
- Coders see each distinct text once, in their own shuffled order, without any classifier
  output. Codes for a text apply to every gold entry with that text.
- Sheets and codes stay in <DATA_DIR>/gold_set/ (gitignored); only suppressed aggregates
  (kappa, P/R) leave it.
- Rule 5: the long-term period is drawn only after the OSF registration exists, and
  `evaluate` (classifier P/R) refuses to run before it, so no gold-set result can tune the
  taxonomy or the classifiers pre-registration. Coder agreement (kappa) is about the coders,
  not the classifier, and may run earlier.
"""

from __future__ import annotations

import csv
import hashlib
import random
from pathlib import Path

import polars as pl

from . import config
from .db import frame, one
from .suppress import safe
from .themes import LONG_TERM_PATTERN, exploratory_filter_sql, registration_filed

FLAGS = ("third_party", "pre_vaccine")
FIELDS = ("SD", "SRO", "HCVO")
GOLD_DDL = """CREATE TABLE IF NOT EXISTS gold_entries (
    entry_id BIGINT, registrant VARCHAR, field VARCHAR, period VARCHAR, layer1 BOOLEAN,
    stratum VARCHAR, weight DOUBLE, text_hash VARCHAR, drawn_seed INTEGER)"""
CODES_DDL = """CREATE TABLE IF NOT EXISTS gold_codes (
    text_hash VARCHAR, coder VARCHAR, label VARCHAR, value BOOLEAN)"""


def gold_dir() -> Path:
    return config.DATA_DIR / "gold_set"


def labels(themes: list[str]) -> list[str]:
    return list(themes) + list(FLAGS)


def _period_sql(period: str, alias: str = "e") -> str:
    if period == "early":
        return exploratory_filter_sql(alias)
    if period == "long_term":
        return (f"{alias}.survey_matched AND regexp_matches(coalesce({alias}.survey_type, ''), "
                f"'{LONG_TERM_PATTERN}')")
    raise ValueError(f"period must be 'early' or 'long_term', not {period!r}")


def allocate(pop: dict[str, int], size: int) -> dict[str, int]:
    """Half of `size` equally across strata, half in proportion to stratum size; each capped
    at its population, with any shortfall redistributed to strata that still have room."""
    strata = [s for s, n in pop.items() if n > 0]
    total = sum(pop[s] for s in strata)
    if not strata:
        return {}
    want = {s: size / 2 / len(strata) + size / 2 * pop[s] / total for s in strata}
    alloc = {s: min(pop[s], round(want[s])) for s in strata}
    while (short := size - sum(alloc.values())) > 0:
        room = [s for s in strata if alloc[s] < pop[s]]
        if not room:
            break
        for s in sorted(room, key=lambda s: -pop[s])[:short]:
            alloc[s] += 1
    while (extra := sum(alloc.values()) - size) > 0:      # rounding overshoot
        for s in sorted(strata, key=lambda s: -alloc[s])[:extra]:
            alloc[s] -= 1
    return alloc


def draw(con, *, size: int, period: str = "early", seed: int = 1,
         source: str = "entries_survey") -> dict:
    """Draw `size` gold entries for one period into gold_entries. Refuses to redraw a period."""
    if period == "long_term" and not registration_filed():
        raise PermissionError("The long-term gold set may not be drawn before the OSF "
                              "registration exists (osf_registration in config/analysis.yaml).")
    con.execute(GOLD_DDL)
    if one(con, f"SELECT count(*) FROM gold_entries WHERE period = '{period}'")[0]:
        raise FileExistsError(f"gold_entries already holds the {period} draw; it is never redrawn.")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE gold_pool AS
        SELECT e.entry_id, e.registrant, e.field, md5(e.text) AS text_hash,
               EXISTS (SELECT 1 FROM entry_themes t WHERE t.entry_id = e.entry_id) AS layer1,
               hash(concat_ws('|', e.response_id, e.field, 'gold', '{int(seed)}')) AS h
        FROM {source} e
        WHERE ({_period_sql(period)}) AND NOT coalesce(e.redacted, false)
          AND length(trim(coalesce(e.text, ''))) > 0""")
    con.execute("""CREATE OR REPLACE TEMP TABLE gold_pool2 AS SELECT *,
        field || '|' || CASE WHEN layer1 THEN 'themed' ELSE 'unthemed' END AS stratum
        FROM gold_pool""")
    pop = dict(con.execute("SELECT stratum, count(*) FROM gold_pool2 GROUP BY 1").fetchall())
    alloc = allocate(pop, size)
    for s, k in alloc.items():
        w = pop[s] / k if k else None
        con.execute(f"""INSERT INTO gold_entries
            SELECT entry_id, registrant, field, '{period}', layer1, '{period}|' || stratum,
                   {w}, text_hash, {int(seed)}
            FROM gold_pool2 WHERE stratum = ? ORDER BY h LIMIT {int(k)}""", [s])
    n, texts = one(con, f"""SELECT count(*), count(DISTINCT text_hash) FROM gold_entries
                            WHERE period = '{period}'""")
    return {"period": period, "entries": n, "distinct_texts": texts, "strata": len(alloc)}


def _texts(con, source: str) -> pl.DataFrame:
    """One row per distinct gold text: stable id, a field and the text itself."""
    return frame(con, f"""
        WITH g AS (SELECT text_hash, min(entry_id) AS entry_id FROM gold_entries GROUP BY 1)
        SELECT g.text_hash, e.field, e.text FROM g JOIN {source} e USING (entry_id)
        ORDER BY g.text_hash""")


def text_id(text_hash: str) -> str:
    return "g" + text_hash[:10]


def write_sheet(con, coder: str, themes: list[str], *, source: str = "entries_survey",
                out: Path | None = None, rows: pl.DataFrame | None = None,
                prefill: dict[str, dict] | None = None) -> Path:
    """Blind coding sheet for one coder (its own shuffled order). Cells: 1 = present, blank = no."""
    df = rows if rows is not None else _texts(con, source)
    order = list(range(df.height))
    random.Random(int(hashlib.md5(coder.encode()).hexdigest(), 16)).shuffle(order)
    out = out or gold_dir() / f"sheet_{coder}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = labels(themes)
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "field", "text", *cols, "unsure", "note"])
        for i in order:
            r = df.row(i, named=True)
            pre = (prefill or {}).get(r["text_hash"], {})
            w.writerow([text_id(r["text_hash"]), r["field"], r["text"],
                        *[pre.get(c, "") for c in cols], "", ""])
    return out


def _truthy(v: str) -> bool | None:
    v = (v or "").strip().lower()
    if v in ("", "0", "n", "no", "false"):
        return False
    if v in ("1", "x", "y", "yes", "true"):
        return True
    return None


def load_codes(con, path: Path, coder: str, themes: list[str]) -> dict:
    """Read a completed sheet into gold_codes (replacing that coder's codes)."""
    con.execute(CODES_DDL)
    ids = {text_id(h): h for (h,) in
           con.execute("SELECT DISTINCT text_hash FROM gold_entries").fetchall()}
    cols = labels(themes)
    rows, bad = [], 0
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        missing = set(cols) - set(rd.fieldnames or [])
        if missing:
            raise ValueError(f"sheet lacks columns: {sorted(missing)}")
        for r in rd:
            h = ids.get(r["id"])
            if h is None:
                raise ValueError(f"unknown id in sheet: {r['id']}")
            for c in cols:
                v = _truthy(r[c])
                if v is None:
                    bad += 1
                    continue
                rows.append((h, coder, c, v))
    if bad:
        raise ValueError(f"{bad} cells are neither blank/0 nor 1/x; fix the sheet and reload")
    con.execute("DELETE FROM gold_codes WHERE coder = ?", [coder])
    con.executemany("INSERT INTO gold_codes VALUES (?, ?, ?, ?)", rows)
    return {"coder": coder, "texts": len({r[0] for r in rows}), "cells": len(rows)}


def kappa(a: list[bool], b: list[bool]) -> float | None:
    n = len(a)
    if not n:
        return None
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def agreement(con, coder_a: str, coder_b: str) -> pl.DataFrame:
    """Per label: Cohen's kappa between two coders over texts both coded (suppressed)."""
    df = frame(con, f"""
        SELECT a.label, a.text_hash, a.value AS va, b.value AS vb
        FROM gold_codes a JOIN gold_codes b USING (text_hash, label)
        WHERE a.coder = '{coder_a}' AND b.coder = '{coder_b}'""")
    ppl = frame(con, f"""
        SELECT c.label, count(DISTINCT g.registrant) AS people
        FROM gold_codes c JOIN gold_entries g USING (text_hash)
        WHERE c.coder IN ('{coder_a}', '{coder_b}') AND c.value GROUP BY 1""")
    out = []
    for (lab,), d in df.group_by(["label"], maintain_order=True):
        va, vb = d["va"].to_list(), d["vb"].to_list()
        out.append({"label": lab, "texts": d.height, "a_positive": sum(va),
                    "b_positive": sum(vb), "both_positive": sum(x and y for x, y in zip(va, vb)),
                    "kappa": kappa(va, vb)})
    res = pl.DataFrame(out, schema={"label": pl.Utf8, "texts": pl.Int64, "a_positive": pl.Int64,
                                    "b_positive": pl.Int64, "both_positive": pl.Int64,
                                    "kappa": pl.Float64})
    res = res.join(ppl, on="label", how="left").with_columns(pl.col("people").fill_null(0))
    return safe(res.sort("label"))


def write_adjudication(con, coder_a: str, coder_b: str, themes: list[str], *,
                       source: str = "entries_survey", out: Path | None = None) -> Path:
    """Sheet of texts the coders disagree on: agreed cells prefilled, disputed cells '?'."""
    d = frame(con, f"""
        SELECT a.text_hash, a.label, a.value = b.value AS agree, a.value
        FROM gold_codes a JOIN gold_codes b USING (text_hash, label)
        WHERE a.coder = '{coder_a}' AND b.coder = '{coder_b}'""")
    disputed = set(d.filter(~pl.col("agree"))["text_hash"].to_list())
    pre: dict[str, dict] = {}
    for r in d.filter(pl.col("text_hash").is_in(list(disputed))).iter_rows(named=True):
        pre.setdefault(r["text_hash"], {})[r["label"]] = (
            "?" if not r["agree"] else ("1" if r["value"] else ""))
    t = _texts(con, source).filter(pl.col("text_hash").is_in(list(disputed)))
    return write_sheet(con, "adjudication", themes, source=source,
                       out=out or gold_dir() / "sheet_adjudication.csv", rows=t, prefill=pre)


CONSENSUS_SQL = """
    SELECT a.text_hash, a.label,
           coalesce(j.value, CASE WHEN a.value = b.value THEN a.value END) AS value
    FROM gold_codes a JOIN gold_codes b USING (text_hash, label)
    LEFT JOIN gold_codes j ON j.text_hash = a.text_hash AND j.label = a.label
         AND j.coder = 'adjudication'
    WHERE a.coder = '{a}' AND b.coder = '{b}'"""


def evaluate(con, coder_a: str, coder_b: str, *, layer: str, model: str | None = None,
             period: str | None = None) -> pl.DataFrame:
    """Weighted per-label precision and recall of a layer against the consensus codes.

    layer = 'lexicon' (entry_themes / entry_flags) or 'llm' (llm_labels for `model`).
    Refuses before the OSF registration: gold-set results may not tune anything earlier.
    """
    if not registration_filed():
        raise PermissionError("Classifier precision/recall on the gold set is computed only "
                              "after the OSF registration exists (docs/preregistration).")
    from .classify.llm import PROMPT_VERSION

    if layer == "lexicon":
        pred = """SELECT entry_id, theme AS label FROM entry_themes
                  UNION ALL SELECT entry_id, 'third_party' FROM entry_flags WHERE third_party
                  UNION ALL SELECT entry_id, 'pre_vaccine' FROM entry_flags WHERE pre_vaccine"""
    elif layer == "llm":
        pred = f"""WITH l AS (SELECT * FROM llm_labels WHERE model = '{model}'
                              AND prompt_version = '{PROMPT_VERSION}' AND ok)
                   SELECT g.entry_id, unnest(l.themes) AS label FROM gold_entries g
                   JOIN l USING (text_hash)
                   UNION ALL SELECT g.entry_id, 'third_party' FROM gold_entries g
                   JOIN l USING (text_hash) WHERE l.third_party
                   UNION ALL SELECT g.entry_id, 'pre_vaccine' FROM gold_entries g
                   JOIN l USING (text_hash) WHERE l.pre_vaccine"""
    else:
        raise ValueError("layer must be 'lexicon' or 'llm'")
    where = f"AND g.period = '{period}'" if period else ""
    p = config.analysis()
    df = frame(con, f"""
        WITH c AS ({CONSENSUS_SQL.format(a=coder_a, b=coder_b)}),
        pr AS (SELECT DISTINCT entry_id, label FROM ({pred})),
        x AS (SELECT c.label, g.registrant, g.weight, c.value AS gold,
                     pr.entry_id IS NOT NULL AS predicted
              FROM gold_entries g JOIN c USING (text_hash)
              LEFT JOIN pr ON pr.entry_id = g.entry_id AND pr.label = c.label
              WHERE c.value IS NOT NULL {where})
        SELECT label,
               count(DISTINCT registrant) FILTER (WHERE gold OR predicted) AS people,
               count(*) FILTER (WHERE gold) AS gold_entries,
               round(sum(weight) FILTER (WHERE gold AND predicted)
                     / nullif(sum(weight) FILTER (WHERE predicted), 0), 3) AS precision,
               round(sum(weight) FILTER (WHERE gold AND predicted)
                     / nullif(sum(weight) FILTER (WHERE gold), 0), 3) AS recall
        FROM x GROUP BY label ORDER BY label""")
    df = df.with_columns(((pl.col("precision") >= p["theme_precision_gate"])
                          & (pl.col("recall") >= p["theme_recall_gate"])).alias("passes_gate"))
    out = safe(df)
    return out.with_columns(pl.when(pl.col("suppressed")).then(None)
                            .otherwise(pl.col("passes_gate")).alias("passes_gate"))


def strata_summary(con) -> pl.DataFrame:
    """Gold entries per stratum with weights (aggregate, suppressed)."""
    return safe(frame(con, """
        SELECT stratum, count(*) AS entries, count(DISTINCT text_hash) AS texts,
               count(DISTINCT registrant) AS people, round(any_value(weight), 2) AS weight
        FROM gold_entries GROUP BY 1 ORDER BY 1"""))
