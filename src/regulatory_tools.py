#!/usr/bin/env python3
"""Regulatory instruments named in the corpus (§3.5, regulatory half).

Same instrument as the reporting-completeness detectors: documented term lists,
the matched span returned for every flag, and a count over the measurable set only.
A category means the record *names* an instrument of that kind; it does not mean the
instrument was used, applied or evaluated in that record, and the manuscript says so.

No GPU, no new retrieval: this runs on the included records already in hand.
"""
import json, os, re, sys, collections

ROOT = "/root/cultcrime"
if not os.path.exists(ROOT):
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "processed")
P = os.environ.get("PROCESSED_DIR", P)
if not os.path.isdir(P):
    P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")

CATEGORIES = {
    "criminal_prosecution": [
        r"racketeer", r"\bRICO\b", r"criminal prosecution", r"indict", r"criminal tribunal",
        r"prosecut\w* (?:of|against) (?:the )?(?:group|leader|sect|cult)",
        r"criminal code", r"penal code", r"criminal liability",
    ],
    "trafficking_law": [
        r"human trafficking law", r"trafficking (?:statute|violations act|protection)",
        r"\bTVPA\b", r"anti-?trafficking", r"trafficking in persons",
    ],
    "immigration_law": [
        r"immigration (?:law|status|authorit|proceeding|relief)", r"visa", r"asylum",
        r"undocumented", r"deportation", r"residency status",
    ],
    "family_marriage_law": [
        r"child marriage", r"guardianship", r"custody", r"family law", r"marriage law",
        r"parental rights",
    ],
    "charity_religious_regulation": [
        r"charity commission", r"charitable status", r"religious (?:registration|corporation)",
        r"tax[- ]exempt", r"nonprofit status", r"registration of religious",
    ],
    "civil_commitment_mental_health": [
        r"civil commitment", r"involuntary (?:hold|commitment|hospitali)", r"mental health act",
        r"guardianship order", r"fitness to stand trial",
    ],
    "financial_consumer_regulation": [
        r"securities (?:law|regulation|fraud)", r"\bSEC\b", r"financial regulation",
        r"consumer protection", r"money laundering (?:law|regulation|statute)",
        r"tax (?:law|evasion statute)",
    ],
}
ORDER = list(CATEGORIES)


def code(text):
    out = {}
    for cat, pats in CATEGORIES.items():
        hit = None
        for p in pats:
            m = re.search(p, text, re.I)
            if m:
                s = max(0, m.start() - 20)
                hit = re.sub(r"\s+", " ", text[s:m.end() + 40]).strip()
                break
        out[cat] = hit
    return out


def main():
    rows = [json.loads(l) for l in open(os.path.join(P, "extracted.jsonl"), encoding="utf8")
            if json.loads(l).get("extraction")]
    N = len(rows)
    counts = collections.Counter()
    per = []
    for r in rows:
        text = re.sub(r"\s+", " ", ((r.get("title") or "") + ". " + (r.get("abstract") or "")))
        c = code(text)
        named = [k for k, v in c.items() if v]
        for k in named:
            counts[k] += 1
        per.append({"id": r.get("id"), "n_named": len(named), "named": named, "spans": c})
    any_named = sum(1 for x in per if x["n_named"])
    multi = sum(1 for x in per if x["n_named"] >= 2)
    result = {
        "N": N,
        "any_instrument_named": any_named,
        "any_instrument_pct": round(100.0 * any_named / N, 1) if N else 0,
        "two_or_more_named": multi,
        "counts": {k: {"n": counts[k], "pct": round(100.0 * counts[k] / N, 1) if N else 0}
                   for k in ORDER},
    }
    out = {"summary": result, "records": per}
    os.makedirs(os.path.dirname(os.path.join(P, "regulatory_tools.json")), exist_ok=True)
    json.dump(out, open(os.path.join(P, "regulatory_tools.json"), "w", encoding="utf8"),
              indent=1, ensure_ascii=False)
    print("N =", N, "| any instrument named:", any_named, "(%.1f%%)" % result["any_instrument_pct"],
          "| two or more:", multi)
    for k in ORDER:
        print("   %-32s %3d  %5.1f%%" % (k, counts[k], result["counts"][k]["pct"]))


if __name__ == "__main__":
    main()
