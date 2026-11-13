# Response to the pre-submission review of 2026-11-12

A full critical review of the manuscript was received on 2026-11-12 (before submission). Each point
is listed with what was changed. New analyses are labelled "not pre-registered" in the manuscript,
run from the same frozen taxonomy and classifier outputs, and reported in Results, "Analyses not in
the pre-registration" (R1, R2) and supplement tables S29 to S31. No registered result was rerun or
changed.

## Major concerns

| # | Concern | Response |
|---|---|---|
| 1 | Classifier validity is the central weakness: eight of nine domains failed the gate; layer 3 applied only to long-term residue; exclusion tags imprecise (0.14, 0.31); audit author-coded; low cognitive recall undercounts the domain driving the signal; fatigue pass model-dependent | Limitations rewritten as twelve items. Item 1 now gives cognitive (0.74) and sleep (0.72) recall and states that independent coding sized for domain-level accuracy is required before any confirmatory claim; item 3 states the audit cannot rescue the gate; item 5 (model dependence) and item 9 (exclusion precision 0.14 and 0.31, rate ratio 0.94 to 0.78) are now explicit. Key Point 3 and Conclusions name independent multi-coder validation as the next step. Discussion, Clustering, notes that the strongest ties all involve the domain with the lowest recall among the four |
| 2 | Onset uninformative; biases large; cannot separate late vaccine effect, background illness (including intercurrent COVID-19) and late recognition or reporting | Discussion, Onset, now lists three readings (late effect, background illness, late reporting); Limitations item 7 states that infection history is visible only through the exclusion tags; Conclusions name an onset analysis that treats the survey schedule as the observation process as future work |
| 3 | Persistence partly definitional; same-survey vs group (d) narrows the gap to 37 points; no estimate relative to the general population or non-responders | Discussion, Persistence, now labels the two checks as not pre-registered, explains that group (d) is the single-complaint comparison the question needs, and states that persistence relative to the general population or to people who stopped responding is not estimated. Limitations item 10 says the strictest contrast was specified after the results were seen |
| 4 | Clustering is not causality or a specific entity | Abstract Conclusion, Discussion and Conclusions now say that the data do not establish that vaccination caused the pattern, its prevalence among recipients, or its status as a clinical entity, and that selection into long-term response is a third reading |
| 5 | VAERS comparison is a weak test of the detection hypothesis; rate ratio sensitive to the exclusion reading | Limitations item 11 states that a contrast between two filing rates near 5% is a weak test of under-capture and says nothing about cases who never reach VAERS; item 9 gives the 0.94 to 0.78 range. Discussion, Detection, already made the same point and is unchanged |
| 6 | Author position and audit independence | Conflicts of Interest already declares the Foundation role, prior funding and prior PACVS publications; Limitations item 3 now states the coder was blind to side but not to the hypotheses; the need for independent multi-coder validation is in Key Points, Limitations and Conclusions |
| 7 | Missing covariates: no age, no infection history; cognitive and sleep frequencies partly classifier-driven | Limitations item 7 (new, separate) covers age and infection history; item 1 covers the recall of the cognitive and sleep domains |

## Specific suggestions

| Suggestion | Response |
|---|---|
| Independent blinded dual or triple coding; hybrid retraining; keep the frozen map for the registered comparison | Cannot be done within this submission (human work; the brief forbids presenting LLM coding as human coding). Stated as the next step in Key Points, Limitations and Conclusions; the frozen map is kept |
| Survival-style onset analysis treating survey timing as the observation process; model the probability that an early symptom is written rather than ticked | Named as future work in Conclusions; not attempted here |
| Pre-specify or clearly label the same-survey vs group (d) contrast; compare multi-domain persistence against single-domain complaints | Labelled as not pre-registered in Discussion and Limitations. Group (d) (worse or impacted but fewer than two domains, 10.5% persistence) is that single-complaint comparison, and the Discussion now says so |
| Highlight curveball and text-matched results; report the core four-domain subgraph or a modularity statistic; stratify on sex and dose | New R2, core-subgraph statistic (Results, Table 9; supplement S31): co-occurrences summed over the six core pairs vs the other 30, under every null, computed from the saved pair tables. New R1, Q1 within each sex (Results paragraph; supplement S29 and S30): registered, text-matched and curveball nulls within women and within men, and the registered null within sex x dose strata. Dose and manufacturer strata were already in Results |
| Keep the hypothesis-generating stance; validated classifier plus structured-answer onset analysis; external replication | Conclusions rewritten accordingly |
| Lead Results and Abstract with the gate failure; put the surviving core in Key Points; keep the registered vs exploratory distinction unmistakable | Abstract Results and Key Point 1 now open with the gate failure; Key Point 2 states that the aggregate excess did not survive the strict nulls and the core did; every exploratory table is captioned or introduced as not pre-registered |
| Clarify the 7.55 M vs 7.82 M difference; note on LM cost; age gap more prominent | The Corpus paragraph states the difference and that it is unexplained; the cost paragraph is retained; age is now its own Limitations item |

## Not changed

The registered gate, the frozen map, the case definition and every registered result are unchanged.
A stale drafting instruction at the end of Declarations ("Before submission, replace the bracketed
items...") was found during this pass and removed.
