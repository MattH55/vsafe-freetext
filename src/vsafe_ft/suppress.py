"""Minimum-cell rule: applied to every table and JSON that leaves the analysis machine.

A row is suppressed when any of its people columns (`people`, or any column ending in
`_people`) is under the threshold; every numeric cell in that row is then nulled.
"""

from __future__ import annotations

import polars as pl

from . import config

FORBIDDEN = {"registrant", "text", "text_orig", "zip3", "state", "response_id",
             "survey_static_id", "entry_id"}


def people_columns(df: pl.DataFrame, people_col: str = "people") -> list[str]:
    cols = [c for c in df.columns if c == people_col or c.endswith("_people")]
    if not cols:
        raise ValueError(f"No people column ('{people_col}' or '*_people') in table")
    return cols


def suppress(df: pl.DataFrame, people_col: str = "people", min_people: int | None = None) -> pl.DataFrame:
    """Null out every numeric cell in rows where any distinct-people count is under the threshold."""
    k = min_people if min_people is not None else config.analysis()["min_cell_people"]
    small = pl.any_horizontal([pl.col(c).fill_null(0) < k for c in people_columns(df, people_col)])
    numeric = [c for c, t in df.schema.items() if t.is_numeric()]
    return df.with_columns(
        [pl.when(small).then(None).otherwise(pl.col(c)).alias(c) for c in numeric]
        + [small.alias("suppressed")]
    )


def assert_safe(df: pl.DataFrame, people_col: str = "people") -> None:
    k = config.analysis()["min_cell_people"]
    for c in people_columns(df, people_col):
        bad = df.filter(pl.col(c).is_not_null() & (pl.col(c) < k))
        if bad.height:
            raise ValueError(f"{bad.height} rows below the minimum cell of {k} people in '{c}'")
    forbidden = FORBIDDEN & {c.lower() for c in df.columns}
    if forbidden:
        raise ValueError(f"Identifying or text columns present in an output table: {forbidden}")


def safe(df: pl.DataFrame, people_col: str = "people") -> pl.DataFrame:
    """suppress + assert_safe in one step; returns the suppressed table."""
    out = suppress(df, people_col)
    assert_safe(out, people_col)
    return out
