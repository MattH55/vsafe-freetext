"""Step 1: stream .xlsx releases to Parquet, once.

Each row gets release number, source row index and a content hash so every
downstream record traces back to one cell range in one file.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

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


def xlsx_to_parquet(path: Path, out: Path, release: str) -> int:
    """Convert one release; all source columns kept as strings (typing happens later)."""
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
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    writer = pq.ParquetWriter(out, schema, compression="zstd")
    buf: list[tuple] = []
    n = 0

    def flush():
        if buf:
            writer.write_table(_table(buf, header, release, schema))
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


def _table(buf, header, release, schema) -> pa.Table:
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
    ]
    return pa.Table.from_arrays(arrays, schema=schema)
