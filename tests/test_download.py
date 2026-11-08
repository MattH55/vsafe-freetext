import functools
import http.server
import threading

import pytest

from vsafe_ft import config, download

PAYLOAD = bytes(range(256)) * 400


class RangeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        rng = self.headers.get("Range")
        start = int(rng.split("=")[1].split("-")[0]) if rng else 0
        body = PAYLOAD[start:]
        self.send_response(206 if rng else 200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


@pytest.fixture
def server():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), RangeHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/f.bin"
    srv.shutdown()


def test_fetch_resumes_partial(tmp_path, server):
    dest = tmp_path / "f.bin"
    (tmp_path / "f.bin.part").write_bytes(PAYLOAD[:1000])
    download.fetch(server, dest)
    assert dest.read_bytes() == PAYLOAD
    assert not (tmp_path / "f.bin.part").exists()


def test_manifest_one_row_per_file(tmp_path, server, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "load", functools.partial(
        lambda name: {"p": {"dir": "raw/p", "files": [{"name": "f.bin", "url": server}]}}))
    download.download()
    download.download()
    lines = (tmp_path / "raw" / "MANIFEST.tsv").read_text().splitlines()
    assert len(lines) == 2 and lines[0].startswith("part\tfile\turl\tsha256")
    assert lines[1].split("\t")[3] == download.sha256(tmp_path / "raw" / "p" / "f.bin")
