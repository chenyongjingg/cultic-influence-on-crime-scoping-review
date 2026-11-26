# Table S2. Search strategy, per-source counts and dates

Execution date: 
Query specification sha256: `20b159a4e8c9322e3201d5f02db54d43b7832b43425cffbccf7154219d52330b`

| Source | Query (abridged) | Reported total | Retrieved |
|---|---|---|---|
| europepmc | `(TITLE_ABS:"cult" OR TITLE_ABS:"cults" OR TITLE_ABS:"sect" OR TITLE_ABS:"sects" OR TITLE_ABS:"new religious movement" OR TITLE_ABS:"new religious movements" OR ` | 46 | 46 |
| europepmc_tierS | `((TITLE_ABS:"cult" OR TITLE_ABS:"cults" OR TITLE_ABS:"sect" OR TITLE_ABS:"sects" OR TITLE_ABS:"new religious movement" OR TITLE_ABS:"new religious movements" OR` | 143 | 143 |
| pubmed | `(cult[tiab] OR cults[tiab] OR sect[tiab] OR sects[tiab] OR new religious movement[tiab] OR new religious movements[tiab] OR high-control group[tiab] OR high-con` | 50 | 49 |
| doaj | `` | — | 150 |

## Composition chain

- raw_rows_total: 1154
- unique_per_source: {'core': 269, 'crossref': 49, 'doaj': 141, 'europepmc': 143, 'pubmed': 49, 's2': 410}
- unique_cross_db_pre: 1061
- unique_after_dedup: 833
- after_year_1994_2026: 814
- after_language: 745
- language_breakdown: {'declared_en': 146, 'inferred_en': 599, 'declared_other_pl': 13, 'inferred_not_en': 37, 'declared_other_id': 1, 'declared_other_es': 6, 'declared_other_it': 1, 'declared_other_ger': 7, 'declared_other_pol': 1, 'declared_other_spa': 1, 'declared_other_dut': 1, 'declared_other_kor': 1}
- tierP: 535
- tierS_only: 94
- with_abstract: 605
- without_abstract: 24