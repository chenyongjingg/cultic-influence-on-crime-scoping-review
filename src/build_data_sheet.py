#!/usr/bin/env python3
"""One record-level data sheet instead of three CSV files.

The submission picker makes every attached file a separate upload, and the
record-level tables were four files about the same 628 records. This writes one
CSV: one row per screened record, the screening verdicts and spans in the first
block of columns, the twelve extraction constructs and their anchors in the
second, and the author's decision where one was made. Included records have both
blocks filled; excluded records have only the first.

Nothing is dropped. Column names keep their original prefixes (span_/C*_anchor)
so that any count in the paper can still be recomputed from this file alone.
"""
import csv, io, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")
OUT = os.path.join(ROOT, "out", "supplements", "upload", "Data_S1_record_level_screening_and_extraction.csv")
VERDICTS = os.path.join(ROOT, "out", "supplements", "S10_verdicts.csv")
CONS = ["C1_group_def", "C2_role", "C3_duration", "C4_mechanism", "C5_instrument",
        "C6_offence", "C7_severity", "C8_legal", "C9_jurisdiction", "C10_source",
        "C11_comparison", "C12_n"]


def load(p):
    return [json.loads(l) for l in io.open(p, encoding="utf8")]


def main():
    rows = load(os.path.join(P, "screen_14b_dedup.jsonl"))
    pre = os.path.join(os.path.dirname(P), "processed.preaudit", "included.jsonl")
    machine = {r["id"] for r in load(pre if os.path.exists(pre) else os.path.join(P, "included.jsonl"))}
    analysed = {r["id"] for r in load(os.path.join(P, "included.jsonl"))}
    ext = {r["id"]: (r.get("extraction") or {}) for r in load(os.path.join(P, "extracted.jsonl"))}

    verdicts, notes = {}, {}
    if os.path.exists(VERDICTS):
        t = io.open(VERDICTS, encoding="utf-8-sig").read().replace("﻿", "")
        for rec in csv.DictReader(io.StringIO(t)):
            if rec.get("id"):
                verdicts[rec["id"]] = (rec.get("verdict") or "").strip()
                notes[rec["id"]] = (rec.get("note") or "").strip()

    head = (["id", "db", "year", "title", "venue",
             "I1", "I2", "I3", "I4", "model_decision", "confidence", "reason",
             "span_I1", "span_I2", "span_I3", "span_I4",
             "pipeline_decision", "analysed", "author_decision", "author_note"]
            + CONS + [c + "_anchor" for c in CONS])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf8", newline="") as f:
        w = csv.writer(f)
        w.writerow(head)
        for r in rows:
            s = r.get("screen") or {}
            i = r["id"]
            e = ext.get(i, {})
            w.writerow(
                [i, r.get("db"), r.get("year"), (r.get("title") or "")[:200],
                 r.get("venue") or "", s.get("I1"), s.get("I2"), s.get("I3"), s.get("I4"),
                 s.get("decision_model") or s.get("decision"), s.get("confidence"),
                 (s.get("reason") or "")[:200],
                 (s.get("I1_q") or "")[:200], (s.get("I2_q") or "")[:200],
                 (s.get("I3_q") or "")[:200], (s.get("I4_q") or "")[:200],
                 "included" if i in machine else "excluded",
                 "yes" if i in analysed else "no",
                 verdicts.get(i, ""), notes.get(i, "")]
                + [e.get(c, {}).get("v") for c in CONS]
                + [e.get(c, {}).get("q") for c in CONS])

    n = sum(1 for _ in io.open(OUT, encoding="utf8")) - 1
    print("rows:", n, "| columns:", len(head), "|", OUT)


if __name__ == "__main__":
    main()
