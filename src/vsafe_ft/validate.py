"""Classifier validation against CDC's MedDRA coding (registration amendment 1).

Reference: an entry has theme T if CDC coded it to a PT that the frozen map
taxonomy/v1.0/meddra_map.csv lists for T. Evaluated on every long-term entry with at least
one active 2024-11 code, excluding redacted and pre-vaccine entries. Precision and recall per
theme with 95% Wilson intervals; a theme passes when both are >= the gate. Counts only; every
table goes through suppress.safe.
"""

from __future__ import annotations

import csv
import math

import polars as pl

from . import config
from .classify.llm import PROMPT_VERSION
from .db import frame
from .stats import _wilson, _z
from .suppress import safe
from .themes import LONG_TERM_PATTERN, registration_filed

MAP = config.REPO_ROOT / "taxonomy" / "v1.0" / "meddra_map.csv"
MEDDRA_RELEASE = "2024-11"
GATE = 0.85


def amendment_filed() -> bool:
    return bool(config.analysis().get("amendment_1"))


def _load_map(con, path=MAP) -> None:
    with open(path, encoding="utf-8", newline="") as f:
        rows = [(r["theme"], r["pt"]) for r in csv.DictReader(f)]
    con.execute("CREATE OR REPLACE TEMP TABLE v_map (theme VARCHAR, pt VARCHAR)")
    con.executemany("INSERT INTO v_map VALUES (?, ?)", rows)


def _predicted_sql(layer: str, model: str | None) -> str:
    lex = "SELECT entry_id, theme FROM entry_themes"
    if layer == "lexicon":
        return lex
    if layer != "final":
        raise ValueError("layer must be 'lexicon' or 'final'")
    return f"""{lex} UNION
        SELECT e.entry_id, unnest(l.themes) AS theme FROM ev e
        JOIN llm_labels l ON l.text_hash = md5(e.text) AND l.model = '{model}'
             AND l.prompt_version = '{PROMPT_VERSION}' AND l.ok"""


def meddra_reference(con, *, layer: str = "lexicon", model: str | None = None,
                     source: str = "entries_survey", map_path=MAP,
                     level: float = 0.95) -> pl.DataFrame:
    """Per theme: entries and people labelled, in the reference, and both; precision, recall
    (Wilson CIs) and whether the theme passes the gate. Refused until the amendment is filed."""
    if not (registration_filed() and amendment_filed()):
        raise PermissionError("Validation against MedDRA runs only after amendment 1 is filed "
                              "(amendment_1 in config/analysis.yaml).")
    if layer == "final" and not model:
        raise ValueError("layer='final' needs the layer-3 model name")
    _load_map(con, map_path)
    flags = ("AND NOT EXISTS (SELECT 1 FROM entry_flags f WHERE f.entry_id = e.entry_id "
             "AND f.pre_vaccine)")
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE ev AS
        SELECT e.entry_id, e.registrant, e.text FROM {source} e
        WHERE e.survey_matched AND regexp_matches(coalesce(e.survey_type, ''), '{LONG_TERM_PATTERN}')
          AND NOT coalesce(e.redacted, false) {flags}
          AND EXISTS (SELECT 1 FROM entry_meddra m WHERE m.entry_id = e.entry_id
                      AND m.meddra_release = '{MEDDRA_RELEASE}')""")
    df = frame(con, f"""
        WITH ref AS (SELECT DISTINCT m.entry_id, v.theme FROM entry_meddra m
                     JOIN ev USING (entry_id) JOIN v_map v ON v.pt = m.pt
                     WHERE m.meddra_release = '{MEDDRA_RELEASE}'),
             pred AS (SELECT DISTINCT p.entry_id, p.theme FROM ({_predicted_sql(layer, model)}) p
                      JOIN ev USING (entry_id)
                      WHERE p.theme IN (SELECT theme FROM v_map)),
             j AS (SELECT coalesce(r.entry_id, p.entry_id) AS entry_id,
                          coalesce(r.theme, p.theme) AS theme,
                          r.entry_id IS NOT NULL AS in_ref, p.entry_id IS NOT NULL AS in_pred
                   FROM ref r FULL JOIN pred p USING (entry_id, theme))
        SELECT j.theme,
               count(*) FILTER (WHERE in_pred) AS predicted_entries,
               count(DISTINCT ev.registrant) FILTER (WHERE in_pred) AS predicted_people,
               count(*) FILTER (WHERE in_ref) AS reference_entries,
               count(DISTINCT ev.registrant) FILTER (WHERE in_ref) AS reference_people,
               count(*) FILTER (WHERE in_ref AND in_pred) AS both_entries,
               count(DISTINCT ev.registrant) FILTER (WHERE in_ref AND in_pred) AS both_people
        FROM j JOIN ev USING (entry_id) GROUP BY j.theme ORDER BY j.theme""")
    z = _z(level)
    rows = []
    for r in df.iter_rows(named=True):
        tp, npred, nref = r["both_entries"], r["predicted_entries"], r["reference_entries"]
        p_lo, p_hi = _wilson(tp, npred, z) if npred else (math.nan, math.nan)
        r_lo, r_hi = _wilson(tp, nref, z) if nref else (math.nan, math.nan)
        prec = tp / npred if npred else None
        rec = tp / nref if nref else None
        rows.append({**r, "precision": prec, "precision_lo": p_lo, "precision_hi": p_hi,
                     "recall": rec, "recall_lo": r_lo, "recall_hi": r_hi,
                     "passes_gate": bool(prec is not None and rec is not None
                                         and prec >= GATE and rec >= GATE)})
    out = safe(pl.DataFrame(rows)) if rows else df
    if "passes_gate" in out.columns:    # suppress() nulls numbers only: null the flag too
        out = out.with_columns(pl.when(pl.col("suppressed")).then(None)
                               .otherwise(pl.col("passes_gate")).alias("passes_gate"))
    return out
