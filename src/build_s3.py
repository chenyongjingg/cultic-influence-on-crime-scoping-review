#!/usr/bin/env python3
"""Rebuild the screening worksheet (S3) from the corpus that was actually analysed.

One row per screened record, the model's verdicts and supporting spans, the
pipeline's decision, and the author's decision where one was made. The author
column is filled only for the 30 records the full-corpus audit flagged (S9); for
every other record it is blank, and the paper says so.

The worksheet is rebuilt rather than edited because a stale row count is invisible:
the previous file carried 629 rows against a corpus of 628.
"""
import csv, io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")
OUT = os.path.join(ROOT, "out", "supplements", "S3_author_worksheet.csv")
VERDICTS = os.path.join(ROOT, "out", "supplements", "S10_verdicts.csv")


def load(p):
    return [json.loads(l) for l in io.open(p, encoding="utf8")]


def main():
    rows = load(os.path.join(P, "screen_14b_dedup.jsonl"))
    # pipeline_decision is the MACHINE decision (191 records), author_decision the
    # correction; the analysed corpus is the difference. Read the machine set from
    # the pre-audit snapshot, not from the current included.jsonl.
    pre = os.path.join(os.path.dirname(P), "processed.preaudit", "included.jsonl")
    try:
        machine = {r["id"] for r in load(pre)}
    except FileNotFoundError:
        machine = {r["id"] for r in load(os.path.join(P, "included.jsonl"))}
    analysed = {r["id"] for r in load(os.path.join(P, "included.jsonl"))}
    try:
        drop = {r["id"] for r in csv.DictReader(
            io.StringIO(io.open(VERDICTS, encoding="utf-8-sig").read().replace("﻿", "")))
            if r["verdict"].strip().upper() == "EXCLUDE"}
    except FileNotFoundError:
        drop = set()
    notes = {}
    if os.path.exists(VERDICTS):
        for r in csv.DictReader(io.StringIO(io.open(VERDICTS, encoding="utf-8-sig").read().replace("﻿", ""))):
            notes[r["id"]] = (r.get("note") or "").strip()

    with io.open(OUT, "w", encoding="utf8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "db", "year", "title", "journal", "I1", "I2", "I3", "I4",
                    "model_decision", "confidence", "reason",
                    "span_I1", "span_I2", "span_I3", "span_I4",
                    "pipeline_decision", "author_decision", "author_note"])
        for r in rows:
            s = r.get("screen") or {}
            i = r["id"]
            if i in drop:
                author = "EXCLUDE"
            elif i in analysed:
                author = "INCLUDE" if i in notes else ""
            else:
                author = ""
            w.writerow([
                i, r.get("db"), r.get("year"), (r.get("title") or "")[:200],
                (r.get("venue") or r.get("journal") or s.get("journal") or ""),
                s.get("I1"), s.get("I2"), s.get("I3"), s.get("I4"),
                s.get("decision_model") or s.get("decision"), s.get("confidence"),
                (s.get("reason") or "")[:200],
                (s.get("I1_q") or "")[:200], (s.get("I2_q") or "")[:200],
                (s.get("I3_q") or "")[:200], (s.get("I4_q") or "")[:200],
                "included" if i in machine else "excluded",
                author, notes.get(i, ""),
            ])
    print("S3 rows:", len(rows), "| machine included:", len(machine), "| author excluded:", len(drop))


if __name__ == "__main__":
    main()
