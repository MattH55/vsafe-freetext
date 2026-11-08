"""Command-line entry point: `vsafe-ft <command>`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import config


def cmd_inspect(a):
    from .ingest import inspect_xlsx

    header, rows = inspect_xlsx(Path(a.path), a.n)
    print("columns:", header)
    for r in rows:
        print(r)


def cmd_ingest(a):
    from .ingest import xlsx_to_parquet

    src = Path(a.src)
    out_dir = config.DATA_DIR / "interim" / a.part
    files = sorted(src.glob("*.xlsx")) if src.is_dir() else [src]
    for f in files:
        n = xlsx_to_parquet(f, out_dir / (f.stem + ".parquet"), release=f.stem)
        print(f"{f.name}: {n:,} rows")


def cmd_download(a):
    from .download import download

    download(a.only)


def cmd_link(a):
    from . import link

    con = link.connect()
    interim = config.DATA_DIR / "interim"
    link.build_entries(con, str(interim / "freetext_updated" / "*.parquet"))
    link.link_dose(con, str(interim / "vaccinations" / "*.parquet"))
    link.link_survey(con, str(interim / "health_checkins" / "*.parquet"))
    print(json.dumps(link.join_rates(con), indent=2))


def cmd_gate(a):
    from . import link

    rates = link.join_rates(link.connect())
    need = config.analysis()["join_rate_gate"]
    ok = rates["dose_linked"] >= need and rates["survey_matched"] >= need
    print(json.dumps(rates, indent=2))
    print(f"gate 1 (join rates >= {need}): {'PASS' if ok else 'FAIL - document the reason'}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="vsafe-ft")
    sub = p.add_subparsers(required=True)

    s = sub.add_parser("inspect", help="print header and first rows of an .xlsx")
    s.add_argument("path"); s.add_argument("-n", type=int, default=5)
    s.set_defaults(func=cmd_inspect)

    s = sub.add_parser("download", help="fetch files listed in config/sources.yaml")
    s.add_argument("--only", nargs="*")
    s.set_defaults(func=cmd_download)

    s = sub.add_parser("ingest", help="convert .xlsx release(s) to Parquet")
    s.add_argument("src"); s.add_argument("--part", default="freetext_updated")
    s.set_defaults(func=cmd_ingest)

    s = sub.add_parser("link", help="dedupe and link entries to dose and survey")
    s.set_defaults(func=cmd_link)

    s = sub.add_parser("gate", help="report gate-1 join rates")
    s.set_defaults(func=cmd_gate)

    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
