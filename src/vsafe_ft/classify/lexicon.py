"""Layer 1: lexicon matching with NegEx-style negation and attribution cues."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import Label

NEGATION_PRE = re.compile(
    r"\b(no|not|denies|denied|without|never|none|negative for|free of|resolved|gone)\b", re.IGNORECASE
)
TERMINATORS = re.compile(r"[.;!?]|\b(but|however|although|except)\b", re.IGNORECASE)
THIRD_PARTY = re.compile(
    r"\b(my|our|his|her)\s+(son|daughter|child|kid|baby|husband|wife|partner|mother|father|mom|dad)\b",
    re.IGNORECASE,
)
PRE_VACCINE = re.compile(r"\bbefore (the|my|this) (shot|vaccine|vaccination|jab|dose)\b", re.IGNORECASE)
NEG_WINDOW = 5  # tokens before a match


@dataclass
class Lexicon:
    version: str
    terms: dict[str, list[re.Pattern]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> Lexicon:
        spec = yaml.safe_load(path.read_text())
        terms = {
            theme: [re.compile(rf"\b{t}\b", re.IGNORECASE) for t in body.get("terms", [])]
            for theme, body in spec["themes"].items()
        }
        return cls(version=spec["version"], terms=terms)

    def classify(self, text: str) -> tuple[list[Label], dict[str, bool]]:
        labels: list[Label] = []
        for theme, patterns in self.terms.items():
            for p in patterns:
                m = p.search(text)
                if m and not negated(text, m.start()):
                    labels.append(Label(theme, 1.0, 1, f"lexicon:{self.version}"))
                    break
        flags = {
            "third_party": bool(THIRD_PARTY.search(text)),
            "pre_vaccine": bool(PRE_VACCINE.search(text)),
        }
        return labels, flags


def negated(text: str, start: int) -> bool:
    """True if a negation cue appears within NEG_WINDOW tokens before `start` in the same clause."""
    before = text[:start]
    clause = TERMINATORS.split(before)[-1]
    tokens = clause.split()[-NEG_WINDOW:]
    return bool(NEGATION_PRE.search(" ".join(tokens)))
