# Open questions and immediate next steps

## Settle on first contact with the files
- [ ] Registrant code column name in the free-text files; joins cleanly to `consolidated_registrants`.
- [ ] `SURVEY_STATIC_ID` matches the check-in survey identifier; count of entries that fail to match.
- [ ] Whether the three MedDRA releases cover all entries or a subset (Nov 2024 file is largest, 383 MB).
- [ ] Duplicates across the 12 releases and the under-3 file.
- [ ] Updated files = original files + 3 fields (cross-check).
- [ ] Read the data.cdc.gov v-safe user agreement in full; record date and terms in `docs/data-use.md`.

## Immediate next steps
- [ ] Download the 13 updated free-text files, Nov 2024 MedDRA, registrants, vaccinations, check-ins (~7 GB); add URLs to `config/sources.yaml`.
- [ ] `vsafe-ft inspect` the first release; fill `config/columns.yaml`.
- [ ] Decide the analysis machine (workstation vs cloud VM) and local vs hosted LLM for layer 3.
- [ ] Decide the website home: Vaccine Data Navigator section vs standalone page.
- [ ] Recruit one or two gold-set coders for weeks 6–9.
- [ ] Ask OpenVAERS for the v-safe-to-VAERS match table (else rebuild the 11-field matcher).
- [ ] Start the VAERS-narrative arm (public data; can begin before v-safe files are in hand).
