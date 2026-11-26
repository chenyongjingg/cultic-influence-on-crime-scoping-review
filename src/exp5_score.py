#!/usr/bin/env python3
"""Score the 14B single-question reading against the hand read, and store the result.

The manuscript quotes precision 0.85 and recall 0.18 for this reading. Those numbers
have to exist in an artefact, not only in the prose, so this script recomputes them
from the two files that carry the underlying cells and writes the result where
analysis.json can pick it up.
"""
import io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")
D = os.path.join(ROOT, "out", "data")
CONS = ["C1_group_def", "C2_role", "C3_duration", "C4_mechanism", "C5_instrument",
        "C6_offence", "C7_severity", "C8_legal", "C9_jurisdiction", "C10_source",
        "C11_comparison", "C12_n"]


def main():
    manual = {int(k): v for k, v in json.load(io.open(os.path.join(D, "exp1_manual.json"),
                                                      encoding="utf8")).items()}
    sample = json.load(io.open(os.path.join(D, "exp1_sample.json"), encoding="utf8"))
    llm = json.load(io.open(os.path.join(D, "exp5_llm_construct.json"), encoding="utf8"))
    by_n = {i + 1: s for i, s in enumerate(sample)}

    per = {k: {"both": 0, "missed": 0, "over": 0, "neither": 0} for k in CONS}
    tp = fn = fp = 0
    for n, mine in manual.items():
        rid = by_n[n]["id"]
        for k in CONS:
            ref = k in mine
            got = bool(llm.get(rid, {}).get(k, False))
            if ref and got: tp += 1; per[k]["both"] += 1
            elif ref: fn += 1; per[k]["missed"] += 1
            elif got: fp += 1; per[k]["over"] += 1
            else: per[k]["neither"] += 1

    out = {"n_records": len(manual),
           "precision": round(tp / (tp + fp), 3) if tp + fp else None,
           "recall": round(tp / (tp + fn), 3) if tp + fn else None,
           "per_construct": {k: {**v,
                                 "precision": round(v["both"] / (v["both"] + v["over"]), 3)
                                 if v["both"] + v["over"] else None,
                                 "recall": round(v["both"] / (v["both"] + v["missed"]), 3)
                                 if v["both"] + v["missed"] else None}
                             for k, v in per.items()}}
    json.dump(out, io.open(os.path.join(P, "exp5_scores.json"), "w", encoding="utf8"),
              indent=1, ensure_ascii=False)
    print("precision", out["precision"], "recall", out["recall"], "over", out["n_records"], "records")


if __name__ == "__main__":
    main()
