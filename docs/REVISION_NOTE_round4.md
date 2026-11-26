# Revision note — round 4

Main text **8,440 → 8,054 words** (−386, inside −300…−500). No number added, removed or
altered: a multiset comparison of numeric tokens against the round-3 build is empty
except for two section cross-references. Citation set unchanged.

## Task 1 — adjudication contradiction, resolved to what S3 actually contains

**Checked first.** `supplements/S3_author_worksheet.csv` has **629 rows and 0 filled
`author_decision` cells, 0 `author_note` cells**. There is no adjudication record and
therefore no overturn rate to report. Branch 3 of the instruction applies.

Changed:

- **Author contributions** — removed "(recorded in Supplementary Table S3)"; Songze Zhu's
  line now reads "conceptualization, methodology, correspondence", followed by a new
  sentence: *"Adjudication of the screening table (Supplementary Table S3) remains
  outstanding. The worksheet is complete and blank for the author's decisions, and the
  numbers reported here are the machine record; Section 2.4 says how they should be read
  in consequence."*
- **§2.4** — the sentence that read "the operative check is the author adjudication of
  the full table" now reads "…will be the author adjudication of the full table, which
  has not yet been performed." The disclosure that adjudication "remains outstanding, and
  the numbers here are the machine record, not a claim of human review" is untouched.
- **§2.6–§2.8** scanned: no other sentence presupposes that human adjudication happened.
  The blind second-read sentence in §2.4 is future tense and stays consistent with
  outstanding.

The two locations now say the same thing, and that thing matches the file.

## Task 2 — Zhu (2026): not added, TODO record left in the source

Verification was attempted against every route available from this environment:

| Route | Result |
|---|---|
| Crossref (journal name, journal name romanised, title keywords) | no record |
| Baidu Scholar | returns an 8-character shell |
| Bing (three queries, exact and partial title) | "There are no results" / query echo only |
| Wanfang | empty page |
| CQVIP | HTTP 412 |
| CNKI | requires an authenticated session |

《信息技术与管理应用》 does not register DOIs with Crossref, so the citation cannot be
checked the way the other 25 were. Per the instruction, it is kept **out of the
manuscript**; an HTML comment now sits in the source (`manuscript/sections/s35.md`, above
the "Identification, assessment, disclosure" paragraph) recording the exact citation as
supplied, the six failed routes, and the one-line action needed to add it. Pandoc drops
the comment, so nothing reaches the built document (verified: `TODO` absent from
`word/document.xml`).

**Author-group self-citations: 0.** Adding this one would have been 1 of a permitted 2.

## Task 3 — redundancy removed (−386 words net, before Task 4 additions)

| Where | What was cut |
|---|---|
| §3.5 ¶"That distribution is a governance finding" | the anticipatory "regulates after the fact, almost never on information" sentence (the asymmetry paragraph states it), the duplicate "converts an unverifiable narrative into a record" clause, and the "Section 4.2's cheapest possible intervention" cross-reference |
| §3.5 ¶"That shape follows…" | the third restatement of the disclosure mechanism ("a registration or disclosure requirement attaches where the group already holds the information and costs little to impose") |
| §3.5 ¶"Read in those terms…" | "It closes with a pathway of minimum burden, where the obligation attaches to disclosure and not to conduct" — the second restatement |
| §2.7 | five verbose E1–E5 descriptions compressed; the results are in §3.4.2 and Table S5 |
| §2.3 | the OpenAlex/­yield paragraph compressed |
| §2.5 | the two LLM paragraphs compressed; the scope paragraph compressed |
| §3.3 | A-1/A-2/A-3 and the synthesis paragraph compressed |
| §3.4.2 | sensitivity paragraph compressed |

The MRS-CI disclosure claim now appears **once** in full, in the paragraph that follows
the 20/171 (11.7%) count — the pairing the instruction asked for. The other two
appearances are gone rather than shortened, because the sequence paragraph now carries
the idea forward on its own.

"Fewer than the underlying cases contain" appeared once in §3.5 already; no change.

Filler scaffolding: "It is worth noting", "Importantly," sentence-initial, and
"In other words" — **0 occurrences** in the current text.

## Task 4 — contributions, abstract, audiences

- **Introduction**: "Three contributions" → "Four contributions", one sentence each, no
  adjectives: (i) the reading-interface finding with the length-matched control;
  (ii) the twelve-construct map; (iii) the investigative record map (§3.5); (iv) the
  regulatory asymmetry with MRS-CI as a disclosure instrument.
- **Abstract Conclusions**: one clause added — "…framed as a disclosure instrument a
  regulator could impose at low cost." Nothing else in the abstract touched.
- **§4 opening**: one sentence naming reviewers (what to require), investigators (what
  the record supports), regulators (where the instrument gap sits).

## Task 5 — de-AI pass

| Measure | Round 3 | Now |
|---|---|---|
| `, not …` contrastive constructions | 30 | **19** |
| `not … but …` | 7 | **7** |

Eleven were converted to direct statements at the weakest points ("The unit of analysis
is the record"; "Two disclosures belong here"; "larger than the bars suggest"; "each
assessment is an argument, and arguments do not aggregate"; "It is neither an
investigative guide nor a legislative proposal"). The two load-bearing ones named in the
instruction were left alone, as were "the machine record, not a claim of human review",
"an absent public trace, not an absent practice", "These are gap findings, not
judgements of capability", and "The parallel is structural, not empirical".

## Task 6 — build

- `fill.py`: no unresolved placeholders.
- `check_numbers.py`: **all numbers trace to `analysis.json`**.
- Word-count line: **8,054 words; 5 figures; 2 tables** — figures and tables unchanged.
- Word count now excludes HTML comments, so the printed figure equals the rendered text.
- `.docx` and `.pdf` rebuilt; Figures 1–5 and S1 regenerated from the current artefacts.

## Acceptance checklist

- [x] §2.4 and Author contributions agree, and both match S3 (629 rows, 0 decisions)
- [x] Zhu (2026) not cited; TODO comment in source with the citation, the six failed
      routes and the one-line fix; absent from the built document; self-citations 0
- [x] Introduction states four contributions; abstract Conclusions names MRS-CI's
      regulatory character; §4 opening names three audiences
- [x] `, not` count 19 (≤20)
- [x] Every numeric value traceable to a pipeline artefact
- [x] No new accusations; no single-jurisdiction governance discourse (see note below)
- [x] Neutral terminology; author order, §3.5 substance, all prior fixes intact
- [x] Word count updated

## One thing to watch

The §3.5 governance passage is written in general regulatory-theory terms, without any
jurisdiction-specific vocabulary — it names "risk-assessment registration" and
"algorithmic accountability" as instrument families, not any national policy framework.
That was deliberate and should stay that way if the Zhu citation is added later: cite
the mechanism, not the policy doctrine.
