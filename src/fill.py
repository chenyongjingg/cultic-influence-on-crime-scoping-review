#!/usr/bin/env python3
"""Fill manuscript placeholders from analysis.json.  No number is hand-typed.

Two placeholder forms:
  {{NAMED}}        resolved from a small dictionary of headline numbers
  {{a.b.c}}        resolved by walking analysis.json (e.g. {{guiding_questions.A3_mechanism_and_legal.n}})
Any placeholder that cannot be resolved is reported and makes the build fail:
an unfilled {{...}} in a draft survives proofreading far too easily.
"""
import json, re, sys, os


def walk(obj, path):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return None
    return cur


def fmt(v):
    if isinstance(v, float):
        return ("%g" % v)
    return str(v)


def build_named(a):
    pr = a["prisma"]
    ct = {r["construct"]: r for r in a["construct_table"]}
    named = {
        "N_SOURCES": str(len([k for k in pr["identification"] if not k.endswith("_tierS")])),
        "N_RETRIEVED": str(pr["records_retrieved_total"]),
        "N_UNIQUE": str(pr["unique_after_cross_db_dedup"]),
        "N_SCREENED": str(pr["screened"]),
        "N_INCLUDED": str(pr["final_included"]),
        "N_AUTOEXCLUDED": str(pr["auto_excluded_conf_ge_090"]),
        "N_SECONDPASS": str(pr["advanced_to_second_pass"]),
    }
    for k, r in ct.items():
        named["N_" + k] = str(r["n_reported_verified"])
        named["PCT_" + k] = fmt(r["pct"])
    named["N_ALL"] = str(ct["C12_n"]["N"])
    # short aliases used in the abstract
    for short, key in (("GROUP_DEF", "C1_group_def"), ("ROLE", "C2_role"),
                       ("DURATION", "C3_duration"), ("MECHANISM", "C4_mechanism"),
                       ("INSTRUMENT", "C5_instrument"), ("OFFENCE", "C6_offence"),
                       ("LEGAL", "C8_legal"), ("JURISDICTION", "C9_jurisdiction")):
        # one decimal always: "7.0%" reads as a rate, "7%" reads as a count
        named["PCT_" + short] = "%.1f" % ct[key]["pct"]
        named["N_" + short] = str(ct[key]["n_reported_verified"])
    return named


def sources_text(a):
    ident = a["prisma"]["identification"]
    parts = []
    for s, v in ident.items():
        if "reported_total" in v:
            parts.append("%s (%s records reported)" % (s, v["reported_total"]))
        elif v.get("per_term_reported"):
            parts.append("%s (%s retrieved)" % (s, v.get("retrieved", "—")))
        else:
            parts.append("%s (%s retrieved)" % (s, v.get("retrieved", "—")))
    return ("Bibliographic sources were " + "; ".join(parts) +
            ". The full strings and per-source counts are in Supplementary Table S2.")


def main(path_in, path_out, analysis):
    a = json.load(open(analysis, encoding="utf8"))
    named = build_named(a)
    named["SOURCES_TEXT"] = sources_text(a)
    ident = (a.get("prisma") or {}).get("identification") or {}
    for short, key in (("CROSSREF", "crossref"), ("S2", "s2"), ("CORE", "core"),
                       ("EPMC", "europepmc"), ("PUBMED", "pubmed"), ("DOAJ", "doaj")):
        named["SRC_" + short] = str((ident.get(key) or {}).get("retrieved", "0"))
    named["N_INCLUDED_MEASURABLE"] = str((a.get("tool_families") or {}).get("N", "—"))
    tm = a.get("theory_matrix") or {}
    named["TABLE1"] = (
        "Across %s included records, %s name a psychological mechanism theory "
        "(coercive control, bounded choice, cognitive dissonance, groupthink, trauma "
        "bonding, obedience to authority), %s name a criminological theory "
        "(differential association, social control, neutralisation, strain, routine "
        "activity, labelling, social learning), and %s name both. The cells that a "
        "theoretical integration would need to fill — a named forensic-psychological "
        "mechanism paired with a named criminological explanation in the same record — "
        "are therefore %s in this corpus."
        % (tm.get("N", "—"), tm.get("records_with_psychological_theory", "—"),
           tm.get("records_with_criminological_theory", "—"),
           tm.get("records_with_both", "—"),
           "empty" if not tm.get("records_with_both") else "filled in %d record(s)"
           % tm.get("records_with_both", 0)))
    txt = open(path_in, encoding="utf8").read()

    # splice section files into {{SECTION_n}} markers
    base = os.path.dirname(os.path.abspath(path_in))
    for n in list(range(3, 11)) + [35]:
        marker = "{{SECTION_%d}}" % n
        if marker in txt:
            fp = os.path.join(base, "sections", "s%d.md" % n)
            if os.path.exists(fp):
                txt = txt.replace(marker, open(fp, encoding="utf8").read().strip())
            else:
                print("missing section file:", fp)

    missing = []

    def sub(m):
        key = m.group(1)
        if key in named:
            return named[key]
        v = walk(a, key)
        if v is None:
            missing.append(key)
            return m.group(0)
        return fmt(v)

    txt = re.sub(r"\{\{([A-Za-z0-9_.]+)\}\}", sub, txt)
    # WORDCOUNT is computed by build_frontiers.py after this step, by design
    left = sorted(set(re.findall(r"\{\{([A-Za-z0-9_.]+)\}\}", txt)) - {"WORDCOUNT"})
    open(path_out, "w", encoding="utf8").write(txt)
    print("WROTE %s  %d chars" % (path_out, len(txt)))
    if left:
        print("UNRESOLVED:", left)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
