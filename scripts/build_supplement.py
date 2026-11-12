"""Write docs/submission/supplement.md from the aggregate files (tables only, all suppressed).

Usage: python scripts/build_supplement.py
Tables that are not yet computed are listed as pending.
"""

from __future__ import annotations

import sys
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vsafe_ft import config

AGG = config.DATA_DIR / "aggregates" / config.DB_NAME
OUT = Path(__file__).resolve().parents[1] / "docs" / "submission" / "supplement.md"

# (title, file, columns to show or None for all, note)
TABLES = [
    ("S1. Q1 co-occurrence by stratum (registered)", "analysis_sens9_q1_strata.csv",
     ["stratum", "people", "observed_pairs", "null_mean_pairs", "ratio", "p_pairs", "reject_h0"],
     "p = 0.001 is the smallest value possible with 1,000 permutations. Strata with fewer than 1,000 person-doses were not tested."),
    ("S2. Q1 domain pairs under the registered null", "analysis_sens9_q1_pairs.csv",
     ["domain_a", "domain_b", "both_people", "expected_people", "p", "p_holm"], None),
    ("S3. Q1 domain pairs under the text-matched nulls (not pre-registered)", "analysis_expl_q1_textmatched_pairs.csv",
     ["null", "domain_a", "domain_b", "both_people", "expected_people", "ratio", "p_holm"], None),
    ("S4. Mean domains per person-dose by decile of long-term characters", "analysis_expl_q1_textmatched_by_amount.csv",
     ["character_decile", "people", "mean_domains"], None),
    ("S5. Q1 domain pairs under the curveball null (not pre-registered)", "sub_b2_curveball_pairs.csv",
     ["null", "domain_a", "domain_b", "both_people", "expected_people", "ratio", "p_upper", "p_lower", "p_upper_holm"],
     "Both margins fixed: each person-dose's domain count and each domain's frequency. The total pair count is invariant under this null."),
    ("S6. Curveball null, summary", "sub_b2_curveball_summary.csv", None, None),
    ("S7. Q1 replication on VAERS COVID-19 report text, domain pairs", "analysis_sens9_q1_vaers_pairs.csv",
     ["domain_a", "domain_b", "both_people", "expected_people", "p", "p_holm"], None),
    ("S8. Q1 replication on VAERS, domain prevalence", "analysis_sens9_q1_vaers_prevalence.csv", None, None),
    ("S9. Onset survey of cases (registered classifier)", "analysis_sens9_q2_onset_distribution.csv",
     ["onset_survey", "people"], None),
    ("S10. Exclusion-criterion variants: groups (keyword tags only)", "analysis_expl_excl_lexicon_groups.csv", None, None),
    ("S11. Exclusion-criterion variants: groups (no criterion 3)", "analysis_expl_excl_none_groups.csv", None, None),
    ("S12. Exclusion-criterion variants: Q3 recorded VAERS filing (keyword tags only)", "analysis_expl_excl_lexicon_q3_capture.csv", None, None),
    ("S13. Exclusion-criterion variants: Q3 recorded VAERS filing (no criterion 3)", "analysis_expl_excl_none_q3_capture.csv", None, None),
    ("S14. Persistence by case route and comparison group (not pre-registered)", "sub_b3_persistence.csv", None, None),
    ("S15. Week-1 structured answers, cases with the domain vs group (a) (not pre-registered)", "sub_b4_structured_vs_a.csv", None,
     "Group (a) is a 1-in-20 sample of person-doses; its week-1 impact is 0 by construction (person-doses with a week-1 impact fall in group (c))."),
    ("S16. Validation audit: disagreements between layer 3 and CDC coding, by domain", "sub_b5_audit_pool.csv", None,
     "Entry-domain pairs. The coded sample result is pending human coding."),
    ("S17. Q3 dispersion with small-sample corrections (not pre-registered)", "sub_b6_dispersion.csv", None, None),
    ("S18. Q1 and case count with criterion 3 off and with redacted entries included (not pre-registered)", "sub_b7_q1_variants.csv", None, None),
    ("S19. Reconciliation of counts", "sub_b8_reconcile.csv", ["quantity", "value"], None),
    ("S20. Layer-3 runs: tokens and logged cost", "sub_b9_llm_cost.csv",
     ["model", "prompt_version", "runs", "texts", "tokens", "cost_usd_logged", "first_run", "last_run"], None),
    ("S21. Model sensitivity: entries per theme, DeepSeek vs Claude, fixed long-term sample",
     "phase1_llm_model_shift_deepseek_v4_1_flash_residue2000_s1_longterm.csv",
     ["theme", "model1_entries", "model2_entries", "shift", "model_sensitive"], None),
    ("S22. Layer-1 (lexicon only) precision and recall against CDC coding", "validate_meddra_lexicon.csv",
     ["theme", "predicted_entries", "reference_entries", "both_entries", "precision", "recall", "passes_gate"], None),
    ("S23. Final classifier precision and recall against CDC coding", "validate_meddra_final_deepseek-v4_1-flash.csv",
     ["theme", "predicted_entries", "reference_entries", "both_entries", "precision", "precision_lo", "precision_hi",
      "recall", "recall_lo", "recall_hi", "passes_gate"], None),
    ("S24. Share of case person-doses naming each theme in long-term text", "analysis_sens9_case_symptom_shares.csv",
     ["theme", "person_doses", "pct"], None),
    ("S25. Sex, manufacturer and dose by group, % of person-doses", "analysis_sens9_table1.csv",
     ["variable", "category", "grp", "person_doses", "pct"], None),
]


def md_table(df: pl.DataFrame) -> str:
    cols = df.columns
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in df.iter_rows():
        cells = []
        for v in row:
            if v is None:
                cells.append("")
            elif isinstance(v, float):
                cells.append(f"{v:,.4g}" if abs(v) < 1 else f"{v:,.3f}".rstrip("0").rstrip("."))
            elif isinstance(v, int):
                cells.append(f"{v:,}")
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main() -> int:
    parts = ["# Electronic supplementary material",
             "",
             ("A PACVS signature in v-safe free text: a pre-registered study whose primary analysis was not feasible, "
             "with exploratory results. Matthew Halma. All cells have at least 10 people; smaller cells are suppressed (blank)."),
             ""]
    pending = []
    for title, file, cols, note in TABLES:
        path = AGG / file
        if not path.exists():
            pending.append(title)
            parts += [f"## {title}", "", "*Pending: not yet computed.*", ""]
            continue
        df = pl.read_csv(path, infer_schema_length=10000)
        if "suppressed" in df.columns:
            df = df.drop("suppressed")
        if cols:
            df = df.select([c for c in cols if c in df.columns])
        parts += [f"## {title}", "", md_table(df), ""]
        if note:
            parts += [note, ""]
    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"{len(TABLES) - len(pending)} tables written, {len(pending)} pending -> {OUT}")
    for t in pending:
        print("  pending:", t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
