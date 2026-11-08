"""Layer 3: closed-list LLM labelling of the ambiguous residue and validation samples.

Rules (protocol, Limitations section):
- Never send registrant codes or any identifier; send text only.
- If a hosted API is used, entries with detectable names, phone numbers or emails are
  stripped first, and the provider's retention terms at time of use are logged in docs/.
- The prompt and the taxonomy list are fixed and versioned with the taxonomy.
"""

from __future__ import annotations

import re

PII = [
    re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),                    # email
    re.compile(r"\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b"),  # phone
]


def has_pii(text: str) -> bool:
    return any(p.search(text) for p in PII)


PROMPT = """You label free-text entries from a vaccine-safety smartphone survey.
Assign every theme from the closed list that the entry reports as a current symptom or event
in the person writing (not negated, not before vaccination, not in a third party).
Return JSON: {{"themes": [...], "third_party": bool, "pre_vaccine": bool, "persistence": bool}}.

Themes: {themes}

Entry: {text}"""
