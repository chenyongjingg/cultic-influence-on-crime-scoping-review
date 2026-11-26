#!/usr/bin/env python3
"""Six-source retrieval stack (protocol V1.6 §3.11).

Engineering contract, implemented here rather than promised:
  * resumable — each (source, query, page) writes a line to a JSONL and the
    cursor/offset to a state file, so a restart continues instead of restarting;
  * counts land as they are obtained, not at the end;
  * exponential backoff, and a circuit breaker that honours a 429's retry-after
    and then stops hammering that source for the rest of the run;
  * a SHA-256 manifest of every artefact at completion.

Sources: crossref (relevance, term-stratified), core (boolean, OA aggregation),
semanticscholar (boolean bulk; frequently 429 from cloud IPs), plus the three that
already ran (europepmc, pubmed, doaj) which are re-read rather than re-fetched.

Usage:  python3 src/harvest2.py crossref core s2 [--pages N]
"""
import argparse, hashlib, json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

ROOT = "/root/cultcrime"
RAW = os.path.join(ROOT, "data", "raw")
STATE = os.path.join(ROOT, "data", "harvest_state.json")
UA = "cultcrime-scoping-review/1.0 (mailto:cultcrime.review@example.org)"

core_terms = json.load(open(os.path.join(ROOT, "src", "query_spec.json"))) if os.path.exists(
    os.path.join(ROOT, "src", "query_spec.json")) else None


def state_load():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"done": {}, "counts": {}, "circuit": {}}


def state_save(s):
    tmp = STATE + ".tmp"
    json.dump(s, open(tmp, "w"), indent=1, ensure_ascii=False)
    os.replace(tmp, STATE)


def http(url, headers=None, timeout=120, tries=5, source="?", state=None):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = "HTTP %d" % e.code
            if e.code == 429:
                ra = e.headers.get("Retry-After")
                wait = int(ra) if (ra or "").isdigit() else 30
                wait = min(wait, 300)
                print("  429 on %s, sleeping %ds" % (source, wait), flush=True)
                if state is not None and wait > 240:
                    state["circuit"][source] = "off"
                    state_save(state)
                    raise RuntimeError("CIRCUIT_OPEN %s" % source)
                time.sleep(wait)
                continue
            time.sleep(min(2 ** i * 3, 45))
        except Exception as e:
            last = repr(e)[:100]
            time.sleep(min(2 ** i * 2, 30))
    raise RuntimeError("GET failed %s :: %s" % (last, url[:180]))


# ------------------------------------------------------------------ Crossref
GRP = re.compile(r"\b(cult|cults|cultic|sect|sects|high.control group|high demand group|"
                 r"destructive cult|new religious movement|new religious movements|"
                 r"charismatic group|commune)\b", re.I)
CRM = re.compile(r"\b(crim\w*|offen[cs]e\w*|victimi[sz]\w*|fraud\w*|homicid\w*|murder\w*|"
                 r"kill\w*|traffick\w*|abuse\w*|assault\w*)\b", re.I)


def strip_jats(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def crossref(state, pages):
    queries = [
        'cult crime', '"destructive cult"', '"satanic cult"', '"cult" homicide',
        '"new religious movement" crime', '"high-control group"', 'sect homicide',
        '"cult leader" crime', '"ritual abuse"', '"satanic ritual abuse"',
        'cult fraud', 'cult trafficking',
    ]
    out = open(os.path.join(RAW, "crossref.jsonl"), "a")
    n = 0
    for q in queries:
        cursor = state["done"].get("crossref:%s" % q)
        if cursor == "DONE":
            continue
        params = {"query.bibliographic": q, "rows": 1000,
                  "select": "DOI,title,abstract,type,issued,container-title,author",
                  "filter": "from-pub-date:1994-01-01",
                  "mailto": "cultcrime.review@example.org"}
        if cursor:
            params["cursor"] = cursor
        page_no = 0
        while page_no < pages:
            url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
            msg = json.loads(http(url, source="crossref", state=state))["message"]
            items = msg.get("items", [])
            if not items:
                break
            got = 0
            for x in items:
                title = " ".join(x.get("title") or [])
                ab = strip_jats(x.get("abstract"))
                txt = title + " " + ab
                if not (GRP.search(txt) and CRM.search(txt)):
                    continue
                out.write(json.dumps({
                    "db": "crossref", "id": x.get("DOI"), "doi": (x.get("DOI") or "").lower(),
                    "title": title, "abstract": ab,
                    "year": ((x.get("issued", {}).get("date-parts") or [[None]])[0] or [None])[0],
                    "lang": None, "type": x.get("type"),
                    "source": " ".join(x.get("container-title") or []) or None,
                    "is_oa": None, "cited_by": None,
                    "authors": [a.get("family", "") for a in (x.get("author") or [])][:8],
                    "query": q,
                }, ensure_ascii=False) + "\n")
                got += 1
            out.flush()
            n += got
            page_no += 1
            nxt = msg.get("next-cursor")
            print("  crossref %-32s page %d  kept %d  total %d" % (q[:30], page_no, got, n), flush=True)
            state["done"]["crossref:%s" % q] = nxt
            state["counts"]["crossref"] = state["counts"].get("crossref", 0) + got
            state_save(state)
            if not nxt:
                break
            params["cursor"] = nxt
            time.sleep(1.0)
        state["done"]["crossref:%s" % q] = "DONE"
        state_save(state)
    out.close()
    return n


# ---------------------------------------------------------------------- CORE
def core(state, pages):
    expr = ('(cult OR cults OR "new religious movement" OR "high-control group" OR '
            '"destructive cult" OR sect) AND (crime OR criminal OR homicide OR fraud OR '
            'victimization OR trafficking OR abuse)')
    out = open(os.path.join(RAW, "core.jsonl"), "a")
    n = 0
    start = state["done"].get("core:offset", 0)
    if start == "DONE":
        return 0
    for page in range(pages):
        off = start + page * 100
        params = {"q": expr, "limit": 100, "offset": off}
        url = "https://api.core.ac.uk/v3/search/works/?" + urllib.parse.urlencode(params)
        d = json.loads(http(url, source="core", state=state, tries=3))
        res = d.get("results", [])
        if not res:
            break
        got = 0
        for x in res:
            title = x.get("title") or ""
            ab = strip_jats(x.get("abstract") or x.get("fullText") or "")
            txt = title + " " + ab
            if not (GRP.search(txt) and CRM.search(txt)):
                continue
            doi = (x.get("doi") or "").lower()
            out.write(json.dumps({
                "db": "core", "id": str(x.get("id")), "doi": doi, "title": title,
                "abstract": ab[:6000],
                "year": x.get("yearPublished"),
                "lang": x.get("language", {}).get("code") if isinstance(x.get("language"), dict) else None,
                "type": x.get("documentType"), "source": (x.get("publisher") or None),
                "is_oa": True, "cited_by": x.get("citationCount"),
                "authors": [a.get("name", "") for a in (x.get("authors") or [])][:8],
            }, ensure_ascii=False) + "\n")
            got += 1
        out.flush()
        n += got
        print("  core offset %d  kept %d  total %d  (hits %s)" % (off, got, n, d.get("totalHits")), flush=True)
        state["done"]["core:offset"] = off + 100
        state["counts"]["core"] = state["counts"].get("core", 0) + got
        state_save(state)
        time.sleep(8)
    out.close()
    return n


# ---------------------------------------------------------- Semantic Scholar
def s2(state, pages):
    expr = ('(cult | cults | "new religious movement" | "high-control group") + '
            '(crime | criminal | homicide | fraud | victimization | trafficking)')
    out = open(os.path.join(RAW, "s2.jsonl"), "a")
    n = 0
    tok = state["done"].get("s2:token")
    if tok == "DONE":
        return 0
    for _ in range(pages):
        params = {"query": expr, "fields": "title,abstract,year,venue,externalIds,publicationTypes",
                  "year": "1994-2026"}
        if tok:
            params["token"] = tok
        url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode(params)
        try:
            d = json.loads(http(url, source="s2", state=state, tries=3))
        except RuntimeError as e:
            print("  s2 unavailable:", str(e)[:80], flush=True)
            state["circuit"]["s2"] = "off"
            state_save(state)
            break
        for x in d.get("data", []):
            txt = (x.get("title") or "") + " " + (x.get("abstract") or "")
            if not (GRP.search(txt) and CRM.search(txt)):
                continue
            ids = x.get("externalIds") or {}
            out.write(json.dumps({
                "db": "s2", "id": x.get("paperId"), "doi": (ids.get("DOI") or "").lower(),
                "title": x.get("title") or "", "abstract": x.get("abstract") or "",
                "year": x.get("year"), "lang": None, "type": ",".join(x.get("publicationTypes") or []),
                "source": x.get("venue"), "is_oa": None, "cited_by": None, "authors": [],
            }, ensure_ascii=False) + "\n")
            n += 1
        out.flush()
        tok = d.get("token")
        print("  s2 page kept %d total %d" % (n, n), flush=True)
        state["done"]["s2:token"] = tok or "DONE"
        state["counts"]["s2"] = state["counts"].get("s2", 0) + n
        state_save(state)
        if not tok:
            break
        time.sleep(3)
    out.close()
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--pages", type=int, default=6)
    a = ap.parse_args()
    os.makedirs(RAW, exist_ok=True)
    state = state_load()
    for s in a.sources:
        if state["circuit"].get(s) == "off":
            print("%s: circuit open, skipped" % s, flush=True); continue
        t0 = time.time()
        fn = {"crossref": crossref, "core": core, "s2": s2}[s]
        try:
            n = fn(state, a.pages)
        except Exception as e:  # noqa
            print("%s FAILED: %s" % (s, repr(e)[:160]), flush=True)
            state["circuit"][s] = "off"; state_save(state); continue
        print("%s DONE kept=%d %.0fs" % (s, n, time.time() - t0), flush=True)
    # manifest
    man = {}
    for f in sorted(os.listdir(RAW)):
        p = os.path.join(RAW, f)
        man[f] = {"bytes": os.path.getsize(p),
                  "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest()}
    json.dump(man, open(os.path.join(ROOT, "data", "raw_manifest.json"), "w"), indent=1)
    print("MANIFEST_WRITTEN", len(man), "files")


if __name__ == "__main__":
    main()
