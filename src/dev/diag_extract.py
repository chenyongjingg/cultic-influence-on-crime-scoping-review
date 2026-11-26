#!/usr/bin/env python3
"""Diagnostic: can the model answer ONE construct at a time?"""
import json, sys
sys.path.insert(0, "/root/cultcrime/src")
from llm import LLM
import extract as E

llm = LLM("/root/cultcrime/models/Qwen2.5-7B-Instruct")
recs = [json.loads(l) for l in open("/root/cultcrime/data/processed/included.jsonl")]
KEYS = ["C6_offence", "C8_legal", "C9_jurisdiction", "C12_n"]
prompts, meta = [], []
for r in recs[:8]:
    ab = (r.get("abstract") or "").strip()[:1500]
    for k in KEYS:
        p = [{"role": "system", "content": "You read one abstract and answer one question."},
             {"role": "user", "content":
              "Question: does this text %s?\nAnswer YES or NO on the first line, and on the second line "
              "copy the exact words from the text that justify it (or nothing).\n\nTITLE: %s\nTEXT: %s"
              % (E.CONSTRUCTS[k], r["title"], ab)}]
        prompts.append(p); meta.append((r["title"][:40], k))

outs = []
for i in range(0, len(prompts), 8):
    outs.extend(llm.generate(prompts[i:i + 8], max_new_tokens=90))

for (t, k), o in zip(meta, outs):
    first = o.strip().split("\n")[0][:40]
    print("%-16s %-22s %s" % (k, first, t))
