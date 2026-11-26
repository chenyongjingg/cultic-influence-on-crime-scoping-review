#!/usr/bin/env python3
"""Exp 1: compare manual coding (30 records) with the lexical detectors.

Manual codes were made blind to the detector output (the dump omits it). Agreement
is reported per construct as: both, manual-only (detector missed), detector-only
(detector over-fired), neither. Precision and recall are computed against the manual
read treated as reference — with the caveat that a single reader is not a gold
standard, so the numbers are an agreement estimate, not a validation certificate.
"""
import json, os

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
CONS = ["C1_group_def", "C2_role", "C3_duration", "C4_mechanism", "C5_instrument",
        "C6_offence", "C7_severity", "C8_legal", "C9_jurisdiction", "C10_source",
        "C11_comparison", "C12_n"]

MANUAL = {
 1: ["C4_mechanism", "C6_offence"],
 2: ["C6_offence", "C9_jurisdiction"],
 3: ["C4_mechanism", "C6_offence", "C9_jurisdiction", "C10_source", "C12_n"],
 4: ["C1_group_def", "C6_offence", "C9_jurisdiction"],
 5: ["C1_group_def", "C2_role", "C3_duration", "C4_mechanism", "C6_offence",
     "C8_legal", "C9_jurisdiction", "C10_source"],
 6: ["C6_offence"],
 7: ["C1_group_def", "C6_offence", "C9_jurisdiction", "C10_source"],
 8: ["C6_offence", "C8_legal"],
 9: ["C1_group_def", "C2_role", "C6_offence", "C7_severity", "C8_legal",
     "C9_jurisdiction", "C10_source", "C12_n"],
 10: ["C1_group_def", "C6_offence", "C9_jurisdiction"],
 11: ["C1_group_def", "C6_offence"],
 12: ["C6_offence", "C10_source", "C12_n"],
 13: ["C1_group_def", "C2_role", "C6_offence", "C10_source", "C12_n"],
 14: ["C1_group_def", "C2_role", "C6_offence", "C8_legal", "C9_jurisdiction"],
 15: ["C1_group_def", "C6_offence", "C9_jurisdiction"],
 16: ["C1_group_def", "C4_mechanism", "C6_offence", "C8_legal", "C9_jurisdiction"],
 17: ["C1_group_def", "C6_offence", "C8_legal", "C9_jurisdiction", "C10_source"],
 18: ["C1_group_def", "C6_offence", "C9_jurisdiction", "C10_source"],
 19: ["C1_group_def", "C2_role", "C6_offence", "C10_source"],
 20: ["C1_group_def", "C2_role", "C6_offence", "C9_jurisdiction", "C10_source"],
 21: ["C6_offence"],
 22: ["C1_group_def", "C4_mechanism", "C6_offence", "C9_jurisdiction", "C10_source"],
 23: ["C1_group_def", "C6_offence", "C9_jurisdiction"],
 24: ["C1_group_def", "C6_offence", "C8_legal", "C9_jurisdiction"],
 25: ["C1_group_def", "C2_role", "C4_mechanism", "C6_offence", "C8_legal", "C10_source"],
 26: ["C1_group_def", "C6_offence", "C8_legal", "C9_jurisdiction", "C10_source",
      "C11_comparison"],
 27: ["C1_group_def", "C2_role", "C3_duration", "C4_mechanism", "C6_offence",
      "C8_legal", "C9_jurisdiction", "C10_source", "C12_n"],
 28: ["C4_mechanism", "C6_offence", "C9_jurisdiction", "C10_source", "C12_n"],
 29: ["C1_group_def", "C6_offence", "C8_legal", "C9_jurisdiction", "C10_source", "C12_n"],
}


def main():
    sample = json.load(open(os.path.join(P, "exp1_sample.json")))
    by_n = {i + 1: s for i, s in enumerate(sample)}
    rows = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(P, "extracted.jsonl"))
            if json.loads(l).get("extraction")}

    per = {k: {"both": 0, "manual_only": 0, "det_only": 0, "neither": 0} for k in CONS}
    missing = 0
    for n, mine in MANUAL.items():
        rec = rows.get(by_n[n]["id"])
        if rec is None:
            missing += 1
            continue
        for k in CONS:
            det = rec["extraction"].get(k, {}).get("v") is True
            man = k in mine
            key = ("both" if det and man else "manual_only" if man else
                   "det_only" if det else "neither")
            per[k][key] += 1

    n_rec = len(MANUAL) - missing
    out = {"n_records": n_rec, "records_missing": missing, "per_construct": {}}
    print("%-16s %6s %6s %6s %6s   %8s %8s %8s" %
          ("construct", "both", "man", "det", "neith", "precision", "recall", "agree"))
    for k in CONS:
        c = per[k]
        tp = c["both"]
        prec = tp / (tp + c["det_only"]) if (tp + c["det_only"]) else None
        rec_ = tp / (tp + c["manual_only"]) if (tp + c["manual_only"]) else None
        agree = (tp + c["neither"]) / n_rec
        out["per_construct"][k] = {**c,
                                   "precision": round(prec, 2) if prec is not None else None,
                                   "recall": round(rec_, 2) if rec_ is not None else None,
                                   "agreement": round(agree, 2)}
        print("%-16s %6d %6d %6d %6d   %8s %8s %8.2f" %
              (k, tp, c["manual_only"], c["det_only"], c["neither"],
               "-" if prec is None else "%.2f" % prec,
               "-" if rec_ is None else "%.2f" % rec_, agree))
    tp_all = sum(per[k]["both"] for k in CONS)
    det_all = tp_all + sum(per[k]["det_only"] for k in CONS)
    man_all = tp_all + sum(per[k]["manual_only"] for k in CONS)
    out["overall"] = {"precision": round(tp_all / det_all, 3) if det_all else None,
                      "recall": round(tp_all / man_all, 3) if man_all else None,
                      "cells": tp_all + det_all + man_all + sum(per[k]["neither"] for k in CONS)}
    print("\noverall precision=%.3f recall=%.3f over %d records" %
          (out["overall"]["precision"], out["overall"]["recall"], n_rec))
    json.dump(out, open(os.path.join(P, "exp1_detector_validation.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
