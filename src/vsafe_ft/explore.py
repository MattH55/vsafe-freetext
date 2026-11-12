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


def meddra_theme_map(con, lexicon: Lexicon, source: str = "entries_survey") -> pl.DataFrame:
    """theme -> MedDRA PT, from the dictionary terms CDC assigned to in-scope entries.

    Only codes on exploratory (week-1 / six-week) entries are used, so nothing is learnt from
    long-term check-ins before the registration. A PT maps to a theme when the lexicon matches
    the PT name or any LLT coded under it; only PTs coded for >= min_cell_people people are
    listed. Inputs and outputs are MedDRA dictionary terms, never participant text.
    """
    from . import config

    k = int(config.analysis()["min_cell_people"])
    terms = con.execute(
        f"""
        SELECT m.pt, list(DISTINCT m.llt) AS llts, count(DISTINCT e.registrant) AS people
        FROM entry_meddra m JOIN {source} e USING (entry_id)
        WHERE m.pt IS NOT NULL AND {exploratory_filter_sql("e")}
        GROUP BY m.pt HAVING count(DISTINCT e.registrant) >= {k}
        """
    ).fetchall()
    rows = []
    for pt, llts, people in terms:
        hits = set()
        for name in [pt, *(llts or [])]:
            hits |= {lab.theme for lab in lexicon.classify(str(name))[0]}
        rows += [{"theme": t, "pt": pt, "people": people} for t in hits]
    return (pl.DataFrame(rows, schema={"theme": pl.String, "pt": pl.String, "people": pl.Int64})
            .unique().sort(["theme", "people", "pt"], descending=[False, True, False]))


def theme_pt_cooccurrence(con, top: int = 5, source: str = "entries_survey") -> pl.DataFrame:
    """For each theme, the PTs most often coded on the same entries (precision check).

    Counts entries and people per (theme, PT) over exploratory entries; keeps the `top` PTs
    per theme by people, then suppresses cells under min_cell_people.
    """
    df = frame(con, f"""
        WITH x AS (
            SELECT t.theme, m.pt, count(DISTINCT e.entry_id) AS entries,
                   count(DISTINCT e.registrant) AS people
            FROM entry_themes t
            JOIN {source} e USING (entry_id)
            JOIN entry_meddra m USING (entry_id)
            WHERE {exploratory_filter_sql("e")}
            GROUP BY ALL
        ),
        tot AS (
            SELECT t.theme, count(DISTINCT t.entry_id) AS theme_entries
            FROM entry_themes t JOIN {source} e USING (entry_id)
            WHERE {exploratory_filter_sql("e")} GROUP BY ALL
        )
        SELECT x.theme, x.pt, x.entries, x.people,
               x.entries / tot.theme_entries AS share_of_theme_entries
        FROM x JOIN tot USING (theme)
        QUALIFY row_number() OVER (PARTITION BY x.theme ORDER BY x.people DESC, x.pt) <= {int(top)}
        ORDER BY x.theme, x.people DESC
    """)
    return safe(df)
