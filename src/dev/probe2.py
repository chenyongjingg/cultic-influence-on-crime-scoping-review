#!/usr/bin/env python3
"""Compare Crossref retrieval strategies by base-block yield."""
import json, re, sys, time, urllib.parse, urllib.request

UA = "cultcrime-scoping-review/1.0 (mailto:cultcrime.review@example.org)"
GRP = re.compile(r"\b(cult|cults|cultic|sect|sects|high.control group|high demand group|"
                 r"destructive cult|new religious movement|charismatic group|commune)\b", re.I)
CRM = re.compile(r"\b(crim\w*|offen[cs]e\w*|victimi[sz]\w*|fraud\w*|homicid\w*|murder\w*|"
                 r"kill\w*|traffick\w*|abuse\w*)\b", re.I)


def fetch(params):
    params = dict(params); params["mailto"] = "cultcrime.review@example.org"
    params.setdefault("select", "DOI,title,abstract,type,issued,container-title")
    params.setdefault("rows", 1000)
    params.setdefault("filter", "from-pub-date:1994-01-01")
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=150) as r:
                return json.loads(r.read())["message"]
        except Exception as e:
            print("   retry", repr(e)[:70]); time.sleep(5 + 5 * i)
    return None


def score(msg):
    items = msg["items"]
    keep = 0
    for x in items:
        t = " ".join(x.get("title") or [])
        a = re.sub(r"<[^>]+>", " ", x.get("abstract") or "")
        txt = t + " " + a
        if GRP.search(txt) and CRM.search(txt):
            keep += 1
    return msg["total-results"], len(items), keep, sum(1 for x in items if x.get("abstract"))


def main():
    tests = [
        ("A bibliographic=cult only", {"query.bibliographic": "cult"}),
        ("B bibliographic=\"cult\" quoted", {"query.bibliographic": "\"cult\""}),
        ("C title=cult crime", {"query.title": "cult crime"}),
        ("D bib=cult + filter journal", {"query.bibliographic": "cult", "filter": "from-pub-date:1994-01-01,type:journal-article"}),
        ("E bib=\"destructive cult\"", {"query.bibliographic": "\"destructive cult\""}),
        ("F bib=\"satanic cult\"", {"query.bibliographic": "\"satanic cult\""}),
    ]
    for name, p in tests:
        m = fetch(p)
        if not m:
            print("%-34s FAILED" % name); continue
        tot, n, keep, nabs = score(m)
        print("%-34s total=%-8d got=%-5d abs=%-4d pass=%d" % (name, tot, n, nabs, keep))
        time.sleep(1)


main()
