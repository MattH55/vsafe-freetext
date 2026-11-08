"""Step 8: per-theme aggregates. Reads classified entries, writes suppressed tables only.

Time-based tables (by survey type or by days since dose) report themes per 1,000 check-ins
of that survey type / dose-time bin, never raw entry counts, because survey cadence differs
by orders of magnitude between day-0..7 and 3-12 months.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import polars as pl

from . import config
from .db import frame, one
from .suppress import assert_safe, suppress

# (label, lowest day, highest day) inclusive; anything else -> NULL (pre-dose or > 400 days)
DAYS_BINS = [("0", 0, 0), ("1-7", 1, 7), ("8-42", 8, 42), ("43-120", 43, 120),
             ("121-240", 121, 240), ("241-400", 241, 400)]
DIMENSIONS = ["dose_number", "manufacturer", "age_band", "survey_type", "days_since_dose_bin"]
TIME_DIMENSIONS = {"survey_type", "days_since_dose_bin"}


def days_bin_sql(col: str = "days_since_dose") -> str:
    whens = " ".join(f"WHEN {col} BETWEEN {lo} AND {hi} THEN '{lab}'" for lab, lo, hi in DAYS_BINS)
    return f"CASE {whens} ELSE NULL END"


def days_bin(days: int | None) -> str | None:
    if days is None:
        return None
    return next((lab for lab, lo, hi in DAYS_BINS if lo <= days <= hi), None)


def build_themed(con, source: str = "entries_survey") -> None:
    """View joining entry_themes to the linked entries, with the dose-time bin."""
    con.execute(
        f"""
        CREATE OR REPLACE VIEW themed AS
        SELECT t.theme, t.layer, e.*, {days_bin_sql("e.days_since_dose")} AS days_since_dose_bin
        FROM entry_themes t JOIN {source} e USING (entry_id)
        """
    )


def build_checkin_denominators(con) -> None:
    """checkin_denominators(survey_type, days_since_dose_bin, grouping_id, checkins, people).

    grouping_id 1 = per survey type, 2 = per dose-time bin.

    Dose time for a check-in needs the check-in date (`started_on` in the check-in mapping);
    without it days_since_dose_bin is NULL and only survey-type denominators are usable.
    """
    has_date = one(con, 
        "SELECT count(*) FROM checkins WHERE started_on IS NOT NULL")[0] > 0
    if has_date:
        con.execute(
            f"""
            CREATE OR REPLACE TABLE checkin_denominators AS
            WITH c AS (
                SELECT h.survey_type, h.registrant,
                       {days_bin_sql("date_diff('day', x.vax_date, TRY_CAST(h.started_on AS DATE))")}
                           AS days_since_dose_bin
                FROM checkins h
                ASOF LEFT JOIN vax x
                  ON h.registrant = x.registrant AND TRY_CAST(h.started_on AS DATE) >= x.vax_date
            )
            SELECT survey_type, days_since_dose_bin,
                   GROUPING(survey_type, days_since_dose_bin) AS grouping_id,
                   count(*) AS checkins, count(DISTINCT registrant) AS checkin_people
            FROM c GROUP BY GROUPING SETS ((survey_type), (days_since_dose_bin))
            """
        )
    else:
        con.execute(
            """
            CREATE OR REPLACE TABLE checkin_denominators AS
            SELECT survey_type, NULL::VARCHAR AS days_since_dose_bin, 1 AS grouping_id,
                   count(*) AS checkins, count(DISTINCT registrant) AS checkin_people
            FROM checkins GROUP BY survey_type
            """
        )


def theme_table(con, by: list[str]) -> pl.DataFrame:
    keys = ", ".join(["theme", *by])
    df = frame(con, 
        f"""
        SELECT {keys},
               count(DISTINCT registrant) AS people,
               count(DISTINCT entry_id) AS entries,
               avg(CASE WHEN medical_care IS NOT NULL AND medical_care <> '' THEN 1 ELSE 0 END)
                   AS medical_care_rate
        FROM themed
        GROUP BY {keys}
        """
    )
    time_dims = [d for d in by if d in TIME_DIMENSIONS]
    if not time_dims:
        return df
    if len(time_dims) > 1:
        raise ValueError("One time dimension per table (denominators are marginal)")
    d = time_dims[0]
    gid = 1 if d == "survey_type" else 2      # GROUPING(): bit set = column rolled up
    den = frame(con, 
        f"SELECT {d}, checkins FROM checkin_denominators WHERE grouping_id = {gid}"
    )
    return (
        df.join(den, on=d, how="left")
        .with_columns((pl.col("entries") * 1000 / pl.col("checkins")).alias("per_1000_checkins"))
        .drop("entries", "checkins")     # time-based tables carry rates, never raw counts
    )


def write_aggregates(con, out_dir: Path | None = None) -> dict[str, str]:
    out_dir = out_dir or config.DATA_DIR / "aggregates"
    out_dir.mkdir(parents=True, exist_ok=True)
    build_themed(con)
    checksums = {}
    for by in [[], *[[d] for d in DIMENSIONS]]:
        name = "theme" + ("_by_" + by[0] if by else "")
        df = suppress(theme_table(con, by))
        assert_safe(df)
        path = out_dir / f"{name}.csv"
        df.write_csv(path)
        checksums[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (out_dir / "SHA256SUMS").write_text(
        "".join(f"{h}  {n}\n" for n, h in sorted(checksums.items())))
    return checksums
