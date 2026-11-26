#!/usr/bin/env python3
"""Full-text lift test: same records, abstract layer versus full text.

Design.  For every included record whose full text can be obtained, the same twelve
detectors are run twice — once on title+abstract, once on the retrieved full text —
and the paired difference is reported.  A within-record comparison is the only one
that answers the question the review actually faces: does the field fail to
*measure* these things, or does it fail to *say so in the abstract*?

Retrieval ladder, tried in order, each attempt recorded:
  1. Europe PMC fullTextXML   (open-access biomedical, exact PMCID)
  2. Unpaywall -> best OA location (HTML or PDF)
  3. CORE downloadUrl         (re-queried by DOI)
PDFs need pypdf; if it is absent the PDF branch is skipped and recorded as such.

Resumable: one JSONL line per record as soon as it is fetched, plus a state file.
Nothing is overwritten on restart; records already present are skipped.
"""
import argparse, hashlib, json, os, re, sys, threading, time, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
FT = os.path.join(ROOT, "data", "fulltext")
UA = "cultcrime-scoping-review/1.0 (mailto:cultcrime.review@example.org)"
EMAIL = "cultcrime.review@example.org"

sys.path.insert(0, os.path.join(ROOT, "src"))
import measure as M


def get(url, timeout=20, tries=2, as_json=False, binary=False):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read()
            return json.loads(body) if as_json else body
        except Exception as e:  # noqa
            last = repr(e)[:90]
            time.sleep(1 + i)
    return None


def html_to_text(b):
    s = b.decode("utf8", "replace")
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = re.sub(r"&[a-z]+;", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def pdf_to_text(b):
    try:
        import pypdf, io as _io
        r = pypdf.PdfReader(_io.BytesIO(b))
        return "\n".join((pg.extract_text() or "") for pg in r.pages)
    except Exception:
        return ""


def epmc_xml(pmcid):
    b = get("https://www.ebi.ac.uk/europepmc/webservices/rest/%s/fullTextXML" % pmcid)
    if not b or b[:200].find(b"<") < 0 or len(b) < 5000:
        return None, "epmc-xml-miss"
    return html_to_text(b), "epmc-xml"


def unpaywall(doi):
    d = get("https://api.unpaywall.org/v2/%s?email=%s" % (urllib.parse.quote(doi), EMAIL), as_json=True)
    if not d or not d.get("is_oa"):
        return None, "unpaywall-not-oa"
    loc = d.get("best_oa_location") or {}
    url = loc.get("url_for_pdf") or loc.get("url")
    if not url:
        return None, "unpaywall-no-url"
    b = get(url)
    if not b or len(b) < 5000:
        return None, "unpaywall-fetch-fail"
    txt = pdf_to_text(b) if url.lower().endswith(".pdf") or b[:4] == b"%PDF" else html_to_text(b)
    if len(txt) < 2000:
        return None, "unpaywall-empty"
    return txt, "unpaywall"


def core_by_doi(doi):
    q = 'doi:"%s"' % doi
    url = "https://api.core.ac.uk/v3/search/works/?" + urllib.parse.urlencode({"q": q, "limit": 1})
    d = get(url, as_json=True, tries=1)
    if not d or not d.get("results"):
        return None, "core-miss"
    rec = d["results"][0]
    txt = rec.get("fullText") or ""
    if len(txt) < 2000:
        url2 = rec.get("downloadUrl")
        if url2:
            b = get(url2)
            if b:
                txt = pdf_to_text(b) if b[:4] == b"%PDF" else html_to_text(b)
    if len(txt) < 2000:
        return None, "core-no-fulltext"
    return txt, "core"


def core_by_title(title):
    t = title.replace('"', " ").replace("\\", " ")[:150]
    words = [w for w in re.split(r"\W+", t) if len(w) > 3][:8]
    if not words:
        return None, "core-title-empty"
    url = "https://api.core.ac.uk/v3/search/works/?" + urllib.parse.urlencode(
        {"q": "title:(" + " AND ".join(words) + ")", "limit": 5})
    d = get(url, as_json=True, tries=1)
    if not d or not d.get("results"):
        return None, "core-title-miss"
    import difflib
    for rec in d["results"]:
        cand = (rec.get("title") or "")
        if difflib.SequenceMatcher(None, cand.lower(), title.lower()).ratio() < 0.72:
            continue
        txt = rec.get("fullText") or ""
        if len(txt) > 2000:
            return txt, "core-title"
        u = rec.get("downloadUrl")
        if u:
            b = get(u, timeout=60)
            if b:
                t2 = pdf_to_text(b) if b[:4] == b"%PDF" else html_to_text(b)
                if len(t2) > 2000:
                    return t2, "core-title-file"
    return None, "core-title-no-text"


def s2_oa_pdf(paper_id):
    if not paper_id or len(paper_id) != 40:
        return None, "s2-skip"
    d = get("https://api.semanticscholar.org/graph/v1/paper/%s?fields=openAccessPdf" % paper_id,
            as_json=True, tries=1)
    url = ((d or {}).get("openAccessPdf") or {}).get("url")
    if not url:
        return None, "s2-no-pdf"
    b = get(url, timeout=60)
    if not b:
        return None, "s2-fetch-fail"
    txt = pdf_to_text(b) if b[:4] == b"%PDF" else html_to_text(b)
    return (txt, "s2-pdf") if len(txt) > 2000 else (None, "s2-empty")


def epmc_by_title(title):
    words = [w for w in re.split(r"\W+", title) if len(w) > 3][:8]
    if not words:
        return None, "epmc-title-empty"
    q = " AND ".join('TITLE:"%s"' % w for w in words)
    d = get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" +
            urllib.parse.urlencode({"query": q, "format": "json", "pageSize": 5}),
            as_json=True, tries=1)
    try:
        for r in d["resultList"]["result"]:
            pmcid = r.get("pmcid")
            if pmcid:
                t, how = epmc_xml(pmcid)
                if t:
                    return t, "epmc-title-xml"
    except Exception:
        pass
    return None, "epmc-title-miss"


def fetch_one(rec):
    doi = (rec.get("doi") or "").strip()
    pmcid = ""
    for k in ("pmcid", "id"):
        v = rec.get(k)
        if isinstance(v, str) and v.upper().startswith("PMC"):
            pmcid = v.upper()
    if not pmcid and rec.get("db") == "europepmc":
        d = get("https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID:%s%%20AND%%20SRC:MED&format=json&resultType=lite" % rec.get("id"), as_json=True, tries=1)
        try:
            pmcid = (d["resultList"]["result"][0].get("pmcid") or "")
        except Exception:
            pmcid = ""
    attempts = []
    if pmcid:
        t, how = epmc_xml(pmcid)
        attempts.append(how)
        if t:
            return t, how, attempts
    if doi:
        t, how = unpaywall(doi)
        attempts.append(how)
        if t:
            return t, how, attempts
        t, how = core_by_doi(doi)
        attempts.append(how)
        if t:
            return t, how, attempts
    # fallbacks that do not need a DOI
    if rec.get("db") == "s2":
        t, how = s2_oa_pdf(rec.get("id"))
        attempts.append(how)
        if t:
            return t, how, attempts
    t, how = epmc_by_title(rec.get("title") or "")
    attempts.append(how)
    if t:
        return t, how, attempts
    t, how = core_by_title(rec.get("title") or "")
    attempts.append(how)
    if t:
        return t, how, attempts
    return None, "unavailable", attempts


def run_detectors(text):
    out = {}
    for k, fn in M.DETECTORS.items():
        v, q = fn(text)
        out[k] = {"v": bool(v), "q": q[:160]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--maxchars", type=int, default=120000)
    args = ap.parse_args()
    os.makedirs(FT, exist_ok=True)

    recs = [json.loads(l) for l in open(os.path.join(P, "included.jsonl"))]
    done_path = os.path.join(FT, "fetch.jsonl")
    done = set()
    if os.path.exists(done_path):
        for line in open(done_path):
            try:
                r = json.loads(line)
                # a failed attempt is not a completed one: leave it eligible so a
                # later round can try different endpoints
                if r.get("how") != "unavailable":
                    done.add(r["id"])
            except Exception:
                pass
    if args.limit:
        recs = recs[:args.limit]

    out = open(done_path, "a")
    lock = threading.Lock()
    n_ok = n_fail = 0
    t0 = time.time()
    todo = [r for r in recs if r.get("id") not in done]

    def work(rec):
        txt, how, attempts = fetch_one(rec)
        row = {"id": rec.get("id"), "db": rec.get("db"), "doi": rec.get("doi"),
               "title": (rec.get("title") or "")[:160], "how": how,
               "attempts": attempts, "chars": len(txt or "")}
        if txt:
            txt = txt[:args.maxchars]
            row["text_sha256"] = hashlib.sha256(txt.encode("utf8")).hexdigest()[:16]
            row["abstract_measure"] = run_detectors(
                re.sub(r"\s+", " ", ((rec.get("title") or "") + ". " + (rec.get("abstract") or ""))))
            row["fulltext_measure"] = run_detectors(txt)
            with open(os.path.join(FT, "%s.txt" % hashlib.sha256(str(rec.get("id")).encode()).hexdigest()[:16]),
                      "w", encoding="utf8") as f:
                f.write(txt)
        return row

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(work, rec): rec for rec in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            row = fut.result()
            with lock:
                if row.get("fulltext_measure"):
                    n_ok += 1
                else:
                    n_fail += 1
                out.write(json.dumps(row, ensure_ascii=False) + chr(10))
                out.flush()
            if i % 20 == 0:
                print("  %d/%d ok=%d fail=%d %.0fs" % (i, len(todo), n_ok, n_fail, time.time() - t0), flush=True)

    out.close()
    print("FULLTEXT_DONE ok=%d fail=%d" % (n_ok, n_fail))


if __name__ == "__main__":
    main()
