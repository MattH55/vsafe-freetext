"""Aggregate-only exploration for taxonomy discovery (phase 1, step 4.3-4.4).

Every function returns counts over many people. N-grams are kept only when at least
`min_cell_people` distinct registrants used them, so no single entry can be read back.
"""

from __future__ import annotations

import polars as pl

from .classify.lexicon import Lexicon
from .db import frame
from .suppress import safe
from .themes import exploratory_filter_sql

_STOP_TEXT = """
a about after again all am an and any are as at be been before being but by can could did do
does doing don't down during each few for from further had has have having he her here hers
him his how i i'm i've if in into is it it's its just me more most my no nor not now of off on
once only or other our out over own same she should so some such than that the their them then
there these they this those through to too under until up very was we were what when where
which while who whom why will with would you your also got get like still since day days
"""
STOPWORDS = frozenset(_STOP_TEXT.split())
_STOP_SQL = "[" + ", ".join("'" + w.replace("'", "''") + "'" for w in sorted(STOPWORDS)) + "]"


def candidate_ngrams(con, n_max: int = 3, top: int = 300, source: str = "entries_survey",
                     min_people: int | None = None) -> pl.DataFrame:
    """Frequent 1..n_max-grams in exploratory entries the lexicon left unlabelled.

    Returns ngram, n, entries, people (people >= min_cell_people), most people first.
    """
    from . import config

    k = min_people or config.analysis()["min_cell_people"]
    df = frame(con, 
        f"""
        WITH u AS (
            SELECT e.entry_id, e.registrant,
                   list_filter(regexp_split_to_array(lower(e.text), '[^a-z'']+'),
                               lambda x: length(x) > 1) AS toks
            FROM {source} e
            WHERE {exploratory_filter_sql("e")}
              AND e.entry_id IN (SELECT entry_id FROM entry_flags)
              AND e.entry_id NOT IN (SELECT entry_id FROM entry_themes)
        ),
        p AS (
            SELECT entry_id, registrant, toks, n, unnest(range(1, len(toks) - n + 2)) AS i
            FROM u, (SELECT unnest(range(1, {int(n_max)} + 1)) AS n)
            WHERE len(toks) >= n
        ),
        g AS (SELECT entry_id, registrant, n, toks[i : i + n - 1] AS gram FROM p)
        SELECT array_to_string(gram, ' ') AS ngram, n,
               count(DISTINCT entry_id) AS entries, count(DISTINCT registrant) AS people,
               list_has_all({_STOP_SQL}, gram) AS all_stop
        FROM g GROUP BY ALL HAVING count(DISTINCT registrant) >= {int(k)}
        """
    )
    df = (df.filter(~pl.col("all_stop")).drop("all_stop")
            .sort(["people", "ngram"], descending=[True, False]).head(top))
    return safe(df)


def text_length_profile(con, source: str = "entries_survey") -> pl.DataFrame:
    """Share of exploratory entries by length band and field (aggregate description only)."""
    df = frame(con, 
        f"""
        SELECT e.field,
               CASE WHEN length(e.text) < 20 THEN '<20' WHEN length(e.text) < 50 THEN '20-49'
                    WHEN length(e.text) < 200 THEN '50-199' ELSE '200+' END AS length_chars,
               count(*) AS entries, count(DISTINCT e.registrant) AS people
        FROM {source} e WHERE {exploratory_filter_sql("e")}
        GROUP BY ALL ORDER BY ALL
        """
    )
    return safe(df)


def meddra_theme_map(con, lexicon: Lexicon) -> pl.DataFrame:
    """theme -> MedDRA PT list, from terms seen in the CDC coding file.

    A PT maps to a theme when the lexicon matches the PT name or any LLT coded under it.
    Only PTs coded for >= min_cell_people people are listed. SOC/HLGT are carried when the
    coding file has them (columns `soc`/`hlgt` on the `meddra` table), else left blank.
    """
    from . import config

    k = config.analysis()["min_cell_people"]
    cols = {r[0] for r in con.execute("DESCRIBE meddra").fetchall()}
    soc = "any_value(soc)" if "soc" in cols else "NULL"
    hlgt = "any_value(hlgt)" if "hlgt" in cols else "NULL"
    terms = con.execute(
        f"""
        SELECT pt, list(DISTINCT llt) AS llts, {soc} AS soc, {hlgt} AS hlgt,
               count(DISTINCT registrant) AS people
        FROM meddra WHERE pt IS NOT NULL GROUP BY pt HAVING count(DISTINCT registrant) >= {k}
        """
    ).fetchall()
    rows = []
    for pt, llts, s, h, _ in terms:
        hits = set()
        for name in [pt, *(llts or [])]:
            hits |= {lab.theme for lab in lexicon.classify(str(name))[0]}
        rows += [{"theme": t, "soc": s or "", "hlgt": h or "", "pt": pt} for t in hits]
    return pl.DataFrame(rows, schema={"theme": pl.String, "soc": pl.String, "hlgt": pl.String,
                                      "pt": pl.String}).unique().sort(["theme", "pt"])
