# Actions before submission

The package is `C:\Users\matth\OneDrive\Documents\OpenSourceMed\PACVS-vsafe-DrugSafety-submission-2026-11-12.zip`
(also `docs/submission/` in the repo, tag `v1.0.1-submission`). Decisions taken by Matthew on 2026-11-12
are recorded here; what remains is in section B.

## A. Decided

| Item | Decision | Where applied |
|---|---|---|
| Affiliation and address | Director, Open Source Medicine, Pärnu mnt. 139c, 11317 Tallinn, Estonia | Title page, cover letter |
| Funding | None | Declarations |
| Conflicts of interest | Director of the Open Source Medicine Foundation; previous funding from the Independent Medical Alliance; no role with or payment from OpenVAERS, ICAN or any litigation body; language-model services paid at list price | Declarations |
| Ethics | Review not required (public de-identified records, aggregates only) | Declarations |
| OpenVAERS permission | Not sought; statement stands as "no permission beyond the site's published access rules was sought" | Methods |
| Repository | `MattH55/vsafe-freetext` (the brief's `mhalma/` name does not exist) | Code Availability, cover letter |
| Levi & Lu | Not contacted | — |
| Word count | Submit at the current length (main text about 6,000; abstract 340) | — |
| Suggested reviewers | Seven listed in the cover letter with expertise and last-known affiliation; Levi and Lu excluded | Cover letter |

## B. Remaining

1. ~~Code the 306-entry audit sheet~~ Done 2026-11-12; scored and in the manuscript (Table 12). The original item:
   **Code the 306-entry audit sheet** (`D:\vsafe-data\gold_set\vsafe_full\audit_layer3_vs_cdc_sheet.csv`).
   What it is: the final classifier and CDC's MedDRA coding disagree on whether a symptom domain is
   present in about 335,000 entry-domain pairs. Because CDC's coding is the reference standard,
   every disagreement counted against the classifier in the validation, but a disagreement can be
   either side's error. The sheet holds 306 of them, 17 per domain where only the classifier was
   positive and 17 where only CDC was, in random order with the side hidden. For each row, read the
   entry and the named domain and enter 1 in `present_0_1` if the entry describes a symptom in that
   domain as the respondent's own, current or recent experience, else 0; use `note` for doubt. Do
   not open the key file until finished. Then run
   `vsafe-ft submission --steps audit-score` (with `VSAFE_DATA_DIR=D:/vsafe-data VSAFE_DB=vsafe_full`)
   and the result in `sub_b5_audit_scored.csv` (how often each side was right, by domain) replaces
   `[[HUMAN: pending coding]]` in Results, as an exploratory finding. If you would rather submit
   without it, delete that sentence and the audit paragraph; the manuscript stands without it.
2. **Browser agent, Task A** (`agent-instructions.md`): make the repository public, publish the
   `v1.0.1-submission` release, mint the Zenodo DOI. Then the DOI goes into Code Availability and
   the cover letter.
3. **Browser agent, Task B**: lift the OSF embargo on osf.io/gnfpd and confirm the dates.
4. **Browser agent, Task C**: post the preprint on OSF Preprints (CC BY 4.0); the DOI goes into the
   cover letter.
5. **Coding agent, Task D**: put both DOIs into the manuscript and cover letter, rebuild, re-zip,
   tag `v1.0.2-submission`.
6. **Check reviewer affiliations and e-mail addresses** on the journal's form (the cover letter
   gives names and last-known affiliations only).
7. **Submit to Drug Safety.** Open the live submission-guidelines page first and confirm
   `guidelines-checked.md`; the journal's form will ask for the declarations already in the
   manuscript.
8. Optional: confirm the layer-3 cost on NanoGPT's usage page (manuscript says US$0.022 as logged
   per request); inspect the one 8-word phrase the quote scan flagged
   (`QUOTE_SCAN_N=8 python scripts/quote_scan.py docs/submission/manuscript.txt`).

## C. Things the assistant did not do, by instruction

Did not post the preprint, submit, e-mail anyone, change the repository's visibility, lift the OSF
embargo, edit the OSF registration or amendments, code any entries, or invent any declaration.
