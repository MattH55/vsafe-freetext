import hashlib
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "freeze_taxonomy", Path(__file__).parents[1] / "scripts" / "freeze_taxonomy.py")
freeze_taxonomy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(freeze_taxonomy)


def test_freeze_copies_hashes_and_refuses_overwrite(tmp_path):
    src = tmp_path / "v0"
    (src / "sub").mkdir(parents=True)
    (src / "themes.yaml").write_bytes(b"version: v0\n")
    (src / "sub" / "map.csv").write_bytes(b"theme,pt\n")
    dst = tmp_path / "v1.0"
    digest = freeze_taxonomy.freeze(src, dst)
    sums = (dst / "SHA256SUMS").read_text().splitlines()
    want = hashlib.sha256(b"version: v0\n").hexdigest() + "  themes.yaml"
    assert want in sums and any(s.endswith("  sub/map.csv") for s in sums)
    assert digest == hashlib.sha256((dst / "SHA256SUMS").read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):
        freeze_taxonomy.freeze(src, dst)
    assert freeze_taxonomy.main(["--src", str(src), "--version", "v1.0"]) == 1
