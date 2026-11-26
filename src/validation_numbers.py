#!/usr/bin/env python3
"""Numbers that come from the 25-record validation read, computed rather than typed.

Three quantities in the manuscript depend on that read and were previously written by
hand: the Y/M/N tally, the mean constructs reported by the non-qualifying records, and
the offence-type and jurisdiction rates with those records removed. Each is recomputed
here from the corpus and the recorded verdicts, and written where analysis.json can pick
it up, so a change in the corpus cannot leave the prose behind.

The verdicts live in supplements/S7_validation_read.md as a markdown table. That table is
parsed rather than re-typed: it is the record of the read.
"""
import io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")
OUT = os.path.join(ROOT, "out", "data", "validation_numbers.json")
S7 = os.path.join(ROOT, "out", "supplements", "S7_validation_read.md")
CONS = ["C1_group_def", "C2_role", "C3_duration", "C4_mechanism", "C5_instrument",
        "C6_offence", "C7_severity", "C8_legal", "C9_jurisdiction", "C10_source",
        "C11_comparison", "C12_n"]


def parse_s7():
    s = io.open(S7, encoding="utf8").read()
    verdicts = {}
    for line in s.split("\n"):
        m = re.match(r"^\|\s*(\d+)\s*\|\s*([^|]+)\|\s*(Y|M|N)\s*\|", line)
        if m:
            verdicts[int(m.group(1))] = (m.group(2).strip(), m.group(3))
    return verdicts


def main():
    verdicts = parse_s7()
    tally = {k: sum(1 for v in verdicts.values() if v[1] == k) for k in "YMN"}
    rows = [json.loads(l) for l in io.open(os.path.join(P, "extracted.jsonl"), encoding="utf8")
            if json.loads(l).get("extraction")]
    N = len(rows)

    def ntrue(r):
        return sum(1 for k in CONS if r["extraction"].get(k, {}).get("v") is True)

    # match the non-qualifying titles back to corpus records: S7 carries a short label,
    # not an identifier, so the match is fuzzy and every match is reported with its score
    import difflib
    def norm(x):
        return re.sub(r"[^a-z0-9]+", " ", (x or "").lower()).strip()
    # Two S7 labels are too short or too translated for a title match to find them; the
    # records were located by hand and their identifiers are recorded here rather than
    # loosening the threshold until something matched.
    MANUAL_IDS = {
        "Taxi Driver II (critical communication theory)": "407584552",
        "Judicial competence for military priests": "eeab33b2d1efa9834c43aad47e12edb233156c4a",
    }
    nonq, unmatched, matched = [], [], []
    for n, (label, verdict) in sorted(verdicts.items()):
        if verdict != "N":
            continue
        if label in MANUAL_IDS:
            nonq.append(MANUAL_IDS[label]); matched.append((n, MANUAL_IDS[label], "manual")); continue
        probe = norm(re.sub(r"\([^)]*\)", " ", label))
        best, score = None, 0.0
        for r in rows:
            sc = difflib.SequenceMatcher(None, probe, norm((r.get("title") or "")[:70])).ratio()
            if sc > score:
                best, score = r, sc
        if best is not None and score >= 0.55:
            nonq.append(best["id"]); matched.append((n, best["id"], round(score, 2)))
        else:
            unmatched.append((label[:40], round(score, 2)))

    corpus_mean = round(sum(ntrue(r) for r in rows) / N, 2) if N else None
    nonq_mean = round(sum(ntrue(r) for r in rows if r["id"] in set(nonq)) / len(nonq), 2) if nonq else None

    rest = [r for r in rows if r["id"] not in set(nonq)]
    M = len(rest)

    def rate(sub, key):
        return round(100.0 * sum(1 for r in sub if r["extraction"].get(key, {}).get("v") is True) / len(sub), 1) if sub else None

    sub_nonq = [r for r in rows if r["id"] in set(nonq)]
    out = {"nonqualifying_jurisdiction_n": sum(1 for r in sub_nonq if r["extraction"].get("C9_jurisdiction", {}).get("v") is True),
           "tally": tally, "n_read": len(verdicts),
           "precision_low_pct": round(100 * tally["Y"] / len(verdicts), 0),
           "precision_high_pct": round(100 * (tally["Y"] + tally["M"]) / len(verdicts), 0),
           "nonqualifying_matched": len(nonq), "matches": matched,
           "nonqualifying_unmatched": unmatched,
           "corpus_mean_constructs": corpus_mean,
           "nonqualifying_mean_constructs": nonq_mean,
           "offence_corpus_pct": rate(rows, "C6_offence"),
           "offence_without_pct": rate(rest, "C6_offence"),
           "jurisdiction_corpus_pct": rate(rows, "C9_jurisdiction"),
           "jurisdiction_without_pct": rate(rest, "C9_jurisdiction"),
           "N": N, "N_without_nonqualifying": M}
    json.dump(out, io.open(OUT, "w", encoding="utf8"), indent=1, ensure_ascii=False)
    for k, v in out.items():
        print("%-30s %s" % (k, v))


if __name__ == "__main__":
    main()
