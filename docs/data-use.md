# Data use, privacy and ethics

## Terms
- CDC user agreement (data.cdc.gov MedDRA coded text): bars sub-national analyses and any
  presentation that could identify a participant. **Date read / terms accepted:** _TBD_.
- State is derivable from zip3; nothing is reported by state or zip3.

## Rules enforced in code
- `data/` is gitignored; raw text and registrant codes never enter the repository.
- `suppress.assert_safe` rejects any output table with fewer than 10 people in a cell or with
  identifier/text columns (`registrant`, `text`, `text_orig`, `zip3`, `state`).
- Layer-3 LLM: text only, never identifiers; with a hosted API, entries with detectable
  phones or emails are dropped first (`classify/llm.py`). Provider and terms below.

## Layer-3 provider (approved by the protocol owner, 2026-11-10)

- **Provider:** NanoGPT (nano-gpt.com), OpenAI-compatible API at
  `https://api.nano-gpt.com/api/v1/chat/completions`. NanoGPT does not run inference itself; it
  forwards each request to an underlying model provider.
- **Models:** `anthropic/claude-haiku-5.5` (primary), `openai/gpt-5.4-mini` (second LLM for the
  model-sensitivity check). Both were confirmed to serve zero-data-retention routes.
- **Every request** sets `provider: {zdr: true, data_collection: deny}`. NanoGPT then routes only
  to providers that state they keep no prompts or outputs, and fails rather than falling back
  (verified: a model without a ZDR route is refused with `zdr_provider_required`).
- **Terms read 2026-11-10** (privacy policy and terms of service, both "Last Updated:
  November 9, 2026"):
  - NanoGPT does not store prompt or response content by default. Opt-in request logging and
    Responses-API storage are off, and we do not enable them.
  - NanoGPT does not train on, sell or advertise with content.
  - Metadata (model, token counts, cost, timestamps) is kept for billing and abuse prevention.
  - ZDR is described as "best-effort", based on the provider's own claim; NanoGPT cannot audit
    providers. Some intermediaries screen all routes for CSAM and may keep flagged content.
  - Requests to OpenAI models carry a hashed NanoGPT account or session identifier.
- **What is sent:** normalised entry text only, numbered within a request. No registrant code,
  response id, date, dose, age, sex or location. Redacted (b)(6) entries and entries with a
  detectable phone number or email are never sent.
- **Scope before OSF registration:** week-1 and six-week entries only (enforced in code).
- **API key:** in `<VSAFE_DATA_DIR>/.env` or the `NANOGPT_API_KEY` environment variable, never in
  the repository. The key was shared in an assistant chat on 2026-11-10; rotate it before the
  full run.
- **Spend:** each run has a dollar cap (`--max-usd`); runs are logged in the `llm_runs` table.

## Rules for people
- Quotations in the report or manuscript are paraphrased or composited, never verbatim, never with a registrant code.
- Redacted (b)(6) words are not reconstructed or guessed.
- Gold-set coders read descriptions of death, pregnancy loss and suicide: sessions are time-limited with a debrief.
- Ethics: request a written determination (e.g. VU Amsterdam) that secondary analysis of these data falls outside review.
