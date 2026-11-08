"""Step 8: per-theme aggregates. Reads classified entries, writes suppressed tables only."""

from __future__ import annotations

import hashlib
from pathlib import Path

import polars as pl

from . import config
from .suppress import assert_safe, suppress

DIMENSIONS = ["dose_number", "manufacturer", "age_band", "survey_type", "days_since_dose_bin"]


def theme_table(con, by: list[str]) -> pl.DataFrame:
    keys = ", ".join(["theme", *by])
    return con.execute(
        f"""
        SELECT {keys},
               count(DISTINCT registrant) AS people,
               count(*) AS entries,
               avg(CASE WHEN medical_care IS NOT NULL AND medical_care <> '' THEN 1 ELSE 0 END) AS medical_care_rate
        FROM entry_themes
        GROUP BY {keys}
        """
    ).pl()


def write_aggregates(con, out_dir: Path | None = None) -> dict[str, str]:
    out_dir = out_dir or config.DATA_DIR / "aggregates"
    out_dir.mkdir(parents=True, exist_ok=True)
    checksums = {}
    for by in [[], *[[d] for d in DIMENSIONS]]:
        name = "theme" + ("_by_" + by[0] if by else "")
        df = suppress(theme_table(con, by))
        assert_safe(df.filter(~pl.col("suppressed")))
        path = out_dir / f"{name}.csv"
        df.write_csv(path)
        checksums[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (out_dir / "SHA256SUMS").write_text("".join(f"{h}  {n}\n" for n, h in sorted(checksums.items())))
    return checksums
