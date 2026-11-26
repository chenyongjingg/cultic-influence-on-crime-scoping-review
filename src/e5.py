#!/usr/bin/env python3
"""E5: agreement between the 7B and 14B screening layers, on the same records.

Reports percent agreement and Cohen's kappa for the decision and for each
criterion bit.  Kappa is used only to describe how much of the agreement exceeds
chance; it is not used to adjudicate which model is right — that would need a
human reference set, which the protocol does not have and this run does not
invent.
"""
import json, os, sys, collections

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")


def load(name):
    return [json.loads(l) for l in open(os.path.join(P, name)) if l.strip()]


def kappa(pairs):
    n = len(pairs)
    if not n:
        return None, None
    agree = sum(1 for a, b in pairs if a == b) / n
    labels = {a for a, _ in pairs} | {b for _, b in pairs}
    po = agree
    pe = 0.0
    for L in labels:
        pa = sum(1 for a, _ in pairs if a == L) / n
        pb = sum(1 for _, b in pairs if b == L) / n
        pe += pa * pb
    k = (po - pe) / (1 - pe) if pe < 1 else 0.0
    return round(100 * agree, 1), round(k, 3)


def main():
    a = {r.get("id"): r for r in load("screen_7b.jsonl") if (r.get("screen") or {}).get("decision")}
    b = {r.get("id"): r for r in load("screen_14b.jsonl") if (r.get("screen") or {}).get("decision")}
    common = sorted(set(a) & set(b))
    if not common:
        print("E5: no overlapping records — 14B pass not run yet")
        return
    import random
    n = min(50, len(common))
    common = sorted(random.Random(20261126).sample(common, n))
    out = {"n": n, "overlap_available": len(set(a) & set(b))}
    dpairs = [(a[i]["screen"]["decision"], b[i]["screen"]["decision"]) for i in common]
    out["decision"] = dict(zip(("agree_pct", "kappa"), kappa(dpairs)))
    out["decision_confusion"] = {f"{x}->{y}": c for (x, y), c in
                                 collections.Counter(dpairs).items()}
    for k in ("I1", "I2", "I3", "I4"):
        pairs = [(bool((a[i]["screen"] or {}).get(k)), bool((b[i]["screen"] or {}).get(k)))
                 for i in common]
        ag, kp = kappa(pairs)
        out[k] = {"agree_pct": ag, "kappa": kp,
                  "both_true": sum(1 for x, y in pairs if x and y),
                  "both_false": sum(1 for x, y in pairs if not x and not y)}
    inc_a = sum(1 for i in common if a[i]["screen"]["decision"] == "INCLUDE")
    inc_b = sum(1 for i in common if b[i]["screen"]["decision"] == "INCLUDE")
    out["include_counts"] = {"7B": inc_a, "14B": inc_b}
    json.dump(out, open(os.path.join(P, "e5.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))
    print("E5_DONE")


if __name__ == "__main__":
    main()
