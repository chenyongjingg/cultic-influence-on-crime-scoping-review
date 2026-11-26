#!/usr/bin/env python3
"""Stage 3: LLM-assisted title/abstract screening (one record per prompt).

Disclosed design (goes into Methods verbatim in substance):
  * one fixed open-weight model, greedy decoding, fixed seed, concurrency
    recorded; a prompt-perturbation re-run estimates decision stability and is
    reported as stability, never as an inter-rater statistic;
  * structured output per record: four criterion verdicts each with a verbatim
    span, then decision, reason, confidence.  Asking for the span before the
    verdict forces the model to locate evidence instead of pattern-matching a
    default answer; the pilot showed the default answer was "everything is
    irrelevant" when the verdict came first;
  * auto-exclusion requires EXCLUDE with confidence >= 0.90 AND no title anchor
    (a title carrying both a group term and a crime term is never auto-dropped);
  * every record, included or auto-excluded, is written out with its reason.
"""
import argparse, json, os, sys, time

ROOT = "/root/cultcrime"
sys.path.insert(0, os.path.join(ROOT, "src"))
from llm import LLM, extract_json

MAX_ABS = 1500

CRITERIA = """I1 GROUP: a cult, high-control group, coercive-control group, new religious movement or similar organisation is a topic of the record. FALSE when "cult" only means a film/art/fashion following, a habit ("the cult of the double-blind trial"), or a metaphor. FALSE when the people involved are a couple, a family, a workplace or a commercial sex arrangement: intimate partner violence, domestic abuse and trafficking WITHOUT a high-control group are not cults. FALSE for shared psychotic disorder between two people.
I2 CRIME: crimes, criminal conduct or the criminal-justice process are a topic of the record - offending, victimisation, investigation, prosecution, sentencing, criminal responsibility, forensic evaluation in a criminal matter. FALSE when the record is only about psychological distress, well-being, or non-criminal deviance.
I3 MECHANISM: the record says something about HOW influence works or what it does to members (manipulation, indoctrination, coercive control, isolation, obedience, group pressure). FALSE when the word appears only as a label in a keyword list with no content behind it.
I4 MATERIAL: the record carries data, cases, legal or forensic documents, or a systematic or descriptive review. FALSE for a purely opinion or editorial piece with neither data nor case analysis."""

CRITERIA_PERTURBED = """I1 GROUP: the text deals with a cult or comparable high-control organisation as one of its topics. A metaphor, a habit, or a fan following does not satisfy this.
I2 CRIME: the text deals with criminal behaviour or with the criminal-justice process. Distress or general harm alone is insufficient.
I3 MECHANISM: the text says how influence operates, or what it does to people, rather than just using the word.
I4 MATERIAL: the text carries data, cases, documents, or a review. Comment without data or case analysis is insufficient."""

EXAMPLES = """Worked examples (abbreviated):

EXAMPLE 1
TITLE: Linguistic Functions of "Verb" in Lyrical Poems
ABSTRACT: Lyrical literature expresses the feelings of the speaker; Persian poets of the sect...
ANSWER: {"I1": {"v": false, "q": ""}, "I2": {"v": false, "q": ""}, "I3": {"v": false, "q": ""}, "I4": {"v": true, "q": "analysis of the lyrical elements"}, "decision": "EXCLUDE", "reason": "Literary analysis; cult and crime are not topics.", "confidence": 0.95}

EXAMPLE 2
TITLE: Coercive control and older people: towards definitional consistency
ABSTRACT: Coercive control in intimate relationships involving older adults; we compare definitions used across studies of domestic abuse.
ANSWER: {"I1": {"v": false, "q": ""}, "I2": {"v": true, "q": "domestic abuse"}, "I3": {"v": true, "q": "compare definitions used across studies"}, "I4": {"v": true, "q": "we compare definitions used across studies"}, "decision": "EXCLUDE", "reason": "Coercive control in intimate relationships, not a high-control group.", "confidence": 0.9}

EXAMPLE 3
TITLE: Detecting Patterns of Intimate Partner Violence in Emergency Records
ABSTRACT: We apply text classification to police records of intimate partner violence to detect escalation patterns before a homicide.
ANSWER: {"I1": {"v": false, "q": ""}, "I2": {"v": true, "q": "a homicide"}, "I3": {"v": false, "q": ""}, "I4": {"v": true, "q": "We apply text classification"}, "decision": "EXCLUDE", "reason": "Intimate partner violence; no high-control group.", "confidence": 0.95}

EXAMPLE 4
TITLE: Brainwashing and battering fatigue: psychological abuse in a violent marriage
ABSTRACT: We describe the "brainwashing" process by which an abusive husband isolates his wife and dismantles her self-confidence, and the exhaustion that follows.
ANSWER: {"I1": {"v": false, "q": ""}, "I2": {"v": false, "q": ""}, "I3": {"v": true, "q": "an abusive husband isolates his wife"}, "I4": {"v": true, "q": "We describe"}, "decision": "EXCLUDE", "reason": "Coercive control within a marriage, not a cult group.", "confidence": 0.95}

EXAMPLE 5
TITLE: A Clinical and Forensic Account of a Group Homicide
TITLE: A Clinical and Forensic Account of a Group Homicide
ABSTRACT: Three members of a small religious commune killed a former member after the leader declared her apostate. We review the court record and the forensic assessment of diminished responsibility.
ANSWER: {"I1": {"v": true, "q": "small religious commune"}, "I2": {"v": true, "q": "the court record and the forensic assessment"}, "I3": {"v": true, "q": "after the leader declared her apostate"}, "I4": {"v": true, "q": "We review the court record"}, "decision": "INCLUDE", "reason": "Commune, homicide, court and forensic material all present.", "confidence": 0.95}"""

SYS = ("You are a screening assistant for a PRISMA-ScR scoping review on cultic influence on crime. "
       "You judge a title and abstract against four criteria and answer in strict JSON. "
       "You never invent content that is not in the text.")

FMT = """Return ONLY this JSON object, keys in exactly this order:
{"I1": {"v": true|false, "q": "<verbatim span from the text, <=15 words, or \\"\\" if false>"},
 "I2": {"v": true|false, "q": "..."},
 "I3": {"v": true|false, "q": "..."},
 "I4": {"v": true|false, "q": "..."},
 "decision": "INCLUDE"|"EXCLUDE"|"UNCERTAIN",
 "reason": "<max 20 words in English naming what decided it>",
 "confidence": <0.0-1.0>}
Judge on the whole text; a short abstract can still satisfy several criteria.
INCLUDE requires all four true. EXCLUDE when at least one criterion is clearly false.
UNCERTAIN when a criterion cannot be judged from the text given.
Use confidence >= 0.9 only when the text states the deciding fact explicitly."""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/root/cultcrime/models/Qwen2.5-7B-Instruct")
    ap.add_argument("--inp", default="data/processed/corpus.jsonl")
    ap.add_argument("--out", default="data/processed/screen_pass1.jsonl")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--perturb", action="store_true")
    args = ap.parse_args()

    llm = LLM(args.model)
    recs = [json.loads(l) for l in open(os.path.join(ROOT, args.inp))]
    if args.limit:
        recs = recs[:args.limit]
    if args.sample:
        import random
        random.Random(7).shuffle(recs)
        recs = recs[:args.sample]
    crit = CRITERIA_PERTURBED if args.perturb else CRITERIA
    tag = "perturb" if args.perturb else "1"

    def prompt(r):
        ab = (r.get("abstract") or "").strip()
        if len(ab) > MAX_ABS:
            ab = ab[:MAX_ABS] + " [...]"
        body = ("Criterion definitions:\n%s\n\n%s\n\nNow judge this record.\n\n"
                "TITLE: %s\nYEAR: %s | JOURNAL: %s\nABSTRACT: %s\n\n%s"
                % (crit, EXAMPLES, r.get("title") or "", r.get("year"),
                   (r.get("source") or "")[:80], ab or "(no abstract available)", FMT))
        return [{"role": "system", "content": SYS}, {"role": "user", "content": body}]

    fout = open(os.path.join(ROOT, args.out), "w")
    fails = 0
    t0 = time.time()
    B = args.concurrency
    for s in range(0, len(recs), B):
        batch = recs[s:s + B]
        outs = llm.generate([prompt(r) for r in batch], max_new_tokens=320)
        for r, o in zip(batch, outs):
            j = extract_json(o)
            if not isinstance(j, dict) or "decision" not in j:
                fails += 1
                fout.write(json.dumps({**r, "screen": None, "screen_error": "parse_failure",
                                       "pass": tag}, ensure_ascii=False) + "\n")
                continue
            # The gate is COMPUTED from the criterion flags, not taken from the
            # model's own "decision" field: the pilot showed the model asserting
            # INCLUDE while one of its own criteria was false.
            dec_model = str(j.get("decision", "")).upper()
            j["decision_model"] = dec_model
            try:
                j["confidence"] = round(float(j.get("confidence", 0)), 3)
            except Exception:
                j["confidence"] = 0.0
            for k in ("I1", "I2", "I3", "I4"):
                v = j.get(k)
                if isinstance(v, dict):
                    j[k + "_q"] = str(v.get("q") or "")[:200]
                    j[k] = bool(v.get("v"))
                else:
                    j[k + "_q"] = ""
                    j[k] = bool(v)
            flags = [j["I1"], j["I2"], j["I3"], j["I4"]]
            if all(flags):
                j["decision"] = "INCLUDE"
            elif not any(flags):
                j["decision"] = "EXCLUDE"
            elif "UNCERTAIN" in dec_model and not any(flags):
                j["decision"] = "UNCERTAIN"
            elif sum(flags) >= 3:
                j["decision"] = "UNCERTAIN"
            else:
                j["decision"] = "EXCLUDE"
            fout.write(json.dumps({**r, "screen": j, "pass": tag}, ensure_ascii=False) + "\n")
        fout.flush()
        if s % (B * 10) == 0:
            el = time.time() - t0
            print("screened %d/%d  %.0fs  eta %.0fs  fails=%d"
                  % (min(s + B, len(recs)), len(recs), el,
                     el / max(s + B, 1) * (len(recs) - s - B), fails), flush=True)
    fout.close()
    json.dump({"n": len(recs), "parse_failures": fails, "concurrency": B, "model": args.model,
               "perturb": args.perturb, "seconds": round(time.time() - t0, 1)},
              open(os.path.join(ROOT, "data/processed/screen_stats_%s.json" % tag), "w"), indent=1)
    print("SCREEN_DONE n=%d fails=%d %.0fs" % (len(recs), fails, time.time() - t0))


if __name__ == "__main__":
    main()
