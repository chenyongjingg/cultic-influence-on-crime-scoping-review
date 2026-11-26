#!/usr/bin/env python3
"""Exp 4: how far do the percentages move if the term lists are cut differently?

For the five constructs most exposed to term-list discretion, a stricter variant is
defined — only the terms and rules that would survive a sceptical reviewer — and the
proportion is recomputed. The reported quantity is the delta. A construct whose
proportion moves by a few points is robust to the vocabulary choice; one that halves
is a vocabulary artefact and must be described as such.
"""
import json, os, re

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
import sys
sys.path.insert(0, os.path.join(ROOT, "src"))
import measure as M


def strict_offence(t):
    terms = ["homicide", "murder", "manslaughter", "assassination", "massacre",
             "rape", "sexual assault", "incest", "trafficking", "slavery",
             "fraud", "embezzlement", "kidnapping", "abduction", "terrorism",
             "arson", "assault"]
    return any(re.search(r"\b" + re.escape(x) + r"\b", t, re.I) for x in terms)


def strict_jurisdiction(t):
    # require a jurisdictional frame, not a bare country mention
    pats = [r"\b(?:in|of|under|within)\s+(?:the\s+)?(" + "|".join(map(re.escape, M.COUNTRIES)) + r")\b",
            r"\b(" + "|".join(map(re.escape, M.COUNTRIES)) + r")\s+(?:law|courts?|penal|legal system|jurisdiction)\b"]
    return any(re.search(p, t, re.I) for p in pats)


def strict_legal(t):
    terms = ["convicted", "conviction", "acquitted", "acquittal", "sentenced",
             "verdict", "judgment", "judgement", "found guilty", "not guilty",
             "criminal responsibility", "insane", "insanity", "prosecution", "indicted"]
    return any(re.search(r"\b" + re.escape(x) + r"\b", t, re.I) for x in terms)


def strict_source(t):
    pats = [r"data (were|was) collected", r"we collected", r"were recruited",
            r"sample of", r"case files?", r"court records?", r"medical records?",
            r"interviews? with", r"we interviewed", r"survey of", r"archival",
            r"ethnograph", r"fieldwork", r"self-report"]
    return any(re.search(p, t, re.I) for p in pats)


def strict_mechanism(t):
    terms = ["indoctrination", "thought reform", "mind control", "brainwashing",
             "coercive control", "milieu control", "thought stopping", "love bombing",
             "trauma bonding", "undue influence"]
    return any(re.search(r"\b" + re.escape(x) + r"\b", t, re.I) for x in terms)


VARIANTS = {"C4_mechanism": strict_mechanism, "C6_offence": strict_offence,
            "C8_legal": strict_legal, "C9_jurisdiction": strict_jurisdiction,
            "C10_source": strict_source}


def main():
    rows = [json.loads(l) for l in open(os.path.join(P, "extracted.jsonl"))
            if json.loads(l).get("extraction")]
    N = len(rows)
    out = {"N": N, "constructs": {}}
    print("%-16s %-14s %-14s %s" % ("construct", "base", "strict", "delta (pp)"))
    for k, fn in VARIANTS.items():
        base = sum(1 for r in rows if r["extraction"].get(k, {}).get("v") is True)
        strict = 0
        for r in rows:
            t = re.sub(r"\s+", " ", ((r.get("title") or "") + ". " + (r.get("abstract") or "")))
            if fn(t):
                strict += 1
        bp, sp = 100.0 * base / N, 100.0 * strict / N
        out["constructs"][k] = {"base_n": base, "strict_n": strict,
                                "base_pct": round(bp, 1), "strict_pct": round(sp, 1),
                                "delta_pp": round(sp - bp, 1)}
        print("%-16s %-14s %-14s %+.1f" % (k, "%d/%d (%.1f%%)" % (base, N, bp),
                                           "%d/%d (%.1f%%)" % (strict, N, sp), sp - bp))
    json.dump(out, open(os.path.join(P, "exp4_terms.json"), "w"), indent=1, ensure_ascii=False)
    print("EXP4_DONE")


if __name__ == "__main__":
    main()
