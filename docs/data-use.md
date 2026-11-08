# Data use, privacy and ethics

## Terms
- CDC user agreement (data.cdc.gov MedDRA coded text): bars sub-national analyses and any
  presentation that could identify a participant. **Date read / terms accepted:** _TBD_.
- State is derivable from zip3; nothing is reported by state or zip3.

## Rules enforced in code
- `data/` is gitignored; raw text and registrant codes never enter the repository.
- `suppress.assert_safe` rejects any output table with fewer than 10 people in a cell or with
  identifier/text columns (`registrant`, `text`, `text_orig`, `zip3`, `state`).
- Layer-3 LLM: text only, never identifiers; with a hosted API, entries with detectable names,
  phones or emails are dropped first. Provider and retention terms at time of use: _TBD_.

## Rules for people
- Quotations in the report or manuscript are paraphrased or composited, never verbatim, never with a registrant code.
- Redacted (b)(6) words are not reconstructed or guessed.
- Gold-set coders read descriptions of death, pregnancy loss and suicide: sessions are time-limited with a debrief.
- Ethics: request a written determination (e.g. VU Amsterdam) that secondary analysis of these data falls outside review.
