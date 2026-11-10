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


def test_pots_is_case_sensitive():
    assert "dysautonomia" in themes("diagnosed with POTS last month")
    assert "dysautonomia" not in themes("I was washing pots and pans")


@pytest.mark.parametrize("text", ["for a period of time I felt fine", "over a short period",
                                  "periods of rest helped"])
def test_period_as_time_span_is_not_menstrual(text):
    assert "menstrual" not in themes(text)


@pytest.mark.parametrize("text", ["my period came early", "heavier periods since the shot",
                                  "period was 10 days late"])
def test_period_menstrual(text):
    assert "menstrual" in themes(text)


@pytest.mark.parametrize("text,theme", [
    ("sore arm at the injection site", "injection_site"),
    ("swollen lymph nodes under my arm", "lymphadenopathy"),
    ("runny nose and sneezing", "upper_respiratory"),
    ("chills and hot flashes overnight", "fever_chills"),
    ("itchy rash on chest", "skin"),
    ("lost taste for a day", "taste_smell"),
    ("metallic taste in my mouth", "taste_smell"),
    ("short of breath climbing stairs", "cardiorespiratory"),
    ("felt light headed", "dysautonomia"),
    ("elevated heart rate", "dysautonomia"),
    ("lower back pain", "pain"),
    ("loss of appetite", "gastrointestinal"),
    ("tested positive two days later", "unrelated_cause"),
])
def test_phase1_additions(text, theme):
    assert theme in themes(text)


def test_acute_themes_are_not_pacvs():
    import yaml

    spec = yaml.safe_load((Path(__file__).parents[1] / "taxonomy" / "v0" / "themes.yaml").read_text(
        encoding="utf-8"))
    pacvs = {t for t, b in spec["themes"].items() if b["domain"] == "pacvs"}
    assert pacvs == {"fatigue_pem", "cognitive", "dysautonomia", "sensory_neuropathic", "sleep",
                     "pain", "gastrointestinal", "menstrual",
                     "cardiorespiratory"}       # the nine protocol domains (2026-11-10)
    exclusions = {t for t, b in spec["themes"].items() if b["domain"] == "exclusion"}
    assert {"acute_diagnosis", "unrelated_cause", "upper_respiratory"} <= exclusions
    assert spec["themes"]["taste_smell"]["domain"] == "acute"


@pytest.mark.parametrize("text,hit", [
    ("burning sensation in my feet", True), ("hands are burning", True),
    ("burning when urinating", False), ("burning in my stomach", False)])
def test_burning_is_neuropathic_only(text, hit):
    assert ("sensory_neuropathic" in themes(text)) is hit
