"""Step 1: stream source files to Parquet, once.

.xlsx (free text, pregnancy registry): each row gets release label, source row index and a
content hash so every downstream record traces back to one cell range in one file.
.csv/.txt and .zip (registrants, vaccinations, check-ins, MedDRA, call center): DuckDB
`read_csv(all_varchar=true)` -> `COPY ... (FORMAT parquet)`, which streams, so the 5 GB
check-in file is never held in memory. Zips are unpacked under `<dir>/extracted/<zip stem>/`.
"""

from __future__ import annotations

import hashlib
import re
import zipfile
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from openpyxl import load_workbook

BATCH = 100_000


def inspect_xlsx(path: Path, n: int = 5) -> tuple[list[str], list[tuple]]:
    """Return header and first n rows without loading the whole workbook."""
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = [str(c) if c is not None else "" for c in next(rows)]
    sample = [r for _, r in zip(range(n), rows)]
    wb.close()
    return header, sample


def _hash(values) -> str:
    h = hashlib.sha256()
    for v in values:
        h.update(b"\x1f" + ("" if v is None else str(v)).encode("utf-8"))
    return h.hexdigest()


def xlsx_to_parquet(path: Path, out: Path, release: str, under3: bool = False) -> int:
    """Convert one release; all source columns kept as strings (typing happens later).

    `under3` comes from an explicit `under3: true` on the file in config/sources.yaml.
    """
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = [str(c) if c is not None else f"col_{i}" for i, c in enumerate(next(rows))]
    schema = pa.schema(
        [pa.field(c, pa.string()) for c in header]
        + [
            pa.field("_release", pa.string()),
            pa.field("_row", pa.int64()),
            pa.field("_content_hash", pa.string()),
            pa.field("_under3", pa.bool_()),
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = pq.ParquetWriter(out, schema, compression="zstd")
    buf: list[tuple] = []
    n = 0

    def flush():
        if buf:
            writer.write_table(_table(buf, header, release, under3, schema))
            buf.clear()

    for i, row in enumerate(rows, start=1):
        if row is None or all(v is None for v in row):
            continue
        vals = [None if v is None else str(v) for v in row[: len(header)]]
        vals += [None] * (len(header) - len(vals))
        buf.append((vals, i))
        n += 1
        if len(buf) >= BATCH:
            flush()
    flush()
    writer.close()
    wb.close()
    return n


def _table(buf, header, release, under3, schema) -> pa.Table:
    cols = {c: [] for c in header}
    rows_idx, hashes = [], []
    for vals, i in buf:
        for c, v in zip(header, vals):
            cols[c].append(v)
        rows_idx.append(i)
        hashes.append(_hash(vals))
    arrays = [pa.array(cols[c], pa.string()) for c in header]
    arrays += [
        pa.array([release] * len(buf), pa.string()),
        pa.array(rows_idx, pa.int64()),
        pa.array(hashes, pa.string()),
        pa.array([under3] * len(buf), pa.bool_()),
    ]
    return pa.Table.from_arrays(arrays, schema=schema)


TEXT_SUFFIXES = {".csv", ".txt", ".tsv"}


def _sql_str(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def csv_to_parquet(path: Path, out: Path, release: str, under3: bool = False) -> int:
    """Stream one delimited file to Parquet with DuckDB; every column read as VARCHAR."""
    out.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    src = _sql_str(path.as_posix())
    rel = f"""SELECT *, {_sql_str(release)} AS _release, {str(under3).upper()} AS _under3
              FROM read_csv({src}, all_varchar = true, header = true, sample_size = -1)"""
    con.execute(f"COPY ({rel}) TO {_sql_str(out.as_posix())} (FORMAT parquet, COMPRESSION zstd)")
    n = con.execute(f"SELECT count(*) FROM read_parquet({_sql_str(out.as_posix())})").fetchall()[0][0]
    con.close()
    return n


def extract_zip(path: Path) -> list[Path]:
    """Unpack a zip into `<its dir>/extracted/<zip stem>/` (once) and list delimited files."""
    dest = path.parent / "extracted" / path.stem
    if not dest.exists():
        import zipfile_deflate64  # noqa: F401  (adds Deflate64: the check-in zip uses method 9)

        tmp = dest.with_name(dest.name + ".part")
        with zipfile.ZipFile(path) as z:
            z.extractall(tmp)
        tmp.rename(dest)
    return sorted(p for p in dest.rglob("*") if p.suffix.lower() in TEXT_SUFFIXES
                  and "__MACOSX" not in p.parts and not p.name.startswith("._"))


def header_row(path: Path) -> list[str]:
    """Column names only (no data rows) of an .xlsx or delimited file."""
    if path.suffix.lower() == ".xlsx":
        return inspect_xlsx(path, 0)[0]
    con = duckdb.connect()
    cols = con.execute(
        f"DESCRIBE SELECT * FROM read_csv({_sql_str(path.as_posix())}, all_varchar = true)"
    ).fetchall()
    con.close()
    return [c[0] for c in cols]


def _safe_name(stem: str) -> str:
    """File-name stem without glob characters ('[1]' would be a character class in DuckDB)."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("_")


def ingest_file(path: Path, out_dir: Path, release: str | None = None, under3: bool = False):
    """Choose the converter by file type. Yields (output parquet, rows) per table written."""
    suffix = path.suffix.lower()
    release = release or path.stem
    if suffix == ".xlsx":
        out = out_dir / f"{_safe_name(path.stem)}.parquet"
        yield out, xlsx_to_parquet(path, out, release, under3)
    elif suffix in TEXT_SUFFIXES:
        out = out_dir / f"{_safe_name(path.stem)}.parquet"
        yield out, csv_to_parquet(path, out, release, under3)
    elif suffix == ".zip":
        inner = extract_zip(path)
        for f in inner:
            label = release if len(inner) == 1 else f"{release}/{f.stem}"
            out = out_dir / f"{_safe_name(path.stem)}__{_safe_name(f.stem)}.parquet"
            yield out, csv_to_parquet(f, out, label, under3)
    else:
        raise ValueError(f"Unsupported file type: {path}")
