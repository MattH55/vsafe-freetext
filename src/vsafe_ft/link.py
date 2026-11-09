"""Steps 2-5 and 7: dedupe and link entries to person, dose, survey, MedDRA and outcomes.

All joins run in DuckDB over Parquet so the 5 GB check-in file is never loaded
into memory. Column names come from config/columns.yaml; the functions refuse
to run while any column they use is still TODO.

Tables built here (inside the local DuckDB file only; none leaves the machine):
  entries         one row per de-duplicated (registrant, survey, field, text); entry_id
  entries_dose    + most recent dose (ASOF join)
  entries_survey  + check-in answers
  entry_meddra    entry_id x MedDRA codes, every release kept with its label
  entry_outcomes  entry_id -> call-center cases / VAERS filing within the outcome window
`zip3` is never selected from the registrant file, so it cannot reach any of them.
Report functions (meddra_coverage, crosscheck, duplicate_report) return tables that
have already been through suppress + assert_safe.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl

from . import config
from .db import frame, one
from .normalise import is_redacted, normalise
from .suppress import safe

FIELDS = ("SD", "SRO", "HCVO")


def connect(db: Path | None = None) -> duckdb.DuckDBPyConnection:
    db = db or config.DATA_DIR / "interim" / "vsafe.duckdb"
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    register_udfs(con)
    return con


def register_udfs(con) -> None:
    """Expose normalise.py to SQL so there is a single definition of normalisation."""
    for name, fn, ret in [("vsafe_normalise", normalise, "VARCHAR"),
                          ("vsafe_is_redacted", is_redacted, "BOOLEAN")]:
        try:
            con.create_function(name, fn, ["VARCHAR"], ret, side_effects=False)
        except duckdb.CatalogException:
            pass  # already registered on this connection


def _q(col: str) -> str:
    return '"' + col.replace('"', '""') + '"'


def _s(val: str) -> str:
    return "'" + str(val).replace("'", "''") + "'"


# --------------------------------------------------------------------------- entries

def build_entries(con, parquet_glob: str) -> None:
    """Long format: one row per (check-in, field) with non-empty text; exact duplicates dropped.

    `text_orig` is the cell as delivered. `text` is normalise(text_orig); `redacted` is
    is_redacted(text_orig); both come from normalise.py. `under3` comes from the explicit
    `under3: true` flag in config/sources.yaml (column `_under3`, set at ingest).
    """
    register_udfs(con)
    c = config.columns("freetext", keys=["registrant", "survey_static_id", "response_id",
                                         "started_on", "text_sd", "text_sro", "text_hcvo"])
    cols = {"SD": c["text_sd"], "SRO": c["text_sro"], "HCVO": c["text_hcvo"]}
    unions = "\nUNION ALL\n".join(
        f"""SELECT {_q(c['registrant'])} AS registrant,
                   {_q(c['survey_static_id'])} AS survey_static_id,
                   {_q(c['response_id'])} AS response_id,
                   TRY_CAST({_q(c['started_on'])} AS TIMESTAMP) AS started_on,
                   '{f}' AS field, {_q(col)} AS text_orig,
                   _release, _row, _content_hash, coalesce(_under3, false) AS under3
            FROM read_parquet({_s(parquet_glob)}, union_by_name = true)
            WHERE {_q(col)} IS NOT NULL AND trim({_q(col)}) <> ''"""
        for f, col in cols.items()
    )
    con.execute(f"CREATE OR REPLACE TABLE entries_raw AS {unions}")
    con.execute(
        """
        CREATE OR REPLACE TABLE entries AS
        WITH d AS (
            SELECT *,
                   count(*) OVER (PARTITION BY registrant, survey_static_id, field, text_orig)
                       AS n_copies
            FROM entries_raw
            QUALIFY row_number() OVER (
                PARTITION BY registrant, survey_static_id, field, text_orig
                ORDER BY under3, _release, _row) = 1
        )
        SELECT row_number() OVER (ORDER BY _release, _row, field) AS entry_id,
               *,
               vsafe_normalise(text_orig) AS text,
               vsafe_is_redacted(text_orig) AS redacted
        FROM d
        """
    )


def link_registrants(con, registrants_parquet: str) -> None:
    """Add sex, relationship, guardian and registration_date to `entries` (zip3 never read).

    The guardian column holds another registrant's code, so only a boolean is kept.
    """
    keep = ["sex", "relationship", "guardian", "registration_date"]
    r = config.columns("registrants", keys=["registrant", *keep])
    g = _q(r["guardian"])
    sel = ", ".join(
        f"({g} IS NOT NULL AND trim({g}) <> '') AS guardian" if k == "guardian"
        else f"{_q(r[k])} AS {k}" for k in keep)
    con.execute(
        f"""
        CREATE OR REPLACE TABLE registrants AS
        SELECT {_q(r['registrant'])} AS registrant, {sel}
        FROM read_parquet({_s(registrants_parquet)}, union_by_name = true)
        QUALIFY row_number() OVER (PARTITION BY {_q(r['registrant'])}) = 1
        """
    )
    prior = [k for k in [*keep, "registrant_matched"] if _has(con, "entries", k)]
    exclude = f"EXCLUDE ({', '.join(prior)})" if prior else ""
    con.execute(
        f"""
        CREATE OR REPLACE TABLE entries AS
        SELECT e.* {exclude}, {", ".join(f"r.{k}" for k in keep)},
               r.registrant IS NOT NULL AS registrant_matched
        FROM entries e LEFT JOIN registrants r USING (registrant)
        """
    )


def _has(con, table: str, col: str) -> bool:
    return col in [r[0] for r in con.execute(f"DESCRIBE {table}").fetchall()]


def link_dose(con, vaccinations_parquet: str) -> None:
    """days_since_dose = STARTED_ON - most recent vaccination at or before STARTED_ON (ASOF join)."""
    v = config.columns("vaccinations", keys=["registrant", "vaccination_date", "dose_number",
                                             "manufacturer"])
    max_days = config.analysis()["max_days_since_dose"]
    age = (_q(v["age_band"]) if v.get("age_band") not in (None, "TODO")
           else "NULL::VARCHAR")           # the v-safe vaccinations file has no age column
    con.execute(
        f"""
        CREATE OR REPLACE TABLE vax AS
        SELECT {_q(v['registrant'])} AS registrant,
               TRY_CAST({_q(v['vaccination_date'])} AS DATE) AS vax_date,
               {_q(v['dose_number'])} AS dose_number, {_q(v['manufacturer'])} AS manufacturer,
               {age} AS age_band
        FROM read_parquet({_s(vaccinations_parquet)}, union_by_name = true)
        """
    )
    con.execute(
        f"""
        CREATE OR REPLACE TABLE entries_dose AS
        SELECT e.*, x.vax_date, x.dose_number, x.manufacturer, x.age_band,
               date_diff('day', x.vax_date, CAST(e.started_on AS DATE)) AS days_since_dose,
               x.vax_date IS NULL AS flag_before_any_dose,
               date_diff('day', x.vax_date, CAST(e.started_on AS DATE)) > {max_days}
                   AS flag_beyond_window
        FROM entries e
        ASOF LEFT JOIN vax x
          ON e.registrant = x.registrant AND CAST(e.started_on AS DATE) >= x.vax_date
        """
    )


# The v-safe check-in files have no survey-type column. Survey type is derived from DAYS_SINCE
# (days since the vaccination the check-in belongs to): daily check-ins days 0-7, weekly to
# week 6, then 3-, 6- and 12-month surveys. PROVISIONAL bins: confirm against the DAYS_SINCE
# distribution (aggregate counts only) before relying on them.
def survey_type_from_days(col: str) -> str:
    d = f"TRY_CAST({col} AS INTEGER)"
    return (f"CASE WHEN {d} BETWEEN 0 AND 7 THEN 'day ' || {d} "
            f"WHEN {d} BETWEEN 8 AND 42 THEN 'week ' || ceil({d} / 7.0)::INTEGER "
            f"WHEN {d} BETWEEN 43 AND 135 THEN '3m' WHEN {d} BETWEEN 136 AND 270 THEN '6m' "
            f"WHEN {d} BETWEEN 271 AND 450 THEN '12m' ELSE NULL END")


def load_checkins(con, checkins_parquet: str) -> None:
    """Canonical `checkins` table, one row per survey_static_id."""
    h = config.columns("health_checkins", keys=["registrant", "survey_static_id", "survey_day",
                                                "medical_care", "health_impact"])
    opt = ", ".join(
        f"{_q(h[k])} AS {k}" if h.get(k) not in (None, "TODO") else f"NULL::VARCHAR AS {k}"
        for k in ["health_now", "started_on", "tested_positive", "pregnant"]
    )
    stype = (_q(h["survey_type"]) if h.get("survey_type") not in (None, "TODO")
             else survey_type_from_days(_q(h["survey_day"])))
    con.execute(
        f"""
        CREATE OR REPLACE TABLE checkins AS
        SELECT {_q(h['survey_static_id'])} AS survey_static_id, {_q(h['registrant'])} AS registrant,
               {stype} AS survey_type, {_q(h['survey_day'])} AS survey_day,
               {_q(h['medical_care'])} AS medical_care, {_q(h['health_impact'])} AS health_impact,
               {opt}
        FROM read_parquet({_s(checkins_parquet)}, union_by_name = true)
        QUALIFY row_number() OVER (PARTITION BY {_q(h['survey_static_id'])}) = 1
        """
    )


def link_survey(con, checkins_parquet: str | None = None) -> None:
    if checkins_parquet is not None:
        load_checkins(con, checkins_parquet)
    con.execute(
        """
        CREATE OR REPLACE TABLE entries_survey AS
        SELECT e.*, h.survey_type, h.survey_day, h.medical_care, h.health_impact, h.health_now,
               h.survey_static_id IS NOT NULL AS survey_matched
        FROM entries_dose e
        LEFT JOIN checkins h ON e.survey_static_id = h.survey_static_id
        """
    )


def join_rates(con) -> dict[str, float]:
    """Gate-1 metrics: share of entries matched on registrant (dose) and survey keys."""
    reg = "avg(CASE WHEN registrant_matched THEN 1 ELSE 0 END)" if _has(
        con, "entries_survey", "registrant_matched") else "NULL"
    row = one(con, 
        f"""SELECT avg(CASE WHEN NOT flag_before_any_dose THEN 1 ELSE 0 END),
                  avg(CASE WHEN survey_matched THEN 1 ELSE 0 END), count(*), {reg}
           FROM entries_survey"""
    )
    return {"dose_linked": row[0], "survey_matched": row[1], "n_entries": row[2],
            "registrant_matched": row[3]}


# --------------------------------------------------------------------------- MedDRA

def link_meddra(con, sources: list[tuple[str, str]],
                field_values: dict[str, str] | None = None) -> None:
    """Join CDC MedDRA codes to entries.

    The join key is (response_id, field) when the coding file has a response id (the
    2024-11 files do), else (registrant, date, field). `sources` is [(parquet glob, release
    label)]; every release is kept with its label. When the `field` column is null in
    config/columns.yaml the field is read from the file name carried in `_release`
    (`..._sd`, `..._sro`, `..._hcvo`). `field_values` maps other field codes to SD/SRO/HCVO.
    """
    parts = []
    for glob, label in sources:
        m = config.columns("meddra", keys=["registrant", "date", "pt", "llt"], release=label)
        field = (f"upper(trim({_q(m['field'])}))" if m.get("field") not in (None, "TODO")
                 else "upper(regexp_extract(_release, '_(sd|sro|hcvo)$', 1, 'i'))")
        rid = (f"{_q(m['response_id'])}" if m.get("response_id") not in (None, "TODO")
               else "NULL")
        active = f"{_q(m['active'])}" if m.get("active") not in (None, "TODO") else "NULL"
        parts.append(
            f"""SELECT {_q(m['registrant'])} AS registrant,
                       CAST({rid} AS VARCHAR) AS response_id,
                       TRY_CAST({_q(m['date'])} AS DATE) AS code_date,
                       {field} AS field_raw,
                       {_q(m['pt'])} AS pt, {_q(m['llt'])} AS llt,
                       CAST({active} AS VARCHAR) AS active, {_s(label)} AS meddra_release
                FROM read_parquet({_s(glob)}, union_by_name = true)"""
        )
    fmap = {k.upper(): v for k, v in (field_values or {}).items()}
    case = ("CASE field_raw " + " ".join(f"WHEN {_s(k)} THEN {_s(v)}" for k, v in fmap.items())
            + " ELSE field_raw END") if fmap else "field_raw"
    con.execute(
        f"CREATE OR REPLACE TABLE meddra AS SELECT *, {case} AS field "
        f"FROM ({' UNION ALL '.join(parts)})"
    )
    con.execute(
        """
        CREATE OR REPLACE TABLE entry_meddra AS
        SELECT e.entry_id, m.meddra_release, m.pt, m.llt, m.active
        FROM entries e
        JOIN meddra m
          ON m.field = e.field
         AND CASE WHEN m.response_id IS NOT NULL
                  THEN m.response_id = e.response_id AND m.registrant = e.registrant
                  ELSE m.registrant = e.registrant
                       AND m.code_date = CAST(e.started_on AS DATE) END
        """
    )


def meddra_coverage(con) -> pl.DataFrame:
    """Share of entries with >= 1 code, by entry release, field and MedDRA release (+ 'any')."""
    df = frame(con, 
        """
        WITH rel AS (SELECT DISTINCT meddra_release FROM meddra UNION ALL SELECT 'any'),
             hit AS (SELECT DISTINCT entry_id, meddra_release FROM entry_meddra
                     UNION SELECT DISTINCT entry_id, 'any' FROM entry_meddra)
        SELECT e._release AS release, e.field, r.meddra_release,
               count(*) AS entries,
               count(DISTINCT e.registrant) AS people,
               count(h.entry_id) AS coded_entries,
               count(DISTINCT CASE WHEN h.entry_id IS NOT NULL THEN e.registrant END)
                   AS coded_people,
               count(h.entry_id) / count(*) AS share_coded
        FROM entries e CROSS JOIN rel r
        LEFT JOIN hit h ON h.entry_id = e.entry_id AND h.meddra_release = r.meddra_release
        GROUP BY ALL ORDER BY ALL
        """
    )
    return safe(df)


# --------------------------------------------------------------------------- outcomes

TRUTHY = ("Y", "YES", "TRUE", "T", "1")


def link_outcomes(con, sources: list[tuple[str, str]], truthy: tuple[str, ...] = TRUTHY) -> None:
    """Call-center cases and VAERS filing within `outcome_window_days` after each entry.

    `sources` is [(parquet glob, label)] so the two FOIA files can map columns separately
    (`call_center_by_release` in columns.yaml).
    """
    window = int(config.analysis()["outcome_window_days"])
    parts = []
    for glob, label in sources:
        c = config.columns("call_center", keys=["registrant", "report_date", "vaers_filed"],
                           release=label)
        parts.append(
            f"""SELECT {_q(c['registrant'])} AS registrant,
                       TRY_CAST({_q(c['report_date'])} AS DATE) AS report_date,
                       upper(trim({_q(c['vaers_filed'])})) IN ({", ".join(map(_s, truthy))})
                           AS vaers_filed,
                       {_s(label)} AS cc_source
                FROM read_parquet({_s(glob)}, union_by_name = true)"""
        )
    con.execute(f"CREATE OR REPLACE TABLE call_center AS {' UNION ALL '.join(parts)}")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE entry_outcomes AS
        SELECT e.entry_id,
               count(c.registrant) AS cc_cases,
               coalesce(bool_or(c.vaers_filed), false) AS vaers_filed
        FROM entries e
        LEFT JOIN call_center c
          ON c.registrant = e.registrant
         AND c.report_date >= CAST(e.started_on AS DATE)
         AND c.report_date <= CAST(e.started_on AS DATE) + INTERVAL {window} DAY
        GROUP BY e.entry_id
        """
    )


# --------------------------------------------------------------------------- QA reports

ADDED_FIELDS = ("SURVEY_STATIC_ID", "RESPONSE_ID", "STARTED_ON")


def _data_cols(con, glob: str) -> list[str]:
    cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet({_s(glob)})").fetchall()
    return [c[0] for c in cols if not c[0].startswith("_")]


def crosscheck(con, original: Path, updated: Path, registrant_col: str,
               added: tuple[str, ...] = ADDED_FIELDS) -> tuple[pl.DataFrame, dict]:
    """Check each updated release == original + `added` fields, matching files by name.

    Returns (suppressed long table: release, metric, rows, people) and a dict of
    column-level differences per release (column names only).
    """
    rows, colinfo = [], {}
    for o in sorted(original.glob("*.parquet")):
        u = updated / o.name
        if not u.exists():
            colinfo[o.stem] = {"missing_updated_file": True}
            continue
        oc, uc = _data_cols(con, str(o)), _data_cols(con, str(u))
        colinfo[o.stem] = {
            "original_only": sorted(set(oc) - set(uc)),
            "updated_extra": sorted(set(uc) - set(oc) - set(added)),
            "added_present": sorted(set(added) & set(uc)),
        }
        shared = [c for c in oc if c in uc]
        key = "md5(concat_ws(chr(31), " + ", ".join(
            f"coalesce(CAST({_q(c)} AS VARCHAR), '')" for c in shared) + "))"
        reg = _q(registrant_col) if registrant_col in shared else "NULL"
        df = frame(con, 
            f"""
            WITH o AS (SELECT {key} AS k, {reg} AS reg FROM read_parquet({_s(str(o))})),
                 u AS (SELECT {key} AS k, {reg} AS reg FROM read_parquet({_s(str(u))})),
                 oc AS (SELECT k, reg, row_number() OVER (PARTITION BY k) AS i FROM o),
                 uc AS (SELECT k, reg, row_number() OVER (PARTITION BY k) AS i FROM u),
                 only_o AS (SELECT oc.* FROM oc ANTI JOIN uc USING (k, i)),
                 only_u AS (SELECT uc.* FROM uc ANTI JOIN oc USING (k, i))
            SELECT 'rows_original' AS metric, count(*) AS rows, count(DISTINCT reg) AS people FROM o
            UNION ALL SELECT 'rows_updated', count(*), count(DISTINCT reg) FROM u
            UNION ALL SELECT 'only_in_original', count(*), count(DISTINCT reg) FROM only_o
            UNION ALL SELECT 'only_in_updated', count(*), count(DISTINCT reg) FROM only_u
            """
        )
        rows.append(df.with_columns(pl.lit(o.stem).alias("release")))
    out = pl.concat(rows).select("release", "metric", "rows", "people") if rows else pl.DataFrame(
        schema={"release": pl.String, "metric": pl.String, "rows": pl.Int64, "people": pl.Int64})
    return safe(out), colinfo


def duplicate_report(con) -> pl.DataFrame:
    """Duplicates within a release, across releases, and between the under-3 file and the rest.

    Counts on `entries_raw` (before dedupe), keyed on (registrant, survey, field, text).
    """
    df = frame(con, 
        """
        WITH k AS (
            SELECT registrant, survey_static_id, field, text_orig, _release, under3,
                   count(*) AS n
            FROM entries_raw GROUP BY ALL
        ),
        per_key AS (
            SELECT registrant, survey_static_id, field, text_orig,
                   sum(n) AS copies,
                   count(DISTINCT _release) FILTER (WHERE NOT under3) AS main_releases,
                   bool_or(under3) AS in_u3, bool_or(NOT under3) AS in_main
            FROM k GROUP BY ALL
        )
        SELECT 'raw_rows' AS metric, sum(n)::BIGINT AS entries,
               count(DISTINCT registrant) AS people FROM k
        UNION ALL
        SELECT 'within_release_extra_copies', sum(n - 1)::BIGINT,
               count(DISTINCT registrant) FILTER (WHERE n > 1) FROM k
        UNION ALL
        SELECT 'keys_in_more_than_one_release', count(*),
               count(DISTINCT registrant) FROM per_key WHERE main_releases > 1
        UNION ALL
        SELECT 'keys_in_under3_and_main_files', count(*),
               count(DISTINCT registrant) FROM per_key WHERE in_u3 AND in_main
        UNION ALL
        SELECT 'extra_copies_removed', (sum(copies) - count(*))::BIGINT,
               count(DISTINCT registrant) FILTER (WHERE copies > 1) FROM per_key
        UNION ALL
        SELECT 'distinct_entries', count(*), count(DISTINCT registrant) FROM per_key
        """
    )
    return safe(df)
