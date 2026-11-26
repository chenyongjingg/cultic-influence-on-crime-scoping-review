#!/usr/bin/env python3
"""Exp 3: descriptive stratification (module M5) — by decade and by jurisdiction.

Descriptive only: counts and proportions within strata, no test, no inference.
The question it answers is whether the reporting profile is carried by one stratum.
"""
import json, os, re, collections

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
CONS = ["C1_group_def", "C2_role", "C3_duration", "C4_mechanism", "C5_instrument",
        "C6_offence", "C7_severity", "C8_legal", "C9_jurisdiction", "C10_source",
        "C11_comparison", "C12_n"]

COUNTRY = re.compile(r"\b(United States|USA|U\.S\.|America|United Kingdom|UK|England|"
                     r"Scotland|Wales|Ireland|Canada|Australia|New Zealand|Nigeria|"
                     r"India|China|Japan|Brazil|Italy|Spain|France|Germany|Poland|Russia|"
                     r"Korea|Malaysia|Indonesia|Finland|Estonia|Serbia|Croatia|Mexico|"
                     r"Israel|Iran|Turkey|South Africa|Netherlands|Belgium|Sweden|Norway)\b", re.I)


def main():
    rows = [json.loads(l) for l in open(os.path.join(P, "extracted.jsonl"))
            if json.loads(l).get("extraction")]

    def profile(sub):
        n = len(sub)
        if not n:
            return None
        return {"N": n,
                **{k: {"n": sum(1 for r in sub if r["extraction"].get(k, {}).get("v") is True),
                       "pct": round(100.0 * sum(1 for r in sub
                                                if r["extraction"].get(k, {}).get("v") is True) / n, 1)}
                   for k in CONS}}

    by_decade = {}
    for r in rows:
        y = r.get("year")
        if not y:
            continue
        d = "%d0s" % (int(y) // 10 * 10)
        by_decade.setdefault(d, []).append(r)
    decades = {d: profile(v) for d, v in sorted(by_decade.items())}

    by_jur = collections.defaultdict(list)
    for r in rows:
        txt = (r.get("title") or "") + " " + (r.get("abstract") or "")
        m = COUNTRY.search(txt)
        by_jur[m.group(1).title() if m else "not stated"].append(r)
    jur = {k: profile(v) for k, v in sorted(by_jur.items(), key=lambda kv: -len(kv[1]))[:8]}

    out = {"by_decade": decades, "by_jurisdiction": jur}
    json.dump(out, open(os.path.join(P, "exp3_strata.json"), "w"), indent=1, ensure_ascii=False)

    print("decade      N   offence juris  instrument comparison")
    for d, v in decades.items():
        print("%-10s %3d   %5.1f%% %5.1f%% %8.1f%% %8.1f%%" % (
            d, v["N"], v["C6_offence"]["pct"], v["C9_jurisdiction"]["pct"],
            v["C5_instrument"]["pct"], v["C11_comparison"]["pct"]))
    print()
    print("jurisdiction        N   offence juris  instrument")
    for d, v in jur.items():
        print("%-18s %3d   %5.1f%% %5.1f%% %8.1f%%" % (
            d[:18], v["N"], v["C6_offence"]["pct"], v["C9_jurisdiction"]["pct"],
            v["C5_instrument"]["pct"]))
    print("EXP3_DONE")


if __name__ == "__main__":
    main()
