#!/usr/bin/env python3
"""Sensitivity experiments E1–E4 (protocol V1.6 §3.11).

All four run on artefacts already produced; none retrieves anything new.  Each
writes a JSON block into data/processed/experiments.json and prints a table.

E1  confidence-threshold sweep for automatic exclusion
E2  I1 conjunctive vs disjunctive
E3  per-source independent contribution and topical composition
E4  year / language restriction sensitivity
"""
import json, os, re, collections

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
OUT = {}


def load(p):
    with open(os.path.join(ROOT, p)) as f:
        return [json.loads(l) for l in f if l.strip()]


def e1(screen_rows):
    """Replay the auto-exclusion rule at a range of confidence thresholds."""
    base = []
    for r in screen_rows:
        s = r.get("screen")
        if not s:
            continue
        base.append((str(s.get("decision", "")).upper(), float(s.get("confidence") or 0),
                     bool(s.get("I1"))))
    res = []
    for thr in (0.60, 0.70, 0.80, 0.85, 0.90, 0.95, 1.00):
        auto = sum(1 for d, c, _ in base if d == "EXCLUDE" and c >= thr)
        # records that would survive to the second pass: everything not auto-excluded
        res.append({"threshold": thr, "auto_excluded": auto,
                    "advanced": len(base) - auto,
                    "advanced_pct": round(100.0 * (len(base) - auto) / len(base), 1)})
    return {"n": len(base), "sweep": res}


def e2(screen_rows, included_ids):
    """Conjunctive (lexical group anchor AND model I1) vs disjunctive (model I1 only)."""
    SECT = re.compile(r"\b(cult|cults|cultic|sect|sects|high.control group|high demand group|"
                      r"destructive cult|new religious movement|new religious movements|"
                      r"charismatic group|commune)\b", re.I)
    conj = set(included_ids)
    disj = set()
    for r in screen_rows:
        s = r.get("screen") or {}
        if not s:
            continue
        txt = (r.get("title") or "") + " " + (r.get("abstract") or "")
        if bool(s.get("I1")) and bool(SECT.search(txt)):
            conj.add(r.get("id"))
        if bool(s.get("I1")):
            disj.add(r.get("id"))
    # classify the extra records a disjunctive rule would admit
    by = {r.get("id"): r for r in screen_rows}
    extra = disj - conj
    mech = re.compile(r"(coercive control|intimate partner|domestic (violence|abuse)|"
                      r"commercial sexual|trafficking|nerve agent|chemical weapon)", re.I)
    kinds = collections.Counter()
    for i in extra:
        t = ((by.get(i) or {}).get("title") or "") + " " + ((by.get(i) or {}).get("abstract") or "")
        kinds["IPV/exploitation/other non-group" if mech.search(t) else "other"] += 1
    return {"conjunctive_n": len(conj), "disjunctive_n": len(disj),
            "extra_if_disjunctive": len(extra), "extra_composition": dict(kinds)}


def e3():
    """Per-source independent contribution and topical composition."""
    db_of = {}
    top = collections.defaultdict(set)
    for f in sorted(os.listdir(os.path.join(ROOT, "data", "raw"))):
        if not f.endswith(".jsonl"):
            continue
        db = f[:-6]
        for line in open(os.path.join(ROOT, "data", "raw", f)):
            r = json.loads(line)
            key = (r.get("doi") or "").lower().strip() or (r.get("title") or "").strip().lower()
            if not key:
                continue
            db_of.setdefault(key, set()).add(db)
            top[db].add(key)
    n_by_db = {db: len(v) for db, v in top.items()}
    exclusive = {db: len([k for k in v if db_of[k] == {db}]) for db, v in top.items()}
    return {"records_per_source_raw": n_by_db, "source_exclusive_records": exclusive,
            "n_unique_overall": len(db_of)}


def e4(compose_report):
    return {k: compose_report.get(k) for k in
            ("unique_after_dedup", "after_year_1994_2026", "after_language",
             "excluded_year", "excluded_language", "language_breakdown",
             "tierP", "tierS_only", "without_abstract")}


def main():
    rows = load("data/processed/screen_pass1.jsonl") if os.path.exists(
        os.path.join(P, "screen_pass1.jsonl")) else []
    inc = load("data/processed/included.jsonl") if os.path.exists(
        os.path.join(P, "included.jsonl")) else []
    inc_ids = [r.get("id") for r in inc]
    comp = json.load(open(os.path.join(P, "compose_report.json")))

    OUT["E1_confidence_threshold"] = e1(rows) if rows else {"status": "no screen file"}
    OUT["E2_i1_conjunction"] = e2(rows, inc_ids) if rows else {"status": "no screen file"}
    OUT["E3_source_contribution"] = e3()
    OUT["E4_restriction_sensitivity"] = e4(comp)

    json.dump(OUT, open(os.path.join(P, "experiments.json"), "w"), indent=1, ensure_ascii=False)

    if rows:
        print("E1 confidence sweep (n=%d)" % OUT["E1_confidence_threshold"]["n"])
        for r in OUT["E1_confidence_threshold"]["sweep"]:
            print("   thr=%.2f  auto-excluded=%-4d advanced=%-4d (%.1f%%)"
                  % (r["threshold"], r["auto_excluded"], r["advanced"], r["advanced_pct"]))
        e = OUT["E2_i1_conjunction"]
        print("E2 conjunctive=%d disjunctive=%d extra=%d %s"
              % (e["conjunctive_n"], e["disjunctive_n"], e["extra_if_disjunctive"],
                 e["extra_composition"]))
    print("E3 per-source raw:", OUT["E3_source_contribution"]["records_per_source_raw"])
    print("E3 exclusive:", OUT["E3_source_contribution"]["source_exclusive_records"])
    print("EXPERIMENTS_DONE")


if __name__ == "__main__":
    main()
