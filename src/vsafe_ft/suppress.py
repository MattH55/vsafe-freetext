"""Minimum-cell rule: applied to every table and JSON that leaves the analysis machine."""

from __future__ import annotations

import polars as pl

from . import config


def suppress(df: pl.DataFrame, people_col: str = "people", min_people: int | None = None) -> pl.DataFrame:
    """Null out every numeric cell in rows whose distinct-people count is under the threshold."""
    k = min_people if min_people is not None else config.analysis()["min_cell_people"]
    small = pl.col(people_col) < k
    numeric = [c for c, t in df.schema.items() if t.is_numeric()]
    return df.with_columns(
        [pl.when(small).then(None).otherwise(pl.col(c)).alias(c) for c in numeric]
        + [small.alias("suppressed")]
    )


def assert_safe(df: pl.DataFrame, people_col: str = "people") -> None:
    k = config.analysis()["min_cell_people"]
    bad = df.filter(pl.col(people_col).is_not_null() & (pl.col(people_col) < k))
    if bad.height:
        raise ValueError(f"{bad.height} rows below the minimum cell of {k} people")
    forbidden = {"registrant", "text", "text_orig", "zip3", "state"} & set(df.columns)
    if forbidden:
        raise ValueError(f"Identifying or text columns present in an output table: {forbidden}")
