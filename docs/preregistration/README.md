# Pre-registration (OSF Registries, Secondary Data Preregistration template)

Filed after the one-release prototype and before any gold-set result is used for tuning.
Public, no embargo. Amendments are filed as OSF updates, never edited in place.

Attach at registration:
- `taxonomy/v1.0/` (frozen themes, lexicon, prototype sentences)
- the git commit hash of this repository
- `config/analysis.yaml` (thresholds, suppression rule, alpha, permutations)
- `data/raw/MANIFEST.tsv` (file names, URLs, sha256)

Tiers:
- **Confirmatory:** Q1 coherence (co-occurrence vs 1,000-permutation null preserving domain
  marginals), Q2 onset and persistence, Q3 VAERS capture-rate ratio and PT dispersion.
- **Exploratory (labelled):** LCA with BIC (decided 2026-11-10), blind clustering of long-term
  free text, taxonomy discovery,
  menstrual/neurological/cardiac deep dives.

Prior-knowledge disclosure: record here which release was opened in phase 1, what was seen,
and that no long-term-survey free text was read against the PACVS domains before registration.
