"""PACVS-like case definition (docs/protocol.md) and the three comparison groups, as SQL.

Inputs (canonical tables; `prepare` builds them from the linked data):

  ph_surveys(registrant, dose_number, response_id, survey_type, worse, impact)
      one row per completed check-in. survey_type is canonical: w1, 6w, 3m, 6m, 12m.
      worse  = "health now" worse than baseline; impact = unable to do normal activities,
      missed work/school, or needed care.
  ph_entry_themes(registrant, dose_number, response_id, theme, domain)
      classified free text; domain is 'pacvs' for the nine candidate domains and
      'exclusion' for named acute diagnoses / unrelated causes.

Case (per registrant x dose), all of:
  1. a completed 3-, 6- or 12-month survey S with worse OR impact;
  2. free text at S classified to >= 2 PACVS domains, OR free text at >= 2 long-term
     surveys of that dose that together cover >= 2 PACVS domains;
  3. no exclusion theme in the free text at S.

Comparison groups (mutually exclusive, priority case > b > c > a):
  a no_symptoms         long-term completer; no long-term survey worse/impact; no PACVS text
                        at any long-term survey
  b acute_event         any free text (any survey, that dose) naming an acute diagnosis
  c severe_w1_recovered week-1 impact or >= 2 PACVS domains at week 1; completed >= 1
                        long-term survey; no long-term survey worse/impact
Denominator: registrant x dose with >= 1 completed long-term survey (`in_denominator`).

Before the OSF registration exists, run this on synthetic data only (brief rule 5).
"""

from __future__ import annotations

from .db import frame

LONG_TERM = ("3m", "6m", "12m")
WEEK1 = ("w1",)

PHENOTYPE_SQL = """
CREATE OR REPLACE TABLE phenotype_groups AS
WITH lt AS (
    SELECT * FROM ph_surveys WHERE survey_type IN {long_term}
),
denom AS (SELECT DISTINCT registrant, dose_number FROM lt),
pd AS (
    SELECT t.* FROM ph_entry_themes t
    WHERE t.domain = 'pacvs'
),
pd_lt AS (SELECT pd.* FROM pd SEMI JOIN lt USING (response_id)),
per_survey AS (
    SELECT response_id, count(DISTINCT theme) AS n_dom FROM pd_lt GROUP BY ALL
),
across AS (
    SELECT registrant, dose_number, count(DISTINCT response_id) AS n_surveys,
           count(DISTINCT theme) AS n_dom
    FROM pd_lt GROUP BY ALL
),
excluded AS (
    SELECT DISTINCT response_id FROM ph_entry_themes WHERE domain = 'exclusion'
),
cases AS (
    SELECT DISTINCT s.registrant, s.dose_number
    FROM lt s
    LEFT JOIN per_survey p USING (response_id)
    LEFT JOIN across a ON a.registrant = s.registrant AND a.dose_number = s.dose_number
    WHERE (s.worse OR s.impact)
      AND (coalesce(p.n_dom, 0) >= 2 OR (coalesce(a.n_surveys, 0) >= 2 AND a.n_dom >= 2))
      AND NOT EXISTS (SELECT 1 FROM excluded x WHERE x.response_id = s.response_id)
),
lt_unwell AS (
    SELECT DISTINCT registrant, dose_number FROM lt WHERE worse OR impact
),
lt_text AS (SELECT DISTINCT registrant, dose_number FROM pd_lt),
acute AS (
    SELECT DISTINCT registrant, dose_number FROM ph_entry_themes WHERE theme = 'acute_diagnosis'
),
w1_severe AS (
    SELECT DISTINCT s.registrant, s.dose_number
    FROM ph_surveys s
    LEFT JOIN (SELECT response_id, count(DISTINCT theme) AS n FROM pd GROUP BY ALL) w
      USING (response_id)
    WHERE s.survey_type IN {week1} AND (s.impact OR coalesce(w.n, 0) >= 2)
),
everyone AS (
    SELECT registrant, dose_number FROM denom
    UNION SELECT registrant, dose_number FROM acute
    UNION SELECT registrant, dose_number FROM w1_severe
)
SELECT p.registrant, p.dose_number,
       CASE
         WHEN c.registrant IS NOT NULL THEN 'case'
         WHEN a.registrant IS NOT NULL THEN 'acute_event'
         WHEN w.registrant IS NOT NULL AND d.registrant IS NOT NULL AND u.registrant IS NULL
           THEN 'severe_w1_recovered'
         WHEN d.registrant IS NOT NULL AND u.registrant IS NULL AND t.registrant IS NULL
           THEN 'no_symptoms'
         ELSE 'other'
       END AS grp,
       d.registrant IS NOT NULL AS in_denominator
FROM everyone p
LEFT JOIN cases c     USING (registrant, dose_number)
LEFT JOIN acute a     USING (registrant, dose_number)
LEFT JOIN w1_severe w USING (registrant, dose_number)
LEFT JOIN denom d     USING (registrant, dose_number)
LEFT JOIN lt_unwell u USING (registrant, dose_number)
LEFT JOIN lt_text t   USING (registrant, dose_number)
"""


def _tuple(vals) -> str:
    return "(" + ", ".join("'" + v + "'" for v in vals) + ")"


def build(con) -> None:
    """Create phenotype_groups(registrant, dose_number, grp, in_denominator)."""
    con.execute(PHENOTYPE_SQL.format(long_term=_tuple(LONG_TERM), week1=_tuple(WEEK1)))


def group_sizes(con):
    """People per group among the denominator (suppressed)."""
    from .suppress import safe

    df = frame(con, 
        """SELECT grp, dose_number, count(DISTINCT registrant) AS people
           FROM phenotype_groups WHERE in_denominator OR grp = 'acute_event'
           GROUP BY ALL ORDER BY ALL"""
    )
    return safe(df)


def prepare(con, survey_type_map: dict[str, str], worse_values: list[str],
            impact_values: list[str], domains: dict[str, str]) -> None:
    """Build ph_surveys / ph_entry_themes from checkins, vax and entry_themes.

    `survey_type_map` maps raw check-in survey types to w1/6w/3m/6m/12m; `worse_values` and
    `impact_values` are the raw answers that count as worse-than-baseline / health impact.
    Refuses long-term survey types until the OSF registration exists (brief rule 5).
    """
    from .themes import registration_filed

    if not registration_filed() and set(survey_type_map.values()) & set(LONG_TERM):
        raise PermissionError("Case definition on long-term surveys needs the OSF registration "
                              "(osf_registration in config/analysis.yaml).")
    cases = " ".join(f"WHEN '{k}' THEN '{v}'" for k, v in survey_type_map.items())
    worse = ", ".join(f"'{v}'" for v in worse_values) or "NULL"
    impact = ", ".join(f"'{v}'" for v in impact_values) or "NULL"
    con.execute(
        f"""
        CREATE OR REPLACE TABLE ph_surveys AS
        SELECT h.registrant, x.dose_number, h.response_id,
               CASE h.survey_type {cases} END AS survey_type,
               coalesce(h.health_now IN ({worse}), false) AS worse,
               coalesce(h.health_impact IN ({impact}), false) AS impact
        FROM checkins h
        ASOF LEFT JOIN vax x
          ON h.registrant = x.registrant AND TRY_CAST(h.started_on AS DATE) >= x.vax_date
        WHERE CASE h.survey_type {cases} END IS NOT NULL
        """
    )
    dom = " ".join(f"WHEN '{t}' THEN '{d}'" for t, d in domains.items())
    con.execute(
        f"""
        CREATE OR REPLACE TABLE ph_entry_themes AS
        SELECT e.registrant, e.dose_number, e.response_id, t.theme,
               CASE t.theme {dom} END AS domain
        FROM entry_themes t JOIN entries_survey e USING (entry_id)
        """
    )
