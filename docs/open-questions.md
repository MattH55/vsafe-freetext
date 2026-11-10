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

- The vaccinations file has no age column (`REGISTRANT_CODE, MANUFACTURER, DOSE_NUMBER,
  VACCINATION_DATE, COADMINISTERED, COADMINISTERED_VAX`); age band must come from registrants.

- Registrants (`REGISTRANT_CODE, ZIP_CODE, SEX, REGISTERED_DATE, TIME_ZONE, RELATIONSHIP,
  GUARDIAN_REGISTRANT_CODE`) has no age column either. Check the check-in file for age; if none,
  `age_band` cannot be a reporting dimension.
- `GUARDIAN_REGISTRANT_CODE` is another person's code: only a boolean `guardian` is carried.
- VAERS: the full bundle `AllVAERSDataCSVS.zip` (data dated 2026-06-03, 1990-2026 +
  NonDomestic, 585,977,435 bytes, sha256 f8900934e55cc06ee7b41ed0938c876e625a48bf5726e9e7baadd1d417ed1280)
  was already on this machine (downloaded by hand for ParentsVaccineGUide); copied to
  `<data dir>/raw/vaers/`. Add to MANIFEST.tsv when the scripted downloads finish.

- Check-ins have no survey-type column: survey type is derived from `DAYS_SINCE`
  (provisional bins in `link.survey_type_from_days`; verify on the day distribution).
- `consolidated_health_checkin.zip` is compressed with Deflate64 (zip method 9), which Python's
  zipfile cannot read; ingest uses `zipfile-deflate64`.
- Still no age column after check-ins: `age_band` cannot be a reporting dimension unless
  another file supplies it. Decide whether to drop it from `aggregate.DIMENSIONS`.

## Immediate next steps
- [ ] Download the 13 updated free-text files, Nov 2024 MedDRA, registrants, vaccinations, check-ins (~7 GB); add URLs to `config/sources.yaml`.
- [ ] `vsafe-ft inspect` the first release; fill `config/columns.yaml`.
- [ ] Decide the analysis machine (workstation vs cloud VM) and local vs hosted LLM for layer 3.
- [ ] Decide the website home: Vaccine Data Navigator section vs standalone page.
- [ ] Recruit one or two gold-set coders for weeks 6–9.
- [ ] Ask OpenVAERS for the v-safe-to-VAERS match table (else rebuild the 11-field matcher).
- [ ] Start the VAERS-narrative arm (public data; can begin before v-safe files are in hand).

## Check-in key (resolved 2026-11-09)

`SURVEY_STATIC_ID` identifies the survey form (146 values across 144,972,337 check-ins), not
a check-in. `RESPONSE_ID` is the check-in key: never null, unique but for 236 values, and
every one of the 390,000 response ids in updated release 1 is found in the check-in files.
Entries now join check-ins on (response id, registrant) and dedupe on (registrant, response
id, field, text). Survey type stays derived from `DAYS_SINCE`: a form id's days can span up
to a year.
