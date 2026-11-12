"""Analyses added for the Drug Safety submission (addendum 2, 2026-11-12). None is in the
pre-registration; every output is prefixed `sub_` and reported as "not pre-registered".

B2  curveball null for Q1 (row and column margins fixed), overall and within strata
B3  persistence by qualification route, and against a new comparison group (d)
B4  structured week-1 answers, cases vs group (a)
B5  audit sheet: layer 3 vs CDC disagreements, for human coding (text stays local)
B6  Q3 dispersion with Miller-Madow correction, rarefaction and a two-sided test
B7  case count and Q1 with criterion 3 off and with redacted entries included
B8  reconciliation of the counts quoted in the manuscript
B9  layer-3 cost from the logged runs
Counts only; every table goes through suppress.safe.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import polars as pl

from . import config, stats
from .analysis import SEED, _safe_pairs, pacvs_domains, q1_matrix
from .db import frame, one
from .suppress import safe

MATRIX = "q1_matrix.parquet"      # DATA_DIR/interim; no identifiers, never committed


# --- B2 ------------------------------------------------------------------------------------------

def export_q1_matrix(con, domains: list[str]) -> Path:
    path = config.DATA_DIR / "interim" / MATRIX
    q1_matrix(con, domains).write_parquet(path)
    return path


def q1_curveball(domains: list[str], permutations: int, path: Path | None = None,
                 log=print) -> dict[str, pl.DataFrame]:
    """Curveball null: each person-dose keeps its number of domains and each domain keeps its
    frequency. The total pairwise co-occurrence is then fixed by construction
    (sum over rows of C(r, 2)), so only the 36 pairs carry a test."""
    path = path or config.DATA_DIR / "interim" / MATRIX
    m = pl.read_parquet(path)
    X = m.select(domains).to_numpy().astype(bool)
    chars = m["chars"].fill_null(0).to_numpy()
    n_ent = m["n_entries"].fill_null(1).to_numpy()
    tert = np.searchsorted(np.quantile(chars, [1 / 3, 2 / 3]), chars)
    ent = np.minimum(n_ent, 3) - 1                     # 1, 2, 3+
    rows, pair_tabs = [], []
    k = len(domains)
    iu = np.triu_indices(k, 1)
    for name, st in [("curveball, unstratified", None),
                     ("curveball within entries 1 / 2 / 3+", ent),
                     ("curveball within text-length tertiles", tert)]:
        r = stats.curveball_test(X, domains, permutations=permutations, seed=SEED, strata=st, log=log)
        rows.append({"null": name, "people": X.shape[0],
                     "strata": 1 if st is None else int(np.unique(st).size),
                     "observed_pairs": r.observed_pairs,
                     "null_mean_pairs": round(r.null_mean_pairs, 1),
                     "ratio": round(r.observed_pairs / r.null_mean_pairs, 4),
                     "pairs_above_null_holm": int((stats.holm(r.pair_p_upper[iu]) < 0.05).sum()),
                     "pairs_below_null_holm": int((stats.holm(r.pair_p_lower[iu]) < 0.05).sum()),
                     "permutations": r.permutations})
        pair_tabs.append(pl.DataFrame({
            "null": name, "domain_a": [domains[i] for i in iu[0]],
            "domain_b": [domains[j] for j in iu[1]],
            "both_people": r.pair_observed[iu].astype(np.int64),
            "expected_people": r.pair_null_mean[iu].round(1),
            "ratio": (r.pair_observed[iu] / np.maximum(r.pair_null_mean[iu], 1e-9)).round(3),
            "p_upper": r.pair_p_upper[iu].round(4), "p_lower": r.pair_p_lower[iu].round(4),
            "p_upper_holm": stats.holm(r.pair_p_upper[iu]).round(4)}))
    return {"summary": safe(pl.DataFrame(rows)), "pairs": _safe_pairs(pl.concat(pair_tabs))}


# --- B3 ------------------------------------------------------------------------------------------

def persistence_variants(con, groups: str = "phenotype_groups") -> dict[str, pl.DataFrame]:
    """Cases by qualification route; persistence for same-survey cases; persistence against
    group (d): long-term responders worse or impacted at some long-term survey who named fewer
    than two domains there (and are not cases or acute events)."""
    con.execute(f"""CREATE OR REPLACE TEMP TABLE b3_case_route AS
        WITH c AS (SELECT registrant, dose_number FROM {groups} WHERE grp = 'case'),
             per_survey AS (SELECT t.registrant, t.dose_number, t.response_id,
                                   count(DISTINCT t.theme) AS n_dom
                            FROM ph_entry_themes t JOIN ph_lt l USING (response_id)
                            JOIN c ON c.registrant = t.registrant AND c.dose_number = t.dose_number
                            WHERE t.domain = 'pacvs' GROUP BY ALL),
             excluded AS (SELECT DISTINCT response_id FROM ph_entry_themes WHERE domain = 'exclusion'),
             same AS (SELECT DISTINCT l.registrant, l.dose_number FROM ph_lt l
                      JOIN per_survey p USING (response_id)
                      WHERE (l.worse OR l.impact) AND p.n_dom >= 2
                        AND NOT EXISTS (SELECT 1 FROM excluded x WHERE x.response_id = l.response_id))
        SELECT c.registrant, c.dose_number,
               CASE WHEN s.registrant IS NOT NULL THEN 'same_survey' ELSE 'across_surveys_only' END AS route
        FROM c LEFT JOIN same s USING (registrant, dose_number)""")
    routes = safe(frame(con, """SELECT route, count(*) AS person_doses, count(DISTINCT registrant) AS people
                                 FROM b3_case_route GROUP BY route ORDER BY route"""))
    # group (d)
    con.execute(f"""CREATE OR REPLACE TEMP TABLE b3_group_d AS
        WITH per_survey AS (SELECT t.response_id, count(DISTINCT t.theme) AS n_dom
                            FROM ph_entry_themes t JOIN ph_lt l USING (response_id)
                            WHERE t.domain = 'pacvs' GROUP BY 1),
             unwell AS (SELECT l.registrant, l.dose_number, min(l.rnk) AS ref FROM ph_lt l
                        LEFT JOIN per_survey p USING (response_id)
                        WHERE (l.worse OR l.impact) AND coalesce(p.n_dom, 0) < 2 GROUP BY ALL)
        SELECT u.registrant, u.dose_number, u.ref FROM unwell u JOIN {groups} g USING (registrant, dose_number)
        WHERE g.in_denominator AND g.grp NOT IN ('case', 'acute_event')""")

    def persist(case_sql: str, comp_sql: str, label: str) -> dict:
        d = frame(con, f"""
            WITH g AS ({case_sql} UNION ALL {comp_sql}),
                 ref AS (SELECT g.registrant, g.dose_number, g.grp, g.ref, max(l.rnk) AS last_survey
                         FROM g JOIN ph_lt l USING (registrant, dose_number) GROUP BY ALL),
                 dm AS (SELECT d.registrant, d.dose_number, max(d.rnk) AS last_domain FROM ph_dom d
                        SEMI JOIN g USING (registrant, dose_number) WHERE d.rnk >= 3 GROUP BY ALL),
                 later AS (SELECT r.grp, r.last_survey > r.ref AS has_later,
                                  coalesce(dm.last_domain, 0) > r.ref AS persists
                           FROM ref r LEFT JOIN dm USING (registrant, dose_number) WHERE r.ref IS NOT NULL)
            SELECT grp, count(*) FILTER (WHERE has_later) AS n,
                   count(*) FILTER (WHERE has_later AND persists) AS x FROM later GROUP BY grp""")
        dd = {r["grp"]: (r["x"], r["n"]) for r in d.iter_rows(named=True)}
        (x1, n1), (x2, n2) = dd.get("case", (0, 0)), dd.get("comp", (0, 0))
        rd = stats.risk_difference(x1, n1, x2, n2) if n1 and n2 else None
        return {"comparison": label, "case_people": n1, "case_persist_people": x1,
                "comparison_people": n2, "comparison_persist_people": x2,
                "case_share": rd and round(rd.p1, 4), "comparison_share": rd and round(rd.p2, 4),
                "risk_difference": rd and round(rd.diff, 4), "ci_low": rd and round(rd.lower, 4),
                "ci_high": rd and round(rd.upper, 4), "p_one_sided": rd and rd.p_one_sided}

    case_all = """SELECT r.registrant, r.dose_number, 'case' AS grp,
                   min(l.rnk) FILTER (WHERE l.worse OR l.impact) AS ref
                   FROM b3_case_route r JOIN ph_lt l USING (registrant, dose_number) GROUP BY ALL"""
    case_same = case_all.replace("FROM b3_case_route r", "FROM b3_case_route r") + " HAVING any_value(r.route) = 'same_survey'"
    comp_c = f"""SELECT g.registrant, g.dose_number, 'comp' AS grp, min(l.rnk) AS ref
                 FROM {groups} g JOIN ph_lt l USING (registrant, dose_number)
                 WHERE g.grp = 'severe_w1_recovered' GROUP BY ALL"""
    comp_d = "SELECT registrant, dose_number, 'comp' AS grp, ref FROM b3_group_d"
    rows = [persist(case_all, comp_c, "registered: all cases vs group (c)"),
            persist(case_same, comp_c, "same-survey cases only vs group (c)"),
            persist(case_all, comp_d, "all cases vs group (d): worse/impacted, < 2 domains"),
            persist(case_same, comp_d, "same-survey cases vs group (d)")]
    return {"routes": routes, "persistence": safe(pl.DataFrame(rows))}


# --- B4 ------------------------------------------------------------------------------------------

def structured_onset_vs_a(con, groups: str = "phenotype_groups") -> pl.DataFrame:
    """Week-1 check-box symptoms (any, and moderate or severe), by domain, for cases whose case
    domains include that domain, against group (a). Group (a) is a 1-in-20 sample."""
    from .analysis import STRUCTURED_FIELDS, _week1_structured
    _week1_structured(con, groups)
    glob = str(config.DATA_DIR / "interim" / "health_checkins" / "*.parquet").replace("\\", "/")
    parts = []
    for d, (cols, _) in STRUCTURED_FIELDS.items():
        test = " OR ".join(c + " IN ('Moderate', 'Severe')" for c in cols)
        parts.append(f"({test}) AS {d}_modsev")
    sev = ", ".join(parts)
    cols = sorted({c for cs, _ in STRUCTURED_FIELDS.values() for c in cs})
    con.execute(f"""CREATE OR REPLACE TEMP TABLE w1_sev AS
        SELECT i.registrant, i.dose_number,
               bool_or(s.fatigue_pem_modsev) AS fatigue_pem_modsev, bool_or(s.pain_modsev) AS pain_modsev,
               bool_or(s.gastrointestinal_modsev) AS gastrointestinal_modsev,
               bool_or(coalesce(s.HEALTH_IMPACT, 'N/A') NOT IN ('N/A', '')) AS w1_impact
        FROM (SELECT RESPONSE_ID AS response_id, HEALTH_IMPACT, {sev}
              FROM read_parquet('{glob}', union_by_name = true)
              WHERE RESPONSE_ID IN (SELECT response_id FROM w1_ids)) s
        JOIN w1_ids i USING (response_id) GROUP BY i.registrant, i.dose_number""")
    rows = []
    for dom in STRUCTURED_FIELDS:
        df = frame(con, f"""
            WITH cd AS (SELECT DISTINCT registrant, dose_number FROM ph_dom WHERE rnk >= 3 AND theme = '{dom}'),
                 x AS (SELECT w.grp, w.{dom} AS any_sym, v.{dom}_modsev AS modsev, v.w1_impact
                       FROM w1_struct w JOIN w1_sev v USING (registrant, dose_number)
                       WHERE w.grp = 'no_symptoms'
                          OR (w.grp = 'case' AND EXISTS (SELECT 1 FROM cd WHERE cd.registrant = w.registrant
                                                         AND cd.dose_number = w.dose_number)))
            SELECT grp, count(*) AS people, round(avg(any_sym::INT), 4) AS week1_any,
                   round(avg(modsev::INT), 4) AS week1_moderate_or_severe,
                   round(avg(w1_impact::INT), 4) AS week1_impact
            FROM x GROUP BY grp""")
        for r in df.iter_rows(named=True):
            rows.append({"domain": dom, "group": "cases with this domain" if r["grp"] == "case"
                         else "group (a), 1-in-20 sample", **{k: v for k, v in r.items() if k != "grp"}})
    return safe(pl.DataFrame(rows))


# --- B5 ------------------------------------------------------------------------------------------

def audit_sample(con, model: str, n_per_side: int = 150, seed: int = 20261112) -> dict:
    """Long-term entries where layer 3 and CDC disagree on a PACVS domain: a seeded sample,
    stratified by domain, half layer-3-only, half CDC-only. Writes a blind coding sheet (text,
    domain, question) and a separate key to gold_set/<db>/; nothing leaves the machine."""
    from .classify.llm import PROMPT_VERSION
    from .gold import gold_dir
    from .themes import LONG_TERM_PATTERN
    from .validate import MEDDRA_RELEASE, _load_map
    _load_map(con)
    doms = pacvs_domains()
    con.execute(f"""CREATE OR REPLACE TEMP TABLE au_ev AS
        SELECT e.entry_id, e.registrant, e.text FROM entries_survey e
        WHERE e.survey_matched AND regexp_matches(coalesce(e.survey_type, ''), '{LONG_TERM_PATTERN}')
          AND NOT coalesce(e.redacted, false)
          AND NOT EXISTS (SELECT 1 FROM final_flags f WHERE f.entry_id = e.entry_id AND f.pre_vaccine)
          AND EXISTS (SELECT 1 FROM entry_meddra m WHERE m.entry_id = e.entry_id
                      AND m.meddra_release = '{MEDDRA_RELEASE}')""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE au_dis AS
        WITH ref AS (SELECT DISTINCT m.entry_id, v.theme FROM entry_meddra m JOIN au_ev USING (entry_id)
                     JOIN v_map v ON v.pt = m.pt WHERE m.meddra_release = '{MEDDRA_RELEASE}'),
             l3 AS (SELECT DISTINCT e.entry_id, unnest(l.themes) AS theme FROM au_ev e
                    JOIN llm_labels l ON l.text_hash = md5(e.text) AND l.model = '{model}'
                         AND l.prompt_version = '{PROMPT_VERSION}' AND l.ok),
             fin AS (SELECT DISTINCT entry_id, theme FROM final_themes)
        SELECT e.entry_id, x.theme, x.side FROM au_ev e JOIN (
            SELECT entry_id, theme, 'layer3_only' AS side FROM l3
            WHERE (entry_id, theme) NOT IN (SELECT entry_id, theme FROM ref)
            UNION ALL
            SELECT entry_id, theme, 'cdc_only' AS side FROM ref
            WHERE (entry_id, theme) NOT IN (SELECT entry_id, theme FROM fin)) x USING (entry_id)
        WHERE x.theme IN ({", ".join(repr(d) for d in doms)})""")
    pool = safe(frame(con, """SELECT side, theme, count(*) AS entries, count(DISTINCT e.registrant) AS people
                              FROM au_dis d JOIN au_ev e USING (entry_id) GROUP BY ALL ORDER BY ALL"""))
    per = max(1, round(n_per_side / len(doms)))
    con.execute(f"""CREATE OR REPLACE TEMP TABLE au_pick AS
        SELECT entry_id, theme, side FROM (
            SELECT d.*, row_number() OVER (PARTITION BY side, theme
                   ORDER BY hash(concat_ws('|', d.entry_id, d.theme, '{seed}'))) AS rn FROM au_dis d)
        WHERE rn <= {per}""")
    sheet = frame(con, f"""
        SELECT row_number() OVER (ORDER BY hash(concat_ws('|', p.entry_id, p.theme, '{seed}', 'x'))) AS item,
               p.theme AS domain, e.text, p.entry_id, p.side
        FROM au_pick p JOIN au_ev e USING (entry_id)""")
    out = gold_dir()
    out.mkdir(parents=True, exist_ok=True)
    sheet.select("item", "domain", "text").with_columns(pl.lit("").alias("present_0_1"), pl.lit("").alias("note")) \
        .write_csv(out / "audit_layer3_vs_cdc_sheet.csv")
    sheet.select("item", "domain", "entry_id", "side").write_csv(out / "audit_layer3_vs_cdc_key.csv")
    drawn = safe(frame(con, """SELECT side, theme, count(*) AS entries, count(DISTINCT e.registrant) AS people
                               FROM au_pick p JOIN au_ev e USING (entry_id) GROUP BY ALL ORDER BY ALL"""))
    return {"pool": pool, "drawn": drawn, "sheet": str(out / "audit_layer3_vs_cdc_sheet.csv"),
            "items": sheet.height}


# --- B6 ------------------------------------------------------------------------------------------

def q3_dispersion_extended(con, match_sets: dict[str, pl.DataFrame], permutations: int,
                           groups: str = "phenotype_groups") -> pl.DataFrame:
    from .analysis import _person_groups, vaers_symptoms
    _person_groups(con, groups)
    vaers_symptoms(con)
    rows = []
    for name, ms in match_sets.items():
        con.register("_ms", ms.with_columns(pl.col("vaers_id").cast(pl.String)).to_arrow())
        pts = frame(con, """SELECT p.grp, p.registrant, v.pt FROM q3_people p JOIN _ms m USING (registrant)
                            JOIN vaers_pt v ON v.vaers_id = trim(m.vaers_id)""")
        con.unregister("_ms")
        a = pts.filter(pl.col("grp") == "case")["pt"].to_numpy()
        b = pts.filter(pl.col("grp") == "acute_event")["pt"].to_numpy()
        r = stats.dispersion_extended(a, b, permutations=permutations, seed=SEED)
        rows.append({"match_set": name, "case_people": int(pts.filter(pl.col("grp") == "case")["registrant"].n_unique()),
                     "group_b_people": int(pts.filter(pl.col("grp") == "acute_event")["registrant"].n_unique()),
                     "case_pt_codes": int(a.size), "group_b_pt_codes": int(b.size),
                     "entropy_cases": round(r["h_a"], 4), "entropy_group_b": round(r["h_b"], 4),
                     "entropy_cases_miller_madow": round(r["h_a_mm"], 4),
                     "entropy_group_b_miller_madow": round(r["h_b_mm"], 4),
                     "entropy_cases_rarefied": round(r["h_a_rare"], 4),
                     "entropy_group_b_rarefied": round(r["h_b_rare"], 4),
                     "rarefied_to_codes": r["rare_n"], "difference": round(r["diff"], 4),
                     "p_one_sided_cases_more_dispersed": r["p_upper"], "p_two_sided": r["p_two"]})
    return safe(pl.DataFrame(rows))


# --- B7 ------------------------------------------------------------------------------------------

def q1_variants(con, domains: list[str], permutations: int) -> pl.DataFrame:
    """Q1 with redacted entries included in the person-dose rows (their layer-1 themes already
    count). Criterion 3 does not enter Q1; the case count without it is reported beside."""
    con.execute("""CREATE OR REPLACE TEMP TABLE ph_lt_text_all AS
        SELECT DISTINCT e.registrant, e.dose_number FROM entries_survey e
        SEMI JOIN ph_lt l ON l.response_id = e.response_id
        WHERE length(trim(coalesce(e.text, ''))) > 0""")
    cols = ", ".join(f"coalesce(bool_or(d.theme = '{t}'), false) AS {t}" for t in domains)
    m = frame(con, f"""
        WITH rows_ AS (SELECT t.* FROM ph_lt_text_all t JOIN phenotype_groups g USING (registrant, dose_number)
                       WHERE g.in_denominator),
             d AS (SELECT registrant, dose_number, theme FROM ph_dom WHERE rnk >= 3)
        SELECT {cols} FROM rows_ r LEFT JOIN d USING (registrant, dose_number)
        GROUP BY r.registrant, r.dose_number""")
    X = m.select(domains).to_numpy().astype(bool)
    r = stats.cooccurrence_test(X, domains, permutations=permutations, seed=SEED)
    cases_no3 = one(con, "SELECT count(*) FROM phenotype_groups_excl_none WHERE grp = 'case'")[0]
    cases_reg = one(con, "SELECT count(*) FROM phenotype_groups WHERE grp = 'case'")[0]
    return safe(pl.DataFrame([
        {"variant": "registered", "people": one(con, "SELECT count(*) FROM ph_lt_text t JOIN phenotype_groups g USING (registrant, dose_number) WHERE g.in_denominator")[0],
         "case_person_doses": cases_reg, "q1_ratio": None, "q1_p": None},
        {"variant": "criterion 3 off", "people": None, "case_person_doses": cases_no3,
         "q1_ratio": None, "q1_p": None},
        {"variant": "redacted entries included", "people": X.shape[0], "case_person_doses": cases_reg,
         "q1_ratio": round(r.observed_pairs / r.null_mean_pairs, 3), "q1_p": round(r.p_pairs, 4)}]))


# --- B8, B9 --------------------------------------------------------------------------------------

def reconcile(con) -> pl.DataFrame:
    glob = str(config.DATA_DIR / "interim" / "health_checkins" / "*.parquet").replace("\\", "/")
    rows = []
    def add(name, sql):
        rows.append({"quantity": name, "value": one(con, sql)[0]})
    add("entries after de-duplication", "SELECT count(*) FROM entries")
    add("entries_raw rows", "SELECT count(*) FROM entries_raw")
    add("entries matched to a long-term survey", "SELECT count(*) FROM entries_survey WHERE survey_matched AND regexp_matches(coalesce(survey_type,''), '(?i)(\\b(3|6|12|three|six|twelve)\\s*-?\\s*(m|mo|mon|month)s?\\b)|(\\byear)')")
    add("entries matched to an early survey", "SELECT count(*) FROM entries_survey WHERE survey_matched AND NOT regexp_matches(coalesce(survey_type,''), '(?i)(\\b(3|6|12|three|six|twelve)\\s*-?\\s*(m|mo|mon|month)s?\\b)|(\\byear)')")
    add("entries not matched to a survey", "SELECT count(*) FROM entries_survey WHERE NOT coalesce(survey_matched, false)")
    add("entries with survey_matched NULL", "SELECT count(*) FROM entries_survey WHERE survey_matched IS NULL")
    add("check-ins in the linked table", "SELECT count(*) FROM checkins")
    add("check-in rows in the raw adult file", f"SELECT count(*) FROM read_parquet('{glob}', union_by_name = true) WHERE NOT coalesce(_under3, false)")
    add("check-in rows in the raw under-3 file", f"SELECT count(*) FROM read_parquet('{glob}', union_by_name = true) WHERE coalesce(_under3, false)")
    add("distinct RESPONSE_ID in raw check-ins", f"SELECT count(DISTINCT RESPONSE_ID) FROM read_parquet('{glob}', union_by_name = true)")
    add("person-doses with any check-in (ph_rank)", "SELECT count(*) FROM (SELECT DISTINCT registrant, dose_number FROM ph_rank)")
    add("person-doses with a long-term survey", "SELECT count(*) FROM (SELECT DISTINCT registrant, dose_number FROM ph_lt)")
    add("person-doses in any phenotype group", "SELECT count(*) FROM phenotype_groups")
    add("person-doses in groups and in denominator", "SELECT count(*) FROM phenotype_groups WHERE in_denominator")
    add("group (b) people, group table", "SELECT count(DISTINCT registrant) FROM phenotype_groups WHERE grp = 'acute_event'")
    add("group (b) people, Q3 (not a case at any dose)", "SELECT count(*) FROM (SELECT registrant FROM phenotype_groups GROUP BY registrant HAVING bool_or(grp = 'acute_event') AND NOT bool_or(grp = 'case'))")
    add("registrants in registrants table", "SELECT count(*) FROM registrants")
    add("registrants with any check-in", "SELECT count(DISTINCT registrant) FROM checkins")
    return pl.DataFrame(rows)


def llm_cost(con) -> pl.DataFrame:
    """Tokens and logged cost per model and prompt version from llm_runs (the provider's own
    usage figures as returned per request), plus the price used."""
    from .classify.llm import CLAUDE_PRICES
    df = frame(con, """SELECT model, prompt_version, count(*) AS runs, sum(texts) AS texts,
                       sum(tokens) AS tokens, round(sum(cost_usd), 4) AS cost_usd_logged,
                       min(started_at) AS first_run, max(started_at) AS last_run
                       FROM llm_runs GROUP BY ALL ORDER BY ALL""")
    return df.with_columns(pl.col("model").map_elements(
        lambda m: str(CLAUDE_PRICES.get(m, "")), return_dtype=pl.String).alias("claude_price_in_out_per_M"))
