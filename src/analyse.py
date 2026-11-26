#!/usr/bin/env python3
"""Stage 7-8: descriptive analysis.  No hypothesis test is computed anywhere.

Every reported number carries its own denominator, and the denominator is
always printed next to the number so that a reader cannot assemble a ratio the
code did not compute.
"""
import json, os, csv, collections, re, glob

# The analysis runs either on the execution host or, after archiving, against the
# frozen snapshot taken from it. Both layouts are resolved here so a rebuild does
# not depend on which one is present.
if os.path.isdir("/root/cultcrime"):
    ROOT = "/root/cultcrime"
    P = os.path.join(ROOT, "data", "processed")
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    P = os.path.join(ROOT, "data", "processed")
    if not os.path.isdir(P):
        P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")
OUT_JSON = os.environ.get("ANALYSIS_OUT", os.path.join(P, "analysis.json"))
CONS = ["C1_group_def", "C2_role", "C3_duration", "C4_mechanism", "C5_instrument",
        "C6_offence", "C7_severity", "C8_legal", "C9_jurisdiction", "C10_source",
        "C11_comparison", "C12_n"]


def _resolve(p):
    """Paths in the calls are relative to the project root; on the archived layout
    the processed files live one level deeper."""
    direct = os.path.join(ROOT, p)
    if os.path.exists(direct):
        return direct
    alt = os.path.join(P, os.path.basename(p))
    return alt if os.path.exists(alt) else direct


def load(p):
    with open(_resolve(p), encoding="utf8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main():
    data_root = ROOT if os.path.isdir(os.path.join(ROOT, "data")) else os.path.dirname(P)
    counts = json.load(open(os.path.join(data_root, "counts.json"), encoding="utf8"))
    comp = json.load(open(os.path.join(P, "compose_report.json"), encoding="utf8"))
    adj = json.load(open(os.path.join(P, "adjudication_summary.json"), encoding="utf8"))
    ext_stats = json.load(open(os.path.join(P, "extract_stats.json"), encoding="utf8"))
    ext = load("data/processed/extracted.jsonl")

    out = collections.OrderedDict()
    prisma = collections.OrderedDict()
    for k in ("reported_total", "retrieved"):
        pass
    # identification: authoritative row counts come from the raw files themselves
    raw_counts = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "raw", "*.jsonl"))):
        name = os.path.basename(f)[:-6]
        with open(f) as fh:
            raw_counts[name] = sum(1 for line in fh if line.strip())
    prisma["identification"] = {
        s: {"retrieved": raw_counts.get(s, 0),
            "reported_total": counts.get("sources", {}).get(s, {}).get("reported_total")}
        for s in raw_counts
    }
    prisma["records_retrieved_total"] = comp["raw_rows_total"]
    prisma["unique_per_source"] = comp["unique_per_source"]
    prisma["unique_after_cross_db_dedup"] = comp["unique_after_dedup"]
    prisma["excluded_year"] = comp["unique_after_dedup"] - comp["after_year_1994_2026"]
    prisma["excluded_language"] = comp["after_year_1994_2026"] - comp["after_language"]
    prisma["excluded_no_base_block"] = comp["after_language"] - (comp["tierP"] + comp["tierS_only"])
    dd = os.path.join(P, "dedup_screened_report.json")
    if os.path.exists(dd):
        d = json.load(open(dd, encoding="utf8"))
        prisma["model_scored_rows"] = d.get("input")
        prisma["duplicates_removed_after_screening"] = d.get("dropped")
    prisma["screened"] = adj["screened"]
    prisma["auto_excluded_conf_ge_090"] = adj["model_EXCLUDE_conf_ge_090_auto_excluded"]
    prisma["advanced_to_second_pass"] = adj["advanced_to_second_pass"]
    prisma["second_pass_included"] = adj["second_pass_included"]
    prisma["final_included"] = adj["final_included"]
    prisma["second_pass_excluded"] = adj["second_pass_excluded"]
    out["prisma"] = prisma

    # ---------------- construct table (n/N with explicit N)
    ok = [r for r in ext if r.get("extraction")]
    N = len(ok)
    rows = []
    for c in CONS:
        n_true = sum(1 for r in ok if r["extraction"].get(c, {}).get("v") is True)
        n_unver = sum(1 for r in ok if r["extraction"].get(c, {}).get("v") == "UNVERIFIED")
        rows.append({"construct": c, "n_reported_verified": n_true, "n_anchor_unverified": n_unver,
                     "N": N, "pct": round(100.0 * n_true / N, 1) if N else None})
    out["construct_table"] = rows

    # split by source type (pubmed/epmc = biomedical index; doaj = open-access journal; openalex = broad)
    by_db = {}
    for db in sorted({r.get("db") for r in ok}):
        sub = [r for r in ok if r.get("db") == db]
        by_db[db] = {"N": len(sub),
                     **{c: sum(1 for r in sub if r["extraction"].get(c, {}).get("v") is True) for c in CONS}}
    out["construct_by_source"] = by_db

    # ---------------- BITE domain x crime type evidence map
    bite_terms = ["behaviour", "information", "thought", "emotion"]
    crime_cats = ["homicide/murder", "sexual abuse", "child abuse", "trafficking",
                  "fraud/financial", "drug", "assault/violence", "terrorism", "kidnapping",
                  "exploitation", "other/unspecified"]
    grid = collections.Counter()
    for r in ok:
        ds = [d.lower() for d in (r["extraction"].get("bite_domains") or [])]
        cts = [c.lower() for c in (r["extraction"].get("crime_types") or [])]
        for d in bite_terms:
            if any(d in x for x in ds):
                if not cts:
                    grid[(d, "other/unspecified")] += 1
                for c in cts:
                    hit = "other/unspecified"
                    for cat in crime_cats[:-1]:
                        key = cat.split("/")[0]
                        if key in c:
                            hit = cat; break
                    grid[(d, hit)] += 1
    out["evidence_map"] = [{"bite_domain": d, "crime_type": ct, "n": grid[(d, ct)]}
                           for d in bite_terms for ct in crime_cats]

    # ---------------- named instruments (toolchain section)
    INSTR = re.compile(r"\b([A-Z][A-Za-z-]{2,}(?:\s+[A-Z][A-Za-z-]{2,}){0,5}\s+"
                       r"(?:Scale|Inventory|Questionnaire|Checklist|Test|Index|Survey))\b")
    inst = collections.Counter()
    for r in ok:
        a = r["extraction"].get("C5_instrument", {})
        if a.get("v") is True:
            found = INSTR.findall(a.get("q") or "")
            for m in found:
                inst[m.strip()] += 1
            if not found:
                inst["(named, form not extracted)"] += 1
    out["instruments_named"] = inst.most_common(25)

    # ---------------- corpus profile
    years = collections.Counter(r.get("year") for r in ok)
    journals = collections.Counter((r.get("source") or "unknown") for r in ok)
    out["corpus_profile"] = {
        "n_included": N,
        "years": {int(y): c for y, c in sorted(years.items()) if y},
        "top_sources": journals.most_common(15),
        "n_distinct_sources": len(journals),
        "open_access_share": round(100.0 * sum(1 for r in ok if str(r.get("is_oa")).lower() in ("true", "1", "y"))
                                   / N, 1) if N else None,
    }

    # ---------------- MRS-CI frequencies (the back-fill the protocol left blank)
    mrs = []
    labels = {
        "C1_group_def": "1. Group operational definition",
        "C2_role": "2. Participant role",
        "C3_duration": "3. Involvement / exit duration",
        "C4_mechanism": "4. Named manipulation mechanism",
        "C5_instrument": "5. Standardised instrument",
        "C6_offence": "6. Offence type",
        "C7_severity": "7. Offence severity",
        "C8_legal": "8. Legal outcome",
        "C9_jurisdiction": "9. Jurisdiction",
        "C10_source": "10. Data source",
        "C11_comparison": "10b. Comparison / baseline",
        "C12_n": "n. Sample size",
    }
    for r in rows:
        mrs.append({"item": labels[r["construct"]], "n": r["n_reported_verified"], "N": r["N"],
                    "pct": r["pct"]})
    out["mrs_ci_frequencies"] = mrs

    # ---- guiding-question operands (A-1, A-2, A-3): co-occurrence counts
    def both(a, b):
        return sum(1 for r in ok if r["extraction"].get(a, {}).get("v") is True
                   and r["extraction"].get(b, {}).get("v") is True)
    dom = {d: sum(1 for r in ok if any(d in x.lower() for x in (r["extraction"].get("bite_domains") or [])))
           for d in ["behaviour", "information", "thought", "emotion"]}
    out["domain_counts"] = {"per_domain": dom,
                            "any_domain": sum(1 for r in ok if r["extraction"].get("bite_domains")),
                            "N": N}
    out["guiding_questions"] = {
        "A1_role_and_duration": {"n": both("C2_role", "C3_duration"), "N": N},
        "A1_duration_and_legal": {"n": both("C3_duration", "C8_legal"), "N": N},
        "A2_instrument_any": {"n": sum(1 for r in ok if r["extraction"].get("C5_instrument", {}).get("v") is True), "N": N},
        "A3_mechanism_and_legal": {"n": both("C4_mechanism", "C8_legal"), "N": N},
        "A3_mechanism_and_jurisdiction": {"n": both("C4_mechanism", "C9_jurisdiction"), "N": N},
        "mechanism_only_no_legal": {"n": sum(1 for r in ok if r["extraction"].get("C4_mechanism", {}).get("v") is True
                                              and r["extraction"].get("C8_legal", {}).get("v") is not True), "N": N},
    }
    # ---- tool families named (for the tool-question misalignment figure)
    FAM = {
        "Risk assessment (HCR-20, SVR-20, VRAG, Static-99, LSI-R)":
            r"HCR-?20|SVR-?20|VRAG|Static-?99|LSI-?R",
        "General psychopathology (MMPI, PAI, SCL-90, BPRS, SCID)":
            r"MMPI|PAI|SCL-?90|BPRS|SCID|PHQ-?9|GAD-?7",
        "Cult-specific (GPA, BITE)": r"Group Psychological Abuse|GPA|BITE",
        "Trauma / PTSD (PCL, CAPS, CTQ)": r"PCL-?[CR5]|CAPS|CTQ|Impact of Event",
        "Responsibility / fitness (none standardised)": r"fitness to stand trial|McNaughton|M'Naghten|criminal responsibility assessment",
    }
    fam_counts = {}
    for name, pat in FAM.items():
        fam_counts[name] = sum(1 for r in ok
                               if re.search(pat, (r.get("title") or "") + " " + (r.get("abstract") or ""), re.I))
    out["tool_families"] = {"N": N, "counts": fam_counts,
                            "any_instrument": sum(1 for r in ok
                                                  if r["extraction"].get("C5_instrument", {}).get("v") is True)}

    # ---- Table 1: theory-integration matrix (M7)
    PSY = ["coercive control", "bounded choice", "cognitive dissonance", "groupthink",
           "trauma bond", "trauma bonding", "obedience to authority", "learned helplessness",
           "attachment theory", "manipulation", "indoctrination", "thought reform"]
    CRIM = ["differential association", "social control", "neutralization", "neutralisation",
            "strain theory", "routine activity", "labeling", "labelling", "social learning",
            "subcultural", "desistance", "rational choice", "control theory"]
    pair_rows = []
    n_psy = n_crim = n_both = 0
    for r in ok:
        t = " ".join(r["extraction"].get("theory_terms") or []).lower()
        p_ = [x for x in PSY if x in t]
        c_ = [x for x in CRIM if x in t]
        n_psy += bool(p_); n_crim += bool(c_); n_both += bool(p_ and c_)
        if p_ or c_:
            pair_rows.append({"title": (r.get("title") or "")[:90], "psychological": p_,
                              "criminological": c_})
    out["theory_matrix"] = {"records_with_psychological_theory": n_psy,
                            "records_with_criminological_theory": n_crim,
                            "records_with_both": n_both, "N": N, "detail": pair_rows}

    ep = os.path.join(P, "embed_dedup_report.json")
    if os.path.exists(ep):
        e = json.load(open(ep, encoding="utf8"))
        out["embed_dedup_summary"] = {
            "clusters_095": (e.get("0.95") or {}).get("clusters"),
            "absorbed_095": (e.get("0.95") or {}).get("records_absorbed"),
            "clusters_090": (e.get("0.90") or {}).get("clusters"),
        }

    fl = os.path.join(P, "fulltext_lift.json")
    if os.path.exists(fl):
        out["fulltext_lift"] = json.load(open(fl, encoding="utf8"))

    fp5 = os.path.join(P, "exp5_llm_construct.json")
    if os.path.exists(fp5):
        out["llm_construct_read"] = json.load(open(fp5, encoding="utf8"))

    for key, fn in (("detector_validation", "exp1_detector_validation.json"),
                    ("term_sensitivity", "exp4_terms.json"),
                    ("strata", "exp3_strata.json")):
        fp = os.path.join(P, fn)
        if os.path.exists(fp):
            out[key] = json.load(open(fp, encoding="utf8"))

    for key, fn in (("experiments", "experiments.json"), ("e5", "e5.json")):
        fp = os.path.join(P, fn)
        if os.path.exists(fp):
            out[key] = json.load(open(fp, encoding="utf8"))

    rtp = os.path.join(P, "regulatory_tools.json")
    if os.path.exists(rtp):
        out["regulatory_tools"] = json.load(open(rtp, encoding="utf8"))["summary"]

    m8p = os.path.join(P, "m8_m10.json")
    if os.path.exists(m8p):
        out["m8_m10"] = json.load(open(m8p, encoding="utf8"))["summary"]

    out["extraction_audit"] = ext_stats
    out["adjudication"] = adj

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(out, open(OUT_JSON, "w", encoding="utf8"), indent=1, ensure_ascii=False)

    # CSVs
    with open(os.path.join(P, "construct_table.csv"), "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(os.path.join(P, "evidence_map.csv"), "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=["bite_domain", "crime_type", "n"])
        w.writeheader(); w.writerows(out["evidence_map"])

    for k, v in prisma.items():
        print("%-42s %s" % (k, v))
    print()
    for r in rows:
        print("%-16s %4d/%-4d %5s%%" % (r["construct"], r["n_reported_verified"], r["N"], r["pct"]))
    print("ANALYSE_DONE")


if __name__ == "__main__":
    main()
