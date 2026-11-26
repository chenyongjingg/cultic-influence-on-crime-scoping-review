#!/usr/bin/env python3
"""Stage 6-7: abstract-level extraction of reporting-completeness constructs.

Contract enforced by code (the protocol's "string back-check"):
  * a construct is REPORTED only with a verbatim anchor (<=18 words) copied from
    the record; every anchor is re-checked against the source text, and a flag
    whose anchor is not found is demoted to UNVERIFIED and counted;
  * absence is recorded as "not reported", never inferred;
  * the unit measured is TITLE+ABSTRACT.  Stated in the manuscript: what is
    measured is what the literature shows at its reading interface.
"""
import argparse, json, os, re, sys, time, unicodedata

ROOT = "/root/cultcrime"
sys.path.insert(0, os.path.join(ROOT, "src"))
from llm import LLM

CONSTRUCTS = {
 "C1_group_def":   "states how the group was identified as a cult / high-control group (explicit definitional criterion or named checklist)",
 "C2_role":        "distinguishes participant roles (leader, core executor, ordinary member, victim, former member) rather than only 'cult member'",
 "C3_duration":    "states a duration: time in the group, or time since leaving",
 "C4_mechanism":   "names a manipulation mechanism with an explicit term (indoctrination, coercive control, thought reform, mind control, isolation, trauma bonding)",
 "C5_instrument":  "names a standardised psychological instrument or scale used to measure manipulation or group abuse",
 "C6_offence":     "specifies the criminal offence(s) by type (homicide, fraud, sexual abuse, trafficking, ...)",
 "C7_severity":    "grades offence severity (statutory or study-internal severity level, or sentence length)",
 "C8_legal":       "reports a legal or judicial outcome (charge, conviction, sentence, responsibility finding, court ruling)",
 "C9_jurisdiction":"states the jurisdiction (country, state or legal system) of the events or the proceeding",
 "C10_source":     "states where the data came from or how participants were recruited",
 "C11_comparison": "reports a comparison group, baseline, or an explicit statement that none was used",
 "C12_n":          "reports a sample size (n) for the persons, cases or documents analysed",
}
ORDER = list(CONSTRUCTS)

SYS = ("You extract structured evidence from a title and abstract. You copy short verbatim spans; "
       "you never paraphrase an anchor and you never supply what the text does not say.")

HEAD = ("Constructs (true only if the TEXT states it):\n"
        + "\n".join("- %s: %s" % (k, v) for k, v in CONSTRUCTS.items()) +
        "\n\nbite_domains: subset of [behaviour, information, thought, emotion] that the text names or squarely describes.\n"
        "crime_types: offence types actually named in the text. theory_terms: named theories actually cited.\n\n")

FMT = """Answer with one line per construct, in this exact form and in this order.
Use YES only when the TEXT states it. Copy the quote character for character from the TEXT;
the quote must be at most 18 words. When the answer is NO, put an empty quote.

C1: YES|NO | "quote or empty"
C2: YES|NO | "quote or empty"
C3: YES|NO | "quote or empty"
C4: YES|NO | "quote or empty"
C5: YES|NO | "quote or empty"
C6: YES|NO | "quote or empty"
C7: YES|NO | "quote or empty"
C8: YES|NO | "quote or empty"
C9: YES|NO | "quote or empty"
C10: YES|NO | "quote or empty"
C11: YES|NO | "quote or empty"
C12: YES|NO | "quote or empty"
BITE: comma-separated subset of behaviour, information, thought, emotion
CRIMES: comma-separated offence types named in the text
THEORIES: comma-separated named theories cited in the text"""

LINE = re.compile(r"^\s*(C\d+)[:.]?\s*(YES|NO|TRUE|FALSE)\b\s*\|?\s*(.*)$", re.I | re.M)
TAGS = re.compile(r"^\s*(BITE|CRIMES|THEORIES)\s*:\s*(.*)$", re.I | re.M)


def parse_lines(text):
    """Parse the checklist format.  Returns (verdicts, extras) or None."""
    pairs = LINE.findall(text)
    if len({k.upper() for k, _, _ in pairs}) < 10:
        return None
    verdicts = {}
    for key, verdict, tail in pairs:
        key = key.upper()
        if key in verdicts:
            continue
        q = (tail or "").strip().strip('"').strip("“”").strip()
        verdicts[key] = (verdict.upper() in ("YES", "TRUE"), q[:200])
    extras = {}
    for tag, val in TAGS.findall(text):
        extras[tag.upper()] = [v.strip() for v in re.split(r"[,;]", val.strip().strip('"'))
                               if v.strip()][:12]
    return verdicts, extras


def norm(s):
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", s).strip()


def anchor_ok(anchor, text):
    a = norm(anchor)
    if len(a) < 8:
        return False
    if a in norm(text):
        return True
    frags = [p.strip() for p in re.split(r"\.\.\.|\[…\]|…", a) if len(p.strip()) >= 12]
    return bool(frags) and all(f in norm(text) for f in frags)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/root/cultcrime/models/Qwen2.5-7B-Instruct")
    ap.add_argument("--inp", default="data/processed/included.jsonl")
    ap.add_argument("--out", default="data/processed/extracted.jsonl")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    llm = LLM(args.model)
    recs = [json.loads(l) for l in open(os.path.join(ROOT, args.inp))]
    if args.limit:
        recs = recs[:args.limit]

    def prompt(r):
        ab = (r.get("abstract") or "").strip()
        if len(ab) > 1700:
            ab = ab[:1700] + " [...]"
        return [{"role": "system", "content": SYS},
                {"role": "user", "content": HEAD + "TITLE: %s\nTEXT: %s\n\n%s"
                 % (r.get("title") or "", ab, FMT)}]

    fout = open(os.path.join(ROOT, args.out), "w")
    stats = {"records": 0, "parse_fail": 0, "flags_true": 0, "verified": 0, "unverified": 0,
             "concurrency": args.concurrency}
    t0 = time.time()
    B = args.concurrency
    for s in range(0, len(recs), B):
        batch = recs[s:s + B]
        outs = llm.generate([prompt(r) for r in batch], max_new_tokens=560)
        for r, o in zip(batch, outs):
            parsed = parse_lines(o)
            if parsed is None:
                stats["parse_fail"] += 1
                fout.write(json.dumps({**r, "extraction": None, "error": "parse_failure"},
                                      ensure_ascii=False) + "\n")
                continue
            verdicts, extras = parsed
            src = (r.get("title") or "") + " " + (r.get("abstract") or "")
            clean = {}
            for k in ORDER:
                v, q = verdicts.get(k.upper().split("_")[0], (False, ""))
                if v:
                    stats["flags_true"] += 1
                    if anchor_ok(q, src):
                        clean[k] = {"v": True, "q": q}; stats["verified"] += 1
                    else:
                        clean[k] = {"v": "UNVERIFIED", "q": q}; stats["unverified"] += 1
                else:
                    clean[k] = {"v": False, "q": ""}
            for k, src_tag in (("bite_domains", "BITE"), ("crime_types", "CRIMES"),
                               ("theory_terms", "THEORIES")):
                clean[k] = extras.get(src_tag, [])
            fout.write(json.dumps({**r, "extraction": clean}, ensure_ascii=False) + "\n")
            stats["records"] += 1
        fout.flush()
        if s % (B * 10) == 0:
            el = time.time() - t0
            print("extracted %d/%d  %.0fs  eta %.0fs  unverified=%d"
                  % (stats["records"], len(recs), el,
                     el / max(stats["records"], 1) * (len(recs) - stats["records"]), stats["unverified"]),
                  flush=True)
    fout.close()
    json.dump(stats, open(os.path.join(ROOT, "data/processed/extract_stats.json"), "w"), indent=1)
    print("EXTRACT_DONE", stats)


if __name__ == "__main__":
    main()
