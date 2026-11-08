from pathlib import Path

import pytest

from vsafe_ft import config


def test_refuses_data_dir_under_onedrive(tmp_path, monkeypatch):
    monkeypatch.setenv("OneDrive", str(tmp_path / "OneDrive"))
    with pytest.raises(RuntimeError):
        config.assert_local_data_dir(tmp_path / "OneDrive" / "proj" / "data")
    config.assert_local_data_dir(tmp_path / "elsewhere")


def test_source_dir_is_under_data_dir():
    assert config.source_dir({"dir": "raw/x"}) == config.DATA_DIR / "raw" / "x"
    assert isinstance(config.DATA_DIR, Path)
