# Phase 2 report: full corpus, after registration

Registered 2026-11-11 as https://osf.io/gnfpd (embargoed). Everything here was run after
filing. Aggregates only: every cell has at least 10 people, and smaller cells are suppressed.
Data are in `D:/vsafe-data` (external drive), database `interim/vsafe_full.duckdb`
(`VSAFE_DB=vsafe_full`). The release-1 database `interim/vsafe.duckdb`, with the early gold set
and the LLM pilot labels, is unchanged.

## Link: 12 updated releases and the under-3 file (2026-11-11)

`vsafe-ft link` took 15,434 s (4 h 17 min). It was restarted once, after drive C filled up, and
moved to D:.

| Join | Rate |
|---|---|
| Entry to registrant | 0.998 |
| Entry to dose | 0.998 |
| Entry to check-in survey | 0.945 |

All three rates pass gate 1 (≥ 0.90).

There are 7,819,251 entries after de-duplication. The OSF abstract says 7.55 million entries.
The cause of the difference has not been checked yet.

| Period | Field | Entries | People | Share themed (layer 1) |
|---|---|---|---|---|
| week 1 / six weeks | SD | 1,679,313 | 1,180,793 | 0.767 |
| week 1 / six weeks | SRO | 3,968,173 | 2,142,765 | 0.598 |
| week 1 / six weeks | HCVO | 143,513 | 120,751 | 0.078 |
| long-term | SD | 1,458,795 | 1,207,417 | 0.644 |
| long-term | HCVO | 136,317 | 126,763 | 0.030 |
| long-term | SRO | suppressed (< 10 people) | | |
| survey not matched | SD | 315,973 | 270,666 | 0.665 |
| survey not matched | SRO | 94,608 | 57,021 | 0.650 |
| survey not matched | HCVO | 22,550 | 21,444 | 0.037 |

- **Long-term entries by survey:** 3 months 565,626; 6 months 586,468; 12 months 443,027. In
  total 1,595,121 entries from 1,207,426 people.
- **SRO at long-term surveys:** the long-term surveys have almost no SRO entries.
- **HCVO coverage:** HCVO is the lexicon's weakest field at every period (3–8%). Its recall on
  the gold set decides whether layer 3 is needed there.

## Layer 1 on every entry (2026-11-11)

`vsafe-ft classify --long-term` used the frozen taxonomy v1.0 and took about 84 minutes.

| Flag | SD people | SRO people | HCVO people |
|---|---|---|---|
| third party (kept) | 9,402 | 4,461 | 487 |
| pre-vaccine (dropped) | 2,142 | 2,773 | 35 |

## Gold set, long-term period (drawn 2026-11-11)

`vsafe-ft gold draw --size 1000 --period long_term --seed 1` took 31 s. It drew 1,000 entries,
which are 940 distinct texts. The sheets are `D:/vsafe-data/gold_set/vsafe_full/sheet_A.csv`
and `sheet_B.csv`; I have not opened them.

| Stratum | Entries | Texts | Weight |
|---|---|---|---|
| HCVO, themed | 124 | 119 | 32.44 |
| HCVO, unthemed | 164 | 146 | 800.29 |
| SD, themed | 418 | 402 | 2,242.99 |
| SD, unthemed | 285 | 266 | 1,818.47 |
| SRO, themed and unthemed | suppressed (< 10 people) | | |

The confirmatory theme set is decided by this part of the gold set (precision and recall
≥ 0.85, OSF section 7). Q1–Q3 run only after both coders finish and disagreements are
adjudicated.
