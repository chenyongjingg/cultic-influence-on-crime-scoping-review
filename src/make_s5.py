#!/usr/bin/env python3
"""Supplementary table S5: sensitivity analyses E1-E8 and the M8-M10 summary."""
import json, os

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "out", "supplements")
os.makedirs(OUT, exist_ok=True)


def jl(name):
    fp = os.path.join(P, name)
    return json.load(open(fp)) if os.path.exists(fp) else None


exp = jl("experiments.json") or {}
e5 = jl("e5.json") or {}
m = jl("m8_m10.json") or {}
val = jl("exp1_detector_validation.json")
lift = jl("fulltext_lift.json")
terms = jl("exp4_terms.json")
strata = jl("exp3_strata.json")

L = ["# Table S5. Sensitivity analyses and subsidiary diagnostics\n"]

L.append("## E1. Automatic-exclusion confidence threshold\n")
L.append("| Threshold | Auto-excluded | Advanced to second pass | Advanced (%) |")
L.append("|---|---|---|---|")
for r in (exp.get("E1_confidence_threshold") or {}).get("sweep", []):
    L.append("| %.2f | %d | %d | %.1f |" % (r["threshold"], r["auto_excluded"],
                                             r["advanced"], r["advanced_pct"]))
L.append("\nThe sweep is flat between 0.60 and 0.90 because the model's stated "
         "confidence is concentrated at 0.90 and 0.95; it is not a graded dial.\n")

L.append("## E2. Conjunctive vs disjunctive group criterion\n")
e2 = exp.get("E2_i1_conjunction") or {}
L.append("- conjunctive (lexical anchor AND model verdict): **%s**" % e2.get("conjunctive_n"))
L.append("- disjunctive (model verdict only): **%s**" % e2.get("disjunctive_n"))
L.append("- records admitted only by the disjunctive reading: **%s** — %s\n"
         % (e2.get("extra_if_disjunctive"), e2.get("extra_composition")))

L.append("## E3. Per-source independent contribution\n")
e3 = exp.get("E3_source_contribution") or {}
L.append("| Source | Raw rows | Records no other source returned |")
L.append("|---|---|---|")
for s, n in (e3.get("records_per_source_raw") or {}).items():
    L.append("| %s | %d | %d |" % (s, n, (e3.get("source_exclusive_records") or {}).get(s, 0)))
L.append("\nUnique records overall: %s\n" % e3.get("n_unique_overall"))

L.append("## E4. Year and language restriction\n")
for k, v in (exp.get("E4_restriction_sensitivity") or {}).items():
    if k != "language_breakdown":
        L.append("- %s: %s" % (k, v))
L.append("")

L.append("## E5. 7B vs 14B screening agreement\n")
if e5:
    L.append("Over %s records screened by both layers:\n" % e5.get("n"))
    L.append("| Quantity | Agreement | Cohen's kappa |")
    L.append("|---|---|---|")
    d = e5.get("decision") or {}
    L.append("| Decision | %s%% | %s |" % (d.get("agree_pct"), d.get("kappa")))
    for k in ("I1", "I2", "I3", "I4"):
        v = e5.get(k) or {}
        L.append("| %s | %s%% | %s |" % (k, v.get("agree_pct"), v.get("kappa")))
    L.append("\nINCLUDE counts — 7B: %s, 14B: %s\n"
             % (e5.get("include_counts", {}).get("7B"), e5.get("include_counts", {}).get("14B")))
else:
    L.append("_Not run._\n")

L.append("## E6. Detector validation against a hand read (29 records)\n")
if val:
    L.append("| Construct | both | missed by detector | detector over-fired | precision | recall |")
    L.append("|---|---|---|---|---|---|")
    for k, v in val["per_construct"].items():
        L.append("| %s | %d | %d | %d | %s | %s |"
                 % (k, v["both"], v["manual_only"], v["det_only"], v["precision"], v["recall"]))
    L.append("\nOverall precision %.3f, recall %.3f over %d records. The detectors "
             "under-count; they do not over-count."
             % (val["overall"]["precision"], val["overall"]["recall"], val["n_records"]))
    L.append("")
else:
    L.append("_Not run._\n")

L.append("## E7. Term-list perturbation (strict variant)\n")
if terms:
    L.append("| Construct | base | strict | delta (pp) |")
    L.append("|---|---|---|---|")
    for k, v in terms["constructs"].items():
        L.append("| %s | %d/%d (%.1f%%) | %d/%d (%.1f%%) | %+.1f |"
                 % (k, v["base_n"], terms["N"], v["base_pct"], v["strict_n"], terms["N"],
                    v["strict_pct"], v["delta_pp"]))
    L.append("\nThe two largest bars are the least robust: jurisdiction and data source "
             "lose 15 and 21 percentage points under a strict rule, while offence type "
             "loses 6. The ordering of the top four is therefore vocabulary-dependent;\n"
             "the gap to the bottom group is not.\n")
else:
    L.append("_Not run._\n")

L.append("## E8. Descriptive strata by decade (module M5)\n")
if strata:
    L.append("| Decade | N | offence | jurisdiction | instrument | comparison |")
    L.append("|---|---|---|---|---|---|")
    for name, v in strata["by_decade"].items():
        L.append("| %s | %d | %.1f%% | %.1f%% | %.1f%% | %.1f%% |"
                 % (name, v["N"], v["C6_offence"]["pct"], v["C9_jurisdiction"]["pct"],
                    v["C5_instrument"]["pct"], v["C11_comparison"]["pct"]))
    L.append("\nJurisdiction strata are omitted: stratifying on a detector, then "
             "reporting that same detector inside each stratum, is circular. Only the "
             "decade split carries information.\n")
else:
    L.append("_Not run._\n")

L.append("## E9. Full-text lift, paired on the same records")
if lift:
    L.append("| Construct | abstract | matched window | full text | lift vs window (pp) |")
    L.append("|---|---|---|---|---|")
    for k, v in lift["per_construct"].items():
        L.append("| %s | %d/%d | %d/%d | %d/%d | %+.1f |"
                 % (k, v["abstract_n"], lift["n_pairs"], v["window_n"], lift["n_pairs"],
                    v["fulltext_n"], lift["n_pairs"], v["lift_window_pp"]))
    L.append("Full text obtainable for %d of %d measurable records (%.1f%%). "
             "The matched window is the length control: it reports no more than the "
             "abstract for nine of twelve constructs."
             % (lift["n_pairs"], lift["corpus_n"], lift["availability_pct"]))
else:
    L.append("_Not run._")

if m:
    L.append("## M8-M10 coding summary (N = %s)\n" % m["summary"]["N"])
    L.append("| Module | Code | n | % |")
    L.append("|---|---|---|---|")
    for mod, codes in m["summary"]["modules"].items():
        for code, v in codes.items():
            L.append("| %s | %s | %d | %.1f |" % (mod, code, v["n"], v["pct"]))
    L.append("")

open(os.path.join(OUT, "S5_sensitivity_and_modules.md"), "w").write("\n".join(L))
print("S5 written", len("\n".join(L)), "chars")
