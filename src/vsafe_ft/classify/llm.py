"""Layer 3: closed-list LLM labelling of the ambiguous residue and validation samples.

Providers (approved by the protocol owner 2026-11-10; retention terms in docs/data-use.md):
- primary: a NanoGPT subscription model (OpenAI-compatible), zero-data-retention routes only;
- second LLM (model-sensitivity check): Claude via the Anthropic API (`ClaudeAPI`), whose
  default retention is 30 days, so it receives only the comparison sample.
Rules (protocol, Limitations section; brief rule 4):
- Send text only: never registrant codes, response ids or any identifier. Entries are numbered
  1..n inside one request; the numbers are positions, not ids.
- Entries with a detectable email address or phone number are never sent.
- Every NanoGPT request sets provider.zdr = true and data_collection = deny, so NanoGPT routes
  only to providers that state zero data retention and fails rather than fall back.
- The prompt and the theme list are fixed and versioned with the taxonomy (PROMPT_VERSION).
- Pre-registration guard: the caller selects only week-1 / six-week entries until the OSF
  registration exists (themes.exploratory_filter_sql); `label_entries` enforces it.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

PII = [
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),                    # email
    re.compile(r"\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),  # phone
]

API_URL = "https://api.nano-gpt.com/api/v1/chat/completions"                   # pay per token
SUBSCRIPTION_URL = "https://nano-gpt.com/api/subscription/v1/chat/completions"  # subscription
DEFAULT_MODEL = "z-ai/glm-5.3"              # NanoGPT subscription model, ZDR route verified
SECOND_MODEL = "claude-opus-5-5"            # Anthropic API: second LLM for model sensitivity
PROMPT_VERSION = "v0.1-2026-11-10"
PROVIDER = {"zdr": True, "data_collection": "deny"}


def has_pii(text: str) -> bool:
    return any(p.search(text) for p in PII)


PROMPT = """You label free-text entries from a vaccine-safety smartphone survey (v-safe).
For each numbered entry, assign every theme from the closed list below that the entry reports
as a symptom or event in the person writing. Do not assign a theme that is negated ("no
headache"), that happened before vaccination, or that is about someone else. Use only theme
names from the list; return an empty list when none applies.

Themes:
{themes}

Flags per entry: third_party (the entry is about someone other than the writer), pre_vaccine
(the symptom started before vaccination).

Return only JSON: {{"results": [{{"i": 1, "themes": ["..."], "third_party": false,
"pre_vaccine": false}}, ...]}} with one result for every entry number.

Entries:
{entries}"""


def theme_list(taxonomy: dict) -> dict[str, str]:
    """theme -> description from the parsed themes.yaml."""
    return {t: b.get("description", t.replace("_", " ")) for t, b in taxonomy["themes"].items()}


def build_prompt(themes: dict[str, str], texts: list[str]) -> str:
    th = "\n".join(f"- {k}: {v}" for k, v in themes.items())
    en = "\n".join(f"{i}. {' '.join(t.split())}" for i, t in enumerate(texts, 1))
    return PROMPT.format(themes=th, entries=en)


def api_key(data_dir: Path | None = None, name: str = "NANOGPT_API_KEY") -> str:
    """`name` from the environment, else from <data dir>/.env (never the repo)."""
    if os.environ.get(name):
        return os.environ[name]
    if data_dir is None:
        from .. import config
        data_dir = config.DATA_DIR
    env = Path(data_dir) / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition("=")
            if k.strip() == name and v.strip():
                return v.strip()
    raise RuntimeError(f"{name} not set (environment or <VSAFE_DATA_DIR>/.env)")


def parse_results(content: str, n: int, allowed: set[str]) -> list[dict | None]:
    """Parse the model's JSON into n results (None where an entry is missing or malformed).

    Theme names outside the closed list are dropped.
    """
    out: list[dict | None] = [None] * n
    results = None
    m = re.search(r"\{.*\}", content or "", re.DOTALL)
    if m:
        try:
            results = json.loads(m.group(0)).get("results")
        except (json.JSONDecodeError, AttributeError):
            results = None
    if not isinstance(results, list):
        # truncated or malformed reply: keep every complete per-entry object
        results = []
        for obj in re.findall(r"\{[^{}]*\}", content or ""):
            try:
                results.append(json.loads(obj))
            except json.JSONDecodeError:
                continue
    for r in results if isinstance(results, list) else []:
        try:
            i = int(r.get("i")) - 1
        except (TypeError, ValueError, AttributeError):
            continue
        if 0 <= i < n and out[i] is None:
            themes = r.get("themes") or []
            out[i] = {
                "themes": sorted({t for t in themes if isinstance(t, str) and t in allowed}),
                "third_party": bool(r.get("third_party")),
                "pre_vaccine": bool(r.get("pre_vaccine")),
            }
    return out


def _http_post(url: str, body: dict, key: str, timeout: float) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class NanoGPT:
    """Closed-list labeller over NanoGPT chat completions (zero-data-retention routes only)."""

    def __init__(self, themes: dict[str, str], model: str = DEFAULT_MODEL, key: str | None = None,
                 post: Callable[[str, dict, str, float], dict] | None = None,
                 timeout: float = 180, retries: int = 4, subscription: bool = True):
        self.themes, self.model = themes, model
        self.url = SUBSCRIPTION_URL if subscription else API_URL
        self.key = key if key is not None else api_key()
        self.post = post or _http_post
        self.timeout, self.retries = timeout, retries
        self.cost_usd = 0.0
        self.tokens = 0
        self.requests = 0

    def label(self, texts: list[str]) -> list[dict | None]:
        if any(has_pii(t) for t in texts):
            raise ValueError("refusing to send entries with a detectable email or phone number")
        body = {
            "model": self.model, "temperature": 0, "max_tokens": 1500 + 80 * len(texts),
            "provider": PROVIDER,
            "messages": [{"role": "user", "content": build_prompt(self.themes, texts)}],
        }
        d = self._post_with_retry(body)
        self.requests += 1
        price = d.get("x_nanogpt_pricing") or {}
        self.cost_usd += float(price.get("cost") or 0)
        self.tokens += int((d.get("usage") or {}).get("total_tokens") or 0)
        content = (d.get("choices") or [{}])[0].get("message", {}).get("content", "")
        return parse_results(content, len(texts), set(self.themes))

    def _post_with_retry(self, body: dict) -> dict:
        for attempt in range(self.retries + 1):
            try:
                d = self.post(self.url, body, self.key, self.timeout)
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < self.retries:
                    time.sleep(2 ** attempt * 5)
                    continue
                # the error body never contains our text; status code and reason only
                raise RuntimeError(f"NanoGPT HTTP {e.code}: {e.reason}") from None
            except (urllib.error.URLError, TimeoutError):
                if attempt < self.retries:
                    time.sleep(2 ** attempt * 5)
                    continue
                raise
            if d.get("error"):
                err = d["error"]
                code = err.get("code") if isinstance(err, dict) else str(err)
                raise RuntimeError(f"NanoGPT error: {code}")
            return d
        raise RuntimeError("unreachable")


# USD per million tokens (input, output), Claude API list prices 2026-10; for the spend cap only.
CLAUDE_PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0),
                 "claude-haiku-5-5": (0.10, 0.50)}


def result_schema(themes: list[str]) -> dict:
    """JSON schema for structured output: themes constrained to the closed list."""
    item = {"type": "object", "additionalProperties": False,
            "required": ["i", "themes", "third_party", "pre_vaccine"],
            "properties": {"i": {"type": "integer"},
                           "themes": {"type": "array", "items": {"type": "string", "enum": themes}},
                           "third_party": {"type": "boolean"},
                           "pre_vaccine": {"type": "boolean"}}}
    return {"type": "object", "additionalProperties": False, "required": ["results"],
            "properties": {"results": {"type": "array", "items": item}}}


class ClaudeAPI:
    """Closed-list labeller over the Anthropic Messages API (second LLM).

    Structured output constrains the reply to the theme list. Opus/Sonnet requests opt into
    server-side refusal fallbacks; a refusal that survives yields no labels (stored not ok).
    """

    def __init__(self, themes: dict[str, str], model: str = SECOND_MODEL, client=None,
                 effort: str = "low"):
        self.themes, self.model, self.effort = themes, model, effort
        if client is None:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key(name="ANTHROPIC_API_KEY"),
                                         max_retries=4)
        self.client = client
        self.cost_usd = 0.0
        self.tokens = 0
        self.requests = 0
        self.refusals = 0

    def label(self, texts: list[str]) -> list[dict | None]:
        if any(has_pii(t) for t in texts):
            raise ValueError("refusing to send entries with a detectable email or phone number")
        kwargs = {}
        if self.model.startswith(("claude-opus", "claude-fable", "claude-sonnet")):
            kwargs = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
        r = self.client.beta.messages.create(
            model=self.model, max_tokens=16000,
            output_config={"effort": self.effort,
                           "format": {"type": "json_schema",
                                      "schema": result_schema(list(self.themes))}},
            messages=[{"role": "user", "content": build_prompt(self.themes, texts)}],
            **kwargs)
        self.requests += 1
        u = r.usage
        tin, tout = int(u.input_tokens or 0), int(u.output_tokens or 0)
        self.tokens += tin + tout
        pin, pout = CLAUDE_PRICES.get(self.model, (5.0, 25.0))
        self.cost_usd += (tin * pin + tout * pout) / 1e6
        if r.stop_reason == "refusal":
            self.refusals += 1
            return [None] * len(texts)
        text = next((b.text for b in r.content if b.type == "text"), "")
        return parse_results(text, len(texts), set(self.themes))


def make_labeller(themes: dict[str, str], model: str):
    """Claude models go to the Anthropic API; everything else to the NanoGPT subscription."""
    if model.startswith("claude-"):
        return ClaudeAPI(themes, model=model)
    return NanoGPT(themes, model=model)
