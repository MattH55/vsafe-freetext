"""Levi & Lu (2026) cohorts rebuilt from structured check-in answers (addendum 1, task 3.9), and
their overlap with the text-defined case definition (task 5.4). Not in the pre-registration.

Levi R, Lu N. Reporting on prolonged adverse health impact among V-SAFE enrollees. Research
Square, posted 25 Aug 2026, doi:10.21203/rs.3.rs-10768889/v1. Their rules (section 2.3):
  Prolonged-AE      at >= 1 monthly (3-, 6- or 12-month) survey, health vs before the last dose =
                    "Worse" AND attribution to vaccination = "Yes"; qualifying survey = the earliest
                    such survey by dose then month.
  Prolonged-NoAttr  "Worse" at >= 1 monthly survey and attribution never "Yes".
  Control           everyone else, including people with no monthly survey.
  Sub-cohorts       highest reported dose 1, 2, 3+.
  Population        enrollees aged 16 or older. No age field exists in the released files, so the
                    population here is every registrant in the adult check-in file (the under-3
                    file excluded); that difference is reported, not tuned away.

Canonical inputs (prepare() builds them from the raw files; tests build them directly):
  ll_checkins(registrant, dose_number, rnk, worse BOOLEAN, attributed VARCHAR)  monthly surveys only
  ll_people(registrant, sex, max_dose)
Counts only; every table goes through suppress.safe.
"""

from __future__ import annotations

import polars as pl

from . import config
from .db import frame
from .suppress import safe

TARGETS = {   # published in the preprint
    "enrollees": 9_904_924, "prolonged_ae": 185_285, "prolonged_ae_d1": 32_838,
    "prolonged_ae_d2": 100_564, "prolonged_ae_d3plus": 51_883, "prolonged_noattr": 189_982,
    "prolonged_noattr_d1": 18_710, "prolonged_noattr_d2": 81_462, "prolonged_noattr_d3plus": 89_810,
    "control": 9_529_657, "women_prolonged_ae": 137_430, "women": 6_141_800,
}


def prepare(con) -> dict:
    """ll_checkins and ll_people from the raw adult check-in file, ph_rank (survey rank and dose
    per check-in) and the registrants and vax tables."""
    glob = str(config.DATA_DIR / "interim" / "health_checkins" / "*.parquet").replace("\\", "/")
    con.execute(f"""CREATE OR REPLACE TABLE ll_checkins AS
        SELECT r.registrant, r.dose_number, r.rnk,
               s.HEALTH_NOW_COMPARISON = 'Worse' AS worse, s.VACCINE_CAUSED_HEALTH_ISSUES AS attributed
        FROM (SELECT RESPONSE_ID AS response_id, HEALTH_NOW_COMPARISON, VACCINE_CAUSED_HEALTH_ISSUES
              FROM read_parquet('{glob}', union_by_name = true)
              WHERE NOT coalesce(_under3, false) AND try_cast(DAYS_SINCE AS INTEGER) >= 60) s
        JOIN ph_rank r USING (response_id) WHERE r.rnk >= 3""")
    con.execute(f"""CREATE OR REPLACE TABLE ll_people AS
        WITH adult AS (SELECT DISTINCT REGISTRANT_CODE AS registrant
                       FROM read_parquet('{glob}', union_by_name = true) WHERE NOT coalesce(_under3, false)),
             md AS (SELECT registrant, max(try_cast(dose_number AS INTEGER)) AS max_dose FROM vax GROUP BY 1)
        SELECT a.registrant, any_value(g.sex) AS sex, any_value(md.max_dose) AS max_dose
        FROM adult a LEFT JOIN registrants g USING (registrant) LEFT JOIN md USING (registrant)
        GROUP BY a.registrant""")
    return {"ll_checkins": con.execute("SELECT count(*) FROM ll_checkins").fetchone()[0],
            "ll_people": con.execute("SELECT count(*) FROM ll_people").fetchone()[0]}


COHORT_SQL = """
CREATE OR REPLACE TABLE {out} AS
WITH per AS (
    SELECT registrant,
           bool_or(worse AND attributed = 'Yes') AS ae,
           bool_or(worse) AS any_worse,
           bool_or(attributed = 'Yes') AS ever_yes,
           min(CASE WHEN worse AND attributed = 'Yes' THEN dose_number END) AS ae_dose
    FROM {checkins} GROUP BY registrant)
SELECT p.registrant, p.sex, p.max_dose,
       CASE WHEN c.ae THEN 'prolonged_ae'
            WHEN c.any_worse AND NOT coalesce(c.ever_yes, false) THEN 'prolonged_noattr'
            ELSE 'control' END AS cohort,
       CASE WHEN coalesce(p.max_dose, 0) >= 3 THEN '3+' ELSE coalesce(p.max_dose, 0)::VARCHAR END AS dose_group
FROM {people} p LEFT JOIN per c USING (registrant)
"""


def build(con, checkins: str = "ll_checkins", people: str = "ll_people", out: str = "ll_cohorts") -> None:
    con.execute(COHORT_SQL.format(checkins=checkins, people=people, out=out))


def counts(con, table: str = "ll_cohorts") -> pl.DataFrame:
    """Our counts beside the published ones, with difference and % difference."""
    q = lambda sql: con.execute(sql).fetchone()[0]
    ours = {
        "enrollees": q(f"SELECT count(*) FROM {table}"),
        "prolonged_ae": q(f"SELECT count(*) FROM {table} WHERE cohort = 'prolonged_ae'"),
        "prolonged_ae_d1": q(f"SELECT count(*) FROM {table} WHERE cohort = 'prolonged_ae' AND dose_group = '1'"),
        "prolonged_ae_d2": q(f"SELECT count(*) FROM {table} WHERE cohort = 'prolonged_ae' AND dose_group = '2'"),
        "prolonged_ae_d3plus": q(f"SELECT count(*) FROM {table} WHERE cohort = 'prolonged_ae' AND dose_group = '3+'"),
        "prolonged_noattr": q(f"SELECT count(*) FROM {table} WHERE cohort = 'prolonged_noattr'"),
        "prolonged_noattr_d1": q(f"SELECT count(*) FROM {table} WHERE cohort = 'prolonged_noattr' AND dose_group = '1'"),
        "prolonged_noattr_d2": q(f"SELECT count(*) FROM {table} WHERE cohort = 'prolonged_noattr' AND dose_group = '2'"),
        "prolonged_noattr_d3plus": q(f"SELECT count(*) FROM {table} WHERE cohort = 'prolonged_noattr' AND dose_group = '3+'"),
        "control": q(f"SELECT count(*) FROM {table} WHERE cohort = 'control'"),
        "women_prolonged_ae": q(f"SELECT count(*) FROM {table} WHERE cohort = 'prolonged_ae' AND sex = 'Female'"),
        "women": q(f"SELECT count(*) FROM {table} WHERE sex = 'Female'"),
    }
    rows = [{"group": k, "ours": v, "levi_lu": TARGETS[k], "difference": v - TARGETS[k],
             "pct_difference": round(100 * (v - TARGETS[k]) / TARGETS[k], 2), "people": v}
            for k, v in ours.items()]
    return safe(pl.DataFrame(rows))


def overlap(con, groups: str = "phenotype_groups", cohorts: str = "ll_cohorts") -> pl.DataFrame:
    """Person-level cross-tabulation of the text-defined case (a case at any dose) against the
    Levi & Lu Prolonged-AE cohort, among people in both denominators, with Cohen's kappa."""
    df = frame(con, f"""
        WITH ours AS (SELECT registrant, bool_or(grp = 'case') AS text_case FROM {groups}
                      WHERE in_denominator GROUP BY registrant),
             theirs AS (SELECT registrant, cohort = 'prolonged_ae' AS ll_case FROM {cohorts})
        SELECT o.text_case, t.ll_case, count(*) AS people
        FROM ours o JOIN theirs t USING (registrant) GROUP BY ALL""")
    n = {(r["text_case"], r["ll_case"]): r["people"] for r in df.iter_rows(named=True)}
    both, ours_only, theirs_only, neither = (n.get((True, True), 0), n.get((True, False), 0),
                                             n.get((False, True), 0), n.get((False, False), 0))
    total = both + ours_only + theirs_only + neither
    po = (both + neither) / total
    pe = ((both + ours_only) * (both + theirs_only) + (theirs_only + neither) * (ours_only + neither)) / total ** 2
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return safe(pl.DataFrame([
        {"cell": "both", "people": both}, {"cell": "text-defined only", "people": ours_only},
        {"cell": "Levi & Lu only", "people": theirs_only}, {"cell": "neither", "people": neither},
        {"cell": "total", "people": total},
        {"cell": "share of text-defined cases also Levi & Lu", "people": total,
         "value": round(both / max(both + ours_only, 1), 4)},
        {"cell": "share of Levi & Lu cases also text-defined", "people": total,
         "value": round(both / max(both + theirs_only, 1), 4)},
        {"cell": "Cohen's kappa", "people": total, "value": round(kappa, 4)}]))
