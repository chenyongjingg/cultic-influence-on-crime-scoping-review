#!/usr/bin/env python3
"""Source adapters.  Each returns normalised records with the same schema.

Sources
  epmc      Europe PMC REST   (title+abstract boolean; free, no key)
  pubmed    NCBI E-utilities  (title+abstract boolean; free, no key)
  doaj      DOAJ article API  (open-access journals; free, no key)
  openalex  OpenAlex API      (title+abstract boolean; free but credit-metered,
                               see credits.json for the measured limit)

Boolean composition is expressed in each source's own syntax here; the local
composer re-checks every record against the same term lists, so a source whose
syntax behaves unexpectedly cannot silently change what "eligible" means.
"""
import json, os, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET

ROOT = "/root/cultcrime"
UA = "cultcrime-scoping-review/1.0 (mailto:cultcrime.review@example.org)"


def _get(url, tries=5, timeout=90, headers=None):
    import urllib.error
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
            if e.code in (429, 503):
                time.sleep(6 + 6 * i); continue
        except Exception as e:  # noqa
            last = repr(e)
        time.sleep(min(2 ** i, 20))
    raise RuntimeError("GET failed %s :: %s" % (last, url[:200]))


# ------------------------------------------------------------------ Europe PMC
EP = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def ep_or(terms, field="TITLE_ABS"):
    return "(" + " OR ".join('%s:"%s"' % (field, t) for t in terms) + ")"


def epmc(expr, page=1000):
    url = "%s?query=%s&format=json&pageSize=%d&resultType=core" % (EP, urllib.parse.quote(expr), page)
    d = json.loads(_get(url))
    total, recs = d["hitCount"], list(d.get("resultList", {}).get("result", []))
    while len(recs) < total:
        nxt = d.get("nextCursorMark")
        if not nxt:
            break
        d2 = json.loads(_get(url + "&cursorMark=" + urllib.parse.quote(nxt)))
        got = d2.get("resultList", {}).get("result", [])
        if not got or d2.get("nextCursorMark") == nxt:
            break
        recs.extend(got); d = d2; time.sleep(0.4)
    out = [{
        "db": "europepmc", "id": r.get("id"), "doi": (r.get("doi") or "").lower(),
        "title": r.get("title") or "",
        "abstract": (r.get("abstractText") or ""),
        "year": int(r["pubYear"]) if str(r.get("pubYear", "")).isdigit() else None,
        "lang": r.get("language"), "type": r.get("pubType"),
        "source": r.get("journalInfo", {}).get("journal", {}).get("title"),
        "is_oa": r.get("isOpenAccess"), "cited_by": r.get("citedByCount"), "authors": [],
    } for r in recs]
    return total, out


def epmc_count(expr):
    url = "%s?query=%s&format=json&pageSize=1" % (EP, urllib.parse.quote(expr))
    return json.loads(_get(url))["hitCount"]


# --------------------------------------------------------------------- PubMed
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def pubmed_count(term):
    url = "%s/esearch.fcgi?db=pubmed&term=%s&retmode=json&retmax=0" % (EU, urllib.parse.quote(term))
    return int(json.loads(_get(url))["esearchresult"]["count"])


def pubmed(term):
    ids, retstart = [], 0
    while True:
        url = ("%s/esearch.fcgi?db=pubmed&term=%s&retmode=json&retmax=500&retstart=%d"
               % (EU, urllib.parse.quote(term), retstart))
        r = json.loads(_get(url))["esearchresult"]
        batch = r["idlist"]
        ids.extend(batch)
        if not batch or len(ids) >= int(r["count"]):
            break
        retstart += 500
        time.sleep(0.4)
    recs = []
    for i in range(0, len(ids), 200):
        chunk = ids[i:i + 200]
        url = "%s/efetch.fcgi?db=pubmed&id=%s&retmode=xml" % (EU, ",".join(chunk))
        root = ET.fromstring(_get(url))
        for art in root.iter("PubmedArticle"):
            def txt(path):
                e = art.find(path)
                return "".join(e.itertext()).strip() if e is not None else ""
            pmid = txt(".//PMID")
            year = txt(".//JournalIssue/PubDate/Year") or txt(".//JournalIssue/PubDate/MedlineDate")[:4]
            abs_parts = ["".join(a.itertext()).strip() for a in art.iter("AbstractText")]
            doi = ""
            for aid in art.iter("ArticleId"):
                if aid.get("IdType") == "doi":
                    doi = (aid.text or "").lower()
            recs.append({
                "db": "pubmed", "id": pmid, "doi": doi,
                "title": txt(".//ArticleTitle"),
                "abstract": " ".join(abs_parts),
                "year": int(year) if year.isdigit() else None,
                "lang": txt(".//Language"), "type": txt(".//PublicationType"),
                "source": txt(".//Journal/Title"), "is_oa": None,
                "cited_by": None, "authors": [],
            })
        time.sleep(0.4)
    return len(ids), recs


# ----------------------------------------------------------------------- DOAJ
DOAJ = "https://doaj.org/api/search/articles/"


def doaj(query, page_size=100):
    url = "%s%s?pageSize=%d" % (DOAJ, urllib.parse.quote(query), page_size)
    d = json.loads(_get(url, timeout=90))
    total, recs = d.get("total", 0), list(d.get("results", []))
    page = 1
    while len(recs) < total:
        page += 1
        u = "%s%s?pageSize=%d&page=%d" % (DOAJ, urllib.parse.quote(query), page_size, page)
        d2 = json.loads(_get(u, timeout=90))
        got = d2.get("results", [])
        if not got:
            break
        recs.extend(got); time.sleep(0.4)
    out = []
    for r in recs:
        b = r.get("bibjson", {})
        doi = ""
        for ident in b.get("identifier", []):
            if ident.get("type") == "doi":
                doi = (ident.get("id") or "").lower()
        out.append({
            "db": "doaj", "id": r.get("id"), "doi": doi,
            "title": b.get("title") or "",
            "abstract": b.get("abstract") or "",
            "year": int(b["year"]) if str(b.get("year", "")).isdigit() else None,
            "lang": b.get("language", [None])[0] if isinstance(b.get("language"), list) else b.get("language"),
            "type": "journal-article",
            "source": (b.get("journal") or {}).get("title"),
            "is_oa": True, "cited_by": None,
            "authors": [a.get("name") for a in b.get("author", [])][:8],
        })
    return total, out


# ------------------------------------------------------------------- OpenAlex
OAX = "https://api.openalex.org/works"


def oax_url(expr, per_page=200, cursor=None):
    p = {"filter": expr, "per-page": per_page, "mailto": "cultcrime.review@example.org"}
    if cursor:
        p["cursor"] = cursor
    return OAX + "?" + urllib.parse.urlencode(p)


def oax_headers():
    h = {}
    k = os.environ.get("OPENALEX_KEY")
    if k:
        h["api_key"] = k
    return h


def inv_abstract(idx):
    if not idx:
        return ""
    pos = [(p, w) for w, locs in idx.items() for p in locs]
    pos.sort()
    return " ".join(w for _, w in pos)


def openalex(expr, log=print):
    """Retrieve one boolean query.  Raises on quota exhaustion with the headers."""
    url = oax_url(expr, 200)
    raw = _get(url, headers=oax_headers())
    d = json.loads(raw)
    total, recs = d["meta"]["count"], list(d["results"])
    cur = d["meta"].get("next_cursor")
    while cur and len(recs) < total:
        d2 = json.loads(_get(oax_url(expr, 200, cur), headers=oax_headers()))
        got = d2["results"]
        if not got:
            break
        recs.extend(got)
        cur = d2["meta"].get("next_cursor")
        log("  openalex %d/%d" % (len(recs), total))
        time.sleep(0.25)
    out = []
    for r in recs:
        src = ((r.get("primary_location") or {}).get("source") or {}).get("display_name")
        out.append({
            "db": "openalex", "id": r.get("id"),
            "doi": (r.get("doi") or "").replace("https://doi.org/", "").lower(),
            "title": r.get("display_name") or "",
            "abstract": inv_abstract(r.get("abstract_inverted_index")),
            "year": r.get("publication_year"), "lang": r.get("language"),
            "type": r.get("type"), "source": src,
            "is_oa": (r.get("open_access") or {}).get("is_oa"),
            "cited_by": r.get("cited_by_count"),
            "authors": [a["author"]["display_name"] for a in (r.get("authorships") or [])
                        if a.get("author", {}).get("display_name")][:8],
        })
    return total, out
