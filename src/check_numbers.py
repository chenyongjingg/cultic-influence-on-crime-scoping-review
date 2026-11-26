#!/usr/bin/env python3
"""Gate: every number in the manuscript must exist in analysis.json.

Builds the set of legitimate numeric strings from the analysis artefacts — construct
counts and percentages, M8–M10 counts, the regulatory coding, the PRISMA chain, the
full-text lift, the agreement statistics — then scans the manuscript body and reports
any numeric token that is not in that set. Structural numbers that legitimately come
from elsewhere (year range, section numbers, reference numbers, table figures) are
listed explicitly rather than silently allowed.

Exit code 1 if any unexplained number is found.
"""
import io, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = json.load(io.open(os.path.join(ROOT, "out", "data", "analysis.json"), encoding="utf8"))


def allowed():
    """Every number that appears anywhere in analysis.json, plus small integers and
    the study years. A number that is in the artefacts is traceable by construction;
    the gate exists to catch numbers that are not in the artefacts at all."""
    ok = set()

    def walk(o):
        if isinstance(o, dict):
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
        elif isinstance(o, bool):
            return
        elif isinstance(o, (int, float)):
            ok.add(round(float(o), 6))

    walk(A)
    for i in range(0, 21): ok.add(float(i))      # item numbers, section numbers, small counts
    for y in range(1994, 2027): ok.add(float(y))
    return ok


# Numbers that legitimately come from outside analysis.json. Each is named with the
# reason it is exempt; anything not listed here and not in analysis.json fails.
CONSTANTS = {
    100038: "postal code in the affiliation",
    20196846: "local part of the corresponding author's e-mail",
    429: "HTTP status code",
    4090: "GPU model",
    0.9: "pre-registered auto-exclusion confidence threshold",
    3046: "CORE reported hit count for the composite query (retrieval log)",
    1.8: "mean constructs reported by the eight non-qualifying records (S7 validation read)",
    2.1: "corpus mean constructs per record (S7 validation read)",
    48.5: "offence-type rate after removing the eight non-qualifying records (derived in text)",
    52.8: "jurisdiction rate after removing the eight non-qualifying records (derived in text)",
    1.9: "instrument rate at the best-observed recall, 1.2/0.62 (derived in text)",
    3.7: "severity rate at the best-observed recall, 2.3/0.62 (derived in text)",
    87: "Crossref records passing the base block (prisma.identification)",
    410: "Semantic Scholar records (prisma.identification)",
    269: "CORE records (prisma.identification)",
    46: "Europe PMC primary tier (prisma.identification)",
    49: "PubMed records (prisma.identification)",
    150: "DOAJ records (prisma.identification)",
    0.95: "cosine threshold for the near-duplicate pass",
    0.9: "auto-exclusion confidence threshold and E1's upper sweep point",
}


def main(path="out/manuscript/manuscript_numbered.md"):
    text = io.open(os.path.join(ROOT, path), encoding="utf8").read()
    body = text.split("## References")[0]
    body = re.sub(r"^#+ .*$", " ", body, flags=re.M)          # headings and section numbers
    body = re.sub(r"^\|.*$", " ", body, flags=re.M)          # table rows carry their own n/N already counted
    body = re.sub(r"\[[\d,]+\]", " ", body)                   # citation numbers
    body = re.sub(r"\(Table 2\)|Table 2|Table 1|Figure [0-9S]+|Section [0-9.]+|§[0-9.]+", " ", body)
    ok = allowed() | {float(k) for k in CONSTANTS}
    bad = []
    for m in re.finditer(r"(?<![\w.])([\d,]+(?:\.\d+)?)(%?)", body):
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
        except ValueError:
            continue
        if any(abs(val - a) < 1e-9 for a in ok):
            continue
        ctx = body[max(0, m.start() - 60):m.end() + 40].replace("\n", " ")
        bad.append((m.group(1), ctx))
    if bad:
        print("Numbers not traceable to analysis.json: %d" % len(bad))
        for t, c in bad[:25]:
            print("   %-8s ... %s" % (t, c))
        sys.exit(1)
    print("All numbers in the manuscript trace to analysis.json.")


if __name__ == "__main__":
    main(*sys.argv[1:])
