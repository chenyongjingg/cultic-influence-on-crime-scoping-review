# Duplicate removal and the numbers it moved

One paper was present twice in the corpus. Removing it changes the denominators, so
every percentage in the manuscript moved slightly. All are substituted by `fill.py`
from `analysis.json`; none was typed.

## Why the duplicate survived the first two passes

The two copies of "Preventing Predatory Alienation by High-Control Groups" had the same
title except that one carried the raw HTML entity `&amp;` where the other carried
`and`. Title normalisation kept the ampersand in the first case and dropped it in the
second, so the two records produced different keys and the deduplicator did not join
them.

**Fix**: `html.unescape()` before normalising, and `&` → " and " so that the two forms
collapse to the same key. Applied in `compose.py` and `dedup_screened.py`.

## A second defect found in the same step

The surviving record was chosen by "longest abstract", which in this case kept the copy
**without a DOI** — the citation's DOI would then have pointed at a record no longer in
the corpus. Deduplication now **merges** the pair: identifier from either copy, the
longest real abstract, the entity-decoded title. Both surviving merges are listed in
`dedup_screened_report.json`.

## A third defect, found while recomputing

`S7_validation_read.md` carried a tally line saying **Y = 12, M = 5, N = 8**, but its own
table counts to **Y = 11, M = 5, N = 9**. The manuscript had copied the tally line.
Recounted from the table — which is the record of the read — and corrected in both
places, with a note in S7 that the earlier figure was an arithmetic slip.

## What moved

| Quantity | Before | After |
|---|---|---|
| Unique after deduplication | 833 | **832** |
| After year/language limits | 745 | **744** |
| Eligible / screened | 629 | **628** |
| Duplicates removed after scoring | 14 | **15** |
| Included | 192 | **191** |
| Measurable (denominator) | 171 | **170** |
| Offence type | 84/171 (49.1%) | **83/170 (48.8%)** |
| Jurisdiction | 89/171 (52.0%) | **89/170 (52.4%)** |
| Named mechanism | 26/171 (15.2%) | **25/170 (14.7%)** |
| Standardised instrument | 2/171 (1.2%) | **2/170 (1.2%)** |
| Offence severity | 4/171 (2.3%) | **4/170 (2.4%)** |
| Records naming any regulatory instrument | 20/171 (11.7%) | **19/170 (11.2%)** |
| … naming two or more | 4 | **3** |
| Full text obtainable | 42/171 (24.6%) | **42/170 (24.7%)** |
| Maximum subset drift | 8.6 pp | **8.3 pp** |
| S7 tally | 12 / 5 / 8 | **11 / 5 / 9** |
| Validation precision band | 48–68% | **44–64%** |
| Non-qualifying records: mean constructs | 1.8 vs corpus 2.1 | **1.67 vs 2.08** |
| … reporting a jurisdiction | 4 of 8 | **3 of 9** |
| Removing them: offence / jurisdiction | 49.1→48.5 / 52.0→52.8 | **48.8→48.4 / 52.4→53.4** |
| Recall-corrected lowest two | 1.9% / 3.7% | **1.9% / 3.9%** |

None of these reverses a conclusion. The ordering of Figure 3 is unchanged; the two
lowest bars stay at 1.2% and 2.4%; the regulatory layer stays at about one record in
nine; the ex-post-only finding is unaffected.

## Now computed rather than typed

Four numbers in §2.4 and §2.5 were previously written by hand from the validation read.
They are now produced by `src/validation_numbers.py` (tally, means, with/without rates)
and by `analyse.py` (`recall_corrected`), and reach the text through `fill.py`. The
non-qualifying records are matched to corpus identifiers, with two matched by hand and
their identifiers recorded in the script — the S7 labels are a short paraphrase and a
French original, and no title-similarity threshold found them.

`check_numbers.py` passes: every number in the manuscript resolves to `analysis.json`
or a named constant. The PRISMA chain closes: 744 − 116 = 628, and
412 auto-excluded + 135 advanced + 81 kept = 628.

Word count: **8,052** (was 8,054).

## Still outstanding

- Human adjudication of Table S3 (629 rows, none filled).
- Hassan 2012: the only catalogue record carries 2013 and 2022 editions.
- Lalich 2009: no record anywhere reachable.
- Zhu (2026): TODO comment in the source, awaiting the CNKI record.
