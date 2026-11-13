"""Command-line entry point: `vsafe-ft <command>`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import config


def cmd_inspect(a):
    """Header row only. Data rows are never printed (free text must not reach a terminal log)."""
    from .ingest import extract_zip, header_row

    path = Path(a.path)
    files = extract_zip(path) if path.suffix.lower() == ".zip" else [path]
    for f in files:
        print(f"{f.name}: {header_row(f)}")


def _file_spec(part: str, name: str) -> dict:
    for f in config.load("sources").get(part, {}).get("files") or []:
        if f.get("name") == name:
            return f
    return {}


def cmd_ingest(a):
    import time

    from .ingest import ingest_file

    part = a.part
    spec = config.load("sources").get(part, {})
    src = Path(a.src) if a.src else config.source_dir(spec)
    out_dir = config.DATA_DIR / "interim" / part
    kinds = ("*.xlsx", "*.zip", "*.csv", "*.txt", "*.tsv")
    files = sorted(f for k in kinds for f in src.glob(k)) if src.is_dir() else [src]
    if a.only:
        files = [f for f in files if f.name in a.only]
    for f in files:
        fs = _file_spec(part, f.name)
        t0 = time.time()
        for out, n in ingest_file(f, out_dir, release=f.stem, under3=bool(fs.get("under3"))):
            print(f"{part}\t{f.name}\t{out.name}\t{n}\t{time.time() - t0:.0f}s")


def cmd_download(a):
    from .download import download

    download(a.only, files=a.files)


def _glob(part: str) -> str:
    return str(config.DATA_DIR / "interim" / part / "*.parquet")


def _have(part: str) -> bool:
    return any((config.DATA_DIR / "interim" / part).glob("*.parquet"))


def _labelled(part: str) -> list[tuple[str, str]]:
    """One (parquet path, release label) per ingested file of a part.

    The label is the file's `release:` in config/sources.yaml when it has one (matched on
    the source file stem, which prefixes the Parquet name), else the Parquet stem.
    """
    from pathlib import Path

    from .ingest import _safe_name

    spec = config.load("sources").get(part) or {}
    labels = {_safe_name(Path(f["name"]).stem): f["release"]
              for f in spec.get("files") or [] if f.get("release")}
    files = sorted((config.DATA_DIR / "interim" / part).glob("*.parquet"))
    return [(str(f), labels.get(f.stem.split("__")[0], f.stem)) for f in files]


def cmd_link(a):
    import time

    from . import link

    con = link.connect()
    t0 = time.time()
    if a.outcomes_only:
        link.link_outcomes(con, _labelled("call_center"))
        _write(link.outcome_summary(con), "phase1_call_center_cases")
        _write(link.outcome_rates(con), "phase1_entry_outcomes")
        print(f"outcomes linked in {time.time() - t0:.0f}s")
        return
    ft = (str(config.DATA_DIR / "interim" / "freetext_updated" / f"{a.release}.parquet")
          if a.release else _glob("freetext_updated"))
    link.build_entries(con, ft)
    if _have("registrants"):
        link.link_registrants(con, _glob("registrants"))
    link.link_dose(con, _glob("vaccinations"))
    link.link_survey(con, _glob("health_checkins"))
    if _have("meddra") and not a.skip_meddra:
        link.link_meddra(con, _labelled("meddra"),
                         field_values=config.load("columns").get("meddra_field_values"))
    if _have("call_center") and not a.skip_outcomes:
        link.link_outcomes(con, _labelled("call_center"))
    rates = link.join_rates(con)
    rates["seconds"] = round(time.time() - t0)
    print(json.dumps(rates, indent=2))


def cmd_gate(a):
    from . import link

    rates = link.join_rates(link.connect())
    need = config.analysis()["join_rate_gate"]
    ok = rates["dose_linked"] >= need and rates["survey_matched"] >= need
    print(json.dumps(rates, indent=2))
    print(f"gate 1 (join rates >= {need}): {'PASS' if ok else 'FAIL - document the reason'}")


def _write(df, name: str) -> None:
    """Write a suppressed table to data/aggregates and print it (aggregates only)."""
    import polars as pl

    from .suppress import assert_safe

    assert_safe(df.filter(~pl.col("suppressed")) if "suppressed" in df.columns else df)
    sub = "" if config.DB_NAME == "vsafe" else config.DB_NAME
    out = config.DATA_DIR / "aggregates" / sub / f"{name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(out)
    with pl.Config(tbl_rows=-1, tbl_cols=-1, fmt_str_lengths=60, tbl_width_chars=200):
        print(f"## {name}  ({out})")
        print(df)


def cmd_classify(a):
    from . import link, themes

    con = link.connect()
    # week-1 / six-week only until OSF registration; --long-term adds 3/6/12-month entries
    # (refused by themes.build_entry_themes before registration)
    n = themes.build_entry_themes(con, long_term=a.long_term)
    print(f"classified {n} entries (layer 1{', incl. long-term' if a.long_term else ''})")
    _write(themes.lexicon_coverage(con), "phase1_lexicon_coverage")
    _write(themes.theme_counts(con), "phase1_theme_counts")
    _write(themes.flag_counts(con), "phase1_flag_counts")


def cmd_explore(a):
    from . import explore, link

    con = link.connect()
    _write(explore.text_length_profile(con), "phase1_length_profile")
    _write(explore.candidate_ngrams(con, n_max=a.n, top=a.top), "phase1_candidate_ngrams")
    if _has_table(con, "entry_meddra"):
        _write(explore.theme_pt_cooccurrence(con), "phase1_theme_pt_cooccurrence")


def cmd_meddra_map(a):
    """Write taxonomy/v0/meddra_map.csv (theme -> PT, dictionary terms, >= k people per PT)."""
    from . import explore, link
    from .classify.lexicon import Lexicon
    from .suppress import assert_safe
    from .themes import TAXONOMY

    con = link.connect()
    df = explore.meddra_theme_map(con, Lexicon.load(TAXONOMY))
    assert_safe(df)
    out = config.REPO_ROOT / "taxonomy" / "v0" / "meddra_map.csv"
    out.write_bytes(df.write_csv().encode("utf-8"))
    print(f"wrote {out} ({df.height} rows, {df['pt'].n_unique()} PTs)")


def _llm(model: str):
    import yaml

    from .classify.llm import make_labeller, theme_list
    from .themes import TAXONOMY

    return make_labeller(theme_list(yaml.safe_load(TAXONOMY.read_text(encoding="utf-8"))), model)


def cmd_llm_label(a):
    """Layer 3 on a sample of week-1 / six-week entries (NanoGPT, zero-data-retention routes)."""
    from . import layer3, link

    con = link.connect()
    for model in a.model:
        run = layer3.label_entries(con, _llm(model), sample=None if a.all else a.sample,
                                   seed=a.seed, residue_only=a.residue, batch=a.batch,
                                   max_usd=a.max_usd, long_term=a.long_term,
                                   workers=a.workers)
        print(json.dumps(run, indent=2))


def cmd_llm_report(a):
    from . import layer3, link

    con = link.connect()
    tag = a.model[0].split("/")[-1].replace(".", "_").replace("-", "_")
    smp = {"sample": a.sample, "seed": a.seed, "residue_only": a.residue,
           "long_term": a.long_term}
    tag += f"_{'residue' if a.residue else 'random'}{a.sample}_s{a.seed}"
    tag += "_longterm" if a.long_term else ""
    _write(layer3.coverage(con, a.model[0], sample=smp), f"phase1_llm_coverage_{tag}")
    _write(layer3.agreement(con, a.model[0], sample=smp), f"phase1_llm_agreement_{tag}")
    if len(a.model) > 1:
        _write(layer3.model_shift(con, a.model[0], a.model[1], sample=smp),
               f"phase1_llm_model_shift_{tag}")


def _has_table(con, name: str) -> bool:
    return bool(con.execute("SELECT count(*) FROM duckdb_tables() WHERE table_name = ?",
                            [name]).fetchall()[0][0])


def cmd_qa(a):
    from . import link

    con = link.connect()
    _write(link.duplicate_report(con), "phase1_duplicates")
    if _have("meddra"):
        _write(link.meddra_coverage(con), "phase1_meddra_coverage")
    if _have("freetext_original"):
        df, cols = link.crosscheck(con, config.DATA_DIR / "interim" / "freetext_original",
                                   config.DATA_DIR / "interim" / "freetext_updated",
                                   registrant_col=config.columns("freetext")["registrant"])
        _write(df, "phase1_crosscheck")
        print(json.dumps(cols, indent=2))


def _theme_names() -> list[str]:
    import yaml

    from .themes import TAXONOMY

    return list(yaml.safe_load(TAXONOMY.read_text(encoding="utf-8"))["themes"])


def cmd_gold(a):
    """Gold set: draw, write blind sheets, load codes, agreement, adjudication, evaluation."""
    from pathlib import Path

    from . import gold, link

    con = link.connect()
    th = _theme_names()
    if a.action == "draw":
        print(json.dumps(gold.draw(con, size=a.size, period=a.period or "early", seed=a.seed), indent=2))
        _write(gold.strata_summary(con), "gold_strata")
    elif a.action == "sheets":
        for c in a.coders:
            print(f"wrote {gold.write_sheet(con, c, th)}")
    elif a.action == "load":
        print(json.dumps(gold.load_codes(con, Path(a.path), a.coder, th), indent=2))
    elif a.action == "agreement":
        _write(gold.agreement(con, *a.coders), "gold_agreement")
    elif a.action == "adjudicate":
        print(f"wrote {gold.write_adjudication(con, *a.coders, th)}")
    elif a.action == "evaluate":
        tag = a.layer if a.layer == "lexicon" else a.model.split("/")[-1].replace(".", "_")
        _write(gold.evaluate(con, *a.coders, layer=a.layer, model=a.model, period=a.period),
               f"gold_eval_{tag}_{a.period or 'all'}")


def cmd_openvsafe(a):
    """Read OpenVSafe's VAERS matches for the call-center people with a VAERS-filed case."""
    import duckdb
    import polars as pl

    from . import openvsafe
    from .suppress import safe

    main_db = config.DATA_DIR / "interim" / "vsafe.duckdb"
    with duckdb.connect(str(main_db), read_only=True) as m:
        regs = [r for (r,) in m.execute(
            "SELECT DISTINCT registrant FROM call_center WHERE vaers_filed "
            "ORDER BY hash(registrant)").fetchall()]
    if a.limit:
        regs = regs[: a.limit]
    con = openvsafe.connect()
    if not a.summary_only:
        print(json.dumps(openvsafe.crawl(con, regs, rate=a.rate), indent=2))
    df = pl.DataFrame(openvsafe.summary(con), schema=["status", "confidence", "people"],
                      orient="row")
    _write(safe(df), "openvsafe_match_summary")


def cmd_validate(a):
    """Precision / recall per theme against CDC MedDRA coding (amendment 1), long-term."""
    from . import link, validate

    con = link.connect()
    tag = a.layer if a.layer == "lexicon" else "final_" + a.model.split("/")[-1].replace(".", "_")
    _write(validate.meddra_reference(con, layer=a.layer, model=a.model), f"validate_meddra_{tag}")


def cmd_analyse(a):
    """Confirmatory Q1-Q3 (+ Q4, attrition) on the final classifier; aggregates only."""
    import json
    import time

    import polars as pl

    from . import analysis, link, openvsafe

    con = link.connect()
    con.execute(f"SET memory_limit = '{a.memory}'")     # stay below RAM: paging stalls joins
    con.execute("SET preserve_insertion_order = false")
    t0 = time.time()
    tag = "sens9"
    a.permutations = a.permutations or int(config.analysis()["permutations"])
    if not a.skip_prepare:
        print(json.dumps(analysis.prepare(con, a.model)), f"{time.time() - t0:.0f}s", flush=True)
    if not a.skip_prepare or not a.skip_helpers:
        analysis.helper_tables(con)
        print(f"helper tables {time.time() - t0:.0f}s", flush=True)
    _write(analysis.group_table(con), f"analysis_{tag}_groups")
    domains = analysis.pacvs_domains()
    sub = "" if config.DB_NAME == "vsafe" else config.DB_NAME
    gate = config.DATA_DIR / "aggregates" / sub / (
        "validate_meddra_final_" + a.model.split("/")[-1].replace(".", "_") + ".csv")
    passing = sorted(set(pl.read_csv(gate).filter(pl.col("passes_gate").fill_null(False))["theme"])
                     & set(domains))
    print(f"primary (passing) domains: {passing}; feasible: {len(passing) >= 2}", flush=True)
    steps = a.steps.split(",")
    if "q1" in steps:
        for k, df in analysis.q1(con, domains, a.permutations).items():
            _write(df, f"analysis_{tag}_q1_{k}")
        print(f"q1 done {time.time() - t0:.0f}s", flush=True)
    if "q2" in steps:
        for k, df in analysis.q2(con).items():
            _write(df, f"analysis_{tag}_q2_{k}")
        print(f"q2 done {time.time() - t0:.0f}s", flush=True)
    if "q3" in steps:
        ov = openvsafe.connect()
        sets = {w: openvsafe.analysis_set(ov, w) for w in openvsafe.MATCH_SETS}
        ov.close()
        for k, df in analysis.q3(con, sets, a.permutations).items():
            if df is not None:
                _write(df, f"analysis_{tag}_q3_{k}")
        print(f"q3 done {time.time() - t0:.0f}s", flush=True)
    if "q4" in steps:
        _write(analysis.q4(con), f"analysis_{tag}_q4")
        _write(analysis.attrition(con), f"analysis_{tag}_attrition")
    if "vaers" in steps:
        for k, df in analysis.q1_vaers(domains, a.permutations).items():
            _write(df, f"analysis_{tag}_q1_vaers_{k}")
        print(f"vaers replication done {time.time() - t0:.0f}s", flush=True)
    # Unregistered checks; every output is labelled expl_. "exploratory" runs all three.
    expl = {"textmatched", "exclusion", "onset"} if "exploratory" in steps else set(steps)
    if "textmatched" in expl:
        for k, df in analysis.q1_text_matched(con, domains, a.permutations).items():
            _write(df, f"analysis_expl_q1_textmatched_{k}")
        print(f"text-matched Q1 done {time.time() - t0:.0f}s", flush=True)
    if "exclusion" in expl:
        ov = openvsafe.connect()
        sets = {w: openvsafe.analysis_set(ov, w) for w in openvsafe.MATCH_SETS}
        ov.close()
        for k, df in analysis.exclusion_variants(con, a.permutations, sets).items():
            _write(df, f"analysis_expl_excl_{k}")
        print(f"exclusion variants done {time.time() - t0:.0f}s", flush=True)
    if "onset" in expl:
        for k, df in analysis.onset_structured(con).items():
            _write(df, f"analysis_expl_onset_structured_{k}")
        _write(analysis.onset_symmetric(con, a.model), "analysis_expl_onset_symmetric")
        print(f"onset checks done {time.time() - t0:.0f}s", flush=True)


def cmd_submission(a):
    """Analyses added for the Drug Safety submission (not pre-registered); outputs sub_*."""
    import json
    import time

    import polars as pl

    from . import link, openvsafe, submission
    from .analysis import pacvs_domains

    con = link.connect()
    con.execute(f"SET memory_limit = '{a.memory}'")
    t0 = time.time()
    perms = a.permutations or int(config.analysis()["permutations"])
    domains = pacvs_domains()
    steps = set(a.steps.split(","))
    def log(m):
        print(f"{m} {time.time() - t0:.0f}s", flush=True)

    if "export" in steps:
        print("matrix ->", submission.export_q1_matrix(con, domains), flush=True)
    if "curveball" in steps:
        for k, df in submission.q1_curveball(domains, perms, log=log).items():
            _write(df, f"sub_b2_curveball_{k}")
        log("B2 done")
    if "persistence" in steps:
        for k, df in submission.persistence_variants(con).items():
            _write(df, f"sub_b3_{k}")
        log("B3 done")
    if "structured" in steps:
        _write(submission.structured_onset_vs_a(con), "sub_b4_structured_vs_a")
        log("B4 done")
    if "audit" in steps:
        r = submission.audit_sample(con, a.model)
        _write(r["pool"], "sub_b5_audit_pool")
        _write(r["drawn"], "sub_b5_audit_drawn")
        print(json.dumps({"sheet": r["sheet"], "items": r["items"]}), flush=True)
        log("B5 done")
    if "dispersion" in steps:
        ov = openvsafe.connect()
        sets = {w: openvsafe.analysis_set(ov, w) for w in openvsafe.MATCH_SETS}
        ov.close()
        _write(submission.q3_dispersion_extended(con, sets, perms), "sub_b6_dispersion")
        log("B6 done")
    if "variants" in steps:
        _write(submission.q1_variants(con, domains, perms), "sub_b7_q1_variants")
        log("B7 done")
    if "reconcile" in steps:
        df = submission.reconcile(con)
        _write(df.with_columns(pl.lit(10**9).alias("people"), pl.lit(False).alias("suppressed")), "sub_b8_reconcile")
        _write(submission.llm_cost(con).with_columns(pl.lit(10**9).alias("people"), pl.lit(False).alias("suppressed")), "sub_b9_llm_cost")
        log("B8/B9 done")
    if "levilu" in steps:           # addendum 1, tasks 3.9 and 5.4 (not pre-registered)
        from . import cohorts
        print(json.dumps(cohorts.prepare(con)), flush=True)
        cohorts.build(con)
        _write(cohorts.counts(con), "sub_levilu_counts")
        _write(cohorts.overlap(con), "sub_levilu_overlap")
        log("Levi & Lu cohorts done")
    if "audit-score" in steps:      # after the protocol owner has coded the sheet (B5)
        _write(submission.audit_score(), "sub_b5_audit_scored")
        log("B5 audit scored")
    if "sex" in steps:              # review of 12 Nov, R1 (not pre-registered)
        for k, df in submission.q1_by_sex(domains, perms, log=log).items():
            _write(df, f"sub_r1_q1_sex_{k}")
        log("R1 done")
    if "core" in steps:             # review of 12 Nov, R2 (aggregates of saved pair tables)
        _write(submission.core_subgraph_tables(), "sub_r2_core_subgraph")
        log("R2 done")


def main(argv=None):
    p = argparse.ArgumentParser(prog="vsafe-ft")
    sub = p.add_subparsers(required=True)

    s = sub.add_parser("inspect", help="print the header row of an .xlsx, .csv or .zip")
    s.add_argument("path")
    s.set_defaults(func=cmd_inspect)

    s = sub.add_parser("download", help="fetch files listed in config/sources.yaml")
    s.add_argument("--only", nargs="*", help="parts (keys of sources.yaml)")
    s.add_argument("--files", nargs="*", help="file names within those parts")
    s.set_defaults(func=cmd_download)

    s = sub.add_parser("ingest", help="convert source files (.xlsx, .csv, .zip) to Parquet")
    s.add_argument("src", nargs="?", help="file or directory (default: the part's raw dir)")
    s.add_argument("--part", default="freetext_updated")
    s.add_argument("--only", nargs="*", help="file names to ingest from the directory")
    s.set_defaults(func=cmd_ingest)

    s = sub.add_parser("link", help="dedupe and link entries to person, dose, survey, MedDRA, outcomes")
    s.add_argument("--release", help="one updated release (file stem), e.g. r01")
    s.add_argument("--skip-meddra", action="store_true")
    s.add_argument("--skip-outcomes", action="store_true")
    s.add_argument("--outcomes-only", action="store_true",
                   help="relink call-center outcomes onto the existing entries")
    s.set_defaults(func=cmd_link)

    s = sub.add_parser("gate", help="report gate-1 join rates")
    s.set_defaults(func=cmd_gate)

    s = sub.add_parser("classify", help="layer-1 entry_themes (week-1/six-week only pre-registration)")
    s.add_argument("--long-term", action="store_true",
                   help="include 3-, 6- and 12-month entries (only after OSF registration)")
    s.set_defaults(func=cmd_classify)

    s = sub.add_parser("explore", help="aggregate-only n-grams of unlabelled entries")
    s.add_argument("-n", type=int, default=3)
    s.add_argument("--top", type=int, default=300)
    s.set_defaults(func=cmd_explore)

    s = sub.add_parser("meddra-map", help="write taxonomy/v0/meddra_map.csv")
    s.set_defaults(func=cmd_meddra_map)
    from .classify.llm import DEFAULT_MODEL

    s = sub.add_parser("llm-label", help="layer 3 on a sample of week-1/six-week entries")
    s.add_argument("--model", nargs="+", default=[DEFAULT_MODEL])
    s.add_argument("--sample", type=int, default=1000, help="entries to sample")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--residue", action="store_true", help="only entries layer 1 left unthemed")
    s.add_argument("--long-term", action="store_true",
                   help="3-, 6- and 12-month entries only (refused before OSF registration)")
    s.add_argument("--all", action="store_true", help="every eligible entry, not a sample")
    s.add_argument("--batch", type=int, default=20, help="entries per request")
    s.add_argument("--workers", type=int, default=1, help="requests sent in parallel")
    s.add_argument("--max-usd", type=float, default=5.0, help="stop when spend reaches this")
    s.set_defaults(func=cmd_llm_label)

    s = sub.add_parser("llm-report", help="layer-3 coverage, agreement, model shift (aggregates)")
    s.add_argument("--model", nargs="+", default=[DEFAULT_MODEL])
    s.add_argument("--sample", type=int, default=1000, help="the run's sample size")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--residue", action="store_true")
    s.add_argument("--long-term", action="store_true", help="the sample was a long-term one")
    s.set_defaults(func=cmd_llm_report)

    s = sub.add_parser("qa", help="duplicate, MedDRA-coverage and original-vs-updated reports")
    s.set_defaults(func=cmd_qa)

    s = sub.add_parser("openvsafe", help="read OpenVSafe's VAERS matches (VAERS-filed people)")
    s.add_argument("--rate", type=float, default=1.0, help="requests per second")
    s.add_argument("--limit", type=int, help="only the first N people (stable order)")
    s.add_argument("--summary-only", action="store_true")
    s.set_defaults(func=cmd_openvsafe)

    s = sub.add_parser("gold", help="gold set: draw | sheets | load | agreement | adjudicate | evaluate")
    s.add_argument("action", choices=["draw", "sheets", "load", "agreement", "adjudicate",
                                      "evaluate"])
    s.add_argument("--size", type=int, default=1000, help="draw: entries for this period")
    s.add_argument("--period", choices=["early", "long_term"], default=None,
                   help="draw (default early) / evaluate (default both)")
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--coders", nargs="+", default=["A", "B"])
    s.add_argument("--coder", help="load: whose sheet (A, B or adjudication)")
    s.add_argument("--path", help="load: the completed sheet")
    s.add_argument("--layer", choices=["lexicon", "llm"], default="lexicon")
    s.add_argument("--model", default=DEFAULT_MODEL)
    s.set_defaults(func=cmd_gold)

    s = sub.add_parser("validate", help="precision/recall vs CDC MedDRA coding (amendment 1)")
    s.add_argument("--layer", choices=["lexicon", "final"], default="lexicon")
    s.add_argument("--model", default=DEFAULT_MODEL, help="layer-3 model for --layer final")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("analyse", help="confirmatory Q1-Q3, Q4 and attrition (aggregates)")
    s.add_argument("--model", default="deepseek/deepseek-v4.1-flash", help="layer-3 model")
    s.add_argument("--steps", default="q1,q2,q3,q4,vaers")
    s.add_argument("--permutations", type=int, default=None)
    s.add_argument("--skip-prepare", action="store_true", help="reuse phenotype tables")
    s.add_argument("--skip-helpers", action="store_true", help="reuse ph_lt / ph_dom tables")
    s.add_argument("--memory", default="6GB", help="DuckDB memory limit")
    s.set_defaults(func=cmd_analyse)

    s = sub.add_parser("submission", help="analyses added for the Drug Safety submission (sub_*)")
    s.add_argument("--model", default="deepseek/deepseek-v4.1-flash")
    s.add_argument("--steps", default="export,curveball,persistence,structured,audit,dispersion,variants,reconcile")
    s.add_argument("--permutations", type=int, default=None)
    s.add_argument("--memory", default="6GB")
    s.set_defaults(func=cmd_submission)

    a = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # polars tables on a cp1252 Windows console
    if a.func is not cmd_inspect:
        config.assert_local_data_dir()
    a.func(a)


if __name__ == "__main__":
    main()
