#!/usr/bin/env python3
"""Apply the corrected duplicate rule to an already-screened file.

The screening pass ran on a corpus produced by the earlier rule (DOI if present,
title otherwise), which lets the same paper survive twice when one source carries a
DOI and another only a title. Deduplication is independent of the screening model,
so the correction is applied here rather than by re-running the screen; the number
of records removed is reported and carried into the PRISMA chain.
"""
import html, json, os, re, sys

if os.path.isdir("/root/cultcrime"):
    ROOT = "/root/cultcrime"; P = os.path.join(ROOT, "data", "processed")
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")


def norm_doi(d):
    if not d:
        return ""
    d = d.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d.rstrip(".,;")


def norm_title(t):
    # HTML entities must be decoded first: one copy carrying "&amp;" where another
    # carries "and" gives two different keys for the same paper, which is how a
    # duplicate survived deduplication in the first run.
    t = html.unescape(t or "").replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


PLACEHOLDER_ABS = ("not available for public api users",)


def merge(into, other):
    """Collapse two copies of one paper into one record.

    Choosing between them loses information: the copy with the longer abstract may be
    the one without a DOI, in which case the surviving record could no longer be
    cited. Fields are therefore merged — an identifier from either copy, the longest
    real abstract, and the title with its HTML entities decoded.
    """
    if not into.get("doi") and other.get("doi"):
        into["doi"] = other["doi"]
    a, b = (into.get("abstract") or ""), (other.get("abstract") or "")
    placeholder = lambda s: s.strip().lower() in PLACEHOLDER_ABS or len(s.strip()) < 40
    if placeholder(a) and not placeholder(b):
        into["abstract"] = b
    elif not placeholder(b) and len(b) > len(a):
        into["abstract"] = b
    t = html.unescape(into.get("title") or "")
    into["title"] = t
    into.setdefault("merged_from", []).append(other.get("id"))


def main(src, dst):
    rows = [json.loads(l) for l in open(os.path.join(P, src), encoding="utf8") if l.strip()]
    by_doi, by_title, keep, dropped = {}, {}, [], []
    # records with an identifier first, so the surviving copy is the citable one
    rows.sort(key=lambda r: (0 if r.get("doi") else 1, -len(r.get("abstract") or "")))
    for r in rows:
        d, t = norm_doi(r.get("doi")), norm_title(r.get("title"))
        hit = by_doi.get(d) if d else None
        if hit is None and t:
            hit = by_title.get(t)
        if hit is not None:
            merge(hit, r)
            if d:
                by_doi[d] = hit
            if t:
                by_title[t] = hit
            dropped.append(r); continue
        if d:
            by_doi[d] = r
        if t:
            by_title[t] = r
        keep.append(r)
    with open(os.path.join(P, dst), "w", encoding="utf8") as f:
        for r in keep:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    rep = {"input": len(rows), "kept": len(keep), "dropped": len(dropped),
           "merged_records": [r.get("id") for r in keep if r.get("merged_from")][:10],
           "dropped_examples": [(r.get("title") or "")[:90] for r in dropped[:10]]}
    json.dump(rep, open(os.path.join(P, "dedup_screened_report.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False)
    print(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
