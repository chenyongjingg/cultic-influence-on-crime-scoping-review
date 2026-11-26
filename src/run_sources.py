#!/usr/bin/env python3
"""Harvest driver: runs the sources that are available, writes raw JSONL + counts.

Usage:  python3 src/run_sources.py epmc pubmed doaj [openalex]
Each source writes data/raw/<name>.jsonl (one record per line) and appends to
data/counts.json, which is the single place the manuscript takes its numbers from.
"""
import json, os, sys, time, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sources as S

ROOT = "/root/cultcrime"
RAW = os.path.join(ROOT, "data", "raw")


def main(which):
    spec = json.load(open(os.path.join(ROOT, "src", "query_spec.json")))
    y0, y1 = spec["date_range"]["start_year"], spec["date_range"]["end_year"]
    core, mech, crime = spec["groups"]["core"], spec["groups"]["mechanism_tier"], spec["crime"]
    os.makedirs(RAW, exist_ok=True)
    cpath = os.path.join(ROOT, "data", "counts.json")
    counts = json.load(open(cpath)) if os.path.exists(cpath) else {}
    counts.setdefault("sources", {})

    if "epmc" in which:
        expr = "%s AND %s AND PUB_YEAR:[%d TO %d]" % (
            S.ep_or(core), S.ep_or(crime), y0, y1)
        t0 = time.time()
        total, recs = S.epmc(expr)
        write("europepmc", recs)
        counts["sources"]["europepmc"] = {"query": expr, "reported_total": total,
                                          "retrieved": len(recs), "seconds": round(time.time() - t0, 1)}
        print("epmc total=%d got=%d" % (total, len(recs)), flush=True)

        # sensitivity tier: adds the mechanism-only terms
        expr2 = "(%s OR %s) AND %s AND PUB_YEAR:[%d TO %d]" % (
            S.ep_or(core), S.ep_or(mech), S.ep_or(crime), y0, y1)
        total2, recs2 = S.epmc(expr2)
        write("europepmc_tierS", recs2)
        counts["sources"]["europepmc_tierS"] = {"query": expr2, "reported_total": total2,
                                                "retrieved": len(recs2)}
        print("epmc tierS total=%d got=%d" % (total2, len(recs2)), flush=True)

    if "pubmed" in which:
        q = "(%s) AND (%s) AND %d:%d[dp]" % (
            " OR ".join('%s[tiab]' % t for t in core),
            " OR ".join('%s[tiab]' % t for t in crime), y0, y1)
        t0 = time.time()
        total, recs = S.pubmed(q)
        write("pubmed", recs)
        counts["sources"]["pubmed"] = {"query": q, "reported_total": total,
                                       "retrieved": len(recs), "seconds": round(time.time() - t0, 1)}
        print("pubmed total=%d got=%d" % (total, len(recs)), flush=True)

    if "doaj" in which:
        # DOAJ supports quoted phrases combined with AND; build the same blocks
        q = " AND ".join('"%s"' % t for t in core[:1]) + ' AND ' + " AND ".join('"%s"' % t for t in crime[:1])
        q = "(%s)" % " AND ".join('"%s"' % t for t in core)
        # DOAJ has no OR; run one query per group term and union
        allrecs, tot = [], {}
        for g in core:
            try:
                t, rs = S.doaj('"%s" AND (crime OR criminal OR homicide OR fraud OR murder OR victimization)' % g)
            except Exception as e:  # noqa
                tot[g] = "ERR %r" % e
                continue
            tot[g] = t
            allrecs.extend(rs)
            print("  doaj %-30s %d" % (g, t), flush=True)
            time.sleep(0.5)
        write("doaj", allrecs)
        counts["sources"]["doaj"] = {"per_term_reported": tot, "retrieved": len(allrecs),
                                     "note": "DOAJ has no boolean block syntax; group terms queried one at a time, local composer enforces the base block."}
        print("doaj rows=%d" % len(allrecs), flush=True)

    if "openalex" in which:
        expr = "publication_year:>%d,title_and_abstract.search:(%s) AND (%s)" % (
            y0 - 1, " OR ".join('"%s"' % t for t in core), " OR ".join('"%s"' % t for t in crime))
        t0 = time.time()
        try:
            total, recs = S.openalex(expr, log=lambda m: print(m, flush=True))
        except Exception as e:  # noqa
            counts["sources"]["openalex"] = {"query": expr, "status": "FAILED", "error": repr(e)[:600],
                                             "attempted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            json.dump(counts, open(cpath, "w"), indent=1, ensure_ascii=False)
            print("OPENALEX_FAILED", repr(e)[:300], flush=True)
            raise
        write("openalex", recs)
        counts["sources"]["openalex"] = {"query": expr, "reported_total": total,
                                         "retrieved": len(recs), "seconds": round(time.time() - t0, 1)}
        print("openalex total=%d got=%d" % (total, len(recs)), flush=True)

    counts["query_spec_sha256"] = hashlib.sha256(
        open(os.path.join(ROOT, "src", "query_spec.json"), "rb").read()).hexdigest()
    json.dump(counts, open(cpath, "w"), indent=1, ensure_ascii=False)
    print("SOURCES_DONE")


def write(name, recs):
    with open(os.path.join(RAW, name + ".jsonl"), "w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:] or ["epmc", "pubmed", "doaj"])
