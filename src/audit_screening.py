#!/usr/bin/env python3
"""Full-corpus audit of the screening decisions.

Four measurements, none of which is a human read and none of which is presented as
one. The point is to replace "we do not know how good the screen was" with counts
that a reader can check, and to shrink the set that a human still has to read to the
records where the machine's own evidence does not support its decision.

  A. Rule replay. Every stored decision is re-derived from the stored flags, and
     every inclusion is re-derived from the stored fields using the gates exactly as
     adjudicate.py applies them (title-anchor override, confidence threshold, lexical
     group+crime anchor, second pass on model I1). Zero mismatches means the artefact
     does what Section 2.4 says; it says nothing about whether the model was right.

  B. Metaphor screen. "Cult" used as a figure of speech, over title and abstract. A
     record is flagged when every group-term occurrence in its text lies inside a
     metaphorical phrase, so that nothing is left once those phrases are removed.

  C. Evidence-span screen. Included records for which neither the title nor the
     model's own quoted I1 evidence names a group. The model asserted the group
     criterion; this asks whether its own evidence shows one. This is the sharpest
     automated proxy for the error class the 50-record read found.

  D. Sensitivity. Every headline percentage recomputed with each flagged set
     removed, so the size of the dependence is stated rather than asserted.

The vocabularies below were written before the audit was run and are not tuned to
the validation sample. No record is removed by this script: it produces the audit.
"""
import io, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "out", "server_snapshot", "data", "processed")
OUT_JSON = os.path.join(ROOT, "out", "data", "screening_audit.json")
OUT_MD = os.path.join(ROOT, "out", "supplements", "S9_screening_audit.md")

# Gate vocabularies, copied from adjudicate.py so the replay uses the same rules.
GT = re.compile(r"\b(cult|cults|cultic|sect|sects|high.control|coercive control|"
                r"thought reform|mind control|brainwashing|new religious movement|"
                r"commune|charismatic)\b", re.I)
CT = re.compile(r"\b(crim\w*|offen[cs]e\w*|victimi[sz]\w*|fraud\w*|homicid\w*|murder\w*|"
                r"kill\w*|traffick\w*|abuse\w*|assault\w*|exploit\w*|kidnap\w*)\b", re.I)
SECT = re.compile(r"\b(cult|cults|cultic|sect|sects|high.control group|high demand group|"
                  r"destructive cult|new religious movement|new religious movements|"
                  r"charismatic group|commune)\b", re.I)
CRIMEY = re.compile(r"\b(crim\w*|offen[cs]e\w*|victimi[sz]\w*|fraud\w*|homicid\w*|murder\w*|"
                    r"kill\w*|traffick\w*|prosecut\w*|convict\w*|sentenc\w*|court\w*|trial\w*|"
                    r"forensic\w*)\b", re.I)

# Audit vocabulary. Wider than SECT: it admits inflections and the non-English forms
# that appear in this corpus, so that a record naming a group is not flagged merely
# because it names it in Portuguese, Italian or French.
GROUP = re.compile(r"\b(cults?|cultic|cultism|cultlike|cult-?like|sects?|sectarian\w*|"
                   r"high.control group\w*|high.demand group\w*|destructive cult\w*|"
                   r"new religious movement\w*|nrms?|charismatic group\w*|communes?|"
                   r"sectes?|cultes?|setta|sette)\b", re.I)

# "Cult" naming a taste community, a genre or a metaphorical following.
METAPHOR = re.compile(
    r"\b(cult (classic|classics|film|films|movie|movies|favourite|favorite|following|"
    r"status|hero|heroes|figure|figures|novel|novels|comic|comics|tv|television|"
    r"hit|band|album|show|series|book|books|video|game|games)"
    r"|personality cult|cult of personality|cult of celebrity|cult of youth|"
    r"cult of the body|fitness cult|health cult|cult brand|political cult of)\b", re.I)


def load(p):
    return [json.loads(l) for l in io.open(p, encoding="utf8")]


def replay_decision(s):
    flags = [bool(s.get("I1")), bool(s.get("I2")), bool(s.get("I3")), bool(s.get("I4"))]
    dm = str(s.get("decision_model") or "").upper()
    if all(flags):
        return "INCLUDE"
    if not any(flags):
        return "EXCLUDE"
    if "UNCERTAIN" in dm and not any(flags):
        return "UNCERTAIN"
    if sum(flags) >= 3:
        return "UNCERTAIN"
    return "EXCLUDE"


def replay_inclusion(r):
    """adjudicate.py, re-implemented on the stored fields."""
    s = r.get("screen")
    title = r.get("title") or ""
    txt = title + " " + (r.get("abstract") or "")
    lexical = bool(SECT.search(txt)) and bool(CRIMEY.search(txt))
    if s is None:
        return lexical
    d = str(s.get("decision", "")).upper()
    conf = float(s.get("confidence") or 0)
    anchored = bool(GT.search(title)) and bool(CT.search(title))
    if d == "EXCLUDE" and conf >= 0.90 and not anchored:
        return False          # auto-excluded, never reaches a decision
    if d == "INCLUDE":
        return lexical        # model INCLUDE, kept only with the lexical anchor
    return bool(s.get("I1")) and lexical   # second pass


def main():
    rows = load(os.path.join(P, "screen_14b_dedup.jsonl"))
    inc_ids = {r["id"] for r in load(os.path.join(P, "included.jsonl"))}
    extracted = load(os.path.join(P, "extracted.jsonl"))
    by = {r["id"]: r for r in rows}

    a_mismatch = []
    replay_inc = set()
    for r in rows:
        s = r.get("screen")
        if s is not None and replay_decision(s) != s.get("decision"):
            a_mismatch.append(r["id"])
        if replay_inclusion(r):
            replay_inc.add(r["id"])

    # B. metaphor, whole corpus
    meta_all, meta_inc = [], []
    for r in rows:
        t = (r.get("title") or "") + " " + (r.get("abstract") or "")
        if METAPHOR.search(t) and not GROUP.search(METAPHOR.sub(" ", t)):
            meta_all.append(r["id"])
            if r["id"] in inc_ids:
                meta_inc.append(r["id"])

    # C. included, no group named in title or in the model's own I1 evidence
    no_evidence = []
    for i in inc_ids:
        r = by.get(i) or {}
        s = r.get("screen") or {}
        t = (r.get("title") or "") + " " + (s.get("I1_q") or "")
        if not GROUP.search(t):
            no_evidence.append(i)

    flagged = sorted(set(meta_inc) | set(no_evidence))

    # D. sensitivity over the abstract-bearing included records
    CON = ["C1_group_def", "C2_role", "C3_duration", "C5_instrument", "C8_legal"]
    meas = [r for r in extracted if (r.get("abstract") or "").strip()]

    def rates(keep):
        sub = [r for r in meas if r["id"] in keep]
        n = len(sub)
        return {c: {"n": sum(1 for r in sub if (r.get("extraction") or {}).get(c, {}).get("v")),
                    "N": n, "pct": round(100.0 * sum(1 for r in sub
                                                     if (r.get("extraction") or {}).get(c, {}).get("v")) / n, 1)
                    if n else None} for c in CON}

    all_meas = {r["id"] for r in meas}
    base = rates(all_meas)
    variants = {"minus_metaphor": all_meas - set(meta_inc),
                "minus_no_group_evidence": all_meas - set(no_evidence),
                "minus_union": all_meas - set(flagged)}
    sens = {k: {"N": len(v), "rates": rates(v)} for k, v in variants.items()}
    drift = {c: round(max(abs(sens[k]["rates"][c]["pct"] - base[c]["pct"]) for k in sens
                          if sens[k]["rates"][c]["pct"] is not None), 1) for c in CON}

    audit = {
        "n_screened": len(rows), "n_included": len(inc_ids),
        "A_rule_replay": {"decision_mismatches": len(a_mismatch),
                          "decision_mismatch_ids": a_mismatch[:10],
                          "replay_included": len(replay_inc),
                          "inclusion_mismatch": len(replay_inc ^ inc_ids)},
        "B_metaphor": {"all": len(meta_all), "included": len(meta_inc),
                       "included_ids": meta_inc},
        "C_no_group_evidence": {"included": len(no_evidence), "ids": no_evidence,
                                "titles": [(by.get(i, {}).get("title") or "")[:140] for i in no_evidence]},
        "flagged_for_human_read": {"n": len(flagged), "ids": flagged},
        "D_sensitivity": {"measured_N": len(meas), "base": base, "variants": sens,
                          "max_abs_drift_pp": drift},
    }
    json.dump(audit, io.open(OUT_JSON, "w", encoding="utf8"), indent=1, ensure_ascii=False)

    L = ["# S9. Full-corpus audit of the screening decisions\n",
         "This is not a human adjudication and is not presented as one. It is the part "
         "of the check that can be computed: the decisions are replayed from the stored "
         "fields, the two error classes the 50-record read identified are counted over "
         "the whole corpus, and every headline percentage is recomputed with the "
         "flagged records removed.\n",
         "## A. Does the artefact do what Section 2.4 says\n",
         "| Check | Result |",
         "|---|---|",
         "| Decisions re-derived from the four flags | %d of %d differ |" % (len(a_mismatch), len(rows)),
         "| Inclusions re-derived from the stored fields, against `included.jsonl` | %d symmetric difference |"
         % audit["A_rule_replay"]["inclusion_mismatch"],
         "",
         "A zero here is a check on the pipeline, not on the model: it shows that the "
         "rule described in the paper is the rule the artefact applied.\n",
         "## B. \"Cult\" as a figure of speech, whole corpus\n",
         "| | Records |", "|---|---|",
         "| Text in which every group term is metaphorical | %d of %d screened |" % (len(meta_all), len(rows)),
         "| ... of which included | %d |" % len(meta_inc), ""]
    for i in meta_inc:
        L.append("- `%s` — %s" % (i, (by[i].get("title") or "")[:160]))
    L += ["",
          "## C. Included records whose own evidence names no group\n",
          "Neither the title nor the span the model quoted in support of the group "
          "criterion contains a group term. The criterion may still be true — a record "
          "can name a specific group without using a generic word — but the model's own "
          "evidence does not show it, and these are the records where it is most likely "
          "to have gone wrong.\n",
          "**%d of %d included records.**\n" % (len(no_evidence), len(inc_ids))]
    for i in no_evidence:
        L.append("- `%s` — %s" % (i, (by.get(i, {}).get("title") or "")[:160]))
    L += ["",
          "The union of B and C is **%d records**; that is the list a human should read.\n"
          % len(flagged),
          "## D. How much of the result depends on the flagged records\n",
          "Percentages over the %d included records carrying an abstract.\n" % len(meas),
          "| Construct | Base | Minus metaphor | Minus no-group-evidence | Minus both | Max drift (pp) |",
          "|---|---|---|---|---|---|"]
    for c in CON:
        b = base[c]
        cells = ["%s (%d/%d)" % (sens[k]["rates"][c]["pct"], sens[k]["rates"][c]["n"], sens[k]["rates"][c]["N"])
                 for k in ("minus_metaphor", "minus_no_group_evidence", "minus_union")]
        L.append("| %s | %s (%d/%d) | %s | %s | %s | %s |" % (c, b["pct"], b["n"], b["N"], *cells, drift[c]))
    L += ["",
          "No record was removed: the corpus reported in the manuscript is unchanged by "
          "this table. What the table shows is the size of the dependence, which is what "
          "a reader needs in order to decide how much weight the percentages carry."]
    io.open(OUT_MD, "w", encoding="utf8").write("\n".join(L))

    print("A: decisions %d/%d differ; inclusion symmetric difference %d"
          % (len(a_mismatch), len(rows), audit["A_rule_replay"]["inclusion_mismatch"]))
    print("B: %d metaphor-only records (%d included)" % (len(meta_all), len(meta_inc)))
    print("C: %d included records name no group in title or I1 evidence" % len(no_evidence))
    print("union flagged for human read: %d" % len(flagged))
    print("D: max drift pp =", drift)
    print("written:", OUT_MD)


if __name__ == "__main__":
    main()
