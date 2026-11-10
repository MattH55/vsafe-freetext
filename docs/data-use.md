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

## Layer-3 providers (approved by the protocol owner, 2026-11-10)

Two LLMs label the same closed theme list with the same fixed prompt (`classify/llm.py`):

| Role | Provider | Model | Retention |
|---|---|---|---|
| Primary: labels all in-scope text | NanoGPT subscription | `z-ai/glm-5.3` | Zero-data-retention routes only |
| Second: model-sensitivity sample only | Anthropic API | `claude-opus-5-5` | 30 days (Anthropic default) |

Order chosen by the protocol owner (2026-11-10): the bulk of the text goes to the
zero-retention route; Anthropic receives only the comparison sample.

### NanoGPT (primary)

- Subscription endpoint `https://nano-gpt.com/api/subscription/v1/chat/completions`. NanoGPT does
  not run inference itself; it forwards each request to an underlying model provider.
- **Every request** sets `provider: {zdr: true, data_collection: deny}`. NanoGPT then routes only
  to providers that state they keep no prompts or outputs, and fails rather than falling back
  (verified: a model without a ZDR route is refused with `zdr_provider_required`;
  `z-ai/glm-5.3` was confirmed on a ZDR route with synthetic text).
- **Terms read 2026-11-10** (privacy policy and terms of service, both "Last Updated:
  November 9, 2026"):
  - NanoGPT does not store prompt or response content by default. Opt-in request logging and
    Responses-API storage are off, and we do not enable them.
  - NanoGPT does not train on, sell or advertise with content.
  - Metadata (model, token counts, cost, timestamps) is kept for billing and abuse prevention.
  - ZDR is described as "best-effort", based on the provider's own claim; NanoGPT cannot audit
    providers. Some intermediaries screen all routes for CSAM and may keep flagged content.
- An earlier pilot attempt (2026-11-10) sent a 2,000-entry sample to `anthropic/claude-haiku-5.5`
  through NanoGPT's pay-per-token endpoint, also with ZDR set; its replies were unusable
  (truncated) and are stored as not ok.

### Anthropic API (second LLM)

- Messages API via the official `anthropic` SDK; structured output constrains themes to the list;
  server-side refusal fallback (`fallbacks: "default"`) is enabled for Opus-tier models.
- **Terms read 2026-11-10** (privacy.claude.com; retention article updated July 1, 2026;
  training article updated August 18, 2026):
  - API inputs and outputs are deleted from Anthropic's backend "within 30 days of receipt or
    generation". Zero data retention exists only by separate agreement, which we do not have.
  - Inputs flagged by trust-and-safety classifiers for a Usage Policy violation may be kept up to
    2 years (classification scores up to 7 years).
  - By default Anthropic does not use inputs or outputs from commercial products for training.
    We submit no feedback (feedback data is kept 5 years).
- Because retention is 30 days, Anthropic receives only the model-sensitivity sample, never the
  full corpus.

### Both providers

- **What is sent:** normalised entry text only, numbered within a request. No registrant code,
  response id, date, dose, age, sex or location. Redacted (b)(6) entries and entries with a
  detectable phone number or email are never sent.
- **Scope before OSF registration:** week-1 and six-week entries only (enforced in code).
- **API keys:** `NANOGPT_API_KEY` and `ANTHROPIC_API_KEY` in `<VSAFE_DATA_DIR>/.env` or the
  environment, never in the repository. Both keys were shared in an assistant chat on
  2026-11-10; rotate them before the full run.
- **Spend:** each run has a dollar cap (`--max-usd`); runs are logged in the `llm_runs` table.

## Rules for people
- Quotations in the report or manuscript are paraphrased or composited, never verbatim, never with a registrant code.
- Redacted (b)(6) words are not reconstructed or guessed.
- Gold-set coders read descriptions of death, pregnancy loss and suicide: sessions are time-limited with a debrief.
- Ethics: request a written determination (e.g. VU Amsterdam) that secondary analysis of these data falls outside review.
