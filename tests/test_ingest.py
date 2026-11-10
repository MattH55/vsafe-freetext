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


def test_under3_flag_is_explicit(tmp_path):
    wb = Workbook()
    wb.active.append(["A"])
    wb.active.append(["x"])
    src = tmp_path / "anything.xlsx"   # name says nothing about age
    wb.save(src)
    out = tmp_path / "o.parquet"
    xlsx_to_parquet(src, out, "anything", under3=True)
    assert pq.read_table(out).to_pydict()["_under3"] == [True]


def test_csv_and_zip_ingest(tmp_path):
    import zipfile

    from vsafe_ft.ingest import header_row, ingest_file

    csv = tmp_path / "chk.csv"
    csv.write_text("REG,SID,DAY\nr1,s1,0007\nr2,s2,42\n")
    assert header_row(csv) == ["REG", "SID", "DAY"]
    zp = tmp_path / "chk.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.write(csv, "inner/chk.csv")
    outs = list(ingest_file(zp, tmp_path / "out"))
    assert len(outs) == 1 and outs[0][1] == 2
    t = pq.read_table(outs[0][0]).to_pydict()
    assert t["DAY"] == ["0007", "42"]           # all_varchar: leading zeros kept
    assert t["_release"] == ["chk", "chk"]
    assert (tmp_path / "extracted" / "chk" / "inner" / "chk.csv").exists()


def test_output_names_have_no_glob_characters(tmp_path):
    from vsafe_ft.ingest import ingest_file

    csv = tmp_path / "consolidated_x[1].csv"
    csv.write_bytes(b"A\n1\n")
    (out, n), = ingest_file(csv, tmp_path / "out")
    assert out.name == "consolidated_x_1.parquet" and n == 1


def test_zip_skips_macos_resource_forks(tmp_path):
    import zipfile

    from vsafe_ft.ingest import ingest_file

    zp = tmp_path / "m.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("m/covid_meddra_sd.csv", "A\n1\n")
        z.writestr("__MACOSX/m/._covid_meddra_sd.csv", b"\x00\x05\x16\x07\xb0")
    outs = list(ingest_file(zp, tmp_path / "out"))
    assert [o.name for o, _ in outs] == ["m__covid_meddra_sd.parquet"]


def test_header_row_reads_first_line_only(tmp_path):
    from vsafe_ft.ingest import header_row

    p = tmp_path / "h.csv"
    p.write_bytes(b"A,B,\"C,D\"\r\nsecret1,\xff\xfe,x\r\n")
    assert header_row(p) == ["A", "B", "C,D"]


def test_cp1252_csv_is_transcoded(tmp_path):
    import polars as pl

    from vsafe_ft.ingest import csv_encoding, csv_to_parquet

    p = tmp_path / "w.csv"
    p.write_bytes("A,B\n1,café – ok\n".encode("cp1252"))
    assert csv_encoding(p) == "cp1252"
    out = tmp_path / "w.parquet"
    assert csv_to_parquet(p, out, "r") == 1
    assert pl.read_parquet(out)["B"][0] == "café – ok"
    assert not list(tmp_path.glob("*.tmp.csv"))


def test_duckdb_errors_do_not_quote_rows():
    from vsafe_ft.ingest import sanitised

    e = sanitised(ValueError("CSV Error on Line: 9\nOriginal Line:\nsecret row text"))
    assert "secret" not in str(e) and "Line: 9" in str(e)
