#!/usr/bin/env python3
"""Apply the corrected duplicate rule to an already-screened file.

The screening pass ran on a corpus produced by the earlier rule (DOI if present,
title otherwise), which lets the same paper survive twice when one source carries a
DOI and another only a title. Deduplication is independent of the screening model,
so the correction is applied here rather than by re-running the screen; the number
of records removed is reported and carried into the PRISMA chain.
"""
import json, os, re, sys

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")


def norm_doi(d):
    if not d:
        return ""
    d = d.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d.rstrip(".,;")


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def main(src, dst):
    rows = [json.loads(l) for l in open(os.path.join(P, src)) if l.strip()]
    by_doi, by_title, keep, dropped = {}, {}, [], []
    # keep the version with the longer abstract when two records collide
    rows.sort(key=lambda r: -len(r.get("abstract") or ""))
    for r in rows:
        d, t = norm_doi(r.get("doi")), norm_title(r.get("title"))
        if (d and d in by_doi) or (t and t in by_title):
            dropped.append(r); continue
        if d:
            by_doi[d] = r
        if t:
            by_title[t] = r
        keep.append(r)
    with open(os.path.join(P, dst), "w") as f:
        for r in keep:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    rep = {"input": len(rows), "kept": len(keep), "dropped": len(dropped),
           "dropped_examples": [(r.get("title") or "")[:90] for r in dropped[:10]]}
    json.dump(rep, open(os.path.join(P, "dedup_screened_report.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(rep, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
