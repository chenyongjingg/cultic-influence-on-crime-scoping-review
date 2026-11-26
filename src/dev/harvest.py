#!/usr/bin/env python3
"""Harvest stage: OpenAlex + Europe PMC.

Structure
  A) COUNT-ONLY pass: one query per individual search term -> per-term hit counts
     (supplementary table S2). No records downloaded.
  B) RETRIEVAL pass: one boolean query per tier -> full records via cursor paging.
        tier P (primary)  = CORE group terms AND crime terms
        tier S (sensitivity) = (CORE OR mechanism terms) AND crime terms
     Tier S is a superset of tier P; membership is verified locally.

Every record keeps the tier/terms that produced it, so counting rules stay
inspectable.  Non-200 responses are retried with backoff and abort the run if
they never recover (no silent short corpus).
"""
import json, os, time, hashlib, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = "/root/cultcrime"
RAW = os.path.join(ROOT, "data", "raw")
MAILTO = "cultcrime.review@example.org"
UA = "cultcrime-scoping-review/1.0 (mailto:%s)" % MAILTO
OA = "https://api.openalex.org/works"
EP = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def get(url, tries=7, timeout=90):
    """Retry with backoff; 429/503 get a much longer penalty (polite-pool limits)."""
    import urllib.error
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
                if r.status == 200:
                    return json.loads(body)
                last = "HTTP %s" % r.status
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                last = "HTTP %d" % e.code
                time.sleep(5 + 5 * i)
                continue
            last = "HTTP %d" % e.code
        except Exception as e:  # noqa
            last = repr(e)
        time.sleep(min(2 ** i, 30))
    raise RuntimeError("GET failed: %s :: %s" % (last, url[:300]))


def q(expr, per_page=200):
    params = urllib.parse.urlencode({"filter": expr, "per-page": per_page, "mailto": MAILTO})
    return OA + "?" + params


def oa_count(expr):
    return get(q(expr, per_page=1))["meta"]["count"]


def oa_retrieve(expr, label):
    base = q(expr)
    first = get(base)
    total = first["meta"]["count"]
    recs = list(first["results"])
    cursor = first["meta"].get("next_cursor")
    while cursor and len(recs) < total:
        page = get(base + "&cursor=" + urllib.parse.quote(cursor, safe=""))
        got = page["results"]
        if not got:
            break
        recs.extend(got)
        cursor = page["meta"].get("next_cursor")
        time.sleep(0.2)
        if len(recs) % 1000 < 200:
            print("  %s %d/%d" % (label, len(recs), total), flush=True)
    return total, recs


def inv_abstract(idx):
    if not idx:
        return ""
    pos = [(p, w) for w, locs in idx.items() for p in locs]
    pos.sort()
    return " ".join(w for _, w in pos)


def norm_oa(r):
    src = ((r.get("primary_location") or {}).get("source") or {}).get("display_name")
    return {
        "db": "openalex", "id": r.get("id"),
        "doi": (r.get("doi") or "").replace("https://doi.org/", "").lower(),
        "title": r.get("display_name") or "",
        "abstract": inv_abstract(r.get("abstract_inverted_index")),
        "year": r.get("publication_year"), "lang": r.get("language"),
        "type": r.get("type"), "source": src,
        "is_oa": (r.get("open_access") or {}).get("is_oa"),
        "cited_by": r.get("cited_by_count"),
        "concepts": [c.get("display_name") for c in (r.get("concepts") or [])[:5]],
        "authors": [a["author"]["display_name"] for a in (r.get("authorships") or [])
                    if a.get("author", {}).get("display_name")][:8],
    }


def ep_count(expr):
    url = "%s?query=%s&format=json&pageSize=1" % (EP, urllib.parse.quote(expr))
    return get(url)["hitCount"]


def ep_retrieve(expr):
    url = "%s?query=%s&format=json&pageSize=1000&resultType=core" % (EP, urllib.parse.quote(expr))
    d = get(url)
    total = d["hitCount"]
    recs = list(d.get("resultList", {}).get("result", []))
    while len(recs) < total:
        nxt = d.get("nextCursorMark")
        if not nxt:
            break
        d2 = get(url + "&cursorMark=" + urllib.parse.quote(nxt))
        got = d2.get("resultList", {}).get("result", [])
        if not got or d2.get("nextCursorMark") == nxt:
            break
        recs.extend(got); d = d2; time.sleep(0.3)
    return total, recs


def norm_ep(r):
    return {
        "db": "europepmc", "id": r.get("id"), "doi": (r.get("doi") or "").lower(),
        "title": r.get("title") or "", "abstract": r.get("abstractText") or "",
        "year": int(r["pubYear"]) if str(r.get("pubYear", "")).isdigit() else None,
        "lang": r.get("language"), "type": r.get("pubType"),
        "source": r.get("journalInfo", {}).get("journal", {}).get("title"),
        "is_oa": r.get("isOpenAccess"), "cited_by": r.get("citedByCount"),
        "concepts": [m.get("descriptorName") for m in (r.get("meshHeadingList", {}) or {}).get("meshHeading", [])][:5],
        "authors": [r.get("authorString", "")][:1],
    }


def oa_or(terms):
    return "(" + " OR ".join('"%s"' % t for t in terms) + ")"


def main():
    spec = json.load(open(os.path.join(ROOT, "src", "query_spec.json")))
    y0, y1 = spec["date_range"]["start_year"], spec["date_range"]["end_year"]
    os.makedirs(RAW, exist_ok=True)
    core, mech, crime = spec["groups"]["core"], spec["groups"]["mechanism_tier"], spec["crime"]

    counts = {"started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "openalex": {"terms": {}, "tiers": {}},
              "europepmc": {"terms": {}, "tiers": {}}}

    # ---- A) count-only per term
    for t in core + mech + crime:
        expr = 'publication_year:>%d,title_and_abstract.search:"%s"' % (y0 - 1, t)
        counts["openalex"]["terms"][t] = oa_count(expr)
        print("  oa   %-30s %d" % (t, counts["openalex"]["terms"][t]), flush=True)
        time.sleep(0.4)
    print("openalex per-term counts done", flush=True)
    YR = " AND PUB_YEAR:[%d TO %d]" % (y0, y1)

    def _ep(t):
        return t, ep_count('TITLE_ABS:"%s"%s' % (t, YR))

    with ThreadPoolExecutor(max_workers=8) as ex:
        for t, n in ex.map(_ep, core + mech + crime):
            counts["europepmc"]["terms"][t] = n
            print("  epmc %-30s %d" % (t, n), flush=True)
    print("europepmc per-term counts done", flush=True)

    # ---- B) retrieval per tier
    CORE = oa_or(core); MECH = oa_or(mech); CRIME = oa_or(crime)
    tierP_oa = 'publication_year:>%d,title_and_abstract.search:%s AND %s' % (y0 - 1, CORE, CRIME)
    tierS_oa = 'publication_year:>%d,title_and_abstract.search:(%s OR %s) AND %s' % (y0 - 1, CORE, MECH, CRIME)
    tp, rp = oa_retrieve(tierP_oa, "oa-tierP")
    print("openalex tierP reported=%d retrieved=%d" % (tp, len(rp)), flush=True)
    ts, rs = oa_retrieve(tierS_oa, "oa-tierS")
    print("openalex tierS reported=%d retrieved=%d" % (ts, len(rs)), flush=True)
    counts["openalex"]["tiers"]["P"] = {"reported_total": tp, "retrieved": len(rp)}
    counts["openalex"]["tiers"]["S"] = {"reported_total": ts, "retrieved": len(rs)}

    seenP = {r["id"] for r in rp}
    with open(os.path.join(RAW, "openalex.jsonl"), "w") as f:
        for r in rs:
            o = norm_oa(r); o["tier"] = "P" if r["id"] in seenP else "S"
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

    def ep_or(terms):
        return "(" + " OR ".join('TITLE_ABS:"%s"' % t for t in terms) + ")"

    epP = "%s AND %s%s" % (ep_or(core), ep_or(crime), YR)
    epS = "(%s OR %s) AND %s%s" % (ep_or(core), ep_or(mech), ep_or(crime), YR)
    tp2, rp2 = ep_retrieve(epP)
    ts2, rs2 = ep_retrieve(epS)
    counts["europepmc"]["tiers"]["P"] = {"reported_total": tp2, "retrieved": len(rp2)}
    counts["europepmc"]["tiers"]["S"] = {"reported_total": ts2, "retrieved": len(rs2)}
    print("europepmc tierP=%d tierS=%d" % (tp2, ts2), flush=True)
    seenP2 = {r.get("id") for r in rp2}
    with open(os.path.join(RAW, "europepmc.jsonl"), "w") as f:
        for r in rs2:
            o = norm_ep(r); o["tier"] = "P" if r.get("id") in seenP2 else "S"
            f.write(json.dumps(o, ensure_ascii=False) + "\n")

    counts["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    counts["query_spec_sha256"] = hashlib.sha256(
        open(os.path.join(ROOT, "src", "query_spec.json"), "rb").read()).hexdigest()
    json.dump(counts, open(os.path.join(ROOT, "data", "counts.json"), "w"), indent=1, ensure_ascii=False)
    print("HARVEST_DONE")


if __name__ == "__main__":
    main()
