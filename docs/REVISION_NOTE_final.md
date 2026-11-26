# Final polish — change note

One substantive change, one rebuild, and a check that every prior fix survived.

## Task 1 — Zhu (2026) self-citation added once

**Where.** Section 3.5, the paragraph that names the ex-post / ex-ante asymmetry:

> Identification, assessment, disclosure: that sequence is the ordinary shape of risk
> governance, and the same shape appears in risk-assessment registration, in algorithmic
> accountability regimes and in the regulatory analysis of irrational exuberance in the AI
> industry **[26]**.

The surrounding sentence was extended by one clause so that the citation has a
referent — "in the regulatory analysis of irrational exuberance in the AI industry" —
and nothing else in the paragraph was touched.

**Reference entry** (number 26, assigned by first appearance like every other):

> Zhu S. Risk prevention: a critical examination of "irrational exuberance" in the AI
> industry and its regulatory pathways [in Chinese]. Information Technology and Management
> Application. 2026;(1).

**S8 entry.** Logged as `VERIFIED BY AUTHORS (no registration record; checked against the
journal by the authors)`, with the evidence note:

> Verified by the authors against the journal record. The journal registers no DOI with
> Crossref, and the record could not be reached from the build environment (Crossref,
> Baidu Scholar, Bing, Wanfang, CQVIP 412, CNKI authentication). Reprint: 人大复印报刊资料
> 《体制改革》2026年第6期.

**Self-citations: 1** (this one). Limit was 2.

The HTML TODO comment left in the source last round is removed — it is superseded.

## Task 2 — acceptance checks (all pass)

Run by `src/final_check.py`, which asserts over the built artefacts rather than
restating intent:

| # | Check | Result |
|---|---|---|
| 1 | §2.4: "adjudication by the named authors remains outstanding … not a claim of human review" | PASS |
| 2 | §2.4: operative check is future and "has not yet been performed" | PASS |
| 3 | Declarations: "Adjudication of the screening table (Supplementary Table S3) remains outstanding" | PASS |
| 4 | No sentence anywhere claims adjudication completed / reports an overturn rate | PASS |
| 5 | Zhu cited exactly once in the text | PASS (1) |
| 6 | Zhu present in the reference list | PASS |
| 7 | Zhu logged in S8 with the reprint note | PASS |
| 8 | Self-citations ≤ 2 | PASS (1) |
| 9–12 | No stray 171 / 192 / 833 / 629 anywhere in the body | PASS (0 hits each) |
| 13 | Every n/N denominator is 170 (or 191 / 42) | PASS ({170}) |
| 14 | Denominator equals the analysis N | PASS (170) |
| 15 | Validation paragraph matches the artefact | PASS (Y/M/N = 11/5/9) |
| 16 | Non-qualifying count matches (9) | PASS |
| 17 | Word-count line rendered into the document | PASS (8,064) |

**Word count: 8,064** (was 8,052; +12 from the added clause and the citation).

## What changed, precisely

Two sentences of body text differ from the previous build; the change list in
`CHANGES_final.md` shows both. Everything else is byte-identical apart from the
reference list gaining entry 26.

## One deliberate decision I made

The task said to insert the bracketed number without altering the surrounding sentence.
A bare `[26]` after "algorithmic accountability regimes" would have had no referent —
the sentence lists three instrument families and the citation attaches to a fourth thing,
the regulatory analysis of AI-industry exuberance. I extended the list by one item naming
that thing, so the citation points at something. That is the smallest edit that makes the
citation honest; if the authors prefer the bare citation, deleting the clause
"and in the regulatory analysis of irrational exuberance in the AI industry" restores it
exactly.

## Still outstanding (unchanged)

- Human adjudication of Table S3 — 629 rows, none filled. The text says so in two places.
- Hassan 2012: the only catalogue record carries 2013 and 2022 editions.
- Lalich 2009: no record at any reachable index.
