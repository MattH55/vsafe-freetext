"""Steps 2-5 and 7: dedupe and link entries to person, dose, survey, MedDRA and outcomes.

All joins run in DuckDB over Parquet so the 5 GB check-in file is never loaded
into memory. Column names come from config/columns.yaml; the functions refuse
to run while any required column is still TODO.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from . import config


def connect(db: Path | None = None) -> duckdb.DuckDBPyConnection:
    db = db or config.DATA_DIR / "interim" / "vsafe.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(db))


def build_entries(con, parquet_glob: str) -> None:
    """Long format: one row per (check-in, field) with non-empty text; exact duplicates dropped."""
    c = config.columns("freetext")
    fields = {"SD": c["text_sd"], "SRO": c["text_sro"], "HCVO": c["text_hcvo"]}
    unions = "\nUNION ALL\n".join(
        f"""SELECT "{c['registrant']}" AS registrant, "{c['survey_static_id']}" AS survey_static_id,
                   "{c['response_id']}" AS response_id,
                   TRY_CAST("{c['started_on']}" AS TIMESTAMP) AS started_on,
                   '{f}' AS field, "{col}" AS text_orig,
                   _release, _row, _content_hash
            FROM read_parquet('{parquet_glob}') WHERE "{col}" IS NOT NULL AND trim("{col}") <> ''"""
        for f, col in fields.items()
    )
    con.execute(f"CREATE OR REPLACE TABLE entries_raw AS {unions}")
    con.execute(
        """
        CREATE OR REPLACE TABLE entries AS
        SELECT *,
               regexp_replace(trim(text_orig), '\\s+', ' ', 'g') AS text,
               regexp_matches(text_orig, '\\(\\s*[bB]\\s*\\)\\s*\\(\\s*6\\s*\\)') AS redacted,
               _release ILIKE '%under%3%' AS under3,
               count(*) OVER (PARTITION BY registrant, survey_static_id, field, text_orig) AS n_copies
        FROM entries_raw
        QUALIFY row_number() OVER (
            PARTITION BY registrant, survey_static_id, field, text_orig ORDER BY _release, _row) = 1
        """
    )


def link_dose(con, vaccinations_parquet: str) -> None:
    """days_since_dose = STARTED_ON - most recent vaccination at or before STARTED_ON (ASOF join)."""
    v = config.columns("vaccinations")
    max_days = config.analysis()["max_days_since_dose"]
    con.execute(
        f"""
        CREATE OR REPLACE TABLE vax AS
        SELECT "{v['registrant']}" AS registrant, TRY_CAST("{v['vaccination_date']}" AS DATE) AS vax_date,
               "{v['dose_number']}" AS dose_number, "{v['manufacturer']}" AS manufacturer,
               "{v['age_band']}" AS age_band
        FROM read_parquet('{vaccinations_parquet}')
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE entries_dose AS
        SELECT e.*, x.vax_date, x.dose_number, x.manufacturer, x.age_band,
               date_diff('day', x.vax_date, CAST(e.started_on AS DATE)) AS days_since_dose,
               x.vax_date IS NULL AS flag_before_any_dose,
               date_diff('day', x.vax_date, CAST(e.started_on AS DATE)) > {max_days} AS flag_beyond_window
        FROM entries e
        ASOF LEFT JOIN vax x
          ON e.registrant = x.registrant AND CAST(e.started_on AS DATE) >= x.vax_date
        """
    )


def link_survey(con, checkins_parquet: str) -> None:
    h = config.columns("health_checkins")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE entries_survey AS
        SELECT e.*, h."{h['survey_type']}" AS survey_type, h."{h['survey_day']}" AS survey_day,
               h."{h['medical_care']}" AS medical_care, h."{h['health_impact']}" AS health_impact,
               h."{h['survey_static_id']}" IS NOT NULL AS survey_matched
        FROM entries_dose e
        LEFT JOIN read_parquet('{checkins_parquet}') h
          ON e.survey_static_id = h."{h['survey_static_id']}"
        """
    )


def join_rates(con) -> dict[str, float]:
    """Gate-1 metrics: share of entries matched on registrant (dose) and survey keys."""
    row = con.execute(
        """SELECT avg(CASE WHEN NOT flag_before_any_dose THEN 1 ELSE 0 END),
                  avg(CASE WHEN survey_matched THEN 1 ELSE 0 END), count(*)
           FROM entries_survey"""
    ).fetchone()
    return {"dose_linked": row[0], "survey_matched": row[1], "n_entries": row[2]}
