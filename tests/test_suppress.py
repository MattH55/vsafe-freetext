import polars as pl
import pytest

from vsafe_ft.suppress import assert_safe, suppress


def test_suppress_small_cells():
    df = pl.DataFrame({"theme": ["a", "b"], "people": [3, 50], "entries": [4, 80]})
    out = suppress(df, min_people=10)
    assert out.filter(pl.col("theme") == "a")["entries"][0] is None
    assert out.filter(pl.col("theme") == "b")["entries"][0] == 80


def test_assert_safe_blocks_identifiers():
    with pytest.raises(ValueError):
        assert_safe(pl.DataFrame({"registrant": ["x"], "people": [20]}))
    with pytest.raises(ValueError):
        assert_safe(pl.DataFrame({"people": [5]}))
