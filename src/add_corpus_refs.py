#!/usr/bin/env python3
"""Add representative corpus studies to the reference list, built from the verified record.

The reference string is generated from the Crossref record rather than typed, so the
printed citation cannot drift from the metadata that was checked. A DOI that fails
verification is dropped and reported, not silently kept.

Vancouver format, matching the journal's submitted file:
  Author AB, Author CD, et al. Title. Journal. Year;Volume(Issue):Pages. doi:...
"""
import html, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "cultcrime-scoping-review/1.0 (mailto:cultcrime.review@example.org)"

SELECTED = [
    ("3.1", "10.1016/j.avb.2018.04.004"),
    ("3.1", "10.17759/psylaw.2015100202"),
    ("3.1", "10.1007/s11186-016-9279-6"),
    ("3.1", "10.1111/j.1440-1819.2006.01454.x"),
    ("3.2", "10.1111/1556-4029.15392"),
    ("3.2", "10.1111/j.1440-1819.1997.tb02581.x"),
    ("3.3", "10.1007/s00204-026-04629-z"),
    ("3.3", "10.1353/nvr.2025.a967007"),
    ("3.3", "10.54208/0002/004"),
    ("3.3", "10.1007/978-981-15-9136-5_10"),
    ("3.4", "10.1177/25166069221127375"),
    ("3.4", "10.54208/1000/0008/005"),
]


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except Exception as e:  # noqa
            last = repr(e)[:80]
            time.sleep(1 + i)
    return {"__error__": last}


def clean(t):
    t = re.sub(r"<[^>]+>", "", t or "")          # <scp>, <i>, ...
    t = html.unescape(t)
    t = t.replace("‐", "-").replace("‑", "-").replace("–", "-").replace("—", "-").replace("‘", "'").replace("’", "'")
    return re.sub(r"\s+", " ", t).strip()


def initials(given):
    out = []
    for part in (given or "").replace("-", " -").split():
        if part == "-":
            continue
        out.append(part[0].upper())
    return "".join(out)


def vancouver(rec):
    people = rec.get("author") or rec.get("editor") or []
    names = []
    for a in people[:6]:
        fam = a.get("family") or a.get("name") or ""
        fam = fam.strip()
        if fam.isupper():
            fam = " ".join(w.capitalize() for w in fam.split())
        giv = initials(a.get("given", ""))
        names.append(("%s %s" % (fam, giv)).strip())
    if len(people) > 6:
        names.append("et al.")
    auth = ", ".join(names) if names else "(no author listed)"
    title = clean((rec.get("title") or [""])[0]).rstrip(".")
    cont = rec.get("container-title") or []
    journal = clean(cont[0]) if cont else ""
    yr = None
    for k in ("published-print", "issued", "published", "published-online", "created"):
        if rec.get(k, {}).get("date-parts"):
            yr = rec[k]["date-parts"][0][0]; break
    vol = rec.get("volume") or ""
    iss = rec.get("issue") or ""
    pages = (rec.get("page") or "").replace("–", "-")
    doi = rec.get("DOI") or ""
    if not auth.endswith("."):
        auth = auth + "."
    parts = [auth, title + "."]
    if journal:
        parts.append(journal + ".")
    vol_part = str(yr or "n.d.")
    if vol:
        vol_part += ";%s" % vol
        if iss:
            vol_part += "(%s)" % iss
        if pages:
            vol_part += ":%s" % pages
    parts.append(vol_part + ".")
    parts.append("doi:%s" % doi)
    bits = " ".join(parts)
    bits = re.sub(r"\.\.", ".", bits)
    return bits


def main():
    out = []
    for section, doi in SELECTED:
        d = get("https://api.crossref.org/works/" + urllib.parse.quote(doi))
        rec = d.get("message")
        if not rec:
            print("DROP %s (no record: %s)" % (doi, d.get("__error__", "not found")))
            continue
        t = (rec.get("title") or [""])[0]
        yr = None
        for k in ("published-print", "issued", "published"):
            if rec.get(k, {}).get("date-parts"):
                yr = rec[k]["date-parts"][0][0]; break
        people = rec.get("author") or rec.get("editor") or []
        fam = (people[0].get("family") if people else "") or ""
        if fam.isupper():
            fam = " ".join(w.capitalize() for w in fam.split())
        out.append({"section": section, "doi": doi, "first_author": fam, "title": clean(t), "year": yr,
                    "reference": vancouver(rec),
                    "type": rec.get("type")})
        print("[%s] %s  %s" % (section, yr, t[:70]))
        time.sleep(0.4)
    json.dump(out, open(os.path.join(ROOT, "out", "data", "corpus_refs.json"), "w", encoding="utf8"),
              indent=1, ensure_ascii=False)
    print("\n%d of %d resolved" % (len(out), len(SELECTED)))


if __name__ == "__main__":
    main()
