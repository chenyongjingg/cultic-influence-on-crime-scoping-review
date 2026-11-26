# Table S5. Sensitivity analyses and subsidiary diagnostics

## E1. Automatic-exclusion confidence threshold

| Threshold | Auto-excluded | Advanced to second pass | Advanced (%) |
|---|---|---|---|
| 0.60 | 443 | 184 | 29.3 |
| 0.70 | 443 | 184 | 29.3 |
| 0.80 | 443 | 184 | 29.3 |
| 0.85 | 443 | 184 | 29.3 |
| 0.90 | 443 | 184 | 29.3 |
| 0.95 | 439 | 188 | 30.0 |
| 1.00 | 0 | 627 | 100.0 |

The sweep is flat between 0.60 and 0.90 because the model's stated confidence is concentrated at 0.90 and 0.95; it is not a graded dial.

## E2. Conjunctive vs disjunctive group criterion

- conjunctive (lexical anchor AND model verdict): **236**
- disjunctive (model verdict only): **234**
- records admitted only by the disjunctive reading: **0** — {}

## E3. Per-source independent contribution

| Source | Raw rows | Records no other source returned |
|---|---|---|
| core | 189 | 166 |
| crossref | 49 | 33 |
| doaj | 141 | 103 |
| europepmc | 46 | 0 |
| europepmc_tierS | 143 | 97 |
| pubmed | 49 | 10 |
| s2 | 406 | 344 |

Unique records overall: 860

## E4. Year and language restriction

- unique_after_dedup: 833
- after_year_1994_2026: 814
- after_language: 745
- excluded_year: None
- excluded_language: None
- tierP: 535
- tierS_only: 94
- without_abstract: 24

## E5. 7B vs 14B screening agreement

Over 50 records screened by both layers:

| Quantity | Agreement | Cohen's kappa |
|---|---|---|
| Decision | 74.0% | 0.35 |
| I1 | 86.0% | 0.706 |
| I2 | 66.0% | 0.309 |
| I3 | 90.0% | 0.646 |
| I4 | 76.0% | 0.342 |

INCLUDE counts — 7B: 5, 14B: 5

## E6. Detector validation against a hand read (29 records)

| Construct | both | missed by detector | detector over-fired | precision | recall |
|---|---|---|---|---|---|
| C1_group_def | 5 | 16 | 0 | 1.0 | 0.24 |
| C2_role | 2 | 6 | 3 | 0.4 | 0.25 |
| C3_duration | 1 | 1 | 2 | 0.33 | 0.5 |
| C4_mechanism | 5 | 3 | 0 | 1.0 | 0.62 |
| C5_instrument | 0 | 0 | 1 | 0.0 | None |
| C6_offence | 15 | 14 | 0 | 1.0 | 0.52 |
| C7_severity | 0 | 1 | 0 | None | 0.0 |
| C8_legal | 5 | 6 | 1 | 0.83 | 0.45 |
| C9_jurisdiction | 12 | 8 | 1 | 0.92 | 0.6 |
| C10_source | 8 | 8 | 3 | 0.73 | 0.5 |
| C11_comparison | 0 | 1 | 3 | 0.0 | 0.0 |
| C12_n | 3 | 4 | 0 | 1.0 | 0.43 |

Overall precision 0.800, recall 0.452 over 29 records. The detectors under-count; they do not over-count.

## E7. Term-list perturbation (strict variant)

| Construct | base | strict | delta (pp) |
|---|---|---|---|
| C4_mechanism | 26/171 (15.2%) | 15/171 (8.8%) | -6.4 |
| C6_offence | 84/171 (49.1%) | 74/171 (43.3%) | -5.8 |
| C8_legal | 35/171 (20.5%) | 21/171 (12.3%) | -8.2 |
| C9_jurisdiction | 89/171 (52.0%) | 63/171 (36.8%) | -15.2 |
| C10_source | 55/171 (32.2%) | 19/171 (11.1%) | -21.1 |

The two largest bars are the least robust: jurisdiction and data source lose 15 and 21 percentage points under a strict rule, while offence type loses 6. The ordering of the top four is therefore vocabulary-dependent;
the gap to the bottom group is not.

## E8. Descriptive strata by decade (module M5)

| Decade | N | offence | jurisdiction | instrument | comparison |
|---|---|---|---|---|---|
| 19900s | 9 | 55.6% | 33.3% | 0.0% | 0.0% |
| 20000s | 17 | 52.9% | 41.2% | 0.0% | 0.0% |
| 20100s | 52 | 51.9% | 59.6% | 0.0% | 3.8% |
| 20200s | 93 | 46.2% | 51.6% | 2.2% | 4.3% |

Jurisdiction strata are omitted: stratifying on a detector, then reporting that same detector inside each stratum, is circular. Only the decade split carries information.

## E9. Full-text lift, paired on the same records
| Construct | abstract | matched window | full text | lift vs window (pp) |
|---|---|---|---|---|
| C1_group_def | 2/42 | 2/42 | 15/42 | +0.0 |
| C2_role | 4/42 | 1/42 | 22/42 | -7.1 |
| C3_duration | 2/42 | 4/42 | 13/42 | +4.8 |
| C4_mechanism | 4/42 | 3/42 | 17/42 | -2.4 |
| C5_instrument | 0/42 | 0/42 | 12/42 | +0.0 |
| C6_offence | 17/42 | 5/42 | 27/42 | -28.6 |
| C7_severity | 1/42 | 0/42 | 11/42 | -2.4 |
| C8_legal | 7/42 | 4/42 | 28/42 | -7.1 |
| C9_jurisdiction | 24/42 | 11/42 | 34/42 | -31.0 |
| C10_source | 15/42 | 5/42 | 29/42 | -23.8 |
| C11_comparison | 1/42 | 3/42 | 15/42 | +4.8 |
| C12_n | 3/42 | 5/42 | 19/42 | +4.8 |
Full text obtainable for 42 of 171 measurable records (24.6%). The matched window is the length control: it reports no more than the abstract for nine of twelve constructs.
## M8-M10 coding summary (N = 171)

| Module | Code | n | % |
|---|---|---|---|
| M8_interrogation | methods_accusatorial | 0 | 0.0 |
| M8_interrogation | methods_information | 0 | 0.0 |
| M8_interrogation | reliability | 8 | 4.7 |
| M8_interrogation | subject_core | 0 | 0.0 |
| M8_interrogation | subject_leader | 2 | 1.2 |
| M8_interrogation | subject_member | 23 | 13.5 |
| M8_interrogation | subject_victim | 39 | 22.8 |
| M9_digital_forensics | communications | 0 | 0.0 |
| M9_digital_forensics | devices | 0 | 0.0 |
| M9_digital_forensics | financial | 1 | 0.6 |
| M9_digital_forensics | recruitment_online | 5 | 2.9 |
| M9_digital_forensics | structure_link | 3 | 1.8 |
| M10_case_linking | cross_jurisdiction | 2 | 1.2 |
| M10_case_linking | modus_operandi | 3 | 1.8 |
| M10_case_linking | rescue_risk | 1 | 0.6 |
| M10_case_linking | ringleader_id | 1 | 0.6 |
| M10_case_linking | victim_id | 0 | 0.0 |
