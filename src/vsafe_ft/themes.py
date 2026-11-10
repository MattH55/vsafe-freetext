"""Layer-1 wiring: build `entry_themes` and `entry_flags` from the lexicon.

Rule 5 of the phase-1 brief: before the OSF registration exists, only week-1 and six-week
entries may be classified. `exploratory_filter_sql` enforces that and `build_entry_themes`
refuses long-term text until `osf_registration` is set in config/analysis.yaml.
Text is read into this process only; nothing here prints or returns text.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl

from . import config
from .classify.lexicon import Lexicon
from .db import frame
from .suppress import safe

LONG_TERM_PATTERN = r"(?i)(\b(3|6|12|three|six|twelve)\s*-?\s*(m|mo|mon|month)s?\b)|(\byear)"
TAXONOMY = config.REPO_ROOT / "taxonomy" / "v1.0" / "themes.yaml"   # frozen 2026-11-10


def exploratory_filter_sql(alias: str = "e") -> str:
    """SQL predicate: entry is from a matched week-1 or six-week check-in."""
    max_day = int(config.analysis()["exploratory_max_survey_day"])
    return (
        f"{alias}.survey_matched"
        f" AND TRY_CAST({alias}.survey_day AS INTEGER) BETWEEN 0 AND {max_day}"
        f" AND NOT regexp_matches(coalesce({alias}.survey_type, ''), '{LONG_TERM_PATTERN}')"
    )


def registration_filed() -> bool:
    return bool(config.analysis().get("osf_registration"))


def build_entry_themes(con, lexicon: Lexicon | None = None, *, long_term: bool = False,
                       source: str = "entries_survey", batch: int = 50_000) -> int:
    """Classify entries with layer 1 into entry_themes(entry_id, theme, confidence, layer, method)
    and entry_flags(entry_id, third_party, pre_vaccine). Returns the number of entries classified.
    """
    if long_term and not registration_filed():
        raise PermissionError(
            "Long-term (3/6/12-month) free text may not be classified before the OSF "
            "registration exists (set osf_registration in config/analysis.yaml)."
        )
    lexicon = lexicon or Lexicon.load(TAXONOMY)
    where = "TRUE" if long_term else exploratory_filter_sql("e")
    con.execute("CREATE OR REPLACE TABLE entry_themes (entry_id BIGINT, theme VARCHAR, "
                "confidence DOUBLE, layer INTEGER, method VARCHAR)")
    con.execute("CREATE OR REPLACE TABLE entry_flags (entry_id BIGINT, third_party BOOLEAN, "
                "pre_vaccine BOOLEAN)")
    n, last = 0, -1
    while True:
        page = frame(con, f"""SELECT e.entry_id, e.text FROM {source} e
                              WHERE ({where}) AND e.entry_id > {last}
                              ORDER BY e.entry_id LIMIT {int(batch)}""")
        if page.height == 0:
            break
        ids, texts = page["entry_id"].to_list(), page["text"].to_list()
        last = ids[-1]
        th = {"entry_id": [], "theme": [], "confidence": [], "layer": [], "method": []}
        fl = {"entry_id": [], "third_party": [], "pre_vaccine": []}
        for i, t in zip(ids, texts):
            labels, flags = lexicon.classify(t or "")
            for lab in labels:
                th["entry_id"].append(i)
                th["theme"].append(lab.theme)
                th["confidence"].append(lab.confidence)
                th["layer"].append(lab.layer)
                th["method"].append(lab.method)
            fl["entry_id"].append(i)
            fl["third_party"].append(flags["third_party"])
            fl["pre_vaccine"].append(flags["pre_vaccine"])
        _append(con, "entry_themes", pl.DataFrame(th, schema={
            "entry_id": pl.Int64, "theme": pl.String, "confidence": pl.Float64,
            "layer": pl.Int32, "method": pl.String}))
        _append(con, "entry_flags", pl.DataFrame(fl, schema={
            "entry_id": pl.Int64, "third_party": pl.Boolean, "pre_vaccine": pl.Boolean}))
        n += len(ids)
    return n


def _append(con, table: str, df: pl.DataFrame) -> None:
    if df.height:
        con.register("_batch", df.to_arrow())
        con.execute(f"INSERT INTO {table} SELECT * FROM _batch")
        con.unregister("_batch")


def lexicon_coverage(con, source: str = "entries_survey") -> pl.DataFrame:
    """Share of classified entries with >= 1 theme, by field (suppressed)."""
    df = frame(con, 
        f"""
        SELECT e.field, count(*) AS entries, count(DISTINCT e.registrant) AS people,
               count(t.entry_id) AS themed_entries,
               count(DISTINCT CASE WHEN t.entry_id IS NOT NULL THEN e.registrant END)
                   AS themed_people,
               count(t.entry_id) / count(*) AS share_themed
        FROM {source} e
        SEMI JOIN entry_flags f ON f.entry_id = e.entry_id
        LEFT JOIN (SELECT DISTINCT entry_id FROM entry_themes) t ON t.entry_id = e.entry_id
        GROUP BY ROLLUP (e.field) ORDER BY e.field NULLS LAST
        """
    ).with_columns(pl.col("field").fill_null("all"))
    return safe(df)


def theme_counts(con, source: str = "entries_survey") -> pl.DataFrame:
    """People and entries per theme and field among classified entries (suppressed)."""
    df = frame(con, 
        f"""
        SELECT t.theme, e.field, count(DISTINCT t.entry_id) AS entries,
               count(DISTINCT e.registrant) AS people
        FROM entry_themes t JOIN {source} e USING (entry_id)
        GROUP BY ALL ORDER BY ALL
        """
    )
    return safe(df)


def flag_counts(con, source: str = "entries_survey") -> pl.DataFrame:
    df = frame(con, 
        f"""
        SELECT e.field,
               count(*) FILTER (WHERE f.third_party) AS third_party_entries,
               count(DISTINCT e.registrant) FILTER (WHERE f.third_party) AS third_party_people,
               count(*) FILTER (WHERE f.pre_vaccine) AS pre_vaccine_entries,
               count(DISTINCT e.registrant) FILTER (WHERE f.pre_vaccine) AS pre_vaccine_people
        FROM entry_flags f JOIN {source} e USING (entry_id) GROUP BY ALL ORDER BY ALL
        """
    )
    return safe(df)


def taxonomy_domains(path: Path = TAXONOMY) -> dict[str, str]:
    import yaml

    spec = yaml.safe_load(path.read_text())
    return {t: body.get("domain", "") for t, body in spec["themes"].items()}
