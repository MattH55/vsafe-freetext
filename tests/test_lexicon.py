from pathlib import Path

import pytest

from vsafe_ft.classify.lexicon import Lexicon, negated

LEX = Lexicon.load(Path(__file__).parents[1] / "taxonomy" / "v0" / "themes.yaml")


def themes(text):
    return {l.theme for l in LEX.classify(text)[0]}


def test_multi_domain():
    t = themes("Still exhausted and brain fog, heart racing when I stand, for 3 months now")
    assert {"fatigue_pem", "cognitive", "dysautonomia", "persistence"} <= t


@pytest.mark.parametrize("text", ["no headache", "I did not have a headache", "denies dizziness"])
def test_negation(text):
    assert not themes(text) & {"pain", "dysautonomia"}


def test_negation_scoped_to_clause():
    assert "pain" in themes("No fever, but a bad headache")


def test_attribution_flags():
    _, flags = LEX.classify("My son has had tingling in his hands")
    assert flags["third_party"]
    _, flags = LEX.classify("I had migraines before the shot")
    assert flags["pre_vaccine"]


def test_negated_helper():
    s = "no tinnitus"
    assert negated(s, s.index("tinnitus"))
