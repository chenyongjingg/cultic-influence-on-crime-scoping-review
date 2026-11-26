#!/usr/bin/env python3
"""Embedding-based near-duplicate detection (protocol §3.11, 0.3 GPU·h line).

Exact DOI and normalised-title matching miss two things a bibliographic corpus
really contains: the same work under different titles, and the same work in two
languages. bge-m3 is multilingual and returns a single vector per record, so a
cosine threshold on title+abstract finds both.

This script is diagnostic first. It reports cluster counts at several thresholds
and writes the clusters; merging is a separate, recorded step (--merge) so that the
corpus a number was computed from is never changed silently.
"""
import argparse, json, os, sys, itertools, hashlib

ROOT = "/root/cultcrime"
P = os.path.join(ROOT, "data", "processed")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="/root/cultcrime/models/bge-m3")
    ap.add_argument("--inp", default="data/processed/corpus.jsonl")
    ap.add_argument("--threshold", type=float, default=0.95)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--out", default="data/processed/corpus_dedup.jsonl")
    args = ap.parse_args()

    import torch
    from transformers import AutoTokenizer, AutoModel

    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModel.from_pretrained(args.model, torch_dtype=torch.float16).cuda().eval()

    recs = [json.loads(l) for l in open(os.path.join(ROOT, args.inp))]
    texts = [((r.get("title") or "") + ". " + (r.get("abstract") or ""))[:2000] for r in recs]

    vecs = []
    B = 16
    with torch.inference_mode():
        for i in range(0, len(texts), B):
            enc = tok(texts[i:i + B], padding=True, truncation=True, max_length=1024,
                      return_tensors="pt").to("cuda")
            out = model(**enc).last_hidden_state[:, 0]
            vecs.append(torch.nn.functional.normalize(out.float(), dim=-1).cpu())
            if i % 160 == 0:
                print("embedded %d/%d" % (i, len(texts)), flush=True)
    V = torch.cat(vecs)
    S = V @ V.T
    S.fill_diagonal_(-1)

    report = {}
    for thr in (0.90, 0.93, 0.95, 0.97, 0.99):
        # union-find on pairs above threshold
        parent = list(range(len(recs)))

        def find(a):
            while parent[a] != a:
                parent[a] = parent[parent[a]]; a = parent[a]
            return a

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        idx = (S >= thr).nonzero(as_tuple=False).tolist()
        for a, b in idx:
            union(a, b)
        groups = {}
        for i in range(len(recs)):
            groups.setdefault(find(i), []).append(i)
        clusters = [g for g in groups.values() if len(g) > 1]
        report["%.2f" % thr] = {"clusters": len(clusters),
                                "records_absorbed": sum(len(g) - 1 for g in clusters)}

    json.dump(report, open(os.path.join(P, "embed_dedup_report.json"), "w"), indent=1)
    print(json.dumps(report, indent=1))

    # rebuild the 0.95 clusters for the record list
    thr = args.threshold
    parent = list(range(len(recs)))

    def find2(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a

    for a, b in (S >= thr).nonzero(as_tuple=False).tolist():
        ra, rb = find2(a), find2(b)
        if ra != rb:
            parent[ra] = rb
    groups = {}
    for i in range(len(recs)):
        groups.setdefault(find2(i), []).append(i)
    clusters = [[recs[i] for i in g] for g in groups.values() if len(g) > 1]
    json.dump([{ "members": [{"id": r.get("id"), "db": r.get("db"), "title": (r.get("title") or "")[:140],
                              "year": r.get("year")} for r in c],
                 "n": len(c)} for c in clusters],
              open(os.path.join(P, "embed_dedup_clusters.json"), "w"), indent=1, ensure_ascii=False)

    if args.merge:
        keep, dropped = [], 0
        for g in groups.values():
            g = sorted(g, key=lambda i: -(len(recs[i].get("abstract") or "")))
            keep.append(recs[g[0]]); dropped += len(g) - 1
        with open(os.path.join(ROOT, args.out), "w") as f:
            for r in keep:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("MERGED kept=%d dropped=%d" % (len(keep), dropped))
    print("EMBED_DEDUP_DONE")


if __name__ == "__main__":
    main()
