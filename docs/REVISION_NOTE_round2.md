# Revision note — round 2 (2026-11-26)

Main text **8,030 → 8,440 words** (+410, inside ±500). No method change, no new GPU work,
no number altered. `fill.py` builds with no unresolved placeholder and `check_numbers.py`
confirms every number in the text traces to `analysis.json` or a named constant.

## Task 1 — authorship

Front page: **Authors: Ziying Xue¹, Yongjin Chen¹, Songze Zhu¹**; correspondence unchanged
(Songze Zhu, 20196846@ppsuc.edu.cn).

New paragraph in Declarations:

> **Author contributions.** Ziying Xue: investigation, formal analysis, writing —
> original draft. Yongjin Chen: data curation, validation, visualization. Songze Zhu:
> conceptualization, methodology, adjudication (recorded in Supplementary Table S3),
> correspondence. All three authors contributed to writing — review and editing.

Adjudication is marked as recorded in Table S3, which is where the task is actually
completed; nothing beyond the team's stated division of work is claimed.

## Task 2 — style pass

| Measure | Before | After |
|---|---|---|
| "rather than" constructions | 41 | **17** |
| Metadiscourse ("asymmetry matters", "in its own right", "worth naming") | 4 | **0** |
| Triadic enumerations (rhetorical) | 5 | **2** |
| Consecutive paragraphs opening on the same word | 11 | **0** |
| Sections without a sentence of ≤8 words | 1 (Abstract) | **0** |

Roughly half of the reduction is deletion rather than rewording: the contrast was cut
where it carried nothing ("The choice of sources follows a constraint"; "Two further
observations belong here"), and recast positively where it carried a claim ("an empty
cell is a finding"). Where the contrast *is* the argument it was kept — the
reading-interface claim, the rule-based-versus-human disclosure, the
measurement-effect caveat, exposure-versus-capacity. **37 sentence-level changes are
listed before/after in `STYLE_CHANGES.md`.**

No number, term, citation or heading was touched: a multiset comparison of the numeric
tokens against the previous build shows nothing removed or altered, and the citation
set differs only by one added instance of `[12]`.

## Task 3 — depth and the regulatory reading

Added to §3.5 (regulatory half) and §4.1, net **+410 words**:

- **The ex-post / ex-ante asymmetry, named.** Every instrument the corpus names acts on
  conduct after the event — prosecution, removal or status, trafficking enforcement,
  family-court remedies. No record names a registration, reporting or supervisory
  requirement imposed before harm; the two categories that would capture one,
  charitable-status regulation and civil commitment, are empty. Two records propose
  amending enforcement statutes; neither proposes an instrument that operates on
  information.
- **Why that matters here.** Incidents in this corpus are rare and severe. Enforcement
  arrives after the damage and cannot be calibrated to it; a registration or disclosure
  requirement attaches where the group already holds the information. The field's
  regulatory imagination is anchored to the cases that produced it.
- **MRS-CI as a risk-governance sequence** (identification → assessment → pathway),
  with items 1 and 6–9 making risk countable, items 2, 3 and 5 supplying exposure and
  capacity, and disclosure as the minimum-burden pathway.
- **The caveat, stated plainly:** the parallel is structural, not empirical. The review
  shows the disclosure layer is missing; it offers no evidence that adding it would
  reduce harm.
- **Platform link** (~60 words): online recruitment in 5/171 records, ref [12].

### On the Zhu (2026) self-citation

**Omitted, and here is why.** The reference could not be confirmed from this environment
across four routes: Crossref (no record for the journal or the title), Baidu Scholar
(returned an empty shell), Bing ("There are no results"), and CNKI (requires
authenticated session). 《信息技术与管理应用》 does not register DOIs with Crossref, so
the paper cannot be checked in the way the rest of the reference list was checked.
Under the brief's own rule — verify first, and if verification fails, omit and explain —
no self-citation was added and the self-citation count for this manuscript is **0**.

The three-stage framing is still in the text as a regulatory-theory argument, stated
without attributing it to a specific paper. If the authors can supply the CNKI record
(作者/题名/卷期/页码), the citation can be added in one line at the end of that
paragraph without touching anything else.

## Task 4 — build

- `fill.py`: no unresolved placeholders.
- `check_numbers.py` (new): every numeric token in the body resolves to `analysis.json`
  or to a constant with a stated reason. It caught two numbers that had no artefact
  behind them — the 14B reading's recall (0.18) and a signed drift (−8.6) written as
  "at most"; both are now bound to stored values (`llm_read_scores`, `max_abs_drift_pp`).
- Figures 1–5 and S1 regenerated from the current `analysis.json`.
- Front page: **8,440 words; 5 figures; 2 tables** — still accurate.

## Two defects found while working, not fixed

1. **One duplicate record in the corpus.** "Preventing Predatory Alienation by
   High-Control Groups" is present twice (CORE ids 83503620 and 233755417): one copy has
   the DOI, the other carries CORE's "Not available for public API users" placeholder as
   its abstract and no DOI, so title-based deduplication did not join them. Effect: the
   denominators are 171 where 170 is correct, and the regulatory count is 20 where 19 is
   correct. Fixing it means re-running compose → screen → adjudicate → measure, which
   changes every percentage in the paper — a methodological change this round was told
   not to make. Flagged for a decision.
2. **CORE counts were rendering as zero** in §2.3 until noticed during the diff: porting
   the analysis to run against the local archive broke the raw-directory resolution.
   Fixed; the sentence now reads 87 / 410 / 269 / 46 / 49 / 150 as before.
