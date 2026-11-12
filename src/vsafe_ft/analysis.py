"""Confirmatory analysis Q1-Q3 (and the registered Q4 / attrition descriptives).

Runs on the final classifier: layer 1 (`entry_themes`) plus layer 3 (`llm_labels` of the
registered model) on the long-term residue it labelled (registration section 7, amendments 1
and 2). Every function returns a suppressed aggregate table; nothing returns identifiers or
text. Decisions made where the registration is silent are listed in IMPLEMENTATION_NOTES and
reported with the results.
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import polars as pl

from . import config, phenotype, stats
from .classify.llm import PROMPT_VERSION
from .db import frame, one
from .layer3 import candidate_sql
from .suppress import safe
from .themes import registration_filed, taxonomy_domains

SURVEY_MAP = {**{f"day {d}": "w1" for d in range(8)},
              **{f"week {w}": "6w" for w in range(2, 7)},
              "3m": "3m", "6m": "6m", "12m": "12m"}
SURVEY_RANK = {"w1": 1, "6w": 2, "3m": 3, "6m": 4, "12m": 5}
WORSE_VALUES = ["Worse"]
LT = "('3m', '6m', '12m')"
SEED = 20261110
MIN_STRATUM = 1000

IMPLEMENTATION_NOTES = [
    "Survey types: 'day 0'-'day 7' = week 1 (w1); 'week 2'-'week 6' = six weeks (6w).",
    "Impact = any health_impact answer other than 'N/A' or blank; worse = health_now 'Worse'.",
    "Pre-vaccine entries: dropped if layer 1 or layer 3 flags them.",
    "Layer 3 labelled long-term residue only, so week-1 / six-week text uses layer 1 alone.",
    ("Q2 onset: case domains = PACVS domains in that dose's long-term text; onset = first "
    "survey type (w1 < 6w < 3m < 6m < 12m) whose text names any of them."),
    ("Q2 persistence: reference survey = first long-term survey with worse/impact (cases) or "
    "first long-term survey (group c); outcome = a PACVS domain at a later long-term survey "
    "type, among those who completed one."),
    ("Q3: person level. A person is a case if any dose is a case, else group (b) if any dose is. "
    "VAERS = a call-center VAERS-filed disposition within 90 days of an entry, or an "
    "OpenVSafe match in the analysis set."),
]


# --- final classifier --------------------------------------------------------------------------

def build_final(con, model: str) -> dict:
    """final_themes(entry_id, theme, layer) and final_flags(entry_id, pre_vaccine)."""
    if not registration_filed():
        raise PermissionError("Confirmatory analysis needs the OSF registration.")
    lab = f"""SELECT text_hash, any_value(themes) AS themes, bool_or(pre_vaccine) AS pre_vaccine
              FROM llm_labels WHERE model = '{model}' AND prompt_version = '{PROMPT_VERSION}'
                AND ok GROUP BY text_hash"""
    res = candidate_sql(sample=None, seed=1, residue_only=True, long_term=True)
    con.execute(f"""CREATE OR REPLACE TEMP TABLE l3 AS
        SELECT r.entry_id, l.themes, l.pre_vaccine FROM ({res}) r JOIN ({lab}) l USING (text_hash)""")
    con.execute("""CREATE OR REPLACE TABLE final_themes AS
        SELECT entry_id, theme, 1 AS layer FROM entry_themes
        UNION ALL SELECT entry_id, unnest(themes) AS theme, 3 AS layer FROM l3""")
    con.execute("""CREATE OR REPLACE TABLE final_flags AS
        SELECT f.entry_id, f.pre_vaccine OR coalesce(l.pre_vaccine, false) AS pre_vaccine
        FROM entry_flags f LEFT JOIN l3 l USING (entry_id)""")
    n = one(con, "SELECT count(*), count(*) FILTER (WHERE layer = 3) FROM final_themes")
    return {"final_theme_rows": n[0], "layer3_theme_rows": n[1],
            "layer3_entries": one(con, "SELECT count(*) FROM l3")[0]}


def prepare(con, model: str) -> dict:
    """Final classifier, case-definition inputs and phenotype_groups."""
    out = build_final(con, model)
    impact = [r[0] for r in con.execute(
        "SELECT DISTINCT health_impact FROM checkins WHERE health_impact IS NOT NULL "
        "AND health_impact <> 'N/A'").fetchall()]
    phenotype.prepare(con, SURVEY_MAP, WORSE_VALUES, impact, taxonomy_domains(),
                      themes="final_themes", flags="final_flags")
    phenotype.build(con)
    rank = " ".join(f"WHEN '{k}' THEN {v}" for k, v in SURVEY_RANK.items())
    con.execute(f"""CREATE OR REPLACE TABLE ph_rank AS
        SELECT registrant, dose_number, response_id, survey_type,
               CASE survey_type {rank} END AS rnk, worse, impact FROM ph_surveys""")
    out["impact_values"] = len(impact)
    return out


def pacvs_domains() -> list[str]:
    return sorted(t for t, d in taxonomy_domains().items() if d == "pacvs")


def group_table(con, groups: str = "phenotype_groups") -> pl.DataFrame:
    return safe(frame(con, f"""
        SELECT grp, count(*) AS person_doses, count(DISTINCT registrant) AS people,
               count(*) FILTER (WHERE in_denominator) AS in_denominator
        FROM {groups} GROUP BY grp ORDER BY grp"""))


# --- Q1 -----------------------------------------------------------------------------------------

def helper_tables(con) -> None:
    """Small derived tables so later steps never re-join the 145M check-ins:
    ph_lt (long-term check-ins), ph_dom (PACVS domain x survey rank per person-dose),
    ph_lt_text (person-doses with long-term free text)."""
    con.execute("CREATE OR REPLACE TABLE ph_lt AS SELECT * FROM ph_rank WHERE rnk >= 3")
    con.execute("""CREATE OR REPLACE TABLE ph_dom AS
        SELECT DISTINCT t.registrant, t.dose_number, t.theme, r.rnk FROM ph_entry_themes t
        JOIN ph_rank r USING (response_id) WHERE t.domain = 'pacvs'""")
    con.execute("""CREATE OR REPLACE TABLE ph_lt_text AS
        SELECT DISTINCT e.registrant, e.dose_number FROM entries_survey e
        SEMI JOIN ph_lt l ON l.response_id = e.response_id
        WHERE NOT coalesce(e.redacted, false) AND length(trim(coalesce(e.text, ''))) > 0""")


def q1_matrix(con, domains: list[str]) -> pl.DataFrame:
    """Rows: registrant x dose in the denominator with any long-term free text (no ids kept)."""
    cols = ", ".join(f"coalesce(bool_or(d.theme = '{t}'), false) AS {t}" for t in domains)
    return frame(con, f"""
        WITH rows_ AS (SELECT t.* FROM ph_lt_text t
                       JOIN phenotype_groups g USING (registrant, dose_number)
                       WHERE g.in_denominator),
             d AS (SELECT registrant, dose_number, theme FROM ph_dom WHERE rnk >= 3),
             man AS (SELECT registrant, dose_number, any_value(manufacturer) AS manufacturer
                     FROM vax GROUP BY ALL),
             amt AS (SELECT e.registrant, e.dose_number, count(*)::BIGINT AS n_entries,
                            sum(length(e.text))::BIGINT AS chars FROM entries_survey e
                     SEMI JOIN ph_lt l ON l.response_id = e.response_id
                     WHERE NOT coalesce(e.redacted, false)
                       AND length(trim(coalesce(e.text, ''))) > 0 GROUP BY ALL)
        SELECT coalesce(m.manufacturer, 'unknown') AS manufacturer,
               r.dose_number::VARCHAR AS dose, any_value(a.n_entries) AS n_entries,
               any_value(a.chars) AS chars, {cols}
        FROM rows_ r LEFT JOIN d USING (registrant, dose_number)
        LEFT JOIN man m USING (registrant, dose_number)
        LEFT JOIN amt a USING (registrant, dose_number)
        GROUP BY r.registrant, r.dose_number, m.manufacturer""")


def q1_test(X: np.ndarray, domains: list[str], permutations: int, seed: int = SEED):
    res = stats.cooccurrence_test(X, domains, permutations=permutations, seed=seed)
    k = len(domains)
    iu = np.triu_indices(k, 1)
    adj = stats.holm(res.pair_p[iu])
    marg = X.sum(0)
    pairs = pl.DataFrame({
        "domain_a": [domains[i] for i in iu[0]], "domain_b": [domains[j] for j in iu[1]],
        "both_people": res.pair_observed[iu].astype(np.int64),
        "expected_people": [round(float(marg[i]) * marg[j] / X.shape[0], 1)
                            for i, j in zip(*iu)],
        "p": res.pair_p[iu].round(4), "p_holm": adj.round(4)})
    return res, pairs


def q1(con, domains: list[str], permutations: int) -> dict[str, pl.DataFrame]:
    m = q1_matrix(con, domains)
    X = m.select(domains).to_numpy().astype(bool)
    res, pairs = q1_test(X, domains, permutations)
    n_people = X.shape[0]
    summary = pl.DataFrame({
        "stratum": ["all"], "people": [n_people],
        "domains": [len(domains)], "observed_pairs": [res.observed_pairs],
        "null_mean_pairs": [round(res.null_mean_pairs, 1)],
        "ratio": [round(res.observed_pairs / res.null_mean_pairs, 3)],
        "p_pairs": [round(res.p_pairs, 4)],
        "multi_domain_people": [res.observed_multi],
        "null_mean_multi_people": [round(res.null_mean_multi, 1)],
        "reject_h0": [res.p_pairs < float(config.analysis()["alpha"])]})
    rows = []
    for col in ("manufacturer", "dose"):
        for (val,), g in m.group_by([col]):
            if g.height < MIN_STRATUM:
                continue
            Xs = g.select(domains).to_numpy().astype(bool)
            r = stats.cooccurrence_test(Xs, domains, permutations=permutations, seed=SEED)
            rows.append({"stratum": f"{col}={val}", "people": g.height, "domains": len(domains),
                         "observed_pairs": r.observed_pairs,
                         "null_mean_pairs": round(r.null_mean_pairs, 1),
                         "ratio": round(r.observed_pairs / r.null_mean_pairs, 3)
                         if r.null_mean_pairs else None,
                         "p_pairs": round(r.p_pairs, 4), "multi_domain_people": r.observed_multi,
                         "null_mean_multi_people": round(r.null_mean_multi, 1),
                         "reject_h0": r.p_pairs < float(config.analysis()["alpha"])})
    strata = pl.DataFrame(rows).sort("stratum") if rows else summary.clear()
    prevalence = pl.DataFrame({"domain": domains, "people": X.sum(0).astype(np.int64),
                               "share": (X.mean(0)).round(4)})
    return {"summary": safe(summary), "strata": safe(strata), "pairs": _safe_pairs(pairs), "prevalence": safe(prevalence)}


def _safe_pairs(pairs: pl.DataFrame) -> pl.DataFrame:
    return safe(pairs.rename({"both_people": "people"})).rename({"people": "both_people"})


def q1_vaers(domains: list[str], permutations: int, zip_path: Path | None = None,
             years=range(2020, 2027)) -> dict[str, pl.DataFrame]:
    """Replication: layer 1 on VAERS SYMPTOM_TEXT of COVID-19 vaccine reports, same test.
    One row per report. Text is read in memory and never written or returned."""
    from .classify.lexicon import Lexicon
    from .themes import TAXONOMY

    zip_path = zip_path or config.DATA_DIR / "raw" / "vaers" / "AllVAERSDataCSVS.zip"
    lex = Lexicon.load(TAXONOMY)
    idx = {t: j for j, t in enumerate(domains)}
    rows = []
    with zipfile.ZipFile(zip_path) as z:
        for y in years:
            if f"{y}VAERSDATA.csv" not in z.namelist():
                continue
            vax = pl.read_csv(io.BytesIO(z.read(f"{y}VAERSVAX.csv")), encoding="latin1",
                              infer_schema_length=0, columns=["VAERS_ID", "VAX_TYPE"])
            covid = set(vax.filter(pl.col("VAX_TYPE").str.starts_with("COVID19"))["VAERS_ID"])
            data = pl.read_csv(io.BytesIO(z.read(f"{y}VAERSDATA.csv")), encoding="latin1",
                               infer_schema_length=0, columns=["VAERS_ID", "SYMPTOM_TEXT"])
            data = data.filter(pl.col("VAERS_ID").is_in(list(covid)))
            for t in data["SYMPTOM_TEXT"].to_list():
                r = np.zeros(len(domains), dtype=bool)
                for lab in lex.classify(t or "")[0]:
                    if lab.theme in idx:
                        r[idx[lab.theme]] = True
                rows.append(r)
            del data, vax
    X = np.vstack(rows)
    res, pairs = q1_test(X, domains, permutations)
    summary = pl.DataFrame({
        "stratum": ["vaers_covid_reports"], "people": [X.shape[0]], "domains": [len(domains)],
        "observed_pairs": [res.observed_pairs], "null_mean_pairs": [round(res.null_mean_pairs, 1)],
        "ratio": [round(res.observed_pairs / res.null_mean_pairs, 3)],
        "p_pairs": [round(res.p_pairs, 4)], "multi_domain_people": [res.observed_multi],
        "null_mean_multi_people": [round(res.null_mean_multi, 1)],
        "reject_h0": [res.p_pairs < float(config.analysis()["alpha"])]})
    prevalence = pl.DataFrame({"domain": domains, "people": X.sum(0).astype(np.int64),
                               "share": X.mean(0).round(4)})
    return {"summary": safe(summary), "pairs": _safe_pairs(pairs), "prevalence": safe(prevalence)}


def q1_text_matched(con, domains: list[str], permutations: int) -> dict[str, pl.DataFrame]:
    """Exploratory: the Q1 test under nulls that keep each domain's frequency within strata of
    how much long-term text the person-dose wrote (deciles of characters; entries x deciles).
    """
    m = q1_matrix(con, domains)
    X = m.select(domains).to_numpy().astype(bool)
    chars = m["chars"].fill_null(0).to_numpy()
    n_ent = m["n_entries"].fill_null(1).to_numpy()
    dec = np.searchsorted(np.quantile(chars, np.linspace(0, 1, 11)[1:-1]), chars)
    fine = np.minimum(n_ent, 4) * 10 + dec        # 1, 2, 3, 4+ entries x decile
    rows, pair_tabs = [], []
    k = len(domains)
    iu = np.triu_indices(k, 1)
    for name, st in [("unmatched (registered)", None), ("matched: character deciles", dec),
                     ("matched: entries x character deciles", fine)]:
        r = stats.cooccurrence_test(X, domains, permutations=permutations, seed=SEED, strata=st)
        rows.append({"null": name, "people": X.shape[0],
                     "strata": 1 if st is None else int(np.unique(st).size),
                     "observed_pairs": r.observed_pairs,
                     "null_mean_pairs": round(r.null_mean_pairs, 1),
                     "ratio": round(r.observed_pairs / r.null_mean_pairs, 3),
                     "p_pairs": round(r.p_pairs, 4),
                     "pairs_above_null_holm": int((stats.holm(r.pair_p[iu]) < 0.05).sum())})
        if st is not None:
            exp = np.zeros((k, k))
            for v in np.unique(st):
                idx = st == v
                mm = X[idx].sum(0).astype(float)
                exp += np.outer(mm, mm) / idx.sum()
            pair_tabs.append(pl.DataFrame({
                "null": name, "domain_a": [domains[i] for i in iu[0]],
                "domain_b": [domains[j] for j in iu[1]],
                "both_people": r.pair_observed[iu].astype(np.int64),
                "expected_people": exp[iu].round(1),
                "ratio": (r.pair_observed[iu] / exp[iu]).round(3),
                "p_holm": stats.holm(r.pair_p[iu]).round(4)}))
    amount = safe(pl.DataFrame({"character_decile": np.arange(10),
                                "people": np.bincount(dec, minlength=10),
                                "mean_domains": [round(float(X[dec == d].sum(1).mean()), 3)
                                                 for d in range(10)]}))
    return {"summary": safe(pl.DataFrame(rows)),
            "pairs": _safe_pairs(pl.concat(pair_tabs)), "by_amount": amount}


def exclusion_variants(con, permutations: int, match_sets: dict | None = None) -> dict:
    """Exploratory: group sizes, Q2 and Q3 under the two other exclusion readings."""
    out = {}
    for variant in ("lexicon", "none"):
        table = f"phenotype_groups_excl_{variant}"
        phenotype.build(con, exclusion=variant, table=table)
        out[f"{variant}_groups"] = group_table(con, table)
        for k, df in q2(con, groups=table).items():
            out[f"{variant}_q2_{k}"] = df
        if match_sets:
            for k, df in q3(con, match_sets, permutations, groups=table).items():
                if df is not None:
                    out[f"{variant}_q3_{k}"] = df
    return out


# --- Q2 -----------------------------------------------------------------------------------------

def q2(con, groups: str = "phenotype_groups") -> dict[str, pl.DataFrame]:
    on = frame(con, f"""
        WITH c AS (SELECT registrant, dose_number FROM {groups} WHERE grp = 'case'),
             cd AS (SELECT DISTINCT d.registrant, d.dose_number, d.theme FROM ph_dom d
                    JOIN c USING (registrant, dose_number) WHERE d.rnk >= 3),
             first_ AS (SELECT d.registrant, d.dose_number, min(d.rnk) AS onset FROM ph_dom d
                        JOIN cd USING (registrant, dose_number, theme) GROUP BY ALL),
             p0 AS (SELECT r.registrant, r.dose_number,
                           avg((r.rnk <= 2)::INT) AS p0 FROM ph_rank r
                    JOIN c USING (registrant, dose_number) GROUP BY ALL)
        SELECT f.onset, p.p0 FROM first_ f JOIN p0 p USING (registrant, dose_number)""")
    early = (on["onset"] <= 2).to_numpy()
    res = stats.onset_test(early, on["p0"].to_numpy())
    onset_dist = safe(on.group_by("onset").agg(pl.len().alias("people")).sort("onset")
                      .with_columns(pl.col("onset").replace_strict(
                          {v: k for k, v in SURVEY_RANK.items()}).alias("onset_survey")))
    onset = safe(pl.DataFrame({"people": [res.cases], "early_onset_people": [res.early],
                               "expected_early": [round(res.expected, 1)],
                               "observed_share": [round(res.early / res.cases, 4)],
                               "expected_share": [round(res.expected / res.cases, 4)],
                               "p_one_sided": [res.p]}))
    pers = frame(con, f"""
        WITH g AS (SELECT registrant, dose_number, grp FROM {groups}
                   WHERE grp IN ('case', 'severe_w1_recovered')),
             ref AS (SELECT l.registrant, l.dose_number, g.grp,
                            min(l.rnk) FILTER (WHERE g.grp = 'severe_w1_recovered'
                                               OR l.worse OR l.impact) AS ref,
                            max(l.rnk) AS last_survey
                     FROM ph_lt l JOIN g USING (registrant, dose_number) GROUP BY ALL),
             dm AS (SELECT d.registrant, d.dose_number, max(d.rnk) AS last_domain
                    FROM ph_dom d SEMI JOIN g USING (registrant, dose_number)
                    WHERE d.rnk >= 3 GROUP BY ALL),
             later AS (SELECT f.grp, f.last_survey > f.ref AS has_later,
                              coalesce(dm.last_domain, 0) > f.ref AS persists
                       FROM ref f LEFT JOIN dm USING (registrant, dose_number)
                       WHERE f.ref IS NOT NULL)
        SELECT grp, count(*) FILTER (WHERE has_later) AS n,
               count(*) FILTER (WHERE has_later AND persists) AS x
        FROM later GROUP BY grp""")
    d = {r["grp"]: (r["x"], r["n"]) for r in pers.iter_rows(named=True)}
    x1, n1 = d.get("case", (0, 0))
    x2, n2 = d.get("severe_w1_recovered", (0, 0))
    rd = stats.risk_difference(x1, n1, x2, n2) if n1 and n2 else None
    persistence = safe(pl.DataFrame({
        "case_people": [n1], "case_persist_people": [x1],
        "group_c_people": [n2], "group_c_persist_people": [x2],
        "case_share": [rd and round(rd.p1, 4)], "group_c_share": [rd and round(rd.p2, 4)],
        "risk_difference": [rd and round(rd.diff, 4)], "ci_low": [rd and round(rd.lower, 4)],
        "ci_high": [rd and round(rd.upper, 4)], "p_one_sided": [rd and rd.p_one_sided]}))
    return {"onset": onset, "onset_distribution": onset_dist, "persistence": persistence}


# --- Q3 -----------------------------------------------------------------------------------------

def _person_groups(con, groups: str = "phenotype_groups") -> None:
    con.execute(f"""CREATE OR REPLACE TEMP TABLE q3_people AS
        SELECT registrant,
               CASE WHEN bool_or(grp = 'case') THEN 'case'
                    WHEN bool_or(grp = 'acute_event') THEN 'acute_event' END AS grp
        FROM {groups} GROUP BY registrant
        HAVING bool_or(grp IN ('case', 'acute_event'))""")
    con.execute("""CREATE OR REPLACE TEMP TABLE q3_cc AS
        SELECT DISTINCT e.registrant FROM entry_outcomes o JOIN entries_survey e USING (entry_id)
        WHERE o.vaers_filed""")


def vaers_symptoms(con, zip_path: Path | None = None, years=range(2020, 2027)) -> int:
    """Load VAERS PT codes (VAERSSYMPTOMS, COVID era) into vaers_pt(vaers_id, pt)."""
    zip_path = zip_path or config.DATA_DIR / "raw" / "vaers" / "AllVAERSDataCSVS.zip"
    if one(con, "SELECT count(*) FROM duckdb_tables() WHERE table_name = 'vaers_pt'")[0]:
        return one(con, "SELECT count(*) FROM vaers_pt")[0]
    frames = []
    with zipfile.ZipFile(zip_path) as z:
        for y in years:
            name = f"{y}VAERSSYMPTOMS.csv"
            if name not in z.namelist():
                continue
            df = pl.read_csv(io.BytesIO(z.read(name)), encoding="latin1",
                             infer_schema_length=0)
            frames.append(df.unpivot(index="VAERS_ID", on=[f"SYMPTOM{i}" for i in range(1, 6)],
                                     value_name="pt").select("VAERS_ID", "pt"))
    pts = pl.concat(frames).filter(pl.col("pt").is_not_null() & (pl.col("pt") != ""))
    pts = pts.rename({"VAERS_ID": "vaers_id"})
    con.register("_pts", pts.to_arrow())
    con.execute("CREATE TABLE vaers_pt AS SELECT trim(vaers_id) AS vaers_id, pt FROM _pts")
    con.unregister("_pts")
    return pts.height


def q3(con, match_sets: dict[str, pl.DataFrame], permutations: int,
       groups: str = "phenotype_groups") -> dict[str, pl.DataFrame]:
    _person_groups(con, groups)
    vaers_symptoms(con)
    cap_rows, disp_rows = [], []
    for name, ms in match_sets.items():
        con.register("_ms", ms.with_columns(pl.col("vaers_id").cast(pl.String)).to_arrow())
        c = frame(con, """
            SELECT p.grp, count(*) AS people,
                   count(*) FILTER (WHERE p.registrant IN (SELECT registrant FROM q3_cc)
                                    OR p.registrant IN (SELECT registrant FROM _ms))
                       AS vaers_people,
                   count(*) FILTER (WHERE p.registrant IN (SELECT registrant FROM _ms))
                       AS matched_people
            FROM q3_people p GROUP BY p.grp""")
        d = {r["grp"]: r for r in c.iter_rows(named=True)}
        a, b = d.get("case"), d.get("acute_event")
        rr = stats.risk_ratio(a["vaers_people"], a["people"], b["vaers_people"], b["people"])
        cap_rows.append({"match_set": name, "case_people": a["people"],
                         "case_vaers_people": a["vaers_people"],
                         "case_matched_people": a["matched_people"],
                         "group_b_people": b["people"], "group_b_vaers_people": b["vaers_people"],
                         "group_b_matched_people": b["matched_people"],
                         "case_rate": round(a["vaers_people"] / a["people"], 4),
                         "group_b_rate": round(b["vaers_people"] / b["people"], 4),
                         "rate_ratio": round(rr.ratio, 4), "ci_low": round(rr.lower, 4),
                         "ci_high": round(rr.upper, 4), "lower_capture": rr.lower_capture})
        pts = frame(con, """
            SELECT p.grp, p.registrant, v.pt FROM q3_people p JOIN _ms m USING (registrant)
            JOIN vaers_pt v ON v.vaers_id = trim(m.vaers_id)""")
        con.unregister("_ms")
        pc = pts.filter(pl.col("grp") == "case")
        pb = pts.filter(pl.col("grp") == "acute_event")
        if pc.height and pb.height:
            r = stats.dispersion_test(pc["pt"].to_numpy(), pb["pt"].to_numpy(),
                                      permutations=permutations, seed=SEED)
            disp_rows.append({"match_set": name,
                              "case_people": pc["registrant"].n_unique(),
                              "case_pt_codes": pc.height, "case_distinct_pts": pc["pt"].n_unique(),
                              "group_b_people": pb["registrant"].n_unique(),
                              "group_b_pt_codes": pb.height,
                              "group_b_distinct_pts": pb["pt"].n_unique(),
                              "entropy_cases": round(r.entropy_cases, 4),
                              "entropy_group_b": round(r.entropy_comparison, 4),
                              "difference": round(r.diff, 4), "p_one_sided": r.p})
    return {"capture": safe(pl.DataFrame(cap_rows)),
            "dispersion": safe(pl.DataFrame(disp_rows)) if disp_rows else None}


# --- Q4 and attrition (descriptive) -------------------------------------------------------------

def q4(con) -> pl.DataFrame:
    return safe(frame(con, """
        WITH g AS (SELECT registrant, dose_number, grp FROM phenotype_groups
                   WHERE in_denominator OR grp = 'acute_event'),
             lt AS (SELECT registrant, dose_number, bool_or(impact) AS impact
                    FROM ph_lt GROUP BY ALL),
             care AS (SELECT DISTINCT e.registrant, e.dose_number FROM entries_survey e
                      SEMI JOIN ph_lt l ON l.response_id = e.response_id
                      WHERE coalesce(e.medical_care, '') NOT IN ('', 'N/A')),
             cc AS (SELECT DISTINCT e.registrant, e.dose_number FROM entry_outcomes o
                    JOIN entries_survey e USING (entry_id) WHERE o.cc_cases > 0)
        SELECT g.grp, count(*) AS person_doses, count(DISTINCT g.registrant) AS people,
               round(1000 * avg(coalesce(lt.impact, false)::INT), 1) AS lt_impact_per_1000,
               round(1000 * avg((care.registrant IS NOT NULL)::INT), 1) AS lt_care_per_1000,
               round(1000 * avg((cc.registrant IS NOT NULL)::INT), 1) AS cc_case_per_1000
        FROM g LEFT JOIN lt USING (registrant, dose_number)
        LEFT JOIN care USING (registrant, dose_number) LEFT JOIN cc USING (registrant, dose_number)
        GROUP BY g.grp ORDER BY g.grp"""))


def attrition(con) -> pl.DataFrame:
    """Case prevalence among long-term responders, bounded over early-only non-responders."""
    d = one(con, """
        WITH ever AS (SELECT DISTINCT registrant, dose_number FROM ph_rank),
             resp AS (SELECT DISTINCT registrant, dose_number FROM ph_lt)
        SELECT (SELECT count(*) FROM resp),
               (SELECT count(*) FROM ever) - (SELECT count(*) FROM resp),
               (SELECT count(*) FROM phenotype_groups WHERE grp = 'case')""")
    resp, nonresp, cases = d
    b = stats.attrition_bounds(cases, resp, nonresp)
    sev = frame(con, """
        WITH w AS (SELECT registrant, dose_number, bool_or(impact) AS w1_impact
                   FROM ph_rank WHERE rnk = 1 GROUP BY ALL),
             resp AS (SELECT DISTINCT registrant, dose_number FROM ph_lt)
        SELECT CASE WHEN w1_impact THEN 'week1_impact' ELSE 'week1_no_impact' END AS week1,
               count(*) AS people, round(avg((r.registrant IS NOT NULL)::INT), 4)
                   AS long_term_response
        FROM w LEFT JOIN resp r USING (registrant, dose_number) GROUP BY 1 ORDER BY 1""")
    bounds = pl.DataFrame({"week1": ["bounds"], "people": [resp + nonresp],
                           "long_term_response": [round(resp / (resp + nonresp), 4)],
                           "case_people": [cases], "prevalence_observed": [round(b.observed, 5)],
                           "prevalence_lower": [round(b.lower, 5)],
                           "prevalence_upper": [round(b.upper, 4)]})
    # suppress each part on its own people columns: in a diagonal concat the bounds-only
    # columns are null in the severity rows and would blank them
    return pl.concat([safe(sev), safe(bounds)], how="diagonal")


# --- Exploratory onset checks (not registered) ---------------------------------------------

# Week-1 check-in fields that map onto a PACVS domain. Only three domains have one.
STRUCTURED_FIELDS = {
    "fatigue_pem": (["FATIGUE"], ["Fatigue or tiredness"]),
    "pain": (["HEADACHE", "JOINT_PAINS", "MUSCLE_OR_BODY_ACHES"],
             ["Headache", "Joint pains", "Muscle or body aches"]),
    "gastrointestinal": (["NAUSEA", "DIARRHEA", "VOMITING", "ABDOMINAL_PAIN"],
                         ["Nausea", "Diarrhea", "Vomiting", "Abdominal pain"]),
}


def _week1_structured(con, groups: str = "phenotype_groups") -> None:
    """w1_struct(registrant, dose_number, fatigue_pem, pain, gastrointestinal): whether any
    week-1 check-in of the person-dose ticked a symptom in each domain (raw check-in files)."""
    glob = str(config.DATA_DIR / "interim" / "health_checkins" / "*.parquet").replace("\\", "/")
    parts = []
    for dom, (cols, toks) in STRUCTURED_FIELDS.items():
        c = " OR ".join(f"{x} IS NOT NULL" for x in cols)
        t = " OR ".join(f"list_contains(string_split(coalesce(SYSTEMIC_REACTION, ''), ':'), '{x}')"
                        for x in toks)
        parts.append(f"({c} OR {t}) AS {dom}")
    # Only cases' week-1 check-ins plus a 1-in-20 sample of the other denominator person-doses
    # (for the by-group rates): joining all 60M week-1 check-ins thrashes the external drive.
    con.execute(f"""CREATE OR REPLACE TEMP TABLE w1_ids AS
        SELECT r.response_id, r.registrant, r.dose_number, g.grp
        FROM ph_rank r JOIN {groups} g USING (registrant, dose_number)
        WHERE r.rnk = 1 AND (g.grp = 'case'
              OR (g.in_denominator AND hash(r.registrant || '|' || r.dose_number) % 20 = 0))""")
    cols = sorted({c for cs, _ in STRUCTURED_FIELDS.values() for c in cs})
    con.execute(f"""CREATE OR REPLACE TEMP TABLE w1_struct AS
        SELECT i.registrant, i.dose_number, any_value(i.grp) AS grp,
               bool_or(s.fatigue_pem) AS fatigue_pem, bool_or(s.pain) AS pain,
               bool_or(s.gastrointestinal) AS gastrointestinal
        FROM (SELECT response_id, {", ".join(parts)} FROM
              (SELECT RESPONSE_ID AS response_id, SYSTEMIC_REACTION, {", ".join(cols)}
               FROM read_parquet('{glob}', union_by_name = true)
               WHERE RESPONSE_ID IN (SELECT response_id FROM w1_ids))) s
        JOIN w1_ids i USING (response_id) GROUP BY i.registrant, i.dose_number""")


def onset_structured(con, groups: str = "phenotype_groups") -> dict[str, pl.DataFrame]:
    """Among cases whose long-term case domains include fatigue, pain or gastrointestinal
    symptoms: share with a week-1 structured report of one of those same domains, against the
    share whose week-1 free text named one. Plus the week-1 structured rate by group."""
    _week1_structured(con, groups)
    cases = safe(frame(con, f"""
        WITH c AS (SELECT registrant, dose_number FROM {groups} WHERE grp = 'case'),
             cd AS (SELECT DISTINCT d.registrant, d.dose_number, d.theme FROM ph_dom d
                    JOIN c USING (registrant, dose_number)
                    WHERE d.rnk >= 3 AND d.theme IN ('fatigue_pem', 'pain', 'gastrointestinal')),
             per AS (SELECT cd.registrant, cd.dose_number,
                            bool_or(CASE cd.theme WHEN 'fatigue_pem' THEN w.fatigue_pem
                                    WHEN 'pain' THEN w.pain ELSE w.gastrointestinal END)
                                AS struct_early,
                            bool_or(EXISTS (SELECT 1 FROM ph_dom d2
                                    WHERE d2.registrant = cd.registrant
                                      AND d2.dose_number = cd.dose_number
                                      AND d2.theme = cd.theme AND d2.rnk <= 2)) AS text_early,
                            bool_or(w.registrant IS NOT NULL) AS has_w1
                     FROM cd LEFT JOIN w1_struct w USING (registrant, dose_number) GROUP BY ALL)
        SELECT count(*) AS people, count(*) FILTER (WHERE has_w1) AS with_week1_checkin,
               count(*) FILTER (WHERE struct_early) AS structured_early_people,
               count(*) FILTER (WHERE text_early) AS text_early_people,
               count(*) FILTER (WHERE struct_early OR text_early) AS either_early_people,
               round(count(*) FILTER (WHERE struct_early) / count(*) FILTER (WHERE has_w1), 4)
                   AS structured_early_share_of_week1_responders,
               round(count(*) FILTER (WHERE text_early) / count(*), 4) AS text_early_share
        FROM per"""))
    by_group = safe(frame(con, f"""
        SELECT g.grp, count(*) AS people,
               round(avg(w.fatigue_pem::INT), 4) AS week1_fatigue,
               round(avg(w.pain::INT), 4) AS week1_pain,
               round(avg(w.gastrointestinal::INT), 4) AS week1_gastrointestinal
        FROM {groups} g JOIN w1_struct w USING (registrant, dose_number)
        WHERE g.in_denominator GROUP BY 1 ORDER BY 1"""))
    return {"cases": cases, "by_group": by_group}


def onset_symmetric(con, model: str, groups: str = "phenotype_groups") -> pl.DataFrame:
    """Q2 onset again with layer 3 also applied to cases' week-1 / six-week residue text
    (entries_cases_early), and under a second null: onset uniform over the survey TYPES the
    case completed, not over check-ins."""
    pacvs = ", ".join(repr(t) for t in pacvs_domains())
    con.execute(f"""CREATE OR REPLACE TEMP TABLE early_l3 AS
        SELECT DISTINCT e.registrant, e.dose_number, unnest(l.themes) AS theme, r.rnk
        FROM entries_cases_early e JOIN ph_rank r USING (response_id)
        JOIN llm_labels l ON l.text_hash = md5(e.text) AND l.model = '{model}'
             AND l.prompt_version = '{PROMPT_VERSION}' AND l.ok
        WHERE NOT coalesce(e.redacted, false)
          AND NOT EXISTS (SELECT 1 FROM final_flags f WHERE f.entry_id = e.entry_id
                          AND f.pre_vaccine)""")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE dom_sym AS
        SELECT registrant, dose_number, theme, rnk FROM ph_dom
        UNION SELECT registrant, dose_number, theme, rnk FROM early_l3 WHERE theme IN ({pacvs})""")
    rows = []
    for label, tbl in [("registered: layer 1 only on early text", "ph_dom"),
                       ("symmetric: layer 3 also on cases' early residue", "dom_sym")]:
        on = frame(con, f"""
            WITH c AS (SELECT registrant, dose_number FROM {groups} WHERE grp = 'case'),
                 cd AS (SELECT DISTINCT d.registrant, d.dose_number, d.theme FROM {tbl} d
                        JOIN c USING (registrant, dose_number) WHERE d.rnk >= 3),
                 first_ AS (SELECT d.registrant, d.dose_number, min(d.rnk) AS onset FROM {tbl} d
                            JOIN cd USING (registrant, dose_number, theme) GROUP BY ALL),
                 p0 AS (SELECT r.registrant, r.dose_number,
                               avg((r.rnk <= 2)::INT) AS p0_checkins,
                               count(DISTINCT r.rnk) FILTER (WHERE r.rnk <= 2)
                                   / count(DISTINCT r.rnk)::DOUBLE AS p0_types
                        FROM ph_rank r JOIN c USING (registrant, dose_number) GROUP BY ALL)
            SELECT f.onset, p.p0_checkins, p.p0_types
            FROM first_ f JOIN p0 p USING (registrant, dose_number)""")
        early = (on["onset"] <= 2).to_numpy()
        r1 = stats.onset_test(early, on["p0_checkins"].to_numpy())
        r2 = stats.onset_test(early, on["p0_types"].to_numpy())
        rows.append({"classifier": label, "people": r1.cases, "early_onset_people": r1.early,
                     "observed_share": round(r1.early / r1.cases, 4),
                     "expected_share_checkin_null": round(r1.expected / r1.cases, 4),
                     "p_checkin_null": r1.p,
                     "expected_share_survey_type_null": round(r2.expected / r2.cases, 4),
                     "p_survey_type_null": r2.p,
                     "labelled_early_entries": one(con, "SELECT count(*) FROM early_l3")[0]})
    return safe(pl.DataFrame(rows))
