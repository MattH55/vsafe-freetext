# Amendment 2: primary layer-3 model changed to DeepSeek V4.1 Flash

**Registration:** https://osf.io/gnfpd (filed 2026-11-11; amendment 1 filed 2026-11-11)
**Amendment drafted:** 2026-11-11
**Status:** draft. To be filed on OSF before the final classifier is validated (amendment 1)
and before any Q1–Q3 result is computed.
**Changes:** section 7 of the registration ("Model sensitivity", primary LLM).

## What changes and why

The registration named `z-ai/glm-5.3` (NanoGPT subscription) as the primary layer-3 model.
Layer 3 labels the long-term residue, meaning the entries layer 1 gave no theme: 649,516
entries, 386,862 unique texts.

GLM-5.3 spends most of its tokens on hidden reasoning. After 1,800 texts the run had used
up a large share of the subscription quota, so the full residue was not feasible.

We replace it with **`deepseek/deepseek-v4.1-flash`** on NanoGPT's pay-per-token endpoint,
with reasoning turned off (`reasoning.effort = none`).
- It uses the same zero-data-retention routing as before (`provider.zdr = true`,
  `data_collection = deny`).
- It uses the same prompt (version `v0.1-2026-11-10`) and the same closed theme list
  (taxonomy v1.0).
- Requests are sent four at a time. Each request is independent, so this changes speed, not
  labels.

## Why this is acceptable before results

Layer-1 validation against CDC MedDRA coding (amendment 1) has been computed and is reported
in full (`docs/phase2-report.md`). It shows that layer 3 is needed for any PACVS domain to
pass the gate on recall. No layer-3 label on long-term text has been analysed: the 1,800 GLM
labels were stored but not looked at.

The model change is decided before the final classifier is validated. The amendment-1 gate
(precision and recall ≥ 0.85 against CDC coding) applies to the final classifier whatever
model it uses, so the switch is tested by the same pre-specified standard.

## Pilot of the new model (week-1 / six-week entries only)

On 2026-11-11 DeepSeek V4.1 Flash labelled the phase-1 pilot sample: 2,000 release-1 week-1 /
six-week entries, 1,591 unique texts, seed 1. GLM-5.3 and Claude had already labelled the same
sample. The run had 0 failed requests and 0 refusals, used 123,097 tokens and took 171 s.

The registered model-sensitivity rule flags a theme when its entry count differs by more than
20% between two models.
- **DeepSeek vs Claude** (`claude-opus-5-5`, the registered second LLM): every PACVS domain is
  within 13.3% (fatigue_pem 0.133, sleep 0.108, pain 0.068, the rest ≤ 0.05). Only
  `pre_existing_worsened` is flagged (0.345).
- **DeepSeek vs GLM-5.3**: every PACVS domain is within 18.9% (sleep 0.189, the rest ≤ 0.128).
  `pre_existing_worsened` (0.367) and `acute_diagnosis` (0.263) are flagged.

Aggregates are in `aggregates/phase1_llm_model_shift_deepseek_vs_*_random2000_s1.csv`.

## Procedure from here

1. Layer 3 with `deepseek/deepseek-v4.1-flash` labels every unique long-term residue text.
   Texts with a detectable email or phone number are skipped, as registered.
2. The final classifier is layer 1 plus layer 3, and is validated as in amendment 1.
3. The model-sensitivity check uses DeepSeek as model 1 and Claude as model 2, on the
   registered fixed sample. Themes that shift by more than 20% are reported as model-sensitive.
4. The 1,800 GLM-5.3 long-term labels are not used in any analysis.

## What is unchanged

- The prompt, taxonomy, case definition, gate and Q1–Q4 analysis plan.
- The second LLM (`claude-opus-5-5`, comparison sample only).
- Zero-data-retention routing for every NanoGPT request.
- The disclosure rule: only aggregates with at least 10 people per cell are published.
