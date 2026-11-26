#!/usr/bin/env python3
"""Shared inference helper: tensor-batched, left-padded, greedy, seeded.

Why tensor batching: prompt packing into one sequence keeps the GPU at batch 1
and costs the same wall clock per generated token.  Running N sequences side by
side raises aggregate throughput several-fold on a single 4090, which is the
difference between a ~6 h and a ~1 h extraction stage on a 2,500-record corpus.
Concurrency is recorded in every output file so the methods section can state it.
"""
import json, re, torch
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig


class LLM:
    def __init__(self, path, dtype=torch.bfloat16, device="cuda:0"):
        self.tok = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        self.tok.padding_side = "left"
        if self.tok.pad_token is None:
            self.tok.pad_token = self.tok.eos_token
        cfg = AutoConfig.from_pretrained(path, trust_remote_code=True)
        qc = getattr(cfg, "quantization_config", None) or {}
        if str(qc.get("quant_method", "")).lower() == "awq":
            # AWQ kernels expect fp16 activations.  Load through autoawq, which is
            # already installed; the transformers path requires gptqmodel, which
            # does not install cleanly against torch 2.14 on this host.
            from awq import AutoAWQForCausalLM
            self.model = AutoAWQForCausalLM.from_quantized(
                path, fuse_layers=False, device_map="auto", trust_remote_code=True).model
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                path, torch_dtype=dtype, device_map=device, trust_remote_code=True)
        self.model.eval()
        torch.manual_seed(20261126)
        self.path = path
        self.quant = qc.get("quant_method") if qc else "none"

    def generate(self, prompts, max_new_tokens=256):
        texts = [self.tok.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
                 for m in prompts]
        enc = self.tok(texts, return_tensors="pt", padding=True, truncation=True,
                       max_length=4096).to(self.model.device)
        with torch.inference_mode():
            out = self.model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False,
                                      pad_token_id=self.tok.pad_token_id)
        n_in = enc["input_ids"].shape[1]
        return [self.tok.decode(o[n_in:], skip_special_tokens=True) for o in out]


def extract_json(text):
    """Pull the first complete JSON object or array out of a model response."""
    m = re.search(r"[\{\[]", text)
    if not m:
        return None
    s = text[m.start():]
    for open_c, close_c in (("[", "]"), ("{", "}")):
        if s[0] != open_c:
            continue
        depth = 0
        for i, ch in enumerate(s):
            if ch == open_c:
                depth += 1
            elif ch == close_c:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(s[:i + 1])
                    except Exception:
                        return None
    return None
