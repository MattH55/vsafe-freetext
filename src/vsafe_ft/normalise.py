"""Step 2: normalise text and flag redactions. Original text is never modified."""

from __future__ import annotations

import re
import unicodedata

REDACTION = re.compile(r"\(\s*b\s*\)\s*\(\s*6\s*\)", re.IGNORECASE)
_WS = re.compile(r"\s+")


def normalise(text: str | None) -> str | None:
    if text is None:
        return None
    t = unicodedata.normalize("NFKC", text)
    t = t.replace("’", "'").replace("‘", "'")
    t = _WS.sub(" ", t).strip()
    return t or None


def is_redacted(text: str | None) -> bool:
    return bool(text) and bool(REDACTION.search(text))
