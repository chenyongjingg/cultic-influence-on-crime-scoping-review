#!/usr/bin/env python3
"""Completion self-check (protocol §3.11 engineering requirements).

Checks that the numbers a reader will see are internally consistent, that the
PRISMA chain adds up, and that no artefact is missing. It fails loudly instead of
printing a tick: a green check with no assertion behind it is worse than no check.
"""
import json, os, sys, math

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
fails, warns = [], []


def ok(cond, msg):
    if cond:
        print("  PASS  %s" % msg)
    else:
        fails.append(msg)
        print("  FAIL  %s" % msg)


def main():
    print("1. per-source counts vs raw files")
    a = json.load(open(os.path.join(P, "analysis.json")))
    ident = a["prisma"]["identification"]
    total = 0
    for name, v in ident.items():
        fp = os.path.join(ROOT, "data", "raw", name + ".jsonl")
        n = sum(1 for line in open(fp) if line.strip()) if os.path.exists(fp) else -1
        ok(n == v["retrieved"], "%s: file=%d analysis=%d" % (name, n, v["retrieved"]))
        total += v["retrieved"]
    ok(total == a["prisma"]["records_retrieved_total"],
       "sum of sources %d == records_retrieved_total %d" % (total, a["prisma"]["records_retrieved_total"]))

    print("2. PRISMA chain arithmetic")
    pr = a["prisma"]
    ok(pr["unique_after_cross_db_dedup"] - pr["excluded_year"] - pr["excluded_language"]
       - pr["excluded_no_base_block"] == pr["screened"],
       "unique - year - language - no_base_block == screened (%d)" % pr["screened"])
    adj = a.get("adjudication") or {}
    ok(pr["auto_excluded_conf_ge_090"] + pr["advanced_to_second_pass"]
       + adj.get("model_INCLUDE_kept", 0) == pr["screened"],
       "auto + advanced + kept == screened (%d + %d + %s vs %d)"
       % (pr["auto_excluded_conf_ge_090"], pr["advanced_to_second_pass"],
          adj.get("model_INCLUDE_kept"), pr["screened"]))
    ok(pr["second_pass_included"] + pr["second_pass_excluded"] == pr["advanced_to_second_pass"],
       "second-pass included + excluded == advanced")
    ok(adj.get("model_INCLUDE_kept", -1) + pr["second_pass_included"] == pr["final_included"],
       "model INCLUDE kept (%s) + second-pass included (%d) == final (%d)"
       % (adj.get("model_INCLUDE_kept"), pr["second_pass_included"], pr["final_included"]))
    cc = adj.get("chain_check") or {}
    ok(cc.get("auto_plus_advanced_plus_kept") == cc.get("screened"),
       "auto + advanced + kept (%s) == screened (%s)"
       % (cc.get("auto_plus_advanced_plus_kept"), cc.get("screened")))

    print("3. construct table denominators")
    ct = a["construct_table"]
    Ns = {r["N"] for r in ct}
    ok(len(Ns) == 1, "one denominator across constructs: %s" % Ns)
    for r in ct:
        ok(r["n_reported_verified"] <= r["N"], "%s n<=N" % r["construct"])

    print("4. numeric hygiene")
    def walk(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + "[%d]" % i)
        elif isinstance(o, float):
            if math.isnan(o) or math.isinf(o):
                fails.append("non-finite at %s" % path)
    walk(a)
    ok(not [f for f in fails if f.startswith("non-finite")], "no NaN/inf in analysis.json")

    print("5. artefacts present")
    for f in ("data/processed/included.jsonl", "data/processed/extracted.jsonl",
              "data/processed/experiments.json", "data/processed/m8_m10.json",
              "data/raw_manifest.json"):
        fp = os.path.join(ROOT, f)
        ok(os.path.exists(fp) and os.path.getsize(fp) > 100, "%s exists (>100 B)" % f)
    if not os.path.exists(os.path.join(P, "e5.json")):
        warns.append("E5 not run (14B comparison missing)")

    if warns:
        print("\nWARNINGS")
        for w in warns:
            print("  !", w)
    print("\n%d checks failed" % len(fails))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
