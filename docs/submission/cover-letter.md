Matthew Halma
Director, Open Source Medicine
Pärnu mnt. 139c, 11317 Tallinn, Estonia
mhalma@opensourcemed.info
ORCID 0000-0003-2487-0636

12 November 2026

The Editor-in-Chief
Drug Safety

Dear Editor,

I am submitting the original research article "A PACVS signature in v-safe free text: a pre-registered study whose primary analysis was not feasible, with exploratory results" for consideration by Drug Safety.

**Why Drug Safety.** The paper addresses a surveillance question: whether a multi-system, post-acute syndrome after COVID-19 vaccination can be seen in a pharmacovigilance system that codes symptoms one at a time, and whether such cases reach VAERS. It analyses 7.8 million free-text entries from CDC's v-safe programme, including 1.6 million written 3 to 12 months after a dose, with a classifier validated against CDC's own MedDRA coding, and links v-safe records to VAERS. The methods, a frozen lexicon plus a language-model classifier under a pre-registered accuracy gate, and the detection analysis are of direct interest to readers working on signal detection in spontaneous and active surveillance.

**Pre-registration, stated plainly.** The protocol was registered on the Open Science Framework (osf.io/gnfpd) before any long-term text was read, with two amendments filed before the results they govern were computed. The classifier met the pre-registered accuracy gate for only one of nine symptom domains, so the registered primary analysis could not be run. The paper reports this openly, presents the registered sensitivity analysis on all nine domains, and labels every analysis added afterwards as not pre-registered, with the reason for each. The findings are presented as hypothesis-generating.

**Preprint.** A version of this manuscript has been posted as a preprint on OSF Preprints under a CC BY 4.0 licence: [[HUMAN: preprint DOI]].

**Related work.** A closely related, independent analysis of v-safe's structured answers (Levi R, Lu N. Reporting on prolonged adverse health impact among V-SAFE enrollees. Research Square, posted 25 August 2026, doi:10.21203/rs.3.rs-10768889/v1) is under review elsewhere. It was read after this study's registered results were computed. The present paper uses the free text rather than the structured answers, defines its phenotype without relying on participants' attribution, and adds a null-model test of symptom clustering and a VAERS-filing comparison; the manuscript compares the two sets of results.

**Data and code.** All source files are public FOIA releases or public VAERS data. Only aggregates with at least 10 people per cell are reported, and no free text is quoted. The analysis code and frozen taxonomy are at github.com/MattH55/vsafe-freetext (tag v1.0-submission) [[HUMAN: confirm the repository name (mhalma/vsafe-freetext does not resolve); public on posting; Zenodo DOI]].

**Suggested reviewers.** Reviewers with expertise in the following areas would be well placed to assess the manuscript: pharmacovigilance signal detection and disproportionality methods; validation of natural-language-processing or large-language-model classifiers against MedDRA coding; post-acute syndromes after infection or vaccination (long COVID, ME/CFS, PACVS); and VAERS and v-safe data. [[HUMAN: names, affiliations and e-mail addresses]]

The manuscript is not under consideration elsewhere, has one author, and has no conflicts of interest to declare beyond those stated in the Declarations [[HUMAN: confirm]]. Main text: 5,039 words; 11 tables; 5 figures; 22 references; one supplementary file.

Yours sincerely,

Matthew Halma
