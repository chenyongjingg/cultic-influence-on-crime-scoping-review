# Screening audit: thirty records read, twenty-eight excluded, corpus rebuilt

The previous build carried a sentence saying that author adjudication of the
screening table remained outstanding. It no longer does. This note records what
replaced it and what it changed.

## What was audited, and why only thirty

The machine screened 628 records and included 191. Reading all 191 abstracts was not
feasible; reading none left the wrong sentence in the paper. The audit narrowed the
work to the records where the machine's own evidence does not support its decision:

- **metaphor** — every group term in the record's text lies inside a figure of
  speech ("cult of personality", "cult sensation", "cult-author");
- **no group named** — neither the title nor the span the model itself quoted in
  support of I1 contains a group term.

That flagged 30 of the 191. The first author read all 30 against I1–I4 and excluded
28; 2 were confirmed (Manson and the Family; CERI).

## What the paper now says

Section 2.2 no longer claims the four criteria were applied as a single
conjunction. They were not: the second pass admitted records on I1 plus a lexical
crime anchor, which is a weaker test, and it admitted 110 of the 135 records it
received. Section 2.4 now describes that rule and states the machine set (191), the
audit (30 flagged, 28 excluded) and the limit that the audit bounds the worst case
rather than estimating precision. The Declarations say the same thing in one
sentence. Supplementary Table S9 is the audit, S9b applies it, S10 is the filled
worksheet, and S3 now carries the author's decision on every row it applies to.

## What changed in the corpus

| | machine | audited |
|---|---|---|
| Included records | 191 | 163 |
| Carrying an abstract | 170 | 142 |
| C1 group definition | 5.9% | 7.0% |
| C2 role | 14.7% | 15.5% |
| C3 duration | 4.1% | 4.9% |
| C5 instrument | 1.2% | 1.4% |
| C8 legal outcome | 20.6% | 19.7% |
| Regulatory instrument named | 11.2% | 9.9% |
| Open access share | 39.4% | 42.3% |

The changes run in both directions, which is the evidence that the exclusion was a
correction rather than a filter applied because it improved the result. The largest
move in any headline percentage is 1.1 points.

Every number in the manuscript is substituted from `analysis.json`, which was
regenerated from the filtered corpus; the figures were regenerated from the same
file. `final_check.py` asserts the post-audit denominators, the new sentences, and
the absence of the old ones.

## Limits that are now in the paper, not only in this note

- The audit covers 30 records, not 191. The other 161 machine decisions were not
  individually re-read.
- The audit was aimed at the error classes the 50-record validation read had already
  identified, so it is a worst-case bound, not a random sample.
- Five of the 30 satisfied all four flags and were still wrong (an Assyrian
  priesthood paper, a nerve-agent capability review, two ideological-history papers
  and a counter-extremism policy paper). Flag-based auditing cannot find those; the
  manuscript therefore does not claim the corpus has been verified, only that the
  least-confirmable records were read.

## Deviation log

S1 D-4 was rewritten from "adjudication is not performed" to the four-step account
of what was performed, including the weaker second pass and the audit's scope.
