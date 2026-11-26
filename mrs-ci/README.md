# MRS-CI — Minimum Reporting Set for Cultic Influence on Crime

Version 1.0, 2026-11-26. Machine-readable form: [`mrs-ci.json`](mrs-ci.json).

## What it is

Ten items that an abstract should state when it reports a study of cultic influence
and crime, plus two requirements of general reporting hygiene. Each item is derived
from a *measured* absence in the corpus, not from a committee's preference: the
`measured_*` fields in `mrs-ci.json` record how often the construct actually appears
in the title and abstract of the 171 records that carried an abstract.

## Why it is aimed at the abstract

A paired reading of abstracts against full texts shows the reporting rate for a
standardised instrument rising from 0% to 28.6%, and for a legal outcome from 16.7%
to 66.7%, between the abstract and the body of the same papers. The information is
not missing from the studies; it is missing from the interface through which the
literature is read. That makes a reporting convention, rather than a research
programme, the intervention that fits the problem.

## The ten items

| # | Item | Minimum acceptable form | Measured in corpus |
|---|---|---|---|
| 1 | Group operational definition | the criterion used to classify the group, and its source, in one sentence | see `mrs-ci.json` |
| 2 | Participant role | leader / core executor / ordinary member / victim / former member, with the basis | |
| 3 | Involvement and exit duration | month-level start and end, or years; an explicit "unknown" is acceptable | |
| 4 | Named manipulation mechanism | the term actually used, from a checkable list | |
| 5 | Standardised instrument | name, score, and administration context; a negative statement also satisfies | |
| 6 | Offence type | offence category under a named classification | |
| 7 | Offence severity | a statutory grade, a study-internal grade, or a sentence length | |
| 8 | Legal outcome | charge, conviction, sentence, responsibility finding or ruling, with the date | |
| 9 | Jurisdiction | country and the applicable responsibility framework | |
| 10 | Data source and recruitment | clinical / forensic / self-report / media / court file, and how participants entered | |

Recommended in addition, as general hygiene: a comparison group or an explicit "none",
and a sample size.

## Three properties that are deliberate

- Items 3, 5, 10 and both supplementary requirements can be satisfied by an explicit
  *negative* statement. The failure being removed is silence, not the absence of a
  measurement.
- Items 1–3 form a block: a role without a duration explains nothing.
- No item asks for new data. Every one can be satisfied from what a study already has.
