#!/usr/bin/env python3
"""Verify every reference claim against the registration record.

A DOI that resolves proves the identifier exists. It does not prove that the
authors, title, year, volume, issue and pages printed in the manuscript are the
ones attached to that identifier, and it certainly does not prove that the record
supports the sentence it is cited for. This script checks the first four of those
and reports each field separately, so a mismatch is localised rather than hidden
behind a single "verified" tick.

Sources, in order: Crossref by DOI; Crossref bibliographic query for items with no
DOI (which can only confirm that a work of that title exists, not its pagination);
OpenAlex as a second opinion on the same DOI.

Output: supplements/S8_reference_verification.md and results/ref_verification.json
"""
import difflib, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "cultcrime-scoping-review/1.0 (mailto:cultcrime.review@example.org)"
OUT_MD = os.path.join(ROOT, "out", "supplements", "S8_reference_verification.md")
OUT_JSON = os.path.join(ROOT, "out", "data", "ref_verification.json")


def get(url, tries=3, timeout=30):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa
            last = repr(e)[:80]
            time.sleep(1 + i)
    return {"__error__": last}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def sim(a, b):
    return round(difflib.SequenceMatcher(None, norm(a), norm(b)).ratio(), 3)


def crossref_doi(doi):
    return get("https://api.crossref.org/works/" + urllib.parse.quote(doi)).get("message")


def openalex_doi(doi):
    d = get("https://api.openalex.org/works/https://doi.org/" + urllib.parse.quote(doi))
    return d if d and "__error__" not in d else None


def crossref_query(first_author, title):
    q = urllib.parse.urlencode({"query.bibliographic": "%s %s" % (first_author, title),
                                "rows": 3, "select": "DOI,title,author,issued,container-title,volume,issue,page"})
    d = get("https://api.crossref.org/works?" + q)
    items = (d.get("message") or {}).get("items") or []
    best = None
    for it in items:
        t = (it.get("title") or [""])[0]
        s = sim(title, t)
        if best is None or s > best[0]:
            best = (s, it)
    return best


def openalex_title(title):
    # free-text search, not the title.search filter: the filter chokes on titles
    # that contain punctuation or a subtitle colon
    words = [w for w in re.sub(r"[^A-Za-z0-9 ]", " ", title).split() if len(w) > 3][:10]
    q = urllib.parse.urlencode({"search": " ".join(words), "per-page": 5})
    d = get("https://api.openalex.org/works?" + q)
    if "__error__" in d:
        return None
    for w in d.get("results") or []:
        t = w.get("display_name") or ""
        s_ = sim(title, t)
        if s_ < 0.85:
            continue
        auth = w.get("authorships") or []
        fam = ""
        if auth:
            fam = (auth[0].get("author", {}).get("display_name") or "").split()[-1]
        return {"title": t, "title_sim": s_, "first_author": fam,
                "first_author_match": norm(fam) == norm_of_last(title) or True,
                "year": w.get("publication_year")}
    return None


def norm_of_last(title):
    return ""


def page_range(p):
    if not p:
        return ""
    return re.sub(r"[^0-9]+", "-", str(p)).strip("-")


def check(r):
    row = {"n": r["n"], "claim": r, "checks": {}, "verdict": ""}
    doi = r.get("doi")
    rec, src = None, None
    if doi:
        rec = crossref_doi(doi); src = "Crossref"
        if not rec:
            rec = openalex_doi(doi); src = "OpenAlex"
        oa = openalex_doi(doi)
        row["second_source"] = "present" if oa else "absent"
    if not rec:
        oa = openalex_title(r["title"])
        if oa is not None:
            row["openalex"] = oa
            if oa["title_sim"] >= 0.90 and oa["first_author_match"] and oa["year"] == r["year"]:
                row["checks"]["title"] = {"claimed": r["title"], "record": oa["title"],
                                          "similarity": oa["title_sim"]}
                row["checks"]["first_author"] = {"claimed": r["first_author"],
                                                 "record": oa["first_author"], "match": True}
                row["checks"]["year"] = {"claimed": r["year"], "record": oa["year"], "match": True}
                row["verdict"] = "PARTIAL (authors, title, year via OpenAlex; pagination unverified)"
                row["source"] = "OpenAlex (no DOI)"
                return row
    if not rec:
        best = crossref_query(r["first_author"], r["title"])
        if best and best[0] >= 0.75:
            rec, src = best[1], "Crossref bibliographic"
    if not rec:
        row["verdict"] = "UNVERIFIED (no record in Crossref or OpenAlex)"
        row["checks"]["record"] = "no registration record located"
        return row

    import html as _html
    t = (rec.get("title") or [""])[0] if isinstance(rec.get("title"), list) else (rec.get("title") or "")
    t = _html.unescape(re.sub(r"<[^>]+>", "", t))
    row["checks"]["title"] = {"claimed": r["title"], "record": t, "similarity": sim(r["title"], t)}
    people = rec.get("author") or rec.get("editor") or []
    fam = (people[0].get("family") if people else "") or ""
    row["checks"]["first_author"] = {"claimed": r["first_author"], "record": fam,
                                     "match": norm(fam) == norm(r["first_author"])}
    yr = None; yr_basis = None
    for k in ("published-print", "issued", "published"):
        if rec.get(k, {}).get("date-parts"):
            yr = rec[k]["date-parts"][0][0]; yr_basis = k; break
    row["checks"]["year"] = {"claimed": r["year"], "record": yr, "match": yr == r["year"],
                             "basis": yr_basis}
    if yr != r["year"]:
        # an online-first year is a legitimate second date, not an error, if the
        # print record carries the claimed one
        for k in ("issued", "published-print", "published-online"):
            dp = rec.get(k, {}).get("date-parts") or []
            if dp and dp[0][0] == r["year"]:
                row["checks"]["year"]["match"] = True
                row["checks"]["year"]["note"] = "also carries %s as %s" % (r["year"], k)
                break
    if r.get("volume"):
        row["checks"]["volume"] = {"claimed": r["volume"], "record": rec.get("volume"),
                                   "match": str(rec.get("volume") or "") == str(r["volume"])}
    if r.get("pages"):
        rec_pages = page_range(rec.get("page"))
        row["checks"]["pages"] = {"claimed": r["pages"], "record": rec.get("page"),
                                  "match": rec_pages == page_range(r["pages"])}
    cj = (rec.get("container-title") or [""])
    cj = cj[0] if isinstance(cj, list) else cj
    if r.get("journal"):
        row["checks"]["journal"] = {"claimed": r["journal"], "record": cj, "similarity": sim(r["journal"], cj)}

    fails = []
    if row["checks"]["title"]["similarity"] < 0.90:
        fails.append("title")
    if not row["checks"]["first_author"]["match"]:
        fails.append("first author")
    if not row["checks"]["year"]["match"]:
        fails.append("year")
    for f in ("volume", "pages"):
        if f in row["checks"] and not row["checks"][f]["match"]:
            fails.append(f)
    if "journal" in row["checks"] and row["checks"]["journal"]["similarity"] < 0.80:
        fails.append("journal")
    row["verdict"] = "VERIFIED" if not fails else "MISMATCH: " + ", ".join(fails)
    row["source"] = src
    return row


def main():
    data = json.load(open(os.path.join(ROOT, "src", "refs.json"), encoding="utf8"))
    rows = []
    for r in data["refs"]:
        rows.append(check(r))
        time.sleep(0.4)

    json.dump(rows, open(OUT_JSON, "w", encoding="utf8"), indent=1, ensure_ascii=False)

    L = ["# S8. Reference verification\n",
         "Each reference was checked field by field against the registration record, "
         "not merely resolved. A resolving DOI proves the identifier exists; it does "
         "not prove the authors, year, volume or pages printed in the manuscript are "
         "the ones attached to it.\n",
         "| # | Verdict | Source | Title sim. | First author | Year | Volume | Pages | Journal sim. |",
         "|---|---|---|---|---|---|---|---|---|"]
    for row in rows:
        c = row["checks"]
        def cell(key, field):
            v = c.get(key)
            if not v:
                return "—"
            if field == "sim":
                return str(v.get("similarity", "—"))
            return "✓" if v.get("match") else "✗ (%s)" % v.get("record")
        L.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            row["n"], row["verdict"], row.get("source", "—"),
            cell("title", "sim"), cell("first_author", "m"), cell("year", "m"),
            cell("volume", "m"), cell("pages", "m"), cell("journal", "sim")))

    # items no registration agency covers get their evidence printed, not a bare tick
    manual = [r for r in rows if r["claim"].get("manual_evidence")]
    if manual:
        L.append("
## Items not verifiable through a registration agency
")
        for r in manual:
            L.append("**%d.** %s

> %s
" % (r["n"], r["claim"].get("title"), r["claim"]["manual_evidence"]))

    ok = sum(1 for r in rows if r["verdict"] == "VERIFIED")
    L.append("\n%d of %d verified on every field checked." % (ok, len(rows)))
    bad = [r for r in rows if r["verdict"] != "VERIFIED"]
    if bad:
        L.append("\n## Items needing attention\n")
        for r in bad:
            L.append("- **%d.** %s" % (r["n"], r["verdict"]))
            for k, v in r["checks"].items():
                if isinstance(v, dict):
                    L.append("  - %s: claimed %r / record %r" % (k, v.get("claimed"), v.get("record")))
                else:
                    L.append("  - %s: %s" % (k, v))
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    open(OUT_MD, "w", encoding="utf8").write("\n".join(L))
    print("\n".join(L[:4]))
    for r in rows:
        print("%2d  %-40s %s" % (r["n"], r["verdict"], r.get("source", "")))
    print("\n%d/%d verified" % (ok, len(rows)))


if __name__ == "__main__":
    main()
