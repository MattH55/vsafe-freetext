# Actions for Matthew before submission

The package is `C:\Users\matth\OneDrive\Documents\OpenSourceMed\PACVS-vsafe-DrugSafety-submission-2026-11-12.zip`
(also in `docs/submission/`, built from tag `v1.0-submission`). In order. Every `[[HUMAN: …]]` placeholder in
the manuscript and cover letter is listed in section B.

Also decide: the repository name. GitHub resolves `MattH55/vsafe-freetext`, not `mhalma/vsafe-freetext`
as written in the brief; the manuscript and cover letter use the former with a flag.

## A. In order

1. Fill in affiliation, ORCID (done: 0000-0003-2487-0636), postal address, funding, conflicts of interest and the ethics determination (see B).
2. Code the 306-entry audit sheet (B5; 17 per domain per side): `D:/vsafe-data/gold_set/vsafe_full/audit_layer3_vs_cdc_sheet.csv`. Instructions: for each item, read the entry and the named domain; enter 1 in `present_0_1` if the entry describes a symptom in that domain as the respondent's own, current or recent experience, 0 if not; use `note` for doubt. Do not open the key file until done. Then run `vsafe-ft submission --steps audit-score` [[to be added once coding exists]] and paste the result into the manuscript at the slot marked `[[HUMAN: pending coding]]`.
3. Make the OSF registration public (osf.io/gnfpd). The protocol promised a public registration with no embargo; the manuscript and preprint cite it. Lifting the embargo keeps the original timestamp. Then confirm that the registration and amendment dates in the manuscript (registration 2026-11-11; amendments 1 and 2 filed 2026-11-11) match what OSF shows.
4. Decide on the repository after reading the audit result in `docs/submission/repo-audit.md`: make github.com/mhalma/vsafe-freetext public, mint a Zenodo DOI for tag `v1.0-submission`, and put the DOI in Code Availability.
5. Post the preprint on OSF Preprints under CC BY 4.0; add its DOI to the cover letter where marked.
6. Email Retsef Levi with the preprint and the cohort comparison (addendum 1, task 3.9), proposing collaboration on a follow-up onset paper, not co-authorship of this one. The assistant does not send this.
7. Submit to Drug Safety. Open the live submission-guidelines page first and confirm `docs/submission/guidelines-checked.md`.

## B. Placeholders

| Where | Placeholder | Decision needed |
|---|---|---|
| Title page | affiliation and address | Done 2026-11-12: Open Source Medicine, Pärnu mnt. 139c, 11317 Tallinn, Estonia |
| Declarations, Funding | `[[HUMAN: funding source …]]` | Source, or "No funding was received for this study" |
| Declarations, Conflicts of Interest | `[[HUMAN: conflicts of interest …]]` | Consider: any role with or payment from OpenVAERS, ICAN, Vaccine Data Navigator or another advocacy or litigation body; expert-witness work; language-model provider credits used for layer 3 |
| Declarations, Ethics Approval | `[[HUMAN: applicable rule or jurisdiction]]` and the committee-determination option | (a) a written determination that review was not required, with committee and date, is stronger; (b) the statement as drafted otherwise. Levi & Lu obtained an MIT COUHES determination; reviewers may ask |
| Declarations, Code Availability | `[[HUMAN: make public; Zenodo DOI]]` | After the repo audit |
| Methods, Data sources | `[[HUMAN: OpenVAERS permission]]` | Whether to ask OpenVAERS for permission or acknowledgement of the person-page reads; remove the flag once decided |
| Results, Validation | `[[HUMAN: pending coding]]` | Result of the 300-entry audit (B5) |
| Cover letter | `[[HUMAN: preprint DOI]]`, `[[HUMAN: names]]` | Preprint DOI once posted; suggested reviewers (kinds of expertise listed; the assistant did not pick people) |
| guidelines-checked.md | `[[HUMAN: open the live page …]]` | Confirm the journal's requirements from the live page |

## C. Things the assistant did not do, by instruction

Did not post the preprint, submit, e-mail anyone, change the repository's visibility, lift the OSF embargo,
edit the OSF registration or amendments, code any entries, or invent an affiliation, address, funding
source or conflict.
