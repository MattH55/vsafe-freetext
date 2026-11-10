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
    out = config.DATA_DIR / "aggregates" / f"{name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(out)
    with pl.Config(tbl_rows=-1, tbl_cols=-1, fmt_str_lengths=60, tbl_width_chars=200):
        print(f"## {name}  ({out})")
        print(df)


def cmd_classify(a):
    from . import link, themes

    con = link.connect()
    n = themes.build_entry_themes(con)        # week-1 / six-week only until OSF registration
    print(f"classified {n} entries (layer 1)")
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

    from .classify.llm import NanoGPT, theme_list
    from .themes import TAXONOMY

    return NanoGPT(theme_list(yaml.safe_load(TAXONOMY.read_text(encoding="utf-8"))), model=model)


def cmd_llm_label(a):
    """Layer 3 on a sample of week-1 / six-week entries (NanoGPT, zero-data-retention routes)."""
    from . import layer3, link

    con = link.connect()
    for model in a.model:
        run = layer3.label_entries(con, _llm(model), sample=a.sample, seed=a.seed,
                                   residue_only=a.residue, batch=a.batch, max_usd=a.max_usd)
        print(json.dumps(run, indent=2))


def cmd_llm_report(a):
    from . import layer3, link

    con = link.connect()
    tag = a.model[0].split("/")[-1].replace(".", "_").replace("-", "_")
    _write(layer3.coverage(con, a.model[0]), f"phase1_llm_coverage_{tag}")
    _write(layer3.agreement(con, a.model[0]), f"phase1_llm_agreement_{tag}")
    if len(a.model) > 1:
        _write(layer3.model_shift(con, a.model[0], a.model[1]), "phase1_llm_model_shift")


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
    s.set_defaults(func=cmd_link)

    s = sub.add_parser("gate", help="report gate-1 join rates")
    s.set_defaults(func=cmd_gate)

    s = sub.add_parser("classify", help="layer-1 entry_themes (week-1/six-week only pre-registration)")
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
    s.add_argument("--batch", type=int, default=20, help="entries per request")
    s.add_argument("--max-usd", type=float, default=5.0, help="stop when spend reaches this")
    s.set_defaults(func=cmd_llm_label)

    s = sub.add_parser("llm-report", help="layer-3 coverage, agreement, model shift (aggregates)")
    s.add_argument("--model", nargs="+", default=[DEFAULT_MODEL])
    s.set_defaults(func=cmd_llm_report)

    s = sub.add_parser("qa", help="duplicate, MedDRA-coverage and original-vs-updated reports")
    s.set_defaults(func=cmd_qa)

    a = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # polars tables on a cp1252 Windows console
    if a.func is not cmd_inspect:
        config.assert_local_data_dir()
    a.func(a)


if __name__ == "__main__":
    main()
