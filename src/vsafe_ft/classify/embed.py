"""Layer 2: sentence embeddings + nearest-centroid assignment and theme discovery.

Requires the `embed` extra. Thresholds are tuned on the development split only,
never on the gold set held out for pre-registered evaluation.
"""

from __future__ import annotations

import numpy as np

from . import Label


class CentroidClassifier:
    def __init__(self, model_name: str, threshold: float):
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.threshold = threshold
        self.centroids: dict[str, np.ndarray] = {}

    def fit_prototypes(self, prototypes: dict[str, list[str]]) -> None:
        for theme, sents in prototypes.items():
            v = self.model.encode(sents, normalize_embeddings=True)
            c = v.mean(axis=0)
            self.centroids[theme] = c / np.linalg.norm(c)

    def classify(self, texts: list[str]) -> list[list[Label]]:
        X = self.model.encode(texts, normalize_embeddings=True, batch_size=256)
        themes = list(self.centroids)
        C = np.stack([self.centroids[t] for t in themes])
        sims = X @ C.T
        return [
            [Label(themes[j], float(s[j]), 2, f"embed:{self.model_name}")
             for j in np.where(s >= self.threshold)[0]]
            for s in sims
        ]
