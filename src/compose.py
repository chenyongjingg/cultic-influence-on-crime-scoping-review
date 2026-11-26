#!/usr/bin/env python3
"""Compose stage: deduplicate, restrict, assign tier + nested-block flags.

Counting rules implemented here (each reported separately in the manuscript):
  C1 raw records retrieved (per database)
  C2 unique records after identifier dedup within database
  C3 unique records after cross-database dedup
  C4 eligible after year / language restriction
  C5 tier P (core group term AND crime term in title+abstract)
  C6 tier S (tier P restricted set OR mechanism term AND crime term)
No count is ever used as a denominator for a different count on the chain.
"""
import json, os, re, sys, collections

ROOT = "/root/cultcrime"
RAW = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
spec = json.load(open(os.path.join(ROOT, "src", "query_spec.json")))


def rx(term):
    t = re.escape(term).replace(r"\ ", r"[\s\-]+")
    return re.compile(r"\b" + t + r"\b", re.I)


TERMS = {}
for t in spec["groups"]["core"]:
    TERMS.setdefault("core", []).append((t, rx(t)))
for t in spec["groups"]["mechanism_tier"]:
    TERMS.setdefault("mech", []).append((t, rx(t)))
for t in spec["crime"]:
    TERMS.setdefault("crime", []).append((t, rx(t)))
for k, v in spec["nested_blocks"].items():
    TERMS.setdefault(k, []).extend((t, rx(t)) for t in v)


def hits(text, key):
    return [t for t, r in TERMS[key] if r.search(text)]


def norm_doi(d):
    if not d:
        return ""
    d = d.strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    return d.rstrip(".,;")


def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def ascii_ratio(s):
    if not s:
        return 0.0
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if ord(c) < 128) / len(letters)


def load_all():
    import glob
    rows, per_file = [], {}
    for fp in sorted(glob.glob(os.path.join(RAW, "*.jsonl"))):
        name = os.path.basename(fp)[:-6]
        n = 0
        with open(fp) as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line)); n += 1
        per_file[name] = n
    return rows, per_file


def main():
    report = collections.OrderedDict()
    rows, per_file = load_all()
    report["raw_rows_per_file"] = per_file
    report["raw_rows_total"] = len(rows)
    # collapse duplicate rows of the same record (tier-S file repeats tier-P rows)
    best = {}
    for r in rows:
        k = (r["db"], r["id"])
        if k not in best or r.get("tier") == "P":
            best[k] = r
    report["unique_per_source"] = dict(collections.Counter(k[0] for k in best))
    recs = list(best.values())
    report["unique_cross_db_pre"] = len(recs)

    # ---- dedup: DOI first, then normalised title
    by_doi, by_title, keep = {}, {}, []
    for r in recs:
        d = norm_doi(r.get("doi"))
        t = norm_title(r.get("title"))
        # A record is a duplicate if EITHER key is already taken.  Checking only
        # "DOI if present, title otherwise" lets the same paper survive twice when
        # one source supplies a DOI and another supplies only the title — which is
        # exactly what happens between Crossref and Semantic Scholar.
        if (d and d in by_doi) or (t and t in by_title):
            continue
        if d:
            by_doi[d] = r
        if t:
            by_title[t] = r
        keep.append(r)
    report["unique_after_dedup"] = len(keep)

    # ---- restriction: year
    keep2 = [r for r in keep if r.get("year") and 1994 <= int(r["year"]) <= 2026]
    report["after_year_1994_2026"] = len(keep2)

    # ---- restriction: language (declared, else inferred from script ratio)
    keep3, lang_stats = [], collections.Counter()
    for r in keep2:
        lang = (r.get("lang") or "").lower()
        txt = (r.get("title") or "") + " " + (r.get("abstract") or "")
        if lang.startswith("en"):
            lang_stats["declared_en"] += 1; keep3.append(r)
        elif lang:
            lang_stats["declared_other_" + lang[:5]] += 1
        else:
            if ascii_ratio(txt) >= 0.97 and len(txt) > 60:
                lang_stats["inferred_en"] += 1; r["lang_inferred"] = True; keep3.append(r)
            else:
                lang_stats["inferred_not_en"] += 1
    report["after_language"] = len(keep3)
    report["language_breakdown"] = dict(lang_stats)

    # ---- tier + block flags
    out = []
    for r in keep3:
        txt = (r.get("title") or "") + " \n " + (r.get("abstract") or "")
        g = hits(txt, "core"); m = hits(txt, "mech"); c = hits(txt, "crime")
        nested = {k: hits(txt, k) for k in spec["nested_blocks"]}
        if not c:
            continue
        tier = "P" if g else ("S" if m else None)
        if tier is None:
            continue
        r2 = dict(r)
        r2.update({"hits_group": g, "hits_mech": m, "hits_crime": c,
                   "tier_final": tier, "nested": nested,
                   "has_abstract": bool((r.get("abstract") or "").strip())})
        out.append(r2)

    # cross-database merge: prefer the copy with the longer abstract
    out.sort(key=lambda x: (x["tier_final"], x["db"], -(len(x.get("abstract") or ""))))
    report["tierP"] = sum(1 for r in out if r["tier_final"] == "P")
    report["tierS_only"] = sum(1 for r in out if r["tier_final"] == "S")
    report["with_abstract"] = sum(1 for r in out if r["has_abstract"])
    report["without_abstract"] = sum(1 for r in out if not r["has_abstract"])

    os.makedirs(PROC, exist_ok=True)
    with open(os.path.join(PROC, "corpus.jsonl"), "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(report, open(os.path.join(PROC, "compose_report.json"), "w"), indent=1, ensure_ascii=False)
    for k, v in report.items():
        print("%-28s %s" % (k, v))
    print("COMPOSE_DONE")


if __name__ == "__main__":
    main()
