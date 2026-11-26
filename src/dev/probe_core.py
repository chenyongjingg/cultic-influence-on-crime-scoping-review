#!/usr/bin/env python3
"""Probe CORE v3 without an API key: rate, boolean support, yield."""
import json, sys, time, urllib.parse, urllib.request

UA = "cultcrime-scoping-review/1.0"
BASE = "https://api.core.ac.uk/v3/search/works/"


def q(expr, limit=1, offset=0):
    params = {"q": expr, "limit": limit, "offset": offset}
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for i in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read()
            return json.loads(body)
        except Exception as e:
            last = repr(e)[:90]
            time.sleep(5 + 5 * i)
    print("   FAIL", last)
    return None


TESTS = [
    "cult",
    '"cult" AND "crime"',
    '(cult OR cults OR sect OR sects) AND (crime OR criminal OR homicide OR fraud)',
    '"high-control group"',
    '"new religious movement"',
    'title:"cult" AND title:"crime"',
]

for t in TESTS:
    d = q(t)
    print("%-70s %s" % (t[:68], d.get("totalHits") if d else "FAIL"))
    time.sleep(6)
