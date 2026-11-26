#!/usr/bin/env python3
"""Probe: how much does Crossref yield for the base block at a given depth?"""
import json, re, sys, time, urllib.parse, urllib.request

UA = "cultcrime-scoping-review/1.0 (mailto:cultcrime.review@example.org)"
G = ["cult", "cults", "sect", "sects", "new religious movement", "high-control group",
     "high demand group", "destructive cult", "cultic", "charismatic group"]
C = ["crime", "criminal", "offence", "offense", "victimization", "fraud", "homicide",
     "murder", "trafficking", "abuse"]
GRP = re.compile(r"\b(cult|cults|cultic|sect|sects|high.control group|high demand group|"
                 r"destructive cult|new religious movement|charismatic group|commune)\b", re.I)
CRM = re.compile(r"\b(crim\w*|offen[cs]e\w*|victimi[sz]\w*|fraud\w*|homicid\w*|murder\w*|"
                 r"kill\w*|traffick\w*|abuse\w*)\b", re.I)


def strip_jats(s):
    return re.sub(r"<[^>]+>", " ", s or "")


def query(q, rows=1000):
    params = {
        "query.bibliographic": q, "rows": rows,
        "select": "DOI,title,abstract,type,issued,container-title,author",
        "filter": "from-pub-date:1994-01-01",
        "mailto": "cultcrime.review@example.org",
    }
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except Exception as e:
            print("  retry", repr(e)[:80]); time.sleep(4 + 4 * i)
    return None


def main(term, rows):
    q = term + " " + " ".join(C)
    d = query(q, rows)
    if not d:
        print("FAILED"); return
    items = d["message"]["items"]
    n_abs = sum(1 for x in items if x.get("abstract"))
    keep = 0
    for x in items:
        title = " ".join(x.get("title") or [])
        ab = strip_jats(x.get("abstract") or "")
        txt = title + " " + ab
        if GRP.search(txt) and CRM.search(txt):
            keep += 1
    print("term=%-22s reported_total=%-8d fetched=%d with_abstract=%d pass_baseblock=%d"
          % (term, d["message"]["total-results"], len(items), n_abs, keep))


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1000)
