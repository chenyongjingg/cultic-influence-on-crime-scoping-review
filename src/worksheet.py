#!/usr/bin/env python3
"""Build the author-adjudication worksheet and the §8.2 precheck sample.

Worksheet: one row per screened record with the model's verdicts, the spans that
supported them, the rule that was applied, and empty columns for the author. A
blank column is the point — the manuscript's numbers are the machine record until
someone fills it.

Precheck sample: 50 records drawn half from what the pipeline included and half
from what it auto-excluded, so that the same reading estimates both precision
(are the included records on topic?) and false-negative risk (were any excluded
records on topic?). Written as markdown for reading.
"""
import json, os, random, csv

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "out", "supplements")


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = [json.loads(l) for l in open(os.path.join(P, "screen_pass1.jsonl"))]
    inc = {r.get("id") for r in (json.loads(l) for l in open(os.path.join(P, "included.jsonl")))}
    auto = [r for r in rows
            if (r.get("screen") or {}).get("decision") == "EXCLUDE"
            and float((r.get("screen") or {}).get("confidence") or 0) >= 0.90
            and r.get("id") not in inc]

    # ---- worksheet
    with open(os.path.join(OUT, "S3_author_worksheet.csv"), "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(["id", "db", "year", "title", "journal", "I1", "I2", "I3", "I4",
                    "model_decision", "confidence", "reason",
                    "span_I1", "span_I2", "span_I3", "span_I4",
                    "pipeline_decision", "author_decision", "author_note"])
        for r in rows:
            s = r.get("screen") or {}
            w.writerow([
                r.get("id"), r.get("db"), r.get("year"), (r.get("title") or "")[:200],
                (r.get("source") or "")[:80],
                s.get("I1"), s.get("I2"), s.get("I3"), s.get("I4"),
                s.get("decision_model") or s.get("decision"), s.get("confidence"),
                (s.get("reason") or "")[:160],
                (s.get("I1_q") or "")[:160], (s.get("I2_q") or "")[:160],
                (s.get("I3_q") or "")[:160], (s.get("I4_q") or "")[:160],
                "included" if r.get("id") in inc else "excluded", "", ""])

    # ---- precheck sample
    rnd = random.Random(20261126)
    inc_rows = [r for r in rows if r.get("id") in inc]
    sample_inc = rnd.sample(inc_rows, min(25, len(inc_rows)))
    sample_auto = rnd.sample(auto, min(25, len(auto)))
    md = ["# §8.2 precheck sample\n",
          "25 records the pipeline included and 25 it auto-excluded, drawn at random "
          "with seed 20261126. Read order is randomised so that the two groups are not "
          "separable while reading.\n"]
    items = [(r, "included") for r in sample_inc] + [(r, "auto-excluded") for r in sample_auto]
    rnd.shuffle(items)
    for i, (r, grp) in enumerate(items, 1):
        s = r.get("screen") or {}
        md.append("## %d. %s (%s)\n" % (i, (r.get("title") or "").strip(), r.get("year")))
        md.append("*%s* · %s · pipeline: %s\n" % (r.get("source") or "—", r.get("db"), grp))
        ab = (r.get("abstract") or "").strip()
        md.append((ab[:1400] + (" […]" if len(ab) > 1400 else "")) or "*(no abstract)*")
        md.append("\n\n> model: %s (%.2f) — %s\n" % (s.get("decision_model") or s.get("decision"),
                                                     float(s.get("confidence") or 0),
                                                     (s.get("reason") or "")[:140]))
    open(os.path.join(OUT, "S6_precheck_sample.md"), "w", encoding="utf8").write("\n".join(md))
    print("worksheet rows:", len(rows), "sample:", len(items))


if __name__ == "__main__":
    main()
