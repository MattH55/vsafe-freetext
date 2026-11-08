# Open questions and immediate next steps

## Settle on first contact with the files
- [x] Registrant code column name in the free-text files: `REGISTRANT_CODE` (updated and original, incl. under-3).
- [ ] `REGISTRANT_CODE` joins cleanly to `consolidated_registrants` (join rate at gate 1).
- [ ] `SURVEY_STATIC_ID` matches the check-in survey identifier; count of entries that fail to match.
- [ ] Whether the three MedDRA releases cover all entries or a subset (Nov 2024 file is largest, 383 MB).
- [ ] Duplicates across the 12 releases and the under-3 file.
- [ ] Updated files = original files + 3 fields (cross-check). Header level confirmed for release 1 and
      the under-3 file: updated = original columns + `SURVEY_STATIC_ID`, `RESPONSE_ID`, `STARTED_ON`.
      Row level: `vsafe-ft qa` after ingest.
- [ ] Read the data.cdc.gov v-safe user agreement in full; record date and terms in `docs/data-use.md`.

## Found on first contact
- No redaction-flag column in the free-text files; `redacted` is derived from the `(b)(6)` pattern.
- Field order differs from the column names in the brief: the three text fields are
  `SYMPTOMS_DESCRIPTION` (SD), `SYSTEMIC_REACTION_OTHER` (SRO), `HEALTHCARE_VISITS_OTHER` (HCVO).
- The ICAN page lists 13 original files (12 releases + under-3), not 12; and an under-3
  check-in file (`Consolidated_health_checkin_u3`). Both are in `config/sources.yaml`.
- The updated release 3 is a revised file (`3rd Interim Release 24-01322-FOIA (Revised).xlsx`).
- The GitHub owner `mhalma` does not exist; the repository is `MattH55/vsafe-freetext` (private).

## Immediate next steps
- [ ] Download the 13 updated free-text files, Nov 2024 MedDRA, registrants, vaccinations, check-ins (~7 GB); add URLs to `config/sources.yaml`.
- [ ] `vsafe-ft inspect` the first release; fill `config/columns.yaml`.
- [ ] Decide the analysis machine (workstation vs cloud VM) and local vs hosted LLM for layer 3.
- [ ] Decide the website home: Vaccine Data Navigator section vs standalone page.
- [ ] Recruit one or two gold-set coders for weeks 6–9.
- [ ] Ask OpenVAERS for the v-safe-to-VAERS match table (else rebuild the 11-field matcher).
- [ ] Start the VAERS-narrative arm (public data; can begin before v-safe files are in hand).
