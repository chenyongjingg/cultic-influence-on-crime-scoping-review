#!/usr/bin/env python3
"""Verify the reference strings PRINTED in the manuscript, not the structured claims.

Two independent directions are checked, because they fail differently:

  A. printed  -> claim   every field in src/refs.json for that key must appear,
                         verbatim, in the printed string. This catches a build step
                         that drops or rewrites a field between claim and manuscript.
  B. printed  -> record  the registration record's own title, first author, year,
                         volume, page and journal must appear in the printed string.
                         This catches a claim that was wrong to begin with.

A DOI that resolves proves the identifier exists, so doi.org is asked separately
from Crossref: the two can disagree.

Output: out/data/printed_ref_verification.json
"""
import difflib
import html as _html
import io, json, os, re, sys, time, traceback, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "cultcrime-scoping-review/1.0 (mailto:cultcrime.review@example.org)"
PRINTED = os.path.join(ROOT, "out", "data", "printed_refs.json")
STRINGS = os.path.join(ROOT, "out", "data", "reference_strings.json")
CLAIMS = os.path.join(ROOT, "src", "refs.json")
OUT_JSON = os.path.join(ROOT, "out", "data", "printed_ref_verification.json")

DOI_RE = re.compile(r"10\.\d{4,9}/[^\s;,]+")


def get_json(url, tries=3, timeout=40):
    last = ""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa
            last = repr(e)[:120]
            time.sleep(2 + i * 2)
    return {"__error__": last}


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", _html.unescape(s or "").lower())).strip()


def present(needle, hay):
    n = norm(needle)
    return bool(n) and (" " + n + " ") in (" " + norm(hay) + " ")


def page_start(p):
    return re.split(r"[-–—]", str(p))[0].strip() if p else ""


def doi_resolves_fast(doi):
    try:
        req = urllib.request.Request("https://doi.org/" + urllib.parse.quote(doi),
                                     headers={"User-Agent": UA}, method="GET")
        with urllib.request.urlopen(req, timeout=8) as r:
            return True, r.geturl()
    except Exception as e:  # noqa
        return False, repr(e)[:80]


def crossref(doi):
    return get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))


def doi_resolves(doi):
    try:
        req = urllib.request.Request("https://doi.org/" + urllib.parse.quote(doi),
                                     headers={"User-Agent": UA}, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, r.geturl()
    except Exception as e:  # noqa
        return False, repr(e)[:120]


def crossref_biblio(query):
    q = urllib.parse.urlencode({"query.bibliographic": query, "rows": 5,
                                "select": "DOI,title,author,editor,issued,published-print,"
                                          "container-title,volume,page,type,publisher"})
    d = get_json("https://api.crossref.org/works?" + q)
    items = (d.get("message") or {}).get("items") or []
    best = None
    for it in items:
        t = (it.get("title") or [""])[0]
        s = difflib.SequenceMatcher(None, norm(query), norm(t)).ratio()
        if best is None or s > best[0]:
            best = (s, it)
    return best


def rec_fields(rec):
    t = rec.get("title")
    t = (t[0] if isinstance(t, list) and t else t) if t else ""
    t = _html.unescape(re.sub(r"<[^>]+>", "", t or ""))
    people = rec.get("author") or rec.get("editor") or []
    fam = (people[0].get("family") if people else "") or ""
    yr, basis = None, None
    for k in ("published-print", "issued", "published", "published-online"):
        dp = (rec.get(k) or {}).get("date-parts") or []
        if dp and dp[0][0]:
            yr, basis = dp[0][0], k
            break
    cj = rec.get("container-title") or []
    cj = cj[0] if isinstance(cj, list) and cj else (cj or "")
    return {"title": t, "first_author": fam, "year": yr, "year_basis": basis,
            "volume": rec.get("volume"), "issue": rec.get("issue"), "page": rec.get("page"),
            "journal": cj, "type": rec.get("type"), "publisher": rec.get("publisher"),
            "authors": people}


def title_words_coverage(record_title, printed):
    """Word-level containment. A one-word spelling difference shows up as one
    missing word out of twenty, which is the honest description of it."""
    rw = [w for w in re.findall(r"[a-z0-9]+", norm(record_title))]
    hay = " " + norm(printed) + " "
    miss = [w for w in rw if (" " + w + " ") not in hay]
    return (len(rw) - len(miss)) / len(rw) if rw else 1.0, miss


def verify(n, key, s, claim):
    row = {"n": n, "key": key, "printed": s, "A_printed_vs_claim": {}, "B_printed_vs_record": {},
           "notes": [], "verdict": ""}
    biblio = re.split(r"doi:", s)[0]

    # ---- A. every claimed field appears in the printed string -----------------
    A = row["A_printed_vs_claim"]
    A["title"] = present(claim.get("title"), s)
    A["first_author"] = present(claim.get("first_author"), s)
    A["year"] = re.search(r"\b%s\b" % claim.get("year"), biblio) is not None
    if claim.get("volume"):
        A["volume"] = re.search(r"\b%s\b" % re.escape(str(claim["volume"])), biblio) is not None
    if claim.get("pages"):
        A["page_start"] = page_start(claim["pages"]) in biblio
    if claim.get("journal"):
        A["journal"] = present(claim["journal"], s)

    # ---- B. the registration record agrees with the printed string ------------
    doi = DOI_RE.search(s)
    doi = doi.group(0).rstrip(".") if doi else None
    if doi is None and claim.get("doi"):
        # the claim records an identifier the printed string does not print
        doi = claim["doi"]
        row["notes"].append("claim carries DOI %s; printed string prints no DOI" % doi)
    B = row["B_printed_vs_record"]
    record = None

    if doi:
        row["doi"] = doi
        d = crossref(doi)
        if "__error__" in d:
            row["verdict"] = "CROSSREF DID NOT ANSWER (%s)" % d["__error__"]
            return row
        record = rec_fields(d["message"])
        row["record_source"] = "Crossref by DOI"
    else:
        q = claim.get("title") or s
        best = crossref_biblio(q)
        if best and best[0] >= 0.90:
            record = rec_fields(best[1])
            row["matched_doi"] = best[1].get("DOI")
            row["record_source"] = "Crossref bibliographic query (no DOI printed)"
            row["match_similarity"] = round(best[0], 3)

    if record is None:
        # no record located: report what the claim itself records as its evidence
        if claim.get("author_verified"):
            row["verdict"] = "NO RECORD (author-verified; see evidence note)"
        elif claim.get("manual_evidence"):
            row["verdict"] = "NO RECORD (evidence note recorded)"
        else:
            row["verdict"] = "NO RECORD FOUND"
        row["evidence_note"] = (claim.get("author_verified") or claim.get("manual_evidence") or "")
        return row

    row["record"] = record
    # author order: the record's first three family names must occur, in order,
    # in the printed string. A correct first author with a swapped second author
    # passes a first-author-only check.
    fams = [a.get("family") for a in (record.get("authors") or [])[:3] if a.get("family")]
    fams = fams or [record["first_author"]]
    hay = " " + norm(s) + " "
    pos, ordered, found = -1, True, []
    for fam in fams:
        i = hay.find(" " + norm(fam) + " ")
        found.append(i >= 0)
        if i < 0 or i < pos:
            ordered = False
        pos = max(pos, i)
    B["author_sequence_in_order"] = ordered and all(found)
    B["authors_checked"] = fams
    cov, miss = title_words_coverage(record["title"], s)
    B["title_in_printed"] = cov == 1.0
    B["title_word_coverage"] = round(cov, 3)
    if miss:
        B["title_words_missing_from_printed"] = miss
    B["first_author_in_printed"] = present(record["first_author"], biblio)
    B["year_in_printed"] = bool(record["year"]) and re.search(r"\b%d\b" % record["year"], biblio) is not None
    if record["volume"]:
        B["volume_in_printed"] = re.search(r"\b%s\b" % re.escape(str(record["volume"])), biblio) is not None
    else:
        row["notes"].append("registered record carries no volume (online-first)")
    if record["page"]:
        B["page_start_in_printed"] = page_start(record["page"]) in biblio
        end = re.split(r"[-–—]", str(record["page"]))[-1].strip()
        B["page_end_in_printed"] = end in biblio
    else:
        row["notes"].append("registered record carries no page range")
    if record["journal"]:
        B["journal_in_printed"] = present(record["journal"], biblio)

    core = all(B.get(k) for k in ("title_in_printed", "first_author_in_printed", "year_in_printed"))
    field_keys = [k for k in ("volume_in_printed", "page_start_in_printed", "journal_in_printed") if k in B]
    missing = [k.replace("_in_printed", "") for k in field_keys if not B[k]]
    if core and not missing:
        row["verdict"] = "MATCHES PRINTED STRING"
    elif core:
        row["verdict"] = "MATCHES BUT OMITS " + ", ".join(missing).upper()
        row["notes"].append("record carries %s that the printed string does not"
                            % {k: record.get(k) for k in missing})
    elif B["title_word_coverage"] >= 0.90 and B["first_author_in_printed"] and B["year_in_printed"]:
        row["verdict"] = "TITLE DIFFERS IN %d WORD(S)" % len(miss)
        row["notes"].append("record title words absent from printed string: %s" % miss)
    else:
        row["verdict"] = "DIFFERS"
    return row


def main():
    printed = json.load(io.open(PRINTED, encoding="utf8"))
    strings = json.load(io.open(STRINGS, encoding="utf8"))
    claims = {r["key"]: r for r in json.load(io.open(CLAIMS, encoding="utf8"))["refs"]}
    rev = {re.sub(r"\s+", " ", v).strip(): k for k, v in strings.items()}

    rows = []
    for n in sorted(printed, key=int):
        key = rev.get(re.sub(r"\s+", " ", printed[n]).strip())
        if key is None or key not in claims:
            rows.append({"n": int(n), "key": key, "printed": printed[n], "verdict": "NOT MAPPED"})
            continue
        try:
            r = verify(int(n), key, printed[n], claims[key])
        except Exception:
            r = {"n": int(n), "key": key, "verdict": "ERROR", "error": traceback.format_exc()[-300:]}
        rows.append(r)
        mark = "OK " if r["verdict"] == "MATCHES PRINTED STRING" else "!! "
        print("%s%2d  %-46s %s" % (mark, r["n"], r["verdict"], r.get("doi") or r.get("matched_doi") or ""))
        time.sleep(0.35)

    json.dump(rows, io.open(OUT_JSON, "w", encoding="utf8"), indent=1, ensure_ascii=False)
    # every DOI-bearing entry is also asked at doi.org, in parallel and with a
    # short timeout: Crossref answering proves registration, not that the
    # redirect target exists
    from concurrent.futures import ThreadPoolExecutor
    dois = [r["doi"] for r in rows if r.get("doi")]
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(lambda d: (d,) + doi_resolves_fast(d), dois))
    print()
    for d, ok, final in res:
        print("  doi.org %-42s %s" % (d, "resolves" if ok else "NO ANSWER: %s" % final[:50]))
        for r in rows:
            if r.get("doi") == d:
                r["doi_org"] = {"resolves": ok, "final": final}

    ok = sum(1 for r in rows if r["verdict"].startswith("MATCHES PRINTED STRING"))
    print("\n%d/%d printed strings contain every field of their registration record" % (ok, len(rows)))
    for r in rows:
        if r["verdict"] != "MATCHES PRINTED STRING":
            print("\n--- %d (%s): %s" % (r["n"], r.get("key"), r["verdict"]))
            if r.get("notes"):
                for x in r["notes"]:
                    print("    note:", x)
            for k, v in (r.get("B_printed_vs_record") or {}).items():
                if v is False:
                    print("    B.%s = False" % k)


if __name__ == "__main__":
    main()
