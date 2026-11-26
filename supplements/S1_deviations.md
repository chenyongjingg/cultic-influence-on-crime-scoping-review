# Protocol deviations and constraints register
Project: PRISMA-ScR scoping review, "Cultic influence on crime"
Protocol: 论文写作计划书 V1.4 (2026-11-26, D:/end/邪教影响犯罪论文写作计划书(3)(1).docx)
Execution: 2026-11-26 onwards, 4090 server `cpod-1y5whh3pcsvs.podtcp.compshare.cn`

Every deviation below is recorded with the evidence that forced it. Nothing here
is a preference; each is a constraint that was measured, not assumed.

## D-1  Date range: methods section says 1994, introduction says 1980
The protocol is internally inconsistent: §3.2 (methods) sets 1994 to the search
date, anchored on the GPA scale (Chambers et al. 1994); §2.1 (PCC) writes "1980
年至检索日". Resolved in favour of the methods section (1994–2026). Any 1980–1993
records that would have qualified are therefore out of the corpus, and the
limitation is stated in the manuscript.

## D-2  OpenAlex was unavailable for most of the window (credit exhaustion)
Measured on 2026-11-26 05:20 UTC, from the execution host:
```
HTTP/2 429
retry-after: 67149
x-ratelimit-limit: 1000        x-ratelimit-remaining: 9
x-ratelimit-credits-required: 10
x-ratelimit-onetime-remaining: 0
x-ratelimit-prepaid-remaining-usd: 0
```
OpenAlex's post-2026-02 metered model gives a finite free credit pool; it was
consumed by the reconnaissance queries run earlier the same day, and each query
now needs 10 credits against 9 remaining. The reset lands at ~2026-11-27 00:00 UTC.
Consequence: the primary corpus for the first pass is built from Europe PMC,
PubMed and DOAJ; the OpenAlex pass runs at the reset and is merged into the
corpus before any number in the manuscript is finalised. If the OpenAlex pass
fails, the manuscript reports the three-source corpus and states the coverage
limitation explicitly.

## D-3  Batch inference: prompt packing → tensor batching
Protocol §3.3 specifies batches of 32 records. Prompt packing into a single
sequence keeps the GPU at batch 1 and costs the same wall clock per generated
token; tensor-batched decoding runs N sequences concurrently. Implemented:
one record per prompt, N concurrent sequences, N recorded in every output file.
This changes throughput only; each record is still judged independently and
greedily, so no record's decision depends on its neighbours.

## D-4  Adjudication is partial: an audit of the 30 least-confirmable records
Protocol §3.3 and §7.3 assign adjudication to the first author and forbid double
independent screening. No independent human screening of the full corpus was
performed. What was executed is: (i) model screening with structured output and the
pre-specified auto-exclusion rule; (ii) a rule-based second pass for records the
model left uncertain, which admitted records on I1 plus a lexical crime anchor and
is therefore weaker than the four-criterion conjunction the protocol specifies;
(iii) a full-corpus audit (S9) that replayed every decision from the stored fields
and flagged the included records whose title and quoted I1 evidence named no group,
or whose only group term was metaphorical; (iv) the first author read all 30 flagged
records and excluded 28 (S10). The analysed corpus is therefore the machine set of
191 minus those 28, i.e. 163. The audit covers the records the machine could not
confirm, not the other 161, so it bounds the worst case rather than estimating
precision; the correction moves no headline percentage by more than 1.1 points
(S9b). The manuscript states both the procedure and this limit.

## D-5  No Scopus / Web of Science
No institutional access on the execution host. The limitation on recall is
stated rather than estimated.

## D-6  Verification level is L2 for the whole corpus
No full text was retrieved. Every extracted value is abstract-level, and the
manuscript therefore reports *abstract-level reporting completeness* — what the
literature makes visible at its reading interface — not what the full texts
contain. Constructs that are conventionally reported only in the body of a paper
(instrument names, sample sizes) are under-counted by construction; this is
stated as the principal limitation of the measurement, not as a finding about
the field.

## D-7  The §3.8 ">600 records → tighten" rule
Screening here is automated and auditable, so the 600-record trigger (written for
manual adjudication burden) does not bind at the screening stage. It was applied
where it does bind — the set carried into extraction — rather than by narrowing
the search, which would trade recall for convenience in a design whose whole
point is comprehensiveness. Recorded as a deliberate reading of the rule.

## D-8  Grey literature
Policy reports named in the protocol (Parliament of Victoria 2025, Family
Survival Trust 2025, McIvor et al. 2025) are not indexed in the three sources
and are carried as narrative context, not as corpus records. They do not enter
any denominator.

---

## D-9  OpenAlex replaced by a six-source stack (protocol V1.6 §3.11)
Per V1.6 the OpenAlex wait was abandoned rather than shortened. Replacement stack
and its measured yields (records passing the base block):

| Source | Role | Records in raw files |
|---|---|---|
| Crossref | main substitute (relevance-ranked; no title/abstract boolean) | 87 |
| Semantic Scholar | abstract completion; served only after repeated 429 backoff | 410 |
| CORE | OA full-text aggregation; 3,046 hits, unkeyed quota capped retrieval at three pages | 269 |
| Europe PMC | baseline (46 primary tier + 143 widened tier) | 189 |
| PubMed | baseline | 49 |
| DOAJ | baseline | 150 |
| Total before deduplication | | 1,154 |

Consequences recorded rather than smoothed: (i) Crossref's relevance ranking yields
few on-topic records per thousand rows for a niche field, so its contribution is
small relative to its nominal coverage; (ii) CORE's unkeyed quota allows roughly
three pages before persistent throttling, so a registered key would materially
increase yield; (iii) E3 reports each source's exclusive contribution so that no
source's coverage is allowed to stand in for the field.

## D-10  Screening layer upgraded to 14B, 7B retained for E5
Production screening uses Qwen2.5-14B-Instruct at 4-bit AWQ. The 7B model screens
the same records so that E5 can report agreement. The AWQ checkpoint was verified
against the publisher's sha256 for all three shards before use; the transformers
AWQ path needs `gptqmodel`, which does not install against torch 2.14 on this host,
so loading goes through `autoawq` with `fuse_layers=False` (slower, same weights).

## D-11  M8–M10 coded from abstracts by instrument-assisted procedure
The protocol specifies manual coding of the three investigative modules over full
texts. This run had abstracts only. The coding was performed with documented term
lists and every code carries its triggering span, so a human reviewer can accept,
edit or overturn any code in one pass. The manuscript labels these as
instrument-assisted and states the limitation; they are not presented as manual
codes and no full-text claim is made from them.

## D-12  E1's threshold sweep is degenerate, and that is the result
The confidence-threshold sweep moves nothing between 0.60 and 0.90 because the
screening model emits almost only 0.90 and 0.95. The experiment therefore returns a
statement about model calibration — confidence is not spread across the range and
cannot be used as a graded dial — rather than a menu of inclusion sets. Reporting
the degeneracy as a finding is preferable to presenting a flat table as if it
demonstrated robustness.

## D-13  OpenAlex is a re-planning item, not a drop-in increment
V1.6 §3.11 makes OpenAlex an incremental verification source once its quota
returns. Measured cost if it is added as-is: the tier-P query returns ~3,100
records where the current six-source corpus yields 643 eligible records. Screening
that at the observed 14B-AWQ rate (~11 records/min at concurrency 8) costs roughly
five GPU-hours on its own, which is more than the entire 1.5-hour screening line in
the §3.11 budget table. Adding OpenAlex therefore requires either a re-planned
budget or a screening configuration change (higher concurrency, or the 7B layer for
a first pass), and it should not be presented as a free increment. Recorded here so
the choice is made deliberately rather than by drift.

## D-14  Screening precision is measured, not assumed
A 50-record validation read (S7) put inclusion precision between 48% and 68% and
auto-exclusion false negatives at roughly 8%. The manuscript states this and marks
the percentages as conservative rather than corrected. No post-hoc filter was
applied to raise precision: filtering by "does the record read on topic" after
seeing the reporting profile would tune the corpus to the conclusion, which is the
one failure mode a reporting-completeness study must not have. The adjudication
worksheet is the remedy and it belongs to the authors.

## D-15  The detectors under-count, and by a construct-dependent amount
A 29-record hand read (S5/E6) gives the lexical detectors precision 0.80 and recall
0.45 overall, with recall ranging from 0.24 (group operational definition) to 0.62
(named mechanism). Consequence for the manuscript: every percentage is a lower
bound, and the distance between two constructs is partly a property of the detector
rather than of the literature. The manuscript states this in §2.5 and again in §6,
and leans on the comparison that survives correction — the bottom group stays in
single figures even when credited with the best-observed recall. The alternative
instrument was tested rather than assumed: the 14B model, asked one construct at a
time, gives precision 0.85 and recall 0.18, which is worse for a prevalence estimate.

## D-16  Two of the four largest bars are vocabulary-dependent
Strict term variants (S5/E7) move jurisdiction by -15.2 pp and data source by
-21.1 pp, against -5.8 for offence type. The relative ordering of the top four is
therefore not stable across defensible term lists. What is stable is the gap between
the top group and the bottom group (instrument, comparison, severity, duration), which
moves by at most 3 pp in absolute terms. The manuscript reports the base numbers and
states the ordering caveat rather than silently picking the flattering variant.

## D-17  The full-text comparison changes the paper's claim, and the claim was changed
Paired measurement of 42 of the 171 measurable records (abstract / length-matched
body window / full text) shows every comparison-enabling construct rising sharply
from abstract to full text — standardised instrument 0% to 28.6%, legal outcome
16.7% to 66.7%, sample size 7.1% to 45.2%, participant role 9.5% to 52.4% — while the
length-matched control reports no more than the abstract for nine of twelve
constructs. The earlier draft argued that the field cannot compare its studies; the
evidence supports a narrower and better claim, that the comparison quantities are
present in the papers and absent from the abstracts through which the literature is
read. Abstract, Section 6.1, Section 7 and Section 10 were rewritten accordingly
rather than patched.

Limits recorded with the result: full text was obtainable for only a quarter of the
included records, biased towards open access; the subset drifts from the corpus by at
most 8.6 percentage points at the abstract level; and a full text that names an
instrument does not establish that the study used it well.

## D-18  Full-text retrieval yield is a finding, not a failure to try
The retrieval ladder (Europe PMC XML, Unpaywall, CORE by DOI, CORE by title,
Semantic Scholar open-access PDF) ran to exhaustion, including a second pass over
every failure. The second pass returned zero additional full texts: the inaccessible
records are closed access, not slow endpoints. 24.6% obtainable is the measured
accessibility of this literature, and it belongs in the limitations as such.
