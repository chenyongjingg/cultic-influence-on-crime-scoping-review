#!/usr/bin/env python3
"""Apply the author verdicts from S10 and recompute what they touch.

Runs over the 30 flagged records only. Produces the numbers that would replace the
"sensitivity to non-qualifying records" paragraph if the authors decide to change
the corpus, and the numbers that go in the audit sentence if they do not.

It refuses to run while any verdict is blank: a half-filled form that silently
computes over the filled half would understate the audit.

Every change is reported with its sign. An audit that only reports the changes
which flatter the paper is a post-hoc filter with a paper trail; the point of
printing both directions is that the reader can see which way the corpus moved.
"""
import csv, io, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")
FORM = os.path.join(ROOT, "out", "supplements", "S10_human_audit.csv")
OUT_JSON = os.path.join(ROOT, "out", "data", "author_audit.json")
OUT_MD = os.path.join(ROOT, "out", "supplements", "S9b_author_audit.md")

CON = ["C1_group_def", "C2_role", "C3_duration", "C5_instrument", "C8_legal"]


def load_verdicts(rows):
    """Verdicts come from the sidecar the reading script writes, or from the form.

    The sidecar is authoritative when it exists: the reading script never rewrites
    the worksheet, so the abstracts cannot be damaged by a console encoding round
    trip. A later answer for the same id overrides an earlier one, which is what a
    reader who changed their mind expects.
    """
    side = os.path.join(ROOT, "out", "supplements", "S10_verdicts.csv")
    verdicts, notes = {}, {}
    if os.path.exists(side):
        text = io.open(side, encoding="utf-8-sig").read().replace("﻿", "")
        for rec in csv.DictReader(io.StringIO(text)):
            i = (rec.get("id") or "").strip()
            v = (rec.get("verdict") or "").strip().upper()
            if i and v in ("INCLUDE", "EXCLUDE"):
                verdicts[i] = v
                notes[i] = (rec.get("note") or "").strip()
    for r in rows:
        v = (r.get("author_verdict") or "").strip().upper()
        if r["id"] not in verdicts and v in ("INCLUDE", "EXCLUDE"):
            verdicts[r["id"]] = v
            notes[r["id"]] = (r.get("author_note") or "").strip()
    return verdicts, notes


def main():
    rows = list(csv.DictReader(io.open(FORM, encoding="utf-8-sig")))
    verdicts, notes_by_id = load_verdicts(rows)
    for r in rows:
        r["author_verdict"] = verdicts.get(r["id"], "")
        r["author_note"] = notes_by_id.get(r["id"], "")
    blank = [r["id"] for r in rows if not (r.get("author_verdict") or "").strip()]
    if blank:
        sys.exit("%d of %d verdicts still blank; first: %s" % (len(blank), len(rows), blank[0]))
    bad = [r["id"] for r in rows if r["author_verdict"].strip().upper() not in ("INCLUDE", "EXCLUDE")]
    if bad:
        sys.exit("verdict must be INCLUDE or EXCLUDE; bad rows: %s" % bad)

    excluded = {r["id"] for r in rows if r["author_verdict"].strip().upper() == "EXCLUDE"}
    confirmed = {r["id"] for r in rows if r["author_verdict"].strip().upper() == "INCLUDE"}

    # baseline is the MACHINE set, before these exclusions; the analysed corpus
    # already has them removed, so reading it here would compare a set with itself
    pre = os.path.join(os.path.dirname(P), "processed.preaudit", "extracted.jsonl")
    src = pre if os.path.exists(pre) else os.path.join(P, "extracted.jsonl")
    extracted = [json.loads(l) for l in io.open(src, encoding="utf8")]
    meas = [r for r in extracted if (r.get("abstract") or "").strip()]

    def rates(subset):
        n = len(subset)
        out = {}
        for c in CON:
            k = sum(1 for r in subset if (r.get("extraction") or {}).get(c, {}).get("v"))
            out[c] = {"n": k, "N": n, "pct": round(100.0 * k / n, 1) if n else None}
        return out

    base = rates(meas)
    kept = [r for r in meas if r["id"] not in excluded]
    after = rates(kept)
    delta = {c: round(after[c]["pct"] - base[c]["pct"], 1) for c in CON}

    out = {
        "audited": len(rows), "author_excluded": len(excluded), "author_confirmed": len(confirmed),
        "N_included_before": len(extracted), "N_included_after": len(extracted) - len(excluded),
        "measured_N_before": len(meas), "measured_N_after": len(kept),
        "base": base, "after": after, "delta_pp": delta,
        "max_abs_delta_pp": max(abs(v) for v in delta.values()),
        "excluded_ids": sorted(excluded),
        "notes": {r["id"]: r.get("author_note", "") for r in rows},
    }
    json.dump(out, io.open(OUT_JSON, "w", encoding="utf8"), indent=1, ensure_ascii=False)

    L = ["# S9b. Author audit of the flagged records, applied\n",
         "%d records were read; %d were judged not to meet the inclusion criteria and "
         "%d were confirmed.\n" % (len(rows), len(excluded), len(confirmed)),
         "| Construct | Before | After | Change (pp) |", "|---|---|---|---|"]
    for c in CON:
        L.append("| %s | %s (%d/%d) | %s (%d/%d) | %+.1f |"
                 % (c, base[c]["pct"], base[c]["n"], base[c]["N"],
                    after[c]["pct"], after[c]["n"], after[c]["N"], delta[c]))
    L += ["", "Largest absolute change: **%.1f pp**. Included records %d → %d; "
              "abstract-bearing records %d → %d."
          % (out["max_abs_delta_pp"], out["N_included_before"], out["N_included_after"],
             out["measured_N_before"], out["measured_N_after"]), ""]
    io.open(OUT_MD, "w", encoding="utf8").write("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
