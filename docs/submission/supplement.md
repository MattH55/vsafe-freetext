# Electronic supplementary material

A PACVS signature in v-safe free text: a pre-registered study whose primary analysis was not feasible, with exploratory results. Matthew Halma. All cells have at least 10 people; smaller cells are suppressed (blank).

## S1. Q1 co-occurrence by stratum (registered)

| stratum | people | observed_pairs | null_mean_pairs | ratio | p_pairs | reject_h0 |
| --- | --- | --- | --- | --- | --- | --- |
| dose=1 | 147,659 | 30,825 | 25,068.7 | 1.23 | 0.001 | 1 |
| dose=2 | 827,368 | 156,367 | 129,573.6 | 1.207 | 0.001 | 1 |
| dose=3 | 247,784 | 42,053 | 30,259.4 | 1.39 | 0.001 | 1 |
| dose=4 | 44,660 | 5,934 | 4,383.7 | 1.354 | 0.001 | 1 |
| manufacturer=Janssen/Johnson & Johnson | 55,754 | 12,621 | 10,320.7 | 1.223 | 0.001 | 1 |
| manufacturer=Moderna | 574,355 | 105,796 | 85,728.5 | 1.234 | 0.001 | 1 |
| manufacturer=Pfizer-BioNTech | 637,049 | 116,722 | 92,787 | 1.258 | 0.001 | 1 |

p = 0.001 is the smallest value possible with 1,000 permutations. Strata with fewer than 1,000 person-doses were not tested.

## S2. Q1 domain pairs under the registered null

| domain_a | domain_b | both_people | expected_people | p | p_holm |
| --- | --- | --- | --- | --- | --- |
| cardiorespiratory | cognitive | 1,146 | 640.7 | 0.001 | 0.036 |
| cardiorespiratory | dysautonomia | 4,669 | 2,764.3 | 0.001 | 0.036 |
| cardiorespiratory | fatigue_pem | 9,759 | 6,610 | 0.001 | 0.036 |
| cardiorespiratory | gastrointestinal | 3,411 | 4,073.5 | 1 | 1 |
| cardiorespiratory | menstrual | 353 | 1,116.8 | 1 | 1 |
| cardiorespiratory | pain | 12,648 | 11,566.5 | 0.001 | 0.036 |
| cardiorespiratory | sensory_neuropathic | 1,161 | 1,642.8 | 1 | 1 |
| cardiorespiratory | sleep | 556 | 333.4 | 0.001 | 0.036 |
| cognitive | dysautonomia | 1,999 | 914 | 0.001 | 0.036 |
| cognitive | fatigue_pem | 6,561 | 2,185.5 | 0.001 | 0.036 |
| cognitive | gastrointestinal | 1,446 | 1,346.9 | 0.001 | 0.036 |
| cognitive | menstrual | 257 | 369.3 | 1 | 1 |
| cognitive | pain | 5,253 | 3,824.4 | 0.001 | 0.036 |
| cognitive | sensory_neuropathic | 1,128 | 543.2 | 0.001 | 0.036 |
| cognitive | sleep | 449 | 110.2 | 0.001 | 0.036 |
| dysautonomia | fatigue_pem | 10,418 | 9,428.7 | 0.001 | 0.036 |
| dysautonomia | gastrointestinal | 7,397 | 5,810.6 | 0.001 | 0.036 |
| dysautonomia | menstrual | 852 | 1,593.1 | 1 | 1 |
| dysautonomia | pain | 14,877 | 16,499 | 1 | 1 |
| dysautonomia | sensory_neuropathic | 3,339 | 2,343.3 | 0.001 | 0.036 |
| dysautonomia | sleep | 737 | 475.5 | 0.001 | 0.036 |
| fatigue_pem | gastrointestinal | 19,463 | 13,894.2 | 0.001 | 0.036 |
| fatigue_pem | menstrual | 1,792 | 3,809.3 | 1 | 1 |
| fatigue_pem | pain | 66,439 | 39,452.3 | 0.001 | 0.036 |
| fatigue_pem | sensory_neuropathic | 3,677 | 5,603.3 | 1 | 1 |
| fatigue_pem | sleep | 2,423 | 1,137.1 | 0.001 | 0.036 |
| gastrointestinal | menstrual | 1,222 | 2,347.5 | 1 | 1 |
| gastrointestinal | pain | 31,003 | 24,313 | 0.001 | 0.036 |
| gastrointestinal | sensory_neuropathic | 1,943 | 3,453.1 | 1 | 1 |
| gastrointestinal | sleep | 949 | 700.8 | 0.001 | 0.036 |
| menstrual | pain | 3,357 | 6,665.8 | 1 | 1 |
| menstrual | sensory_neuropathic | 447 | 946.7 | 1 | 1 |
| menstrual | sleep | 197 | 192.1 | 0.3716 | 1 |
| pain | sensory_neuropathic | 10,418 | 9,805 | 0.001 | 0.036 |
| pain | sleep | 2,940 | 1,989.8 | 0.001 | 0.036 |
| sensory_neuropathic | sleep | 498 | 282.6 | 0.001 | 0.036 |

## S3. Q1 domain pairs under the text-matched nulls (not pre-registered)

| null | domain_a | domain_b | both_people | expected_people | ratio | p_holm |
| --- | --- | --- | --- | --- | --- | --- |
| matched: character deciles | cardiorespiratory | cognitive | 1,146 | 865 | 1.325 | 0.036 |
| matched: character deciles | cardiorespiratory | dysautonomia | 4,669 | 3,237.5 | 1.442 | 0.036 |
| matched: character deciles | cardiorespiratory | fatigue_pem | 9,759 | 8,104.3 | 1.204 | 0.036 |
| matched: character deciles | cardiorespiratory | gastrointestinal | 3,411 | 4,682.8 | 0.728 | 1 |
| matched: character deciles | cardiorespiratory | menstrual | 353 | 1,417.6 | 0.249 | 1 |
| matched: character deciles | cardiorespiratory | pain | 12,648 | 13,640.8 | 0.927 | 1 |
| matched: character deciles | cardiorespiratory | sensory_neuropathic | 1,161 | 2,132.1 | 0.545 | 1 |
| matched: character deciles | cardiorespiratory | sleep | 556 | 442.5 | 1.257 | 0.036 |
| matched: character deciles | cognitive | dysautonomia | 1,999 | 1,155.7 | 1.73 | 0.036 |
| matched: character deciles | cognitive | fatigue_pem | 6,561 | 2,858.3 | 2.295 | 0.036 |
| matched: character deciles | cognitive | gastrointestinal | 1,446 | 1,624.1 | 0.89 | 1 |
| matched: character deciles | cognitive | menstrual | 257 | 515.8 | 0.498 | 1 |
| matched: character deciles | cognitive | pain | 5,253 | 4,721.7 | 1.113 | 0.036 |
| matched: character deciles | cognitive | sensory_neuropathic | 1,128 | 794.5 | 1.42 | 0.036 |
| matched: character deciles | cognitive | sleep | 449 | 166.8 | 2.691 | 0.036 |
| matched: character deciles | dysautonomia | fatigue_pem | 10,418 | 10,848.7 | 0.96 | 1 |
| matched: character deciles | dysautonomia | gastrointestinal | 7,397 | 6,371.6 | 1.161 | 0.036 |
| matched: character deciles | dysautonomia | menstrual | 852 | 1,884.8 | 0.452 | 1 |
| matched: character deciles | dysautonomia | pain | 14,877 | 18,434 | 0.807 | 1 |
| matched: character deciles | dysautonomia | sensory_neuropathic | 3,339 | 2,862 | 1.167 | 0.036 |
| matched: character deciles | dysautonomia | sleep | 737 | 590.6 | 1.248 | 0.036 |
| matched: character deciles | fatigue_pem | gastrointestinal | 19,463 | 15,739.3 | 1.237 | 0.036 |
| matched: character deciles | fatigue_pem | menstrual | 1,792 | 4,718.7 | 0.38 | 1 |
| matched: character deciles | fatigue_pem | pain | 66,439 | 46,225.1 | 1.437 | 0.036 |
| matched: character deciles | fatigue_pem | sensory_neuropathic | 3,677 | 7,061.3 | 0.521 | 1 |
| matched: character deciles | fatigue_pem | sleep | 2,423 | 1,463.2 | 1.656 | 0.036 |
| matched: character deciles | gastrointestinal | menstrual | 1,222 | 2,736 | 0.447 | 1 |
| matched: character deciles | gastrointestinal | pain | 31,003 | 26,840.3 | 1.155 | 0.036 |
| matched: character deciles | gastrointestinal | sensory_neuropathic | 1,943 | 4,059.8 | 0.479 | 1 |
| matched: character deciles | gastrointestinal | sleep | 949 | 837.6 | 1.133 | 0.036 |
| matched: character deciles | menstrual | pain | 3,357 | 7,888.7 | 0.426 | 1 |
| matched: character deciles | menstrual | sensory_neuropathic | 447 | 1,267.5 | 0.353 | 1 |
| matched: character deciles | menstrual | sleep | 197 | 264.1 | 0.746 | 1 |
| matched: character deciles | pain | sensory_neuropathic | 10,418 | 11,755.8 | 0.886 | 1 |
| matched: character deciles | pain | sleep | 2,940 | 2,422.1 | 1.214 | 0.036 |
| matched: character deciles | sensory_neuropathic | sleep | 498 | 404.1 | 1.232 | 0.036 |
| matched: entries x character deciles | cardiorespiratory | cognitive | 1,146 | 927.7 | 1.235 | 0.036 |
| matched: entries x character deciles | cardiorespiratory | dysautonomia | 4,669 | 3,518.6 | 1.327 | 0.036 |
| matched: entries x character deciles | cardiorespiratory | fatigue_pem | 9,759 | 8,180.1 | 1.193 | 0.036 |
| matched: entries x character deciles | cardiorespiratory | gastrointestinal | 3,411 | 4,904.5 | 0.695 | 1 |
| matched: entries x character deciles | cardiorespiratory | menstrual | 353 | 1,440 | 0.245 | 1 |
| matched: entries x character deciles | cardiorespiratory | pain | 12,648 | 14,042.9 | 0.901 | 1 |
| matched: entries x character deciles | cardiorespiratory | sensory_neuropathic | 1,161 | 2,355.9 | 0.493 | 1 |
| matched: entries x character deciles | cardiorespiratory | sleep | 556 | 473.9 | 1.173 | 0.036 |
| matched: entries x character deciles | cognitive | dysautonomia | 1,999 | 1,249.4 | 1.6 | 0.036 |
| matched: entries x character deciles | cognitive | fatigue_pem | 6,561 | 2,908.4 | 2.256 | 0.036 |
| matched: entries x character deciles | cognitive | gastrointestinal | 1,446 | 1,699.2 | 0.851 | 1 |
| matched: entries x character deciles | cognitive | menstrual | 257 | 523.5 | 0.491 | 1 |
| matched: entries x character deciles | cognitive | pain | 5,253 | 4,877.8 | 1.077 | 0.036 |
| matched: entries x character deciles | cognitive | sensory_neuropathic | 1,128 | 876.4 | 1.287 | 0.036 |
| matched: entries x character deciles | cognitive | sleep | 449 | 180 | 2.494 | 0.036 |
| matched: entries x character deciles | dysautonomia | fatigue_pem | 10,418 | 10,885.4 | 0.957 | 1 |
| matched: entries x character deciles | dysautonomia | gastrointestinal | 7,397 | 6,753.7 | 1.095 | 0.036 |
| matched: entries x character deciles | dysautonomia | menstrual | 852 | 1,920.7 | 0.444 | 1 |
| matched: entries x character deciles | dysautonomia | pain | 14,877 | 19,043.2 | 0.781 | 1 |
| matched: entries x character deciles | dysautonomia | sensory_neuropathic | 3,339 | 3,232.8 | 1.033 | 0.2517 |
| matched: entries x character deciles | dysautonomia | sleep | 737 | 639.5 | 1.152 | 0.036 |
| matched: entries x character deciles | fatigue_pem | gastrointestinal | 19,463 | 15,791.8 | 1.232 | 0.036 |
| matched: entries x character deciles | fatigue_pem | menstrual | 1,792 | 4,726.9 | 0.379 | 1 |
| matched: entries x character deciles | fatigue_pem | pain | 66,439 | 46,549.8 | 1.427 | 0.036 |
| matched: entries x character deciles | fatigue_pem | sensory_neuropathic | 3,677 | 7,135.3 | 0.515 | 1 |
| matched: entries x character deciles | fatigue_pem | sleep | 2,423 | 1,482.5 | 1.634 | 0.036 |
| matched: entries x character deciles | gastrointestinal | menstrual | 1,222 | 2,769.4 | 0.441 | 1 |
| matched: entries x character deciles | gastrointestinal | pain | 31,003 | 27,339 | 1.134 | 0.036 |
| matched: entries x character deciles | gastrointestinal | sensory_neuropathic | 1,943 | 4,345.8 | 0.447 | 1 |
| matched: entries x character deciles | gastrointestinal | sleep | 949 | 875.3 | 1.084 | 0.0799 |
| matched: entries x character deciles | menstrual | pain | 3,357 | 7,942.2 | 0.423 | 1 |
| matched: entries x character deciles | menstrual | sensory_neuropathic | 447 | 1,295.7 | 0.345 | 1 |
| matched: entries x character deciles | menstrual | sleep | 197 | 267.6 | 0.736 | 1 |
| matched: entries x character deciles | pain | sensory_neuropathic | 10,418 | 12,259.1 | 0.85 | 1 |
| matched: entries x character deciles | pain | sleep | 2,940 | 2,496.5 | 1.178 | 0.036 |
| matched: entries x character deciles | sensory_neuropathic | sleep | 498 | 446.5 | 1.115 | 0.1139 |

## S4. Mean domains per person-dose by decile of long-term characters

| character_decile | people | mean_domains |
| --- | --- | --- |
| 0 | 132,529 | 0.258 |
| 1 | 138,505 | 0.284 |
| 2 | 121,766 | 0.431 |
| 3 | 129,567 | 0.489 |
| 4 | 121,492 | 0.589 |
| 5 | 118,585 | 0.663 |
| 6 | 125,339 | 0.742 |
| 7 | 128,811 | 0.818 |
| 8 | 125,035 | 0.898 |
| 9 | 125,880 | 1.069 |

## S5. Q1 domain pairs under the curveball null (not pre-registered)

| null | domain_a | domain_b | both_people | expected_people | ratio | p_upper | p_lower | p_upper_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| curveball, unstratified | cardiorespiratory | cognitive | 1,146 | 925 | 1.239 | 0.001 | 1 | 0.036 |
| curveball, unstratified | cardiorespiratory | dysautonomia | 4,669 | 3,813.9 | 1.224 | 0.001 | 1 | 0.036 |
| curveball, unstratified | cardiorespiratory | fatigue_pem | 9,759 | 8,572.6 | 1.138 | 0.001 | 1 | 0.036 |
| curveball, unstratified | cardiorespiratory | gastrointestinal | 3,411 | 5,487.7 | 0.622 | 1 | 0.001 | 1 |
| curveball, unstratified | cardiorespiratory | menstrual | 353 | 1,590.3 | 0.222 | 1 | 0.001 | 1 |
| curveball, unstratified | cardiorespiratory | pain | 12,648 | 14,098.2 | 0.897 | 1 | 0.001 | 1 |
| curveball, unstratified | cardiorespiratory | sensory_neuropathic | 1,161 | 2,312.7 | 0.502 | 1 | 0.001 | 1 |
| curveball, unstratified | cardiorespiratory | sleep | 556 | 483.7 | 1.149 | 0.002 | 0.999 | 0.044 |
| curveball, unstratified | cognitive | dysautonomia | 1,999 | 1,293.3 | 1.546 | 0.001 | 1 | 0.036 |
| curveball, unstratified | cognitive | fatigue_pem | 6,561 | 2,893.9 | 2.267 | 0.001 | 1 | 0.036 |
| curveball, unstratified | cognitive | gastrointestinal | 1,446 | 1,860.5 | 0.777 | 1 | 0.001 | 1 |
| curveball, unstratified | cognitive | menstrual | 257 | 543.4 | 0.473 | 1 | 0.001 | 1 |
| curveball, unstratified | cognitive | pain | 5,253 | 4,738 | 1.109 | 0.001 | 1 | 0.036 |
| curveball, unstratified | cognitive | sensory_neuropathic | 1,128 | 787.6 | 1.432 | 0.001 | 1 | 0.036 |
| curveball, unstratified | cognitive | sleep | 449 | 166.1 | 2.703 | 0.001 | 1 | 0.036 |
| curveball, unstratified | dysautonomia | fatigue_pem | 10,418 | 12,079.7 | 0.862 | 1 | 0.001 | 1 |
| curveball, unstratified | dysautonomia | gastrointestinal | 7,397 | 7,719.7 | 0.958 | 1 | 0.001 | 1 |
| curveball, unstratified | dysautonomia | menstrual | 852 | 2,232.2 | 0.382 | 1 | 0.001 | 1 |
| curveball, unstratified | dysautonomia | pain | 14,877 | 19,925.8 | 0.747 | 1 | 0.001 | 1 |
| curveball, unstratified | dysautonomia | sensory_neuropathic | 3,339 | 3,249.4 | 1.028 | 0.0539 | 0.95 | 1 |
| curveball, unstratified | dysautonomia | sleep | 737 | 678.1 | 1.087 | 0.011 | 0.991 | 0.2308 |
| curveball, unstratified | fatigue_pem | gastrointestinal | 19,463 | 17,501.2 | 1.112 | 0.001 | 1 | 0.036 |
| curveball, unstratified | fatigue_pem | menstrual | 1,792 | 5,004.3 | 0.358 | 1 | 0.001 | 1 |
| curveball, unstratified | fatigue_pem | pain | 66,439 | 45,877.4 | 1.448 | 0.001 | 1 | 0.036 |
| curveball, unstratified | fatigue_pem | sensory_neuropathic | 3,677 | 7,294.4 | 0.504 | 1 | 0.001 | 1 |
| curveball, unstratified | fatigue_pem | sleep | 2,423 | 1,513 | 1.601 | 0.001 | 1 | 0.036 |
| curveball, unstratified | gastrointestinal | menstrual | 1,222 | 3,207.3 | 0.381 | 1 | 0.001 | 1 |
| curveball, unstratified | gastrointestinal | pain | 31,003 | 28,963.1 | 1.07 | 0.001 | 1 | 0.036 |
| curveball, unstratified | gastrointestinal | sensory_neuropathic | 1,943 | 4,672.3 | 0.416 | 1 | 0.001 | 1 |
| curveball, unstratified | gastrointestinal | sleep | 949 | 974 | 0.974 | 0.8102 | 0.1958 | 1 |
| curveball, unstratified | menstrual | pain | 3,357 | 8,202.6 | 0.409 | 1 | 0.001 | 1 |
| curveball, unstratified | menstrual | sensory_neuropathic | 447 | 1,356.9 | 0.329 | 1 | 0.001 | 1 |
| curveball, unstratified | menstrual | sleep | 197 | 284.7 | 0.692 | 1 | 0.001 | 1 |
| curveball, unstratified | pain | sensory_neuropathic | 10,418 | 11,989.6 | 0.869 | 1 | 0.001 | 1 |
| curveball, unstratified | pain | sleep | 2,940 | 2,478.6 | 1.186 | 0.001 | 1 | 0.036 |
| curveball, unstratified | sensory_neuropathic | sleep | 498 | 413 | 1.206 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | cardiorespiratory | cognitive | 1,146 | 997.3 | 1.149 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | cardiorespiratory | dysautonomia | 4,669 | 4,043.6 | 1.155 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | cardiorespiratory | fatigue_pem | 9,759 | 8,380.6 | 1.164 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | cardiorespiratory | gastrointestinal | 3,411 | 5,508.2 | 0.619 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | cardiorespiratory | menstrual | 353 | 1,570.5 | 0.225 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | cardiorespiratory | pain | 12,648 | 14,264.7 | 0.887 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | cardiorespiratory | sensory_neuropathic | 1,161 | 2,578.9 | 0.45 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | cardiorespiratory | sleep | 556 | 519.6 | 1.07 | 0.0519 | 0.952 | 1 |
| curveball within entries 1 / 2 / 3+ | cognitive | dysautonomia | 1,999 | 1,413 | 1.415 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | cognitive | fatigue_pem | 6,561 | 2,865.4 | 2.29 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | cognitive | gastrointestinal | 1,446 | 1,897.2 | 0.762 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | cognitive | menstrual | 257 | 543 | 0.473 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | cognitive | pain | 5,253 | 4,859 | 1.081 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | cognitive | sensory_neuropathic | 1,128 | 916.4 | 1.231 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | cognitive | sleep | 449 | 184.3 | 2.436 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | dysautonomia | fatigue_pem | 10,418 | 11,881.3 | 0.877 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | dysautonomia | gastrointestinal | 7,397 | 7,814.4 | 0.947 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | dysautonomia | menstrual | 852 | 2,221.1 | 0.384 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | dysautonomia | pain | 14,877 | 20,278.2 | 0.734 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | dysautonomia | sensory_neuropathic | 3,339 | 3,669.2 | 0.91 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | dysautonomia | sleep | 737 | 735.3 | 1.002 | 0.4835 | 0.5295 | 1 |
| curveball within entries 1 / 2 / 3+ | fatigue_pem | gastrointestinal | 19,463 | 16,839.2 | 1.156 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | fatigue_pem | menstrual | 1,792 | 4,751.4 | 0.377 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | fatigue_pem | pain | 66,439 | 44,770.6 | 1.484 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | fatigue_pem | sensory_neuropathic | 3,677 | 7,329.4 | 0.502 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | fatigue_pem | sleep | 2,423 | 1,493.8 | 1.622 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | gastrointestinal | menstrual | 1,222 | 3,090.8 | 0.395 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | gastrointestinal | pain | 31,003 | 28,629 | 1.083 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | gastrointestinal | sensory_neuropathic | 1,943 | 4,888.6 | 0.397 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | gastrointestinal | sleep | 949 | 990.5 | 0.958 | 0.9321 | 0.0729 | 1 |
| curveball within entries 1 / 2 / 3+ | menstrual | pain | 3,357 | 8,032.7 | 0.418 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | menstrual | sensory_neuropathic | 447 | 1,394.9 | 0.32 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | menstrual | sleep | 197 | 282.2 | 0.698 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | pain | sensory_neuropathic | 10,418 | 12,548.2 | 0.83 | 1 | 0.001 | 1 |
| curveball within entries 1 / 2 / 3+ | pain | sleep | 2,940 | 2,525.9 | 1.164 | 0.001 | 1 | 0.036 |
| curveball within entries 1 / 2 / 3+ | sensory_neuropathic | sleep | 498 | 475.4 | 1.047 | 0.1668 | 0.8452 | 1 |
| curveball within text-length tertiles | cardiorespiratory | cognitive | 1,146 | 1,019.1 | 1.125 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | cardiorespiratory | dysautonomia | 4,669 | 3,616.7 | 1.291 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | cardiorespiratory | fatigue_pem | 9,759 | 8,893.2 | 1.097 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | cardiorespiratory | gastrointestinal | 3,411 | 5,177.9 | 0.659 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | cardiorespiratory | menstrual | 353 | 1,635.6 | 0.216 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | cardiorespiratory | pain | 12,648 | 14,400.4 | 0.878 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | cardiorespiratory | sensory_neuropathic | 1,161 | 2,438.6 | 0.476 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | cardiorespiratory | sleep | 556 | 526.8 | 1.055 | 0.1009 | 0.9081 | 1 |
| curveball within text-length tertiles | cognitive | dysautonomia | 1,999 | 1,310.7 | 1.525 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | cognitive | fatigue_pem | 6,561 | 3,191.2 | 2.056 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | cognitive | gastrointestinal | 1,446 | 1,858.8 | 0.778 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | cognitive | menstrual | 257 | 600.2 | 0.428 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | cognitive | pain | 5,253 | 5,080 | 1.034 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | cognitive | sensory_neuropathic | 1,128 | 903.8 | 1.248 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | cognitive | sleep | 449 | 195.4 | 2.297 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | dysautonomia | fatigue_pem | 10,418 | 11,629 | 0.896 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | dysautonomia | gastrointestinal | 7,397 | 6,845.1 | 1.081 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | dysautonomia | menstrual | 852 | 2,120.2 | 0.402 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | dysautonomia | pain | 14,877 | 18,993.1 | 0.783 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | dysautonomia | sensory_neuropathic | 3,339 | 3,162.8 | 1.056 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | dysautonomia | sleep | 737 | 678.7 | 1.086 | 0.018 | 0.985 | 0.3776 |
| curveball within text-length tertiles | fatigue_pem | gastrointestinal | 19,463 | 16,806.2 | 1.158 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | fatigue_pem | menstrual | 1,792 | 5,192.3 | 0.345 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | fatigue_pem | pain | 66,439 | 47,704.9 | 1.393 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | fatigue_pem | sensory_neuropathic | 3,677 | 7,743.1 | 0.475 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | fatigue_pem | sleep | 2,423 | 1,649.3 | 1.469 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | gastrointestinal | menstrual | 1,222 | 3,027 | 0.404 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | gastrointestinal | pain | 31,003 | 27,655.1 | 1.121 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | gastrointestinal | sensory_neuropathic | 1,943 | 4,506.4 | 0.431 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | gastrointestinal | sleep | 949 | 961.2 | 0.987 | 0.6733 | 0.3407 | 1 |
| curveball within text-length tertiles | menstrual | pain | 3,357 | 8,374.2 | 0.401 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | menstrual | sensory_neuropathic | 447 | 1,434 | 0.312 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | menstrual | sleep | 197 | 310.2 | 0.635 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | pain | sensory_neuropathic | 10,418 | 12,450.6 | 0.837 | 1 | 0.001 | 1 |
| curveball within text-length tertiles | pain | sleep | 2,940 | 2,626.1 | 1.12 | 0.001 | 1 | 0.036 |
| curveball within text-length tertiles | sensory_neuropathic | sleep | 498 | 466.5 | 1.068 | 0.0649 | 0.9451 | 1 |

Both margins fixed: each person-dose's domain count and each domain's frequency. The total pair count is invariant under this null.

## S6. Curveball null, summary

| null | people | strata | observed_pairs | null_mean_pairs | ratio | pairs_above_null_holm | pairs_below_null_holm | permutations |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| curveball, unstratified | 1,267,509 | 1 | 235,184 | 235,184 | 1 | 15 | 18 | 1,000 |
| curveball within entries 1 / 2 / 3+ | 1,267,509 | 3 | 235,184 | 235,184 | 1 | 13 | 19 | 1,000 |
| curveball within text-length tertiles | 1,267,509 | 3 | 235,184 | 235,184 | 1 | 15 | 17 | 1,000 |

## S7. Q1 replication on VAERS COVID-19 report text, domain pairs

| domain_a | domain_b | both_people | expected_people | p | p_holm |
| --- | --- | --- | --- | --- | --- |
| cardiorespiratory | cognitive | 1,843 | 827.1 | 0.001 | 0.036 |
| cardiorespiratory | dysautonomia | 12,369 | 4,702.3 | 0.001 | 0.036 |
| cardiorespiratory | fatigue_pem | 10,948 | 6,455.3 | 0.001 | 0.036 |
| cardiorespiratory | gastrointestinal | 9,468 | 5,419.8 | 0.001 | 0.036 |
| cardiorespiratory | menstrual | 766 | 905.5 | 1 | 1 |
| cardiorespiratory | pain | 17,344 | 11,032.9 | 0.001 | 0.036 |
| cardiorespiratory | sensory_neuropathic | 4,774 | 3,232.4 | 0.001 | 0.036 |
| cardiorespiratory | sleep | 750 | 421.1 | 0.001 | 0.036 |
| cognitive | dysautonomia | 6,027 | 2,071.4 | 0.001 | 0.036 |
| cognitive | fatigue_pem | 7,987 | 2,843.6 | 0.001 | 0.036 |
| cognitive | gastrointestinal | 5,036 | 2,387.4 | 0.001 | 0.036 |
| cognitive | menstrual | 486 | 398.9 | 0.001 | 0.036 |
| cognitive | pain | 8,769 | 4,860.1 | 0.001 | 0.036 |
| cognitive | sensory_neuropathic | 3,154 | 1,423.9 | 0.001 | 0.036 |
| cognitive | sleep | 787 | 185.5 | 0.001 | 0.036 |
| dysautonomia | fatigue_pem | 25,825 | 16,166.6 | 0.001 | 0.036 |
| dysautonomia | gastrointestinal | 32,155 | 13,573.2 | 0.001 | 0.036 |
| dysautonomia | menstrual | 2,309 | 2,267.8 | 0.1898 | 0.9491 |
| dysautonomia | pain | 41,779 | 27,630.6 | 0.001 | 0.036 |
| dysautonomia | sensory_neuropathic | 15,282 | 8,095.3 | 0.001 | 0.036 |
| dysautonomia | sleep | 1,931 | 1,054.6 | 0.001 | 0.036 |
| fatigue_pem | gastrointestinal | 44,141 | 18,633.3 | 0.001 | 0.036 |
| fatigue_pem | menstrual | 2,926 | 3,113.3 | 1 | 1 |
| fatigue_pem | pain | 92,853 | 37,931.2 | 0.001 | 0.036 |
| fatigue_pem | sensory_neuropathic | 11,455 | 11,113.1 | 0.001 | 0.036 |
| fatigue_pem | sleep | 3,734 | 1,447.8 | 0.001 | 0.036 |
| gastrointestinal | menstrual | 2,681 | 2,613.8 | 0.0799 | 0.4795 |
| gastrointestinal | pain | 70,543 | 31,846.5 | 0.001 | 0.036 |
| gastrointestinal | sensory_neuropathic | 10,397 | 9,330.5 | 0.001 | 0.036 |
| gastrointestinal | sleep | 2,837 | 1,215.6 | 0.001 | 0.036 |
| menstrual | pain | 4,380 | 5,320.9 | 1 | 1 |
| menstrual | sensory_neuropathic | 1,255 | 1,558.9 | 1 | 1 |
| menstrual | sleep | 313 | 203.1 | 0.001 | 0.036 |
| pain | sensory_neuropathic | 22,115 | 18,993.7 | 0.001 | 0.036 |
| pain | sleep | 5,620 | 2,474.5 | 0.001 | 0.036 |
| sensory_neuropathic | sleep | 1,464 | 725 | 0.001 | 0.036 |

## S8. Q1 replication on VAERS, domain prevalence

| domain | people | share |
| --- | --- | --- |
| cardiorespiratory | 44,551 | 0.0421 |
| cognitive | 19,625 | 0.0186 |
| dysautonomia | 111,573 | 0.1055 |
| fatigue_pem | 153,167 | 0.1449 |
| gastrointestinal | 128,597 | 0.1217 |
| menstrual | 21,486 | 0.0203 |
| pain | 261,781 | 0.2476 |
| sensory_neuropathic | 76,697 | 0.0726 |
| sleep | 9,992 | 0.0095 |

## S9. Onset survey of cases (registered classifier)

| onset_survey | people |
| --- | --- |
| w1 | 7,903 |
| 6w | 16,413 |
| 3m | 29,714 |
| 6m | 21,625 |
| 12m | 11,562 |

## S10. Exclusion-criterion variants: groups (keyword tags only)

| grp | person_doses | people | in_denominator |
| --- | --- | --- | --- |
| acute_event | 64,629 | 63,180 | 52,925 |
| case | 89,198 | 88,262 | 89,198 |
| no_symptoms | 5,879,729 | 4,761,689 | 5,879,729 |
| other | 2,303,226 | 2,064,566 | 998,659 |
| severe_w1_recovered | 1,603,147 | 1,518,791 | 1,603,147 |

## S11. Exclusion-criterion variants: groups (no criterion 3)

| grp | person_doses | people | in_denominator |
| --- | --- | --- | --- |
| acute_event | 103,009 | 100,943 | 91,301 |
| case | 135,252 | 133,615 | 135,252 |
| no_symptoms | 5,877,624 | 4,760,357 | 5,877,624 |
| other | 2,221,525 | 1,999,143 | 916,958 |
| severe_w1_recovered | 1,602,523 | 1,518,229 | 1,602,523 |

## S12. Exclusion-criterion variants: Q3 recorded VAERS filing (keyword tags only)

| match_set | case_people | case_vaers_people | case_matched_people | group_b_people | group_b_vaers_people | group_b_matched_people | case_rate | group_b_rate | rate_ratio | ci_low | ci_high | lower_capture |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | 88,262 | 4,037 | 2,212 | 62,534 | 3,478 | 1,813 | 0.0457 | 0.0556 | 0.8224 | 0.7868 | 0.8595 | 1 |
| high_confidence | 88,262 | 4,021 | 2,088 | 62,534 | 3,463 | 1,726 | 0.0456 | 0.0554 | 0.8227 | 0.787 | 0.8599 | 1 |

## S13. Exclusion-criterion variants: Q3 recorded VAERS filing (no criterion 3)

| match_set | case_people | case_vaers_people | case_matched_people | group_b_people | group_b_vaers_people | group_b_matched_people | case_rate | group_b_rate | rate_ratio | ci_low | ci_high | lower_capture |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | 133,615 | 5,019 | 2,887 | 99,646 | 4,776 | 2,578 | 0.0376 | 0.0479 | 0.7837 | 0.7539 | 0.8147 | 1 |
| high_confidence | 133,615 | 4,994 | 2,692 | 99,646 | 4,757 | 2,443 | 0.0374 | 0.0477 | 0.7829 | 0.7531 | 0.8139 | 1 |

## S14. Persistence by case route and comparison group (not pre-registered)

| comparison | case_people | case_persist_people | comparison_people | comparison_persist_people | case_share | comparison_share | risk_difference | ci_low | ci_high | p_one_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| registered: all cases vs group (c) | 51,221 | 30,907 | 1,169,538 | 17,416 | 0.6034 | 0.0149 | 0.5885 | 0.5843 | 0.5927 | 0 |
| same-survey cases only vs group (c) | 36,478 | 17,177 | 1,169,538 | 17,416 | 0.4709 | 0.0149 | 0.456 | 0.4509 | 0.4611 | 0 |
| all cases vs group (d): worse/impacted, < 2 domains | 51,221 | 30,907 | 308,869 | 32,391 | 0.6034 | 0.1049 | 0.4985 | 0.4942 | 0.5029 | 0 |
| same-survey cases vs group (d) | 36,478 | 17,177 | 308,869 | 32,391 | 0.4709 | 0.1049 | 0.366 | 0.3608 | 0.3713 | 0 |

## S15. Week-1 structured answers, cases with the domain vs group (a) (not pre-registered)

| domain | group | people | week1_any | week1_moderate_or_severe | week1_impact |
| --- | --- | --- | --- | --- | --- |
| fatigue_pem | cases with this domain | 37,326 | 0.7893 | 0.6443 | 0.5658 |
| fatigue_pem | group (a), 1-in-20 sample | 219,910 | 0.3547 | 0.1463 | 0 |
| pain | cases with this domain | 51,151 | 0.8021 | 0.6313 | 0.5545 |
| pain | group (a), 1-in-20 sample | 219,910 | 0.4002 | 0.1599 | 0 |
| gastrointestinal | group (a), 1-in-20 sample | 219,910 | 0.1019 | 0.0273 | 0 |
| gastrointestinal | cases with this domain | 24,325 | 0.4781 | 0.2928 | 0.5331 |

Group (a) is a 1-in-20 sample of person-doses; its week-1 impact is 0 by construction (person-doses with a week-1 impact fall in group (c)).

## S16. Validation audit: disagreements between layer 3 and CDC coding, by domain

| side | theme | entries | people |
| --- | --- | --- | --- |
| cdc_only | cardiorespiratory | 11,180 | 11,026 |
| cdc_only | cognitive | 4,550 | 4,511 |
| cdc_only | dysautonomia | 3,314 | 3,289 |
| cdc_only | fatigue_pem | 27,867 | 27,552 |
| cdc_only | gastrointestinal | 8,938 | 8,837 |
| cdc_only | menstrual | 13,590 | 12,934 |
| cdc_only | pain | 59,686 | 58,073 |
| cdc_only | sensory_neuropathic | 91,968 | 86,811 |
| cdc_only | sleep | 2,559 | 2,534 |
| layer3_only | cardiorespiratory | 14,669 | 14,241 |
| layer3_only | cognitive | 2,527 | 2,473 |
| layer3_only | dysautonomia | 15,745 | 14,905 |
| layer3_only | fatigue_pem | 4,135 | 4,087 |
| layer3_only | gastrointestinal | 26,488 | 25,584 |
| layer3_only | menstrual | 2,840 | 2,742 |
| layer3_only | pain | 28,522 | 27,620 |
| layer3_only | sensory_neuropathic | 14,447 | 13,875 |
| layer3_only | sleep | 2,150 | 2,050 |

Entry-domain pairs. The coded sample result is pending human coding.

## S17. Q3 dispersion with small-sample corrections (not pre-registered)

| match_set | case_people | group_b_people | case_pt_codes | group_b_pt_codes | entropy_cases | entropy_group_b | entropy_cases_miller_madow | entropy_group_b_miller_madow | entropy_cases_rarefied | entropy_group_b_rarefied | rarefied_to_codes | difference | p_one_sided_cases_more_dispersed | p_two_sided |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| main | 2,122 | 2,642 | 18,072 | 19,063 | 8.314 | 8.594 | 8.383 | 8.669 | 8.314 | 8.588 | 18,072 | -0.2802 | 1 | 0.000999 |
| high_confidence | 2,006 | 2,503 | 16,996 | 18,061 | 8.313 | 8.605 | 8.384 | 8.682 | 8.313 | 8.598 | 16,996 | -0.2923 | 1 | 0.000999 |

## S18. Q1 and case count with criterion 3 off and with redacted entries included (not pre-registered)

| variant | people | case_person_doses | q1_ratio | q1_p |
| --- | --- | --- | --- | --- |
| registered | 1,267,509 | 87,229 |  |  |
| criterion 3 off (Q1 unaffected: it does not use the case definition) | 1,267,509 | 135,252 |  |  |
| redacted entries included | 1,269,337 | 87,229 | 1.247 | 0.001 |

## S19. Reconciliation of counts

| quantity | value |
| --- | --- |
| entries after de-duplication | 7,819,251 |
| entries_raw rows | 7,819,275 |
| entries matched to a long-term survey | 1,595,121 |
| entries matched to an early survey | 5,791,000 |
| entries not matched to a survey | 433,130 |
| entries with survey_matched NULL | 0 |
| check-ins in the linked table | 144,972,101 |
| check-in rows in the raw adult file | 144,856,043 |
| check-in rows in the raw under-3 file | 116,294 |
| distinct RESPONSE_ID in raw check-ins | 144,972,101 |
| person-doses with any check-in (ph_rank) | 17,459,757 |
| person-doses with a long-term survey | 8,623,658 |
| person-doses in any phenotype group | 9,939,933 |
| person-doses in groups and in denominator | 8,623,658 |
| group (b) people, group table | 102,616 |
| group (b) people, Q3 (not a case at any dose) | 101,690 |
| registrants in registrants table | 10,094,310 |
| registrants with any check-in | 9,565,929 |

## S20. Layer-3 runs: tokens and logged cost

| model | prompt_version | runs | texts | tokens | cost_usd_logged | first_run | last_run |
| --- | --- | --- | --- | --- | --- | --- | --- |
| claude-opus-5-5 | v0.1-2026-11-10 | 1 | 1,687 | 232,706 | 1.962 | 2026-11-12T11:13:05.000000 | 2026-11-12T11:13:05.000000 |
| deepseek/deepseek-v4.1-flash | v0.1-2026-11-10 | 2 | 27,451 | 2,152,942 | 0.0005 | 2026-11-12T06:21:03.000000 | 2026-11-12T11:25:40.000000 |

## S21. Model sensitivity: entries per theme, DeepSeek vs Claude, fixed long-term sample

| theme | model1_entries | model2_entries | shift | model_sensitive |
| --- | --- | --- | --- | --- |
| acute_diagnosis | 131 | 112 | 0.145 | 0 |
| cardiorespiratory | 68 | 41 | 0.397 | 1 |
| care_sought | 404 | 553 | 0.269 | 1 |
| cognitive | 13 | 10 | 0.231 | 1 |
| dysautonomia | 52 | 54 | 0.037 | 0 |
| fatigue_pem | 20 | 46 | 0.565 | 1 |
| fever_chills | 26 | 24 | 0.077 | 0 |
| gastrointestinal | 105 | 107 | 0.019 | 0 |
| injection_site | 24 | 28 | 0.143 | 0 |
| lymphadenopathy |  |  |  |  |
| menstrual | 18 | 10 | 0.444 | 1 |
| missed_work_school |  |  |  |  |
| pain | 205 | 224 | 0.085 | 0 |
| persistence | 52 | 102 | 0.49 | 1 |
| pre_existing_worsened | 49 | 61 | 0.197 | 0 |
| sensory_neuropathic | 57 | 50 | 0.123 | 0 |
| skin | 54 | 46 | 0.148 | 0 |
| sleep |  |  |  |  |
| taste_smell | 16 | 16 | 0 | 0 |
| unrelated_cause | 429 | 621 | 0.309 | 1 |
| upper_respiratory | 232 | 229 | 0.013 | 0 |

## S22. Layer-1 (lexicon only) precision and recall against CDC coding

| theme | predicted_entries | reference_entries | both_entries | precision | recall | passes_gate |
| --- | --- | --- | --- | --- | --- | --- |
| acute_diagnosis | 36,429 | 28,139 | 24,025 | 0.6595 | 0.8538 | 0 |
| cardiorespiratory | 30,737 | 46,936 | 29,373 | 0.9556 | 0.6258 | 0 |
| cognitive | 13,674 | 17,565 | 12,150 | 0.8885 | 0.6917 | 0 |
| dysautonomia | 55,039 | 61,701 | 53,816 | 0.9778 | 0.8722 | 1 |
| fatigue_pem | 169,299 | 197,809 | 166,614 | 0.9841 | 0.8423 | 0 |
| fever_chills | 120,443 | 122,347 | 116,822 | 0.9699 | 0.9548 | 1 |
| gastrointestinal | 74,645 | 89,894 | 73,836 | 0.9892 | 0.8214 | 0 |
| injection_site | 17,751 | 78,113 | 16,464 | 0.9275 | 0.2108 | 0 |
| lymphadenopathy | 14,073 | 19,250 | 12,194 | 0.8665 | 0.6335 | 0 |
| menstrual | 24,707 | 39,807 | 22,895 | 0.9267 | 0.5752 | 0 |
| pain | 251,945 | 345,148 | 249,776 | 0.9914 | 0.7237 | 0 |
| pre_existing_worsened | 6,209 | 11,667 | 1,303 | 0.2099 | 0.1117 | 0 |
| sensory_neuropathic | 26,035 | 122,015 | 25,159 | 0.9664 | 0.2062 | 0 |
| skin | 34,764 | 48,210 | 33,506 | 0.9638 | 0.695 | 0 |
| sleep | 5,786 | 9,067 | 5,632 | 0.9734 | 0.6212 | 0 |
| taste_smell | 19,638 | 29,463 | 18,312 | 0.9325 | 0.6215 | 0 |
| unrelated_cause | 189,889 | 57,851 | 46,470 | 0.2447 | 0.8033 | 0 |
| upper_respiratory | 352,196 | 367,587 | 349,808 | 0.9932 | 0.9516 | 1 |

## S23. Final classifier precision and recall against CDC coding

| theme | predicted_entries | reference_entries | both_entries | precision | precision_lo | precision_hi | recall | recall_lo | recall_hi | passes_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| acute_diagnosis | 80,609 | 28,139 | 25,108 | 0.3115 | 0.3083 | 0.3147 | 0.8923 | 0.8886 | 0.8959 | 0 |
| cardiorespiratory | 51,823 | 46,936 | 35,754 | 0.6899 | 0.6859 | 0.6939 | 0.7618 | 0.7579 | 0.7656 | 0 |
| cognitive | 17,077 | 17,565 | 13,012 | 0.762 | 0.7555 | 0.7683 | 0.7408 | 0.7343 | 0.7472 | 0 |
| dysautonomia | 75,458 | 61,701 | 58,385 | 0.7737 | 0.7707 | 0.7767 | 0.9463 | 0.9444 | 0.948 | 0 |
| fatigue_pem | 176,760 | 197,809 | 169,934 | 0.9614 | 0.9605 | 0.9623 | 0.8591 | 0.8575 | 0.8606 | 1 |
| fever_chills | 129,253 | 122,347 | 117,750 | 0.911 | 0.9094 | 0.9125 | 0.9624 | 0.9613 | 0.9635 | 1 |
| gastrointestinal | 108,314 | 89,894 | 80,955 | 0.7474 | 0.7448 | 0.75 | 0.9006 | 0.8986 | 0.9025 | 0 |
| injection_site | 23,893 | 78,113 | 20,781 | 0.8698 | 0.8654 | 0.874 | 0.266 | 0.263 | 0.2691 | 0 |
| lymphadenopathy | 16,765 | 19,250 | 13,222 | 0.7887 | 0.7824 | 0.7948 | 0.6869 | 0.6803 | 0.6934 | 0 |
| menstrual | 30,875 | 39,807 | 26,217 | 0.8491 | 0.8451 | 0.8531 | 0.6586 | 0.6539 | 0.6632 | 0 |
| pain | 316,250 | 345,148 | 285,450 | 0.9026 | 0.9016 | 0.9036 | 0.827 | 0.8258 | 0.8283 | 0 |
| pre_existing_worsened | 20,987 | 11,667 | 3,501 | 0.1668 | 0.1618 | 0.1719 | 0.3001 | 0.2918 | 0.3085 | 0 |
| sensory_neuropathic | 45,396 | 122,015 | 30,021 | 0.6613 | 0.6569 | 0.6657 | 0.246 | 0.2436 | 0.2485 | 0 |
| skin | 50,049 | 48,210 | 36,346 | 0.7262 | 0.7223 | 0.7301 | 0.7539 | 0.75 | 0.7577 | 0 |
| sleep | 8,820 | 9,067 | 6,508 | 0.7379 | 0.7286 | 0.7469 | 0.7178 | 0.7084 | 0.7269 | 0 |
| taste_smell | 26,328 | 29,463 | 23,048 | 0.8754 | 0.8714 | 0.8794 | 0.7823 | 0.7775 | 0.7869 | 0 |
| unrelated_cause | 340,256 | 57,851 | 49,145 | 0.1444 | 0.1433 | 0.1456 | 0.8495 | 0.8466 | 0.8524 | 0 |
| upper_respiratory | 435,125 | 367,587 | 357,138 | 0.8208 | 0.8196 | 0.8219 | 0.9716 | 0.971 | 0.9721 | 0 |

## S24. Share of case person-doses naming each theme in long-term text

| theme | person_doses | pct |
| --- | --- | --- |
| pain | 61,259 | 70.2 |
| fatigue_pem | 44,963 | 51.5 |
| gastrointestinal | 28,846 | 33.1 |
| dysautonomia | 21,866 | 25.1 |
| cardiorespiratory | 14,194 | 16.3 |
| care_sought | 14,060 | 16.1 |
| sensory_neuropathic | 12,976 | 14.9 |
| cognitive | 7,402 | 8.5 |
| menstrual | 4,602 | 5.3 |
| persistence | 4,295 | 4.9 |
| sleep | 3,485 | 4 |
| pre_existing_worsened | 1,697 | 1.9 |
| missed_work_school | 177 | 0.2 |

## S25. Sex, manufacturer and dose by group, % of person-doses

| variable | category | grp | person_doses | pct |
| --- | --- | --- | --- | --- |
| age_band | unknown | acute_event | 104,736 | 100 |
| age_band | unknown | case | 87,229 | 100 |
| age_band | unknown | no_symptoms | 5,877,624 | 100 |
| age_band | unknown | other | 963,254 | 100 |
| age_band | unknown | severe_w1_recovered | 1,602,523 | 100 |
| dose | 1 | acute_event | 19,194 | 18.3 |
| dose | 1 | case | 12,466 | 14.3 |
| dose | 1 | no_symptoms | 802,583 | 13.7 |
| dose | 1 | other | 117,613 | 12.2 |
| dose | 1 | severe_w1_recovered | 153,853 | 9.6 |
| dose | 2 | acute_event | 63,474 | 60.6 |
| dose | 2 | case | 60,808 | 69.7 |
| dose | 2 | no_symptoms | 3,561,725 | 60.6 |
| dose | 2 | other | 618,029 | 64.2 |
| dose | 2 | severe_w1_recovered | 1,273,382 | 79.5 |
| dose | 3 | acute_event | 17,033 | 16.3 |
| dose | 3 | case | 12,355 | 14.2 |
| dose | 3 | no_symptoms | 1,186,360 | 20.2 |
| dose | 3 | other | 191,813 | 19.9 |
| dose | 3 | severe_w1_recovered | 153,474 | 9.6 |
| dose | 4 | acute_event | 5,017 | 4.8 |
| dose | 4 | case | 1,596 | 1.8 |
| dose | 4 | no_symptoms | 326,740 | 5.6 |
| dose | 4 | other | 35,767 | 3.7 |
| dose | 4 | severe_w1_recovered | 21,802 | 1.4 |
| dose | 5 | acute_event | 18 | 0 |
| dose | 5 | case |  |  |
| dose | 5 | no_symptoms | 216 | 0 |
| dose | 5 | other | 32 | 0 |
| dose | 5 | severe_w1_recovered | 12 | 0 |
| manufacturer | Janssen/Johnson & Johnson | acute_event | 4,499 | 4.3 |
| manufacturer | Janssen/Johnson & Johnson | case | 4,983 | 5.7 |
| manufacturer | Janssen/Johnson & Johnson | no_symptoms | 196,327 | 3.3 |
| manufacturer | Janssen/Johnson & Johnson | other | 43,305 | 4.5 |
| manufacturer | Janssen/Johnson & Johnson | severe_w1_recovered | 74,533 | 4.7 |
| manufacturer | Moderna | acute_event | 49,585 | 47.3 |
| manufacturer | Moderna | case | 40,027 | 45.9 |
| manufacturer | Moderna | no_symptoms | 2,553,047 | 43.4 |
| manufacturer | Moderna | other | 432,588 | 44.9 |
| manufacturer | Moderna | severe_w1_recovered | 894,660 | 55.8 |
| manufacturer | Other-Unknown | acute_event | 26 | 0 |
| manufacturer | Other-Unknown | case | 22 | 0 |
| manufacturer | Other-Unknown | no_symptoms | 1,877 | 0 |
| manufacturer | Other-Unknown | other | 292 | 0 |
| manufacturer | Other-Unknown | severe_w1_recovered | 95 | 0 |
| manufacturer | Pfizer-BioNTech | acute_event | 50,626 | 48.3 |
| manufacturer | Pfizer-BioNTech | case | 42,197 | 48.4 |
| manufacturer | Pfizer-BioNTech | no_symptoms | 3,126,373 | 53.2 |
| manufacturer | Pfizer-BioNTech | other | 487,069 | 50.6 |
| manufacturer | Pfizer-BioNTech | severe_w1_recovered | 633,235 | 39.5 |
| sex | Female | acute_event | 72,187 | 68.9 |
| sex | Female | case | 67,628 | 77.5 |
| sex | Female | no_symptoms | 3,414,738 | 58.1 |
| sex | Female | other | 677,174 | 70.3 |
| sex | Female | severe_w1_recovered | 1,166,271 | 72.8 |
| sex | Male | acute_event | 31,711 | 30.3 |
| sex | Male | case | 18,579 | 21.3 |
| sex | Male | no_symptoms | 2,416,136 | 41.1 |
| sex | Male | other | 276,532 | 28.7 |
| sex | Male | severe_w1_recovered | 420,244 | 26.2 |
| sex | Other | acute_event | 137 | 0.1 |
| sex | Other | case | 189 | 0.2 |
| sex | Other | no_symptoms | 4,787 | 0.1 |
| sex | Other | other | 1,484 | 0.2 |
| sex | Other | severe_w1_recovered | 2,817 | 0.2 |
| sex | Unknown | acute_event | 701 | 0.7 |
| sex | Unknown | case | 833 | 1 |
| sex | Unknown | no_symptoms | 41,962 | 0.7 |
| sex | Unknown | other | 8,064 | 0.8 |
| sex | Unknown | severe_w1_recovered | 13,191 | 0.8 |
| sex | unknown | no_symptoms |  |  |

## S26. Levi and Lu's cohorts rebuilt from structured answers (not pre-registered)

| group | ours | levi_lu | difference | pct_difference |
| --- | --- | --- | --- | --- |
| enrollees | 9,552,127 | 9,904,924 | -352,797 | -3.56 |
| prolonged_ae | 167,335 | 185,285 | -17,950 | -9.69 |
| prolonged_ae_d1 | 32,732 | 32,838 | -106 | -0.32 |
| prolonged_ae_d2 | 101,064 | 100,564 | 500 | 0.5 |
| prolonged_ae_d3plus | 33,539 | 51,883 | -18,344 | -35.36 |
| prolonged_noattr | 167,930 | 189,982 | -22,052 | -11.61 |
| prolonged_noattr_d1 | 20,389 | 18,710 | 1,679 | 8.97 |
| prolonged_noattr_d2 | 89,862 | 81,462 | 8,400 | 10.31 |
| prolonged_noattr_d3plus | 57,679 | 89,810 | -32,131 | -35.78 |
| control | 9,216,862 | 9,529,657 | -312,795 | -3.28 |
| women_prolonged_ae | 124,376 | 137,430 | -13,054 | -9.5 |
| women | 5,941,118 | 6,141,800 | -200,682 | -3.27 |

No age field exists in the released files, so the adult check-in file stands in for 'aged 16 or older'. Our download of the check-in file holds 6.7 million fewer rows than theirs. The joins were not adjusted to match.

## S27. Overlap of the text-defined case (any dose) with Levi and Lu's Prolonged-AE cohort, people

| cell | people | value |
| --- | --- | --- |
| both | 29,593 |  |
| text-defined only | 56,730 |  |
| Levi & Lu only | 137,742 |  |
| neither | 6,530,766 |  |
| total | 6,754,831 |  |
| share of text-defined cases also Levi & Lu | 6,754,831 | 0.3428 |
| share of Levi & Lu cases also text-defined | 6,754,831 | 0.1768 |
| Cohen's kappa | 6,754,831 | 0.2202 |

## S28. Blind audit of classifier-versus-CDC disagreements: coder agreement with the side that called the domain present

| side | domain | coded | present_1 | share_side_right |
| --- | --- | --- | --- | --- |
| cdc_only | cardiorespiratory | 17 | 14 | 0.824 |
| cdc_only | cognitive | 17 | 9 | 0.529 |
| cdc_only | dysautonomia | 17 | 10 | 0.588 |
| cdc_only | fatigue_pem | 17 | 6 | 0.353 |
| cdc_only | gastrointestinal | 17 | 14 | 0.824 |
| cdc_only | menstrual | 17 | 2 | 0.118 |
| cdc_only | pain | 17 | 11 | 0.647 |
| cdc_only | sensory_neuropathic | 17 | 13 | 0.765 |
| cdc_only | sleep | 17 | 13 | 0.765 |
| layer3_only | cardiorespiratory | 17 | 16 | 0.941 |
| layer3_only | cognitive | 17 | 15 | 0.882 |
| layer3_only | dysautonomia | 17 | 17 | 1 |
| layer3_only | fatigue_pem | 17 | 14 | 0.824 |
| layer3_only | gastrointestinal | 17 | 16 | 0.941 |
| layer3_only | menstrual | 17 | 6 | 0.353 |
| layer3_only | pain | 17 | 15 | 0.882 |
| layer3_only | sensory_neuropathic | 17 | 17 | 1 |
| layer3_only | sleep | 17 | 15 | 0.882 |
| layer3_only | all domains | 153 | 131 | 0.856 |
| cdc_only | all domains | 153 | 92 | 0.601 |

Single coder (the author), blind to side. 'layer3_only' = only the classifier called the domain; 'cdc_only' = only CDC's MedDRA coding did. present_1 = entries the coder judged to contain the domain.
