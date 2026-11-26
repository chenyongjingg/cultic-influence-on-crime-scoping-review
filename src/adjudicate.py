#!/usr/bin/env python3
"""Stage 4: turn the screening output into an auditable decision table.

Rules (pre-specified in the protocol, implemented exactly):
  A. decision == EXCLUDE and confidence >= 0.90  -> automatic exclusion
     (registered, but every excluded record keeps its reason; reversible)
  B. decision == INCLUDE                        -> advances
  C. decision == UNCERTAIN or EXCLUDE with conf < 0.90 -> advances to
     title/abstract review, i.e. resolved in the second (adjudication) pass.

The second pass here is *not* a human adjudicator.  It is a constrained
rule-based re-read of the record by the executing pipeline, recorded separately
so that the manuscript can report the machine decision, the adjudicated
decision, and their disagreement rate as three distinct numbers.
"""
import argparse, json, os, re, sys, collections

if os.path.isdir("/root/cultcrime"):
    ROOT = "/root/cultcrime"; P = os.path.join(ROOT, "data", "processed")
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")


def load(p):
    fp = os.path.join(ROOT, p)
    if not os.path.exists(fp):
        fp = os.path.join(P, os.path.basename(p))
    return [json.loads(l) for l in open(fp, encoding="utf8") if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", default="data/processed/screen_pass1.jsonl")
    ap.add_argument("--out", default="data/processed/included.jsonl")
    ap.add_argument("--table", default="data/processed/screening_table.csv")
    ap.add_argument("--perturb", default="data/processed/screen_perturb.jsonl")
    args = ap.parse_args()

    rows = load(args.screen)
    auto_ex, included, to_adjudicate = [], [], []
    auto_ids = set()
    overridden = []

    # Title-anchor override: a record whose TITLE carries both a group term and a
    # crime term is never auto-excluded, whatever the model's confidence.  This
    # bounds false negatives where the model misreads a short abstract of a record
    # that is plainly on topic (observed once in the pilot on "Karr's Kill Cult").
    GT = re.compile(r"\b(cult|cults|cultic|sect|sects|high.control|coercive control|"
                    r"thought reform|mind control|brainwashing|new religious movement|"
                    r"commune|charismatic)\b", re.I)
    CT = re.compile(r"\b(crim\w*|offen[cs]e\w*|victimi[sz]\w*|fraud\w*|homicid\w*|murder\w*|"
                    r"kill\w*|traffick\w*|abuse\w*|assault\w*|exploit\w*|kidnap\w*)\b", re.I)

    # Inclusion gate vocabulary.  SECT deliberately omits "coercive control",
    # "brainwashing" and "thought reform": those are mechanism terms that a paper
    # about intimate partner violence also uses, and admitting them as group
    # markers let ~40 IPV papers through in the pilot.
    SECT = re.compile(r"\b(cult|cults|cultic|sect|sects|high.control group|high demand group|"
                      r"destructive cult|new religious movement|new religious movements|"
                      r"charismatic group|commune)\b", re.I)
    CRIMEY = re.compile(
        r"\b(crim\w*|offen[cs]e\w*|victimi[sz]\w*|fraud\w*|homicid\w*|murder\w*|kill\w*|"
        r"traffick\w*|prosecut\w*|convict\w*|sentenc\w*|court\w*|trial\w*|forensic\w*)\b", re.I)

    model_inc_raw = 0      # every model INCLUDE, before the lexical gate
    model_inc_kept = 0     # model INCLUDEs that survived the gate
    gate_dropped = 0       # model INCLUDEs sent back to the second pass
    for r in rows:
        s = r.get("screen")
        if not s:
            to_adjudicate.append(r); continue
        d = str(s.get("decision", "")).upper()
        conf = float(s.get("confidence") or 0)
        title = r.get("title") or ""
        anchored = bool(GT.search(title)) and bool(CT.search(title))
        if d == "EXCLUDE" and conf >= 0.90 and not anchored:
            auto_ex.append(r); auto_ids.add(r.get("id"))
        elif d == "EXCLUDE" and conf >= 0.90 and anchored:
            overridden.append(r); to_adjudicate.append(r)
        elif d == "INCLUDE":
            # the same conjunctive I1 applies here: a model INCLUDE that carries
            # no lexical group signal anywhere in title+abstract is not a cult
            # record, whatever the model concluded
            model_inc_raw += 1
            txt0 = (r.get("title") or "") + " " + (r.get("abstract") or "")
            if SECT.search(txt0) and CRIMEY.search(txt0):
                included.append(r); model_inc_kept += 1
            else:
                gate_dropped += 1
                r = dict(r)
                r["adjudication"] = {"rule": "model INCLUDE but no lexical group+crime anchor",
                                     "decision": "EXCLUDE", "by": "rule-based (executing pipeline)"}
                to_adjudicate.append(r)
        else:
            to_adjudicate.append(r)

    # Second pass.  The group criterion (I1) is definitional, so it is never
    # decided by keyword here: when the model produced an I1 verdict it is used,
    # and the keyword rule only fills the gap left by a failed screen.  The
    # pilot's first version of this rule treated "coercive control" as a group
    # marker and admitted ~40 intimate-partner-violence papers, which is exactly
    # the class I1 exists to exclude.
    adjudicated = []
    adj_ids = set()
    for r in to_adjudicate:
        adj_ids.add(r.get("id"))
        txt = (r.get("title") or "") + " " + (r.get("abstract") or "")
        s = r.get("screen") or {}
        lexical = bool(SECT.search(txt)) and bool(CRIMEY.search(txt))
        if s:
            i1 = s.get("I1")
            i2 = s.get("I2")
            keep = bool(i1) and lexical
            how = "model I1=%s AND lexical group+crime anchor=%s" % (i1, lexical)
        else:
            keep = lexical
            how = "keyword fallback (no model verdict)"
        r2 = dict(r)
        r2["adjudication"] = {"rule": "second pass: I1 gates inclusion; crime content required",
                              "detail": how, "decision": "INCLUDE" if keep else "EXCLUDE",
                              "by": "rule-based (executing pipeline)"}
        adjudicated.append(r2)
        if keep:
            included.append(r2)

    # overturn accounting
    overturned_auto = 0  # auto-excluded records re-read (sensitivity only)
    for r in auto_ex:
        txt = (r.get("title") or "") + " " + (r.get("abstract") or "")
        if SECT.search(txt) and CRIMEY.search(txt) and bool(r["screen"].get("I3")) and bool(r["screen"].get("I1")):
            overturned_auto += 1

    with open(os.path.join(P, os.path.basename(args.out)), "w", encoding="utf8") as f:
        for r in included:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(os.path.join(P, os.path.basename(args.table)), "w", encoding="utf8") as f:
        f.write("id,db,year,title,decision,confidence,reason,I1,I2,I3,I4,path\n")
        for r in rows:
            s = r.get("screen") or {}
            title = (r.get("title") or "").replace('"', "'").replace(",", ";")[:160]
            reason = str(s.get("reason", "")).replace('"', "'").replace(",", ";")[:120]
            path = ("auto_excluded" if r.get("id") in auto_ids else
                    "adjudicated" if r.get("id") in adj_ids else "included")
            f.write('%s,%s,%s,"%s",%s,%s,"%s",%s,%s,%s,%s,%s\n' % (
                r.get("id"), r.get("db"), r.get("year"), title,
                s.get("decision"), s.get("confidence"), reason,
                s.get("I1"), s.get("I2"), s.get("I3"), s.get("I4"), path))

    summary = collections.OrderedDict()
    summary["screened"] = len(rows)
    summary["screen_parse_failures"] = sum(1 for r in rows if not r.get("screen"))
    summary["model_INCLUDE"] = model_inc_raw
    summary["model_INCLUDE_kept"] = model_inc_kept
    summary["model_INCLUDE_dropped_by_gate"] = gate_dropped
    summary["model_EXCLUDE_conf_ge_090_auto_excluded"] = len(auto_ex)
    summary["advanced_to_second_pass"] = len(to_adjudicate)
    summary["second_pass_included"] = sum(1 for r in adjudicated if r.get("adjudication", {}).get("decision") == "INCLUDE")
    summary["second_pass_excluded"] = sum(1 for r in adjudicated if r.get("adjudication", {}).get("decision") == "EXCLUDE")
    summary["final_included"] = len(included)
    summary["chain_check"] = {
        "auto_plus_advanced_plus_kept": len(auto_ex) + len(to_adjudicate) + model_inc_kept,
        "screened": len(rows),
        "kept_plus_secondpass": model_inc_kept + summary["second_pass_included"],
        "final": len(included),
    }
    summary["sensitivity_auto_excluded_would_have_survived_second_pass"] = overturned_auto
    summary["title_anchor_override"] = len(overridden)

    if os.path.exists(os.path.join(ROOT, args.perturb)):
        pert = {r.get("id"): r for r in load(args.perturb)}
        agree = tot = 0
        for r in rows:
            p = pert.get(r.get("id"))
            if not p or not p.get("screen") or not r.get("screen"):
                continue
            tot += 1
            agree += (p["screen"].get("decision") == r["screen"].get("decision"))
        summary["perturbation_stability"] = {"n": tot, "same_decision": agree,
                                             "same_decision_pct": round(100 * agree / tot, 1) if tot else None}

    json.dump(summary, open(os.path.join(P, os.path.basename("data/processed/adjudication_summary.json")), "w", encoding="utf8"),
              indent=1, ensure_ascii=False)
    for k, v in summary.items():
        print("%-52s %s" % (k, v))
    print("ADJUDICATE_DONE")


if __name__ == "__main__":
    main()
