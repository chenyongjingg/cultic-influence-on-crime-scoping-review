#!/usr/bin/env python3
"""Build the short human-audit worksheet from the S9 flag lists.

Thirty rows, not six hundred and twenty-nine. Each row is a record the automated
audit could not confirm: either every group term in its text is metaphorical, or
neither its title nor the model's own quoted evidence names a group. The columns
the auditor fills are blank.

The file is a form, not a result. Until `author_verdict` is filled, nothing here
changes the manuscript's numbers.
"""
import csv, io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")
AUDIT = os.path.join(ROOT, "out", "data", "screening_audit.json")
CSV_OUT = os.path.join(ROOT, "out", "supplements", "S10_human_audit.csv")
MD_OUT = os.path.join(ROOT, "out", "supplements", "S10_human_audit.md")


def main():
    audit = json.load(io.open(AUDIT, encoding="utf8"))
    by = {}
    for l in io.open(os.path.join(P, "screen_14b_dedup.jsonl"), encoding="utf8"):
        r = json.loads(l)
        by[r["id"]] = r

    meta = set(audit["B_metaphor"]["included_ids"])
    nogrp = set(audit["C_no_group_evidence"]["ids"])
    ids = audit["flagged_for_human_read"]["ids"]

    rows = []
    for i in ids:
        r = by[i]
        s = r.get("screen") or {}
        reason = "both" if (i in meta and i in nogrp) else ("metaphor" if i in meta else "no group named")
        rows.append({
            "id": i, "year": r.get("year") or "", "db": r.get("db") or "",
            "title": re.sub(r"<[^>]+>", "", (r.get("title") or "")).replace("\n", " ")[:220],
            "doi": r.get("doi") or "",
            "flagged_because": reason,
            "model_I1": s.get("I1"), "model_I2": s.get("I2"),
            "model_I3": s.get("I3"), "model_I4": s.get("I4"),
            "model_confidence": s.get("confidence"),
            "model_reason": (s.get("reason") or "")[:200],
            "I1_evidence_span": (s.get("I1_q") or "")[:200],
            "abstract": (r.get("abstract") or "").replace("\n", " ")[:1500],
            "author_verdict": "", "author_note": "",
        })

    with io.open(CSV_OUT, "w", encoding="utf8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    L = ["# S10. Human audit of the %d flagged records\n" % len(rows),
         "These are the included records the automated audit (S9) could not confirm. "
         "Each is flagged for one of two reasons: every group term in its text is "
         "metaphorical, or neither its title nor the model's own quoted evidence names "
         "a group.\n",
         "Fill `author_verdict` in the CSV with **INCLUDE** or **EXCLUDE** against the "
         "same four criteria used in S3, and add a one-line note. Nothing in the "
         "manuscript changes until this column is filled.\n",
         "This is an audit of the highest-risk subset, not a random sample: it bounds "
         "the worst case and does not estimate precision.\n"]
    for n, r in enumerate(rows, 1):
        L.append("---\n")
        L.append("### %d. %s" % (n, r["title"]))
        L.append("")
        L.append("*%s, %s, %s* — `%s` — flagged: %s\n"
                 % (r["year"], r["db"], r["doi"] or "no DOI", r["id"], r["flagged_because"]))
        L.append("Model: I1=%s I2=%s I3=%s I4=%s (conf %s) — %s"
                 % (r["model_I1"], r["model_I2"], r["model_I3"], r["model_I4"],
                    r["model_confidence"], r["model_reason"]))
        if r["I1_evidence_span"]:
            L.append("\nI1 span quoted by the model: “%s”" % r["I1_evidence_span"])
        L.append("\n**Abstract.** %s" % (r["abstract"] or "(none)"))
        L.append("\n**Verdict:** ☐ INCLUDE ☐ EXCLUDE    note: ______________________")
        L.append("")
    io.open(MD_OUT, "w", encoding="utf8").write("\n".join(L))
    print("wrote", CSV_OUT, "and", MD_OUT, "rows:", len(rows))


if __name__ == "__main__":
    main()
