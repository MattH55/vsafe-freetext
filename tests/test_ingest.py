import pyarrow.parquet as pq
from openpyxl import Workbook

from vsafe_ft.ingest import inspect_xlsx, xlsx_to_parquet


def test_roundtrip(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(["REG", "SURVEY_STATIC_ID", "STARTED_ON", "TEXT"])
    ws.append(["r1", "s1", "2021-03-01", "tired"])
    ws.append([None, None, None, None])
    ws.append(["r2", "s2", "2021-03-02", "dizzy"])
    src = tmp_path / "rel01.xlsx"
    wb.save(src)

    header, _ = inspect_xlsx(src)
    assert header == ["REG", "SURVEY_STATIC_ID", "STARTED_ON", "TEXT"]

    out = tmp_path / "rel01.parquet"
    assert xlsx_to_parquet(src, out, "rel01") == 2
    t = pq.read_table(out).to_pydict()
    assert t["TEXT"] == ["tired", "dizzy"]
    assert t["_row"] == [1, 3]
    assert len(set(t["_content_hash"])) == 2
