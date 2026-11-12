"""DuckDB result helpers that work on duckdb 1.x and 2.x.

duckdb 2.0 removed `.pl()` from execute() results and refuses new work on a connection
while a result is unfinished, so every query here is fetched to completion.
"""

from __future__ import annotations

import polars as pl


def frame(con, sql: str) -> pl.DataFrame:
    rel = con.sql(sql)
    tbl = rel.to_arrow_table() if hasattr(rel, "to_arrow_table") else rel.arrow()
    return pl.from_arrow(tbl)


def one(con, sql: str):
    """First row (fully fetched), or None."""
    rows = con.execute(sql).fetchall()
    return rows[0] if rows else None
