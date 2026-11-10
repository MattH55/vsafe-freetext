"""Layer 3 (NanoGPT) on synthetic entries with a fake transport: no network, no real text."""

import json
import re

import duckdb
import pytest

from vsafe_ft import layer3, themes
from vsafe_ft.classify import llm

THEMES = {"fatigue_pem": "fatigue", "cognitive": "brain fog", "pain": "headache"}


class FakePost:
    """Labels entries containing 'zebra' as fatigue_pem; records every request body."""

    def __init__(self, reply=None):
        self.bodies, self.reply = [], reply

    def __call__(self, url, body, key, timeout):
        self.bodies.append(body)
        if self.reply is not None:
            return self.reply
        prompt = body["messages"][0]["content"]
        entries = re.findall(r"^(\d+)\. (.*)$", prompt.split("Entries:\n", 1)[1], re.MULTILINE)
        res = [{"i": int(i), "themes": ["fatigue_pem", "not_a_theme"] if "zebra" in t else [],
                "third_party": False, "pre_vaccine": False} for i, t in entries]
        return {"choices": [{"message": {"content": "```json\n" + json.dumps({"results": res})
                                         + "\n```"}}],
                "usage": {"total_tokens": 100}, "x_nanogpt_pricing": {"cost": 0.001}}


def labeller(post=None, model="test/model"):
    return llm.NanoGPT(THEMES, model=model, key="k", post=post or FakePost())


def test_request_is_text_only_with_zdr():
    post = FakePost()
    out = labeller(post).label(["zebra glow", "nothing"])
    body = post.bodies[0]
    assert body["provider"] == {"zdr": True, "data_collection": "deny"}
    assert body["temperature"] == 0
    assert set(body) == {"model", "temperature", "max_tokens", "provider", "messages"}
    assert out[0]["themes"] == ["fatigue_pem"]          # unknown theme dropped
    assert out[1]["themes"] == []


def test_pii_never_sent():
    post = FakePost()
    with pytest.raises(ValueError):
        labeller(post).label(["call me at 555-123-4567"])
    with pytest.raises(ValueError):
        labeller(post).label(["mail a@b.com"])
    assert post.bodies == []


@pytest.mark.parametrize("content", ["not json", '{"results": "x"}', '{"results": [{"i": 9}]}'])
def test_malformed_replies_are_none(content):
    assert llm.parse_results(content, 2, set(THEMES)) == [None, None]


def test_provider_error_raises_without_text():
    post = FakePost(reply={"error": {"code": "zdr_provider_required", "message": "..."}})
    with pytest.raises(RuntimeError, match="zdr_provider_required"):
        labeller(post).label(["zebra"])


def test_key_from_data_dir_env(tmp_path, monkeypatch):
    monkeypatch.delenv("NANOGPT_API_KEY", raising=False)
    (tmp_path / ".env").write_text("OTHER=1\nNANOGPT_API_KEY=sk-test\n")
    assert llm.api_key(tmp_path) == "sk-test"


def test_prompt_lists_every_taxonomy_theme():
    import yaml

    spec = yaml.safe_load(themes.TAXONOMY.read_text(encoding="utf-8"))
    tl = llm.theme_list(spec)
    assert set(tl) == set(spec["themes"]) and all(tl.values())
    p = llm.build_prompt(tl, ["a\nb", "c"])
    assert "1. a b\n2. c" in p


@pytest.fixture
def con():
    c = duckdb.connect()
    c.execute("""CREATE TABLE entries_survey (entry_id BIGINT, registrant VARCHAR,
                 response_id VARCHAR, field VARCHAR, text VARCHAR, redacted BOOLEAN,
                 survey_matched BOOLEAN, survey_day VARCHAR, survey_type VARCHAR)""")
    rows, i = [], 0
    for p in range(15):
        rows.append((i := i + 1, f"p{p}", f"r{i}", "SD", "brain fog", False, True, "1", "d"))
    for p in range(12):
        rows.append((i := i + 1, f"q{p}", f"r{i}", "SRO", "weird zebra glow", False, True, "3", "d"))
    for p in range(12):     # long-term: never sent pre-registration
        rows.append((i := i + 1, f"s{p}", f"r{i}", "SD", "zebra long", False, True, "180",
                     "6 month"))
    rows.append((i := i + 1, "t", f"r{i}", "SD", "zebra (b)(6)", True, True, "1", "d"))
    rows.append((i := i + 1, "u", f"r{i}", "SD", "zebra 555-123-4567", False, True, "1", "d"))
    c.executemany("INSERT INTO entries_survey VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
    themes.build_entry_themes(c)
    return c


def _sent_texts(post):
    return [t for b in post.bodies
            for t in re.findall(r"^\d+\. (.*)$", b["messages"][0]["content"].split("Entries:\n")[1],
                                re.MULTILINE)]


def test_label_entries_unique_texts_and_guards(con):
    post = FakePost()
    run = layer3.label_entries(con, labeller(post), sample=100, log=lambda *_: None)
    sent = _sent_texts(post)
    assert sorted(sent) == ["brain fog", "weird zebra glow"]     # unique texts, once each
    assert run["skipped_pii"] == 1 and run["texts_sent"] == 2 and run["failed"] == 0
    # cached: a second run sends nothing
    post2 = FakePost()
    run2 = layer3.label_entries(con, labeller(post2), sample=100, log=lambda *_: None)
    assert post2.bodies == [] and run2["texts_sent"] == 0


def test_residue_only(con):
    post = FakePost()
    layer3.label_entries(con, labeller(post), sample=100, residue_only=True, log=lambda *_: None)
    assert _sent_texts(post) == ["weird zebra glow"]


def test_long_term_refused(con):
    with pytest.raises(PermissionError):
        layer3.label_entries(con, labeller(), sample=10, long_term=True)


def test_cost_cap_stops(con):
    lab = labeller()
    lab.cost_usd = 10.0
    run = layer3.label_entries(con, lab, sample=100, max_usd=1.0, log=lambda *_: None)
    assert run["texts_sent"] == 0


def test_aggregates_are_suppressed(con):
    layer3.label_entries(con, labeller(), sample=100, log=lambda *_: None)
    layer3.label_entries(con, labeller(model="test/second"), sample=100, log=lambda *_: None)
    cov = layer3.coverage(con, "test/model")
    allrow = cov.filter(cov["field"] == "all").row(0, named=True)
    assert allrow["entries"] == 27 and allrow["share_either"] == 1.0
    agr = layer3.agreement(con, "test/model")
    assert "entry_id" not in agr.columns and "registrant" not in agr.columns
    sh = layer3.model_shift(con, "test/model", "test/second")
    row = sh.filter(sh["theme"] == "fatigue_pem").row(0, named=True)
    assert row["model1_entries"] == row["model2_entries"] == 12 and not row["model_sensitive"]
