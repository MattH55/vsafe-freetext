"""Trace every number quoted in the manuscript to a frozen aggregate file.

Reads <VSAFE_DATA_DIR>/aggregates/<VSAFE_DB>/ and writes docs/submission/numbers.csv with one row
per number: label, file, row filter, column, value. With --manuscript <text file> it also reports
which values appear in the text (formatted with thousands separators or as given) and which
numbers in the text are not in the list.

Usage: python scripts/manuscript_numbers.py [--manuscript docs/submission/manuscript.txt]
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vsafe_ft import config

AGG = config.DATA_DIR / "aggregates" / config.DB_NAME
OUT = Path(__file__).resolve().parents[1] / "docs" / "submission" / "numbers.csv"

# (label, file, {filter col: value}, column, formatter)
F = lambda x: f"{x:,.0f}"
P1 = lambda x: f"{x:.1f}"
P2 = lambda x: f"{x:.2f}"
P3 = lambda x: f"{x:.3f}"
PCT1 = lambda x: f"{100 * x:.1f}"
PCT2 = lambda x: f"{100 * x:.2f}"
FIN = "validate_meddra_final_deepseek-v4_1-flash.csv"
LEX = "validate_meddra_lexicon.csv"
SHIFT = "phase1_llm_model_shift_deepseek_v4_1_flash_residue2000_s1_longterm.csv"

SPEC = [
    # corpus and groups
    ("entries after de-duplication", "sub_b8_reconcile.csv", {"quantity": "entries after de-duplication"}, "value", F),
    ("entries_raw rows", "sub_b8_reconcile.csv", {"quantity": "entries_raw rows"}, "value", F),
    ("long-term entries", "sub_b8_reconcile.csv", {"quantity": "entries matched to a long-term survey"}, "value", F),
    ("early entries", "sub_b8_reconcile.csv", {"quantity": "entries matched to an early survey"}, "value", F),
    ("unmatched entries", "sub_b8_reconcile.csv", {"quantity": "entries not matched to a survey"}, "value", F),
    ("check-ins linked", "sub_b8_reconcile.csv", {"quantity": "check-ins in the linked table"}, "value", F),
    ("person-doses with any check-in", "sub_b8_reconcile.csv", {"quantity": "person-doses with any check-in (ph_rank)"}, "value", F),
    ("person-doses in any group", "sub_b8_reconcile.csv", {"quantity": "person-doses in any phenotype group"}, "value", F),
    ("case person-doses", "analysis_sens9_groups.csv", {"grp": "case"}, "person_doses", F),
    ("case people", "analysis_sens9_groups.csv", {"grp": "case"}, "people", F),
    ("group a person-doses", "analysis_sens9_groups.csv", {"grp": "no_symptoms"}, "person_doses", F),
    ("group a people", "analysis_sens9_groups.csv", {"grp": "no_symptoms"}, "people", F),
    ("group b person-doses", "analysis_sens9_groups.csv", {"grp": "acute_event"}, "person_doses", F),
    ("group b people", "analysis_sens9_groups.csv", {"grp": "acute_event"}, "people", F),
    ("group b in denominator", "analysis_sens9_groups.csv", {"grp": "acute_event"}, "in_denominator", F),
    ("group c person-doses", "analysis_sens9_groups.csv", {"grp": "severe_w1_recovered"}, "person_doses", F),
    ("group c people", "analysis_sens9_groups.csv", {"grp": "severe_w1_recovered"}, "people", F),
    ("other person-doses", "analysis_sens9_groups.csv", {"grp": "other"}, "person_doses", F),
    ("other people", "analysis_sens9_groups.csv", {"grp": "other"}, "people", F),
    ("other in denominator", "analysis_sens9_groups.csv", {"grp": "other"}, "in_denominator", F),
    ("long-term response share", "analysis_sens9_attrition.csv", {"week1": "bounds"}, "long_term_response", PCT1),
    ("response after week-1 impact", "analysis_sens9_attrition.csv", {"week1": "week1_impact"}, "long_term_response", PCT1),
    ("response without week-1 impact", "analysis_sens9_attrition.csv", {"week1": "week1_no_impact"}, "long_term_response", PCT1),
    ("prevalence observed", "analysis_sens9_attrition.csv", {"week1": "bounds"}, "prevalence_observed", PCT2),
    ("prevalence lower bound", "analysis_sens9_attrition.csv", {"week1": "bounds"}, "prevalence_lower", PCT2),
    ("prevalence upper bound", "analysis_sens9_attrition.csv", {"week1": "bounds"}, "prevalence_upper", PCT1),
    ("cases female share", "analysis_sens9_table1.csv", {"variable": "sex", "category": "Female", "grp": "case"}, "pct", P1),
    ("group a female share", "analysis_sens9_table1.csv", {"variable": "sex", "category": "Female", "grp": "no_symptoms"}, "pct", P1),
    # validation
    ("fatigue precision final", FIN, {"theme": "fatigue_pem"}, "precision", P3),
    ("fatigue recall final", FIN, {"theme": "fatigue_pem"}, "recall", P3),
    ("dysautonomia precision final", FIN, {"theme": "dysautonomia"}, "precision", P3),
    ("dysautonomia recall final", FIN, {"theme": "dysautonomia"}, "recall", P3),
    ("dysautonomia precision lexicon", LEX, {"theme": "dysautonomia"}, "precision", P3),
    ("dysautonomia recall lexicon", LEX, {"theme": "dysautonomia"}, "recall", P3),
    ("sensory recall final", FIN, {"theme": "sensory_neuropathic"}, "recall", P2),
    ("cognitive recall final", FIN, {"theme": "cognitive"}, "recall", P2),
    ("unrelated_cause precision final", FIN, {"theme": "unrelated_cause"}, "precision", P3),
    ("acute_diagnosis precision final", FIN, {"theme": "acute_diagnosis"}, "precision", P3),
    # model shift
    ("fatigue entries deepseek", SHIFT, {"theme": "fatigue_pem"}, "model1_entries", F),
    ("fatigue entries claude", SHIFT, {"theme": "fatigue_pem"}, "model2_entries", F),
    ("fatigue shift", SHIFT, {"theme": "fatigue_pem"}, "shift", P2),
    ("unrelated_cause entries deepseek", SHIFT, {"theme": "unrelated_cause"}, "model1_entries", F),
    ("unrelated_cause entries claude", SHIFT, {"theme": "unrelated_cause"}, "model2_entries", F),
    # Q1
    ("Q1 people", "analysis_sens9_q1_summary.csv", {"stratum": "all"}, "people", F),
    ("Q1 observed pairs", "analysis_sens9_q1_summary.csv", {"stratum": "all"}, "observed_pairs", F),
    ("Q1 null mean pairs", "analysis_sens9_q1_summary.csv", {"stratum": "all"}, "null_mean_pairs", F),
    ("Q1 ratio", "analysis_sens9_q1_summary.csv", {"stratum": "all"}, "ratio", P2),
    ("Q1 p", "analysis_sens9_q1_summary.csv", {"stratum": "all"}, "p_pairs", P3),
    ("Q1 VAERS reports", "analysis_sens9_q1_vaers_summary.csv", {}, "people", F),
    ("Q1 VAERS observed pairs", "analysis_sens9_q1_vaers_summary.csv", {}, "observed_pairs", F),
    ("Q1 VAERS null mean pairs", "analysis_sens9_q1_vaers_summary.csv", {}, "null_mean_pairs", F),
    ("Q1 VAERS ratio", "analysis_sens9_q1_vaers_summary.csv", {}, "ratio", P2),
    ("Q1 matched ratio, character deciles", "analysis_expl_q1_textmatched_summary.csv", {"null": "matched: character deciles"}, "ratio", P2),
    ("Q1 matched ratio, entries x deciles", "analysis_expl_q1_textmatched_summary.csv", {"null": "matched: entries x character deciles"}, "ratio", P2),
    ("Q1 matched null mean, character deciles", "analysis_expl_q1_textmatched_summary.csv", {"null": "matched: character deciles"}, "null_mean_pairs", F),
    ("Q1 matched null mean, entries x deciles", "analysis_expl_q1_textmatched_summary.csv", {"null": "matched: entries x character deciles"}, "null_mean_pairs", F),
    ("mean domains lowest decile", "analysis_expl_q1_textmatched_by_amount.csv", {"character_decile": 0}, "mean_domains", P2),
    ("mean domains highest decile", "analysis_expl_q1_textmatched_by_amount.csv", {"character_decile": 9}, "mean_domains", P2),
    # Q2
    ("Q2 onset cases", "analysis_sens9_q2_onset.csv", {}, "people", F),
    ("Q2 early onset cases", "analysis_sens9_q2_onset.csv", {}, "early_onset_people", F),
    ("Q2 early observed share", "analysis_sens9_q2_onset.csv", {}, "observed_share", PCT1),
    ("Q2 early expected share", "analysis_sens9_q2_onset.csv", {}, "expected_share", PCT1),
    ("Q2 persistence case people", "analysis_sens9_q2_persistence.csv", {}, "case_people", F),
    ("Q2 persistence case persist people", "analysis_sens9_q2_persistence.csv", {}, "case_persist_people", F),
    ("Q2 persistence group c people", "analysis_sens9_q2_persistence.csv", {}, "group_c_people", F),
    ("Q2 persistence group c persist people", "analysis_sens9_q2_persistence.csv", {}, "group_c_persist_people", F),
    ("Q2 persistence case share", "analysis_sens9_q2_persistence.csv", {}, "case_share", PCT1),
    ("Q2 persistence group c share", "analysis_sens9_q2_persistence.csv", {}, "group_c_share", PCT1),
    ("Q2 risk difference", "analysis_sens9_q2_persistence.csv", {}, "risk_difference", PCT1),
    ("symmetric early share", "analysis_expl_onset_symmetric.csv", {"classifier": "symmetric: layer 3 also on cases' early residue"}, "observed_share", PCT1),
    ("survey-type null expected share", "analysis_expl_onset_symmetric.csv", {"classifier": "symmetric: layer 3 also on cases' early residue"}, "expected_share_survey_type_null", PCT1),
    ("structured early share of week-1 responders", "analysis_expl_onset_structured_cases.csv", {}, "structured_early_share_of_week1_responders", PCT1),
    ("text early share", "analysis_expl_onset_structured_cases.csv", {}, "text_early_share", PCT1),
    # Q3
    ("Q3 case people", "analysis_sens9_q3_capture.csv", {"match_set": "main"}, "case_people", F),
    ("Q3 case VAERS people", "analysis_sens9_q3_capture.csv", {"match_set": "main"}, "case_vaers_people", F),
    ("Q3 group b people", "analysis_sens9_q3_capture.csv", {"match_set": "main"}, "group_b_people", F),
    ("Q3 group b VAERS people", "analysis_sens9_q3_capture.csv", {"match_set": "main"}, "group_b_vaers_people", F),
    ("Q3 rate ratio main", "analysis_sens9_q3_capture.csv", {"match_set": "main"}, "rate_ratio", P2),
    ("Q3 CI low main", "analysis_sens9_q3_capture.csv", {"match_set": "main"}, "ci_low", P2),
    ("Q3 CI high main", "analysis_sens9_q3_capture.csv", {"match_set": "main"}, "ci_high", P2),
    ("Q3 entropy cases main", "analysis_sens9_q3_dispersion.csv", {"match_set": "main"}, "entropy_cases", P2),
    ("Q3 entropy group b main", "analysis_sens9_q3_dispersion.csv", {"match_set": "main"}, "entropy_group_b", P2),
    ("Q3 rate ratio, keyword exclusions", "analysis_expl_excl_lexicon_q3_capture.csv", {"match_set": "main"}, "rate_ratio", P2),
    ("Q3 rate ratio, no criterion 3", "analysis_expl_excl_none_q3_capture.csv", {"match_set": "main"}, "rate_ratio", P2),
    ("cases without criterion 3", "analysis_expl_excl_none_groups.csv", {"grp": "case"}, "person_doses", F),
    ("cases with keyword exclusions", "analysis_expl_excl_lexicon_groups.csv", {"grp": "case"}, "person_doses", F),
    # symptom shares
    ("cases pain share", "analysis_sens9_case_symptom_shares.csv", {"theme": "pain"}, "pct", P1),
    ("cases fatigue share", "analysis_sens9_case_symptom_shares.csv", {"theme": "fatigue_pem"}, "pct", P1),
    ("cases cognitive share", "analysis_sens9_case_symptom_shares.csv", {"theme": "cognitive"}, "pct", P1),
    ("cases sleep share", "analysis_sens9_case_symptom_shares.csv", {"theme": "sleep"}, "pct", P1),
    # addendum-2 analyses (sub_*)
    ("curveball observed pairs", "sub_b2_curveball_summary.csv", {"null": "curveball, unstratified"}, "observed_pairs", F),
    ("curveball cognitive-sleep, unstratified", "sub_b2_curveball_pairs.csv", {"null": "curveball, unstratified", "domain_a": "cognitive", "domain_b": "sleep"}, "ratio", P2),
    ("curveball cognitive-sleep, tertiles", "sub_b2_curveball_pairs.csv", {"null": "curveball within text-length tertiles", "domain_a": "cognitive", "domain_b": "sleep"}, "ratio", P2),
    ("curveball cognitive-fatigue, tertiles", "sub_b2_curveball_pairs.csv", {"null": "curveball within text-length tertiles", "domain_a": "cognitive", "domain_b": "fatigue_pem"}, "ratio", P2),
    ("curveball pairs above null, unstratified", "sub_b2_curveball_summary.csv", {"null": "curveball, unstratified"}, "pairs_above_null_holm", F),
    ("same-survey cases", "sub_b3_routes.csv", {"route": "same_survey"}, "person_doses", F),
    ("across-surveys-only cases", "sub_b3_routes.csv", {"route": "across_surveys_only"}, "person_doses", F),
    ("same-survey persistence share", "sub_b3_persistence.csv", {"comparison": "same-survey cases only vs group (c)"}, "case_share", PCT1),
    ("group d persistence share", "sub_b3_persistence.csv", {"comparison": "all cases vs group (d): worse/impacted, < 2 domains"}, "comparison_share", PCT1),
    ("strictest risk difference", "sub_b3_persistence.csv", {"comparison": "same-survey cases vs group (d)"}, "risk_difference", PCT1),
    ("week-1 fatigue, cases", "sub_b4_structured_vs_a.csv", {"domain": "fatigue_pem", "group": "cases with this domain"}, "week1_any", PCT1),
    ("week-1 fatigue, group a", "sub_b4_structured_vs_a.csv", {"domain": "fatigue_pem", "group": "group (a), 1-in-20 sample"}, "week1_any", PCT1),
    ("audit items drawn", "sub_b5_audit_drawn.csv", {"side": "cdc_only", "theme": "pain"}, "entries", F),
    ("entropy cases Miller-Madow", "sub_b6_dispersion.csv", {"match_set": "main"}, "entropy_cases_miller_madow", P2),
    ("entropy group b Miller-Madow", "sub_b6_dispersion.csv", {"match_set": "main"}, "entropy_group_b_miller_madow", P2),
    ("dispersion two-sided p", "sub_b6_dispersion.csv", {"match_set": "main"}, "p_two_sided", P3),
    ("Q1 with redacted, ratio", "sub_b7_q1_variants.csv", {"variant": "redacted entries included"}, "q1_ratio", P3),
    ("Q1 with redacted, people", "sub_b7_q1_variants.csv", {"variant": "redacted entries included"}, "people", F),
    ("raw adult check-in rows", "sub_b8_reconcile.csv", {"quantity": "check-in rows in the raw adult file"}, "value", F),
    ("raw under-3 check-in rows", "sub_b8_reconcile.csv", {"quantity": "check-in rows in the raw under-3 file"}, "value", F),
    ("Levi-Lu enrollees ours", "sub_levilu_counts.csv", {"group": "enrollees"}, "ours", F),
    ("Levi-Lu prolonged_ae ours", "sub_levilu_counts.csv", {"group": "prolonged_ae"}, "ours", F),
    ("Levi-Lu prolonged_ae d1 ours", "sub_levilu_counts.csv", {"group": "prolonged_ae_d1"}, "ours", F),
    ("Levi-Lu prolonged_ae d2 ours", "sub_levilu_counts.csv", {"group": "prolonged_ae_d2"}, "ours", F),
    ("Levi-Lu overlap both", "sub_levilu_overlap.csv", {"cell": "both"}, "people", F),
    ("Levi-Lu overlap text only", "sub_levilu_overlap.csv", {"cell": "text-defined only"}, "people", F),
    ("Levi-Lu overlap theirs only", "sub_levilu_overlap.csv", {"cell": "Levi & Lu only"}, "people", F),
    ("Levi-Lu kappa", "sub_levilu_overlap.csv", {"cell": "Cohen's kappa"}, "value", P2),
]


def lookup(file: str, where: dict, col: str):
    df = pl.read_csv(AGG / file, infer_schema_length=10000)
    for k, v in where.items():
        df = df.filter(pl.col(k).cast(pl.String) == str(v))
    if df.height != 1:
        raise ValueError(f"{file} {where}: {df.height} rows")
    return df[col][0]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manuscript", help="plain-text export of the manuscript")
    a = ap.parse_args()
    text = Path(a.manuscript).read_text(encoding="utf-8") if a.manuscript else None
    rows, missing = [], []
    for label, file, where, col, fmt in SPEC:
        try:
            raw = lookup(file, where, col)
            val = fmt(float(raw))
        except Exception as e:                      # noqa: BLE001  report, keep going
            rows.append({"label": label, "file": file, "row": where, "column": col, "value": f"ERROR {e}", "in_text": ""})
            continue
        present = ("" if text is None else ("yes" if val in text or val.replace(",", "") in text else "NO"))
        if present == "NO":
            missing.append(label)
        rows.append({"label": label, "file": file, "row": where, "column": col, "value": val, "in_text": present})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["label", "file", "row", "column", "value", "in_text"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} numbers -> {OUT}")
    if text is not None:
        print(f"{len(missing)} listed numbers not found in the text: {missing}")
        # numbers in the text that are not in the list (integers >= 1,000 and decimals)
        listed = {r['value'] for r in rows} | {r['value'].replace(',', '') for r in rows}
        found = set(re.findall(r"\d{1,3}(?:,\d{3})+|\d+\.\d+", text))
        unlisted = sorted(n for n in found if n not in listed and n.replace(",", "") not in listed)
        print(f"{len(unlisted)} numbers in the text not traced: {unlisted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
