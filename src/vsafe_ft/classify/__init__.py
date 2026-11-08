"""Step 6: three-layer classification. Every label records the layer that produced it.

Layer 1  lexicon.py  rules + MedDRA LLT strings + lay synonyms, with negation handling
Layer 2  embed.py    sentence embeddings, nearest-centroid to theme prototypes, clustering
Layer 3  llm.py      closed-list LLM labelling of the low-confidence residue and validation samples
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Label:
    theme: str
    confidence: float
    layer: int          # 1, 2 or 3
    method: str         # e.g. "lexicon:v0", "embed:<model>", "llm:<model>"
