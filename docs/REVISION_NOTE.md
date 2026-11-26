# Revision note — Frontiers_manuscript.docx (2026-11-26)

Pre-submission revision. Main text **7,474 → 8,030 words** (+556, inside the ±800 bound).
All numbers are substituted by `fill.py` from `analysis.json`; no number in the
manuscript was typed by hand.

## P0 — internal contradictions

| # | What changed | Where |
|---|---|---|
| 1 | "twelve constructs corresponding to the items of the minimum reporting set plus sample size, comparison **and a group operational definition**" → "…: the ten items of the minimum reporting set (Table 2), plus sample size and comparison" (10 + 2 = 12) | §2.5 ¶1 |
| 2 | "the two least reported constructs are named in 1.2% and **3.5%**… 1.9% and **5.6%**" → "1.2% and **2.3%** (standardised instrument, Table 2; offence severity) … 1.9% and **3.7%**" | §2.5 ¶2 |
| 3 | Table 2 given a journal caption; §4.1 now calls it out ("The minimum reporting set (Table 2) is derived from…"). Front-matter "2 tables" confirmed: Table 1 (theory matrix) + Table 2 (MRS-CI) | §4.1 |
| 4 | One sentence added: the validation sample will be read blind by a second author and reported side by side in Table S7, together with the Table S3 adjudication. No result is claimed | §2.4 last ¶ |

Reason for #2: the construct table's lowest two entries are instrument (2/171, 1.2%)
and offence severity (4/171, 2.3%); 3.5% is comparison (6/171).

## P1 — investigative and regulatory practice

- **New §3.5 "Investigative and regulatory practice in the corpus"** (~690 words).
  - *Investigative half* reports M8–M10 as n/N over 171 measurable records, framed as
    a gap in the public trace rather than a judgement of capability, and explicitly
    paired with §3.4.1 ("information in the paper but not the abstract" ↔ "practice in
    the file but not the paper").
  - *Regulatory half* reports a new coding of named regulatory instruments
    (20/171, 11.7%; prosecution 14, immigration 4, trafficking 3, family 3, financial 1,
    charity 0, civil commitment 0), then reads MRS-CI as
    **an information-disclosure-based, low-burden regulatory instrument**, placed
    alongside risk-assessment registration and algorithmic accountability.
  - Closes on the topic's three themes and carries the compliance sentence
    (published-literature coding only; not an investigative guide or legislative proposal).
- **§4.1** gained one sentence: items 2, 3 and 8 serve investigative-file comparability
  and regulatory auditability as well as research comparability.
- **§3.4.2 (old investigative subsection) removed** — it reported the same M8–M10
  counts as the new §3.5. §3.4 now runs 3.4.1, 3.4.2 (sensitivity).
- **Three references added**, DOI-verified: Meissner et al. 2014
  (`10.1007/s11292-014-9207-6`), Kassin et al. 2010 (`10.1007/s10979-009-9188-6`),
  Vrij et al. 2010 (`10.1177/1529100610390861`). They carry the interrogation-method
  contrast in §3.5.
- **No self-citation added**: the first author's 2026 risk-governance paper could not be
  confirmed against a registration record from this environment, so it was omitted
  rather than cited on trust.

## P2 — polish

- Grey literature now stated in §2.3: three policy documents inform the background,
  none is peer-reviewed or codable, none enters a denominator.
- `BodyText`, `Compact`, `FirstParagraph` were referenced by pandoc but undefined in the
  template; `build_frontiers.py` now defines all three as Normal-based styles, so Word no
  longer falls back silently.
- Full rebuild: Figures 1–5 and S1 regenerated from the current `analysis.json`;
  `.docx` and `.pdf` re-exported. Word-count line updated.
- §2.4's statement that the numbers are the machine record and that author adjudication
  is outstanding was **left untouched**.

## Where every number comes from

| Number in the manuscript | Value | Source file |
|---|---|---|
| Standardised instrument | 2/171 (1.2%) | `analysis.json › construct_table › C5_instrument` |
| Offence severity | 4/171 (2.3%) | `analysis.json › construct_table › C7_severity` |
| Offence type | 84/171 (49.1%) | `analysis.json › construct_table › C6_offence` |
| Jurisdiction | 89/171 (52.0%) | `analysis.json › construct_table › C9_jurisdiction` |
| Best-observed detector recall | 0.62 | `analysis.json › detector_validation › C4_mechanism.recall` |
| Recall-corrected 1.9% / 3.7% | 1.2/0.62 ; 2.3/0.62 | derived in text from the two rows above |
| M8–M10 counts | modules.* | `analysis.json › m8_m10` (N = 171) |
| Regulatory distribution | counts.* | `analysis.json › regulatory_tools` (new; `src/regulatory_tools.py`) |
| Main-text word count | 8,030 | computed by `src/build_frontiers.py` |

## Reference verification (S8)

25 references, checked field by field against the registration record:
**22 verified**, 3 not covered by any registration agency —
[3] Chambers (OpenAlex confirms authors, title, year; pagination unconfirmed),
[4] Hassan and [9] Lalich (no record in Crossref or OpenAlex). Each carries the evidence
that was available rather than a bare tick.

## Acceptance self-check

- [x] §2.5 contradictions fixed; 12-construct accounting consistent throughout
- [x] Table 2 captioned and called out; "2 tables" matches
- [x] §2.4 blind second-read commitment added, no result claimed
- [x] §3.5 numbers all trace to `m8_m10` / `regulatory_tools` in `analysis.json`
- [x] New references DOI-verified and in S8; no self-citation
- [x] Compliance: no accusatory wording, no restricted material, no domestic-only
      governance discourse, "high-control groups" throughout
- [x] `fill.py` builds with no unresolved placeholder; figures and text share one source
- [x] Revision note (this file)
