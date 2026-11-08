from vsafe_ft.normalise import is_redacted, normalise


def test_whitespace_and_quotes():
    assert normalise("  can’t   sleep \n") == "can't sleep"
    assert normalise("   ") is None


def test_redaction_flag():
    assert is_redacted("my doctor (b)(6) said")
    assert is_redacted("at ( b ) ( 6 ) hospital")
    assert not is_redacted("dose 6 of b vitamins")
