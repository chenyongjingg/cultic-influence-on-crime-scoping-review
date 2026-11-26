#!/usr/bin/env python3
"""Exp 1 support: draw 30 records for manual detector validation.

Records are drawn at random (seed 20261126) from the measurable set, so the sample
is not weighted towards records that either pass or fail many detectors.
The dump deliberately omits the detector outputs; the read has to be independent.
"""
import json, os, random

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
rows = [json.loads(l) for l in open(os.path.join(P, "extracted.jsonl")) if json.loads(l).get("extraction")]
rnd = random.Random(20261126)
sample = rnd.sample(rows, 30)
out = []
for i, r in enumerate(sample, 1):
    ab = (r.get("abstract") or "").strip()
    out.append({"n": i, "id": r.get("id"), "title": (r.get("title") or "")[:150],
                "abstract": ab[:1100]})
json.dump(out, open(os.path.join(P, "exp1_sample.json"), "w"), indent=1, ensure_ascii=False)
for o in out:
    print("### %d" % o["n"])
    print(o["title"])
    print(o["abstract"])
    print()
