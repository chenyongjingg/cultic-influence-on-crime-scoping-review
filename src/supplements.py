#!/usr/bin/env python3
"""Generate supplementary tables from the artefacts that actually ran."""
import json, os, csv, collections

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "out", "supplements")


def main():
    os.makedirs(OUT, exist_ok=True)
    counts = json.load(open(os.path.join(ROOT, "data", "counts.json")))
    comp = json.load(open(os.path.join(P, "compose_report.json")))

    # ---- S2 search strategy and per-source counts
    lines = ["# Table S2. Search strategy, per-source counts and dates\n",
             "Execution date: %s" % counts.get("query_spec_sha256", "")[:0] or "",
             "Query specification sha256: `%s`\n" % counts.get("query_spec_sha256", ""),
             "| Source | Query (abridged) | Reported total | Retrieved |", "|---|---|---|---|"]
    for s, v in counts.get("sources", {}).items():
        q = str(v.get("query", ""))[:160].replace("|", "/")
        lines.append("| %s | `%s` | %s | %s |" % (s, q, v.get("reported_total", "—"), v.get("retrieved", "—")))
    lines.append("\n## Composition chain\n")
    for k, v in comp.items():
        if k.startswith("raw_rows_per_file"):
            continue
        lines.append("- %s: %s" % (k, v))
    open(os.path.join(OUT, "S2_search_and_counts.md"), "w").write("\n".join(lines))

    # ---- S4 extraction table (one row per record, flags + anchors)
    src = os.path.join(P, "extracted.jsonl")
    if os.path.exists(src):
        rows = [json.loads(l) for l in open(src)]
        keys = ["C1_group_def", "C2_role", "C3_duration", "C4_mechanism", "C5_instrument",
                "C6_offence", "C7_severity", "C8_legal", "C9_jurisdiction", "C10_source",
                "C11_comparison", "C12_n"]
        with open(os.path.join(OUT, "S4_extraction.csv"), "w", newline="", encoding="utf8") as f:
            w = csv.writer(f)
            w.writerow(["id", "db", "year", "title"] + keys + [k + "_anchor" for k in keys])
            for r in rows:
                e = r.get("extraction") or {}
                w.writerow([r.get("id"), r.get("db"), r.get("year"), (r.get("title") or "")[:200]]
                           + [e.get(k, {}).get("v") for k in keys]
                           + [e.get(k, {}).get("q") for k in keys])
    print("SUPPLEMENTS_DONE", OUT)


if __name__ == "__main__":
    main()
