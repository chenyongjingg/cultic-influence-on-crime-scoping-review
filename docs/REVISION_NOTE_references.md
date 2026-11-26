# Reference re-verification — what was checked, and what it changed

Every reference in the current build was verified a second time, this time from the
**string printed in the manuscript** rather than from the structured claim file that
generated it. The two can drift apart, and only the printed string is what a reader
or a copy-editor sees.

## Method

Two independent directions, run by `src/verify_printed_refs.py`:

1. **printed → claim.** Every field in `src/refs.json` (title, first author, year,
   volume, page, journal) must appear verbatim in the printed string. This catches a
   build step that drops or rewrites a field between claim and manuscript.
2. **printed → record.** The registration record's own title, first author, year,
   volume, page and journal must appear in the printed string. This catches a claim
   that was wrong to begin with. Author order is checked on the first three authors,
   not only on the first, because a correct lead author with a swapped second author
   passes a first-author-only test.

Each DOI was also resolved at Crossref (a 200 proves the identifier is registered)
and, in a separate parallel pass, at doi.org. Entries with no DOI were searched in
Crossref, OpenAlex and Semantic Scholar; where all three returned nothing, an open
web search was run and the result recorded with its source.

## Result

| Outcome | n | Items |
|---|---|---|
| Printed string contains every field of its Crossref record | 22 | 1, 3–8, 11–25 |
| Record verified outside the DOI indexes; no DOI exists | 3 | 2 (Lalich), 9 (Chambers), 10 (Hassan) |
| Author-verified; not reachable from this environment | 1 | 26 (Zhu 2026) |

The three that had been carried as "outstanding" in earlier rounds are now closed:

- **Lalich 2009** — EBSCO record (gcd:49048565) and the ICSA archive of *Cultic
  Studies Review* Vol. 8 No. 3 give 8(3):281–302, ISSN 1539-0152, exactly as printed.
- **Chambers 1994** — Scopus (0007306098), Mendeley and the ICSA e-library all give
  *Cultic Studies Journal* 11(1):88–117. The journal registered no DOI.
- **Hassan 2012** — ISBN 9780967068817; the year 2012 is confirmed by Hassan's own
  CV, library catalogues and the ICSA book review (IJCS 6, 2015). The 2013 date in
  some catalogues is a later printing of the same edition.

## Corrections made (four)

1. **Entry 6 (Coates).** Printed "socialization"; the publisher's deposit says
   "socialisation". Corrected.
2. **Entry 10 (Hassan).** Printed "Boston: Freedom of Mind Press"; every source —
   Hassan's CV, library catalogues, the ICSA review — gives **Newton, MA**. Corrected.
3. **Entry 19 (Wang).** The chapter carries pages 113–121 in its Crossref record; the
   printed string omitted them. Added.
4. **Entry 1 (Durns).** The book has a registered DOI and every other DOI-bearing
   entry prints one. Added `doi:10.1017/9781009280099`.

## Formatting, not content

Sixteen entries (11–26) had been built without italic markup on the journal title and
with ASCII hyphens in page ranges, while entries 1–10 carried italics and en dashes.
All 26 now render their journal or book title in italic and use en dashes in page
ranges. This changes no word, no number and no identifier; the build was checked to
confirm that exactly those sixteen lines changed and the body text did not.

While making that change, an over-broad rule turned the hyphens inside eight DOIs into
en dashes. It was caught by re-comparing every printed DOI against its claim, repaired,
and the rule now applies only outside DOI spans. The repaired DOIs were re-resolved.

## Content check

`S8b_reference_content_check.md` now covers all 26 entries. The new entry 26 is marked
**PARTIAL**: its title supports the topical part of the sentence it is cited in (a
regulatory analysis of "irrational exuberance" in the AI industry), but no abstract is
retrievable, so the claim that the analysis runs through identify/assess/disclose
cannot be checked here. That is the one judgement in the citation layer that rests on
the authors' own reading.

## Still outstanding

- Zhu (2026): existence verified by the authors; content not independently checkable
  from this environment. Chinese-journal article with no DOI registered.
- Entry 11 (Dayan 2018): the deposited record carries no abstract, so the content
  verdict remains CANNOT JUDGE (record itself verified).
- Human adjudication of the screening table (Supplementary Table S3) — unchanged.

## Acceptance

The rebuild is byte-identical to the previous build in the body: word count 8,064,
`final_check.py` 17/17 PASS, `check_numbers.py` clean.
