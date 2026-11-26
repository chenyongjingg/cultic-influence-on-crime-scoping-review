#!/usr/bin/env python3
"""Exp 5: a third reading.  The 14B model judges each construct one at a time on the
same 29 records that were hand-coded, giving three instruments on one sample:
manual, lexical detector, and model.

One construct per prompt, deliberately: the pilot showed that asking a small model
for twelve constructs at once collapses it to all-false, and single-question prompts
were the form that worked.
"""
import argparse, json, os, sys, time

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")
sys.path.insert(0, os.path.join(ROOT, "src"))
from llm import LLM

Q = {
 "C1_group_def": "does the text state how the group was identified as a cult or high-control group — an explicit definitional criterion, a named checklist, or a stated basis for calling it a cult?",
 "C2_role": "does the text distinguish participant roles (leader, core member, ordinary member, victim, former member), rather than referring only to 'cult members' or 'followers' in general?",
 "C3_duration": "does the text state a duration — how long someone was in the group, or how long since leaving?",
 "C4_mechanism": "does the text name a manipulation mechanism with an explicit term (indoctrination, coercive control, thought reform, mind control, isolation, trauma bonding, manipulation)?",
 "C5_instrument": "does the text name a standardised psychological instrument or scale used to measure manipulation or group abuse?",
 "C6_offence": "does the text specify the criminal offence by type (murder, fraud, sexual abuse, trafficking, assault, and so on)?",
 "C7_severity": "does the text grade offence severity — a statutory or study-internal severity level, or a sentence length?",
 "C8_legal": "does the text report a legal or judicial outcome (charge, conviction, sentence, responsibility finding, court ruling)?",
 "C9_jurisdiction": "does the text state the jurisdiction — the country, state or legal system — in which the events or the proceeding occurred, as opposed to merely mentioning a country in passing?",
 "C10_source": "does the text state where the data came from or how participants were recruited?",
 "C11_comparison": "does the text report a comparison group, a baseline, or an explicit statement that none was used?",
 "C12_n": "does the text report a sample size (n) for the persons, cases or documents analysed?",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/root/cultcrime/models/Qwen2.5-14B-Instruct-AWQ")
    ap.add_argument("--concurrency", type=int, default=8)
    args = ap.parse_args()
    llm = LLM(args.model)

    sample = json.load(open(os.path.join(P, "exp1_sample.json")))
    prompts, meta = [], []
    for s in sample:
        txt = (s["title"] + ". " + s["abstract"])[:1500]
        for k, q in Q.items():
            prompts.append([{"role": "system", "content":
                             "You read one abstract and answer one question about it. "
                             "Answer YES or NO on the first line. Nothing else on that line."},
                            {"role": "user", "content":
                             "Question: %s\n\nTITLE: %s\nTEXT: %s" % (q, s["title"], txt)}])
            meta.append((s["id"], k))

    res = {}
    t0 = time.time()
    for i in range(0, len(prompts), args.concurrency):
        outs = llm.generate(prompts[i:i + args.concurrency], max_new_tokens=12)
        for (rid, k), o in zip(meta[i:i + args.concurrency], outs):
            first = o.strip().split("\n")[0].strip().upper()
            res.setdefault(rid, {})[k] = first.startswith("Y")
        if i % 80 == 0:
            print("  %d/%d  %.0fs" % (i, len(prompts), time.time() - t0), flush=True)

    json.dump(res, open(os.path.join(P, "exp5_llm_construct.json"), "w"), indent=1)
    print("EXP5_DONE", len(res), "records,", len(prompts), "prompts")


if __name__ == "__main__":
    main()
