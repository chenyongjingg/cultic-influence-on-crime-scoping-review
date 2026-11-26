#!/usr/bin/env python3
"""Paired comparison: the same record measured on its abstract, on a length-matched
window of its full text, and on the whole full text.

Why the middle column exists.  A full text is tens of times longer than an abstract,
so any detector that fires on a keyword fires more often there — the raw "lift" from
abstract to full text would be partly a length effect and would make the field look
better reported than it is.  A window matched to the abstract's length, drawn from
the body rather than the opening (where the abstract is usually repeated), holds
length roughly constant: if a construct rises across that control as well, the rise
is about the document, not about the word count.

The unit is the record, so the comparison cannot be confounded by differences between
papers. What it cannot rule out is selection, so the abstract-level profile of the
retrieved subset is printed next to the corpus profile.
"""
import hashlib, json, os, re, sys

if os.path.isdir("/root/cultcrime"):
    ROOT = "/root/cultcrime"
    P = os.path.join(ROOT, "data", "processed")
    FT = os.path.join(ROOT, "data", "fulltext")
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")
    FT = os.path.join(ROOT, "out", "server_snapshot", "data", "fulltext")
sys.path.insert(0, os.path.join(ROOT, "src"))
import measure as M

KEYS = ["C1_group_def", "C2_role", "C3_duration", "C4_mechanism", "C5_instrument",
        "C6_offence", "C7_severity", "C8_legal", "C9_jurisdiction", "C10_source",
        "C11_comparison", "C12_n"]


def text_path(rid):
    return os.path.join(FT, "%s.txt" % hashlib.sha256(str(rid).encode()).hexdigest()[:16])


def measure(text):
    return {k: bool(fn(text)[0]) for k, fn in M.DETECTORS.items()}


def main():
    inc = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(P, "included.jsonl"), encoding="utf8")}
    rows = []
    for line in open(os.path.join(FT, "fetch.jsonl"), encoding="utf8"):
        r = json.loads(line)
        if not r.get("fulltext_measure"):
            continue
        fp = text_path(r["id"])
        if not os.path.exists(fp):
            continue
        txt = open(fp, encoding="utf8").read()
        src = inc.get(r["id"]) or {}
        abs_len = max(400, len(src.get("abstract") or ""))
        start = int(len(txt) * 0.35)
        window = txt[start:start + abs_len] or txt[:abs_len]
        r["window_measure"] = measure(window)
        r["window_chars"] = len(window)
        rows.append(r)

    n = len(rows)
    if not n:
        print("no full texts retrieved yet")
        return
    all_inc = [json.loads(l) for l in open(os.path.join(P, "extracted.jsonl"), encoding="utf8")
               if json.loads(l).get("extraction")]
    N_all = len(all_inc)

    out = {"n_pairs": n, "corpus_n": N_all, "per_construct": {}}
    print("Paired comparison on %d records (corpus %d)\n" % (n, N_all))
    print("%-16s %10s %10s %10s   %8s %8s" %
          ("construct", "abstract", "window", "fulltext", "lift-vs-win", "lift-vs-full"))
    for k in KEYS:
        a = sum(1 for r in rows if r["abstract_measure"].get(k, {}).get("v"))
        w = sum(1 for r in rows if r["window_measure"].get(k))
        f = sum(1 for r in rows if r["fulltext_measure"].get(k, {}).get("v"))
        corpus = sum(1 for r in all_inc if r["extraction"].get(k, {}).get("v") is True)
        ap, wp, fp_ = 100 * a / n, 100 * w / n, 100 * f / n
        cp = 100 * corpus / N_all if N_all else 0
        out["per_construct"][k] = {
            "abstract_n": a, "window_n": w, "fulltext_n": f,
            "abstract_pct": round(ap, 1), "window_pct": round(wp, 1),
            "fulltext_pct": round(fp_, 1),
            "lift_window_pp": round(wp - ap, 1), "lift_full_pp": round(fp_ - ap, 1),
            "corpus_abstract_pct": round(cp, 1), "subset_drift_pp": round(ap - cp, 1)}
        print("%-16s %6d/%-3d %6d/%-3d %6d/%-3d   %+7.1f %+8.1f" %
              (k, a, n, w, n, f, n, wp - ap, fp_ - ap))

    out["availability_pct"] = round(100.0 * n / N_all, 1) if N_all else 0
    out["median_fulltext_chars"] = int(sorted(r.get("chars", 0) for r in rows)[n // 2])
    print("\nfull text obtainable for %d of %d included records (%.1f%%)"
          % (n, N_all, out["availability_pct"]))
    json.dump(out, open(os.path.join(P, "fulltext_lift.json"), "w"), indent=1, ensure_ascii=False)
    print("FULLTEXT_COMPARE_DONE")


if __name__ == "__main__":
    main()
