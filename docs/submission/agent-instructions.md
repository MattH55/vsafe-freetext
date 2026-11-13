# Instructions for the agents that finish the submission

Three web tasks remain. Each needs a logged-in browser session (GitHub, Zenodo, OSF), so each is for a
browser agent acting under Matthew's account, with Matthew present to approve the final click. Rules
for every task: do only what the task says; do not change any file in the repository; do not edit the
OSF registration or its amendments; do not send e-mail; copy the identifiers listed under "Report
back" into `docs/submission/human-actions.md`, and nothing else.

## Task A. Make the repository public and mint a Zenodo DOI (done 2026-11-12: doi:10.5281/zenodo.24178319)

Repository: https://github.com/MattH55/vsafe-freetext (private). The audit is in
`docs/submission/repo-audit.md`: no data files, keys or registrant codes anywhere in the history.

1. GitHub → the repository → Settings → General → Danger Zone → "Change repository visibility" →
   Public. Confirm with the repository name when asked. Matthew approves this step.
2. Zenodo (https://zenodo.org, log in with the GitHub account) → GitHub integration
   (https://zenodo.org/account/settings/github/) → switch on `MattH55/vsafe-freetext`.
3. GitHub → the repository → Releases → "Draft a new release" → choose existing tag
   `v1.0.1-submission` → title "v1.0.1-submission: Drug Safety submission package" → description:
   "Code, frozen taxonomy v1.0 and submission package for 'Detecting post-acute COVID-19 vaccination syndrome in pharmacovigilance data'.
   Aggregates only; no participant data." → Publish release. Zenodo archives it automatically
   within a few minutes.
4. Zenodo → the new record → check: title as above; author Matthew Halma, ORCID
   0000-0003-2487-0636, affiliation Open Source Medicine; licence as the repository states;
   related identifier: the OSF registration https://osf.io/gnfpd ("is supplemented by"). Save.

Report back: the version DOI (10.5281/zenodo.…) and the concept DOI. These go into the manuscript
(Code Availability) and the cover letter. Done: doi:10.5281/zenodo.24178319.

## Task B. Lift the OSF registration embargo

Registration: https://osf.io/gnfpd (project https://osf.io/7wpgy). The protocol promised a public
registration; the manuscript and the preprint cite it. Lifting the embargo keeps the original
registration timestamp. Nothing in the registration or its two updates is to be edited.

1. OSF → log in → open https://osf.io/gnfpd → the registration's "Overview" page.
2. Find "Embargoed" / "End embargo early" (under the registration status or the ⋯ menu) → confirm.
   OSF may ask the contributor to approve by e-mail; approve it.
3. When the page shows "Public", open it in a private window to confirm it is readable without
   logging in, and that updates 1 and 2 (the two amendments) are listed.

Report back: confirmation that the registration is public, the registration date shown on the page,
and the dates of updates 1 and 2. These must match the manuscript (registration 2026-11-11;
amendments 1 and 2 filed 2026-11-11); if they differ, report the difference and change nothing.

## Task C. Post the preprint on OSF Preprints

Files: `docs/submission/manuscript.pdf` (the preprint text), `docs/submission/supplement.docx` or a
PDF export of it (supplementary file). Licence: CC BY 4.0.

1. https://osf.io/preprints → "Add a preprint" → server: OSF Preprints (or MedRxiv is not used;
   see note) → upload `manuscript.pdf`.
2. Title: "Detecting post-acute COVID-19 vaccination syndrome in pharmacovigilance data: a pre-registered analysis of v-safe free text". Author: Matthew Halma (ORCID 0000-0003-2487-0636,
   Open Source Medicine). Abstract: paste the Abstract from the manuscript. Subjects: Medicine and
   Health Sciences → Epidemiology / Public Health; Pharmacology. Tags: v-safe; VAERS; COVID-19
   vaccine; post-acute COVID-19 vaccination syndrome; pharmacovigilance; free text.
3. Licence: CC BY 4.0. Conflicts of interest: copy the Declarations text. Data availability: copy
   the "Availability of Data and Material" and "Code Availability" statements (with the Zenodo DOI
   from Task A if available). Link the preprint to the OSF project https://osf.io/7wpgy.
4. Supplementary file: upload the supplement.
5. Submit. Matthew approves the final submission.

Note: the manuscript's preprint statement names OSF Preprints; do not post to medRxiv as well.

Report back: the preprint DOI and URL, for the submission form and the cover letter's preprint sentence.

## Task D (coding agent, after Tasks A and C): put the identifiers into the package

1. In the Claude Doc manuscript and `docs/submission/cover-letter.md`, replace
   the cover letter's preprint sentence with the preprint DOI (the Zenodo DOI is already in place).
2. Rebuild with `scripts/docx_build/` (see its README), re-export the PDF, re-zip to
   `OpenSourceMed/PACVS-vsafe-DrugSafety-submission-2026-11-12.zip`, commit, tag
   `v1.0.2-submission`.
