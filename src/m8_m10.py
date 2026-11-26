#!/usr/bin/env python3
"""Analysis modules M8–M10 (protocol §3.9): investigative-psychology coding.

Scope discipline stated in the protocol (§3.10): these modules code what
*already published* literature says about investigative practice.  They do not
produce operational guidance for any pending case, and no non-public or
classified material is used.

Coding is instrument-assisted: each code is a documented term list and every code
carries the span that triggered it, so the authors can audit or overturn any code
record by record.  This is the same design as the reporting-completeness
measurement, and it is labelled as assisted rather than manual in the manuscript.

Note on interpretation, which the manuscript repeats: a code means the record
*says something about* the element, not that the element was present in the
investigation.
"""
import json, os, re, sys, collections

if os.path.isdir("/root/cultcrime"):
    ROOT = "/root/cultcrime"; P = os.path.join(ROOT, "data", "processed")
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")

SCHEMES = {
    "M8_interrogation": {
        "subject_leader": [r"ringleader", r"leader of the group", r"guru", r"prophet",
                           r"head of the (cult|sect|group)"],
        "subject_core": [r"core member", r"inner circle", r"lieutenant", r"second in command"],
        "subject_member": [r"ordinary member", r"rank and file", r"follower", r"recruit"],
        "subject_victim": [r"victim", r"complainant", r"witness"],
        "reliability": [r"false confession", r"coerced confession", r"confession",
                        r"reliability of (the )?(statement|confession|testimony)",
                        r"voluntariness", r"corroborat"],
        "methods_information": [r"information.gathering", r"PEACE model", r"cognitive interview"],
        "methods_accusatorial": [r"accusatorial", r"reid technique", r"confrontational",
                                 r"coercive interrogation", r"deceptive (interrogation|technique)"],
    },
    "M9_digital_forensics": {
        "communications": [r"phone records", r"call detail", r"messaging", r"text message",
                           r"email", r"chat log", r"communication records"],
        "financial": [r"financial records", r"bank account", r"money transfer", r"wire transfer",
                      r"financial flow", r"account statements"],
        "devices": [r"seized device", r"mobile phone", r"laptop", r"hard drive", r"digital device"],
        "recruitment_online": [r"online recruitment", r"social media", r"website",
                               r"internet recruitment", r"messaging app"],
        "structure_link": [r"hierarch(y|ical)", r"network structure", r"command chain",
                           r"organisational structure", r"organizational structure"],
    },
    "M10_case_linking": {
        "cross_jurisdiction": [r"cross.border", r"multi.?(jurisdiction|state|country)",
                               r"international (investigation|network)", r"extradit"],
        "modus_operandi": [r"modus operandi", r"similar pattern", r"linked cases",
                           r"series of (offences|offenses|crimes)", r"pattern of offending"],
        "ringleader_id": [r"ringleader", r"mastermind", r"identif(y|ication) of (the )?(leader|organiser|organizer)"],
        "victim_id": [r"victim identification", r"identifying victims", r"trace the victims"],
        "rescue_risk": [r"rescue", r"liberation", r"risk assessment (during|for) (the )?(operation|rescue)"],
    },
}


def code(text, key):
    out = {}
    for code_name, pats in SCHEMES[key].items():
        for p in pats:
            m = re.search(p, text, re.I)
            if m:
                s = max(0, m.start() - 25)
                out[code_name] = re.sub(r"\s+", " ", text[s:m.end() + 45]).strip()
                break
        else:
            out[code_name] = ""
    return out


def main():
    recs = [json.loads(l) for l in open(os.path.join(P, "included.jsonl"), encoding="utf8")]
    rows, agg = [], {k: collections.Counter() for k in SCHEMES}
    for r in recs:
        ab = (r.get("abstract") or "").strip()
        if len(ab) < 30:
            continue
        text = re.sub(r"\s+", " ", (r.get("title") or "") + ". " + ab)
        rec = {"id": r.get("id"), "title": (r.get("title") or "")[:120], "year": r.get("year")}
        for k in SCHEMES:
            c = code(text, k)
            rec[k] = c
            for cn, span in c.items():
                if span:
                    agg[k][cn] += 1
        rows.append(rec)
    N = len(rows)
    summary = {"N": N,
               "modules": {k: {cn: {"n": agg[k][cn], "pct": round(100.0 * agg[k][cn] / N, 1) if N else 0}
                               for cn in sorted(SCHEMES[k])} for k in SCHEMES}}
    json.dump({"summary": summary, "records": rows},
              open(os.path.join(P, "m8_m10.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False)
    for k in SCHEMES:
        print(k, "N=%d" % N)
        for cn, v in summary["modules"][k].items():
            print("   %-22s %3d/%d  %5.1f%%" % (cn, v["n"], N, v["pct"]))
    print("M8_M10_DONE")


if __name__ == "__main__":
    main()
