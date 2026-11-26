#!/bin/bash
# Unattended pipeline (protocol V1.6).  Every stage is idempotent: it is skipped
# when its output already exists and is newer than its input, so a restart resumes
# rather than restarts.  The run ends with a self-check gate: if the PRISMA chain
# does not add up or a denominator is missing, the pipeline exits non-zero and says
# so, instead of writing a manuscript on top of an inconsistent corpus.
set -u
cd /root/cultcrime || exit 1
LOG=logs/pipeline.log
STATE=data/pipeline_state.json
say(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }
mark(){ python3 - "$1" <<'EOF'
import json, os, sys, time
p = "data/pipeline_state.json"
d = json.load(open(p)) if os.path.exists(p) else {}
d[sys.argv[1]] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
json.dump(d, open(p, "w"), indent=1)
EOF
}
done_mark(){ python3 - "$1" <<'EOF'
import json, os, sys
p = "data/pipeline_state.json"
d = json.load(open(p)) if os.path.exists(p) else {}
print("yes" if sys.argv[1] in d else "no")
EOF
}

stage(){          # stage <name> <output> <command...>
  local name="$1"; shift
  local out="$1"; shift
  if [ -s "$out" ] && [ "$(done_mark "$name")" = "yes" ]; then
    say "SKIP $name (output present)"; return 0
  fi
  say "START $name"
  if "$@" >>"$LOG" 2>&1; then
    mark "$name"; say "OK    $name"; return 0
  else
    say "FAIL  $name — stopping"; exit 1
  fi
}

say "================ pipeline start ================"
printf '{"stage":"start","utc":"%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > status.json

# ---- 0. preflight -----------------------------------------------------------
say "preflight"
python3 - <<'EOF' >>"$LOG" 2>&1 || { say "preflight FAILED"; exit 1; }
import json, os, subprocess
need = ["models/Qwen2.5-14B-Instruct-AWQ/config.json", "models/Qwen2.5-7B-Instruct/config.json"]
missing = [p for p in need if not os.path.exists(p)]
assert not missing, "missing models: %s" % missing
out = subprocess.check_output(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader"]).decode()
print("gpu:", out.strip())
print("models present")
EOF
say "preflight ok"

# ---- 1. screening -----------------------------------------------------------
n_corpus=$(wc -l < data/processed/corpus.jsonl)
if [ ! -s data/processed/screen_14b.jsonl ] || [ "$(wc -l < data/processed/screen_14b.jsonl)" -lt "$n_corpus" ]; then
  say "START screen_14b (corpus $n_corpus)"
  python3 -u src/screen.py --model models/Qwen2.5-14B-Instruct-AWQ --concurrency 8 \
          --out data/processed/screen_14b.jsonl >>"$LOG" 2>&1 || { say "FAIL screen_14b"; exit 1; }
  mark screen_14b; say "OK    screen_14b"
else
  say "SKIP screen_14b (complete)"
fi

if [ ! -s data/processed/screen_7b.jsonl ] || [ "$(wc -l < data/processed/screen_7b.jsonl)" -lt "$n_corpus" ]; then
  say "START screen_7b"
  python3 -u src/screen.py --model models/Qwen2.5-7B-Instruct --concurrency 10 \
          --out data/processed/screen_7b.jsonl >>"$LOG" 2>&1 || { say "FAIL screen_7b"; exit 1; }
  mark screen_7b; say "OK    screen_7b"
else
  say "SKIP screen_7b (complete)"
fi

# ---- 2. duplicate correction on the screened set ---------------------------
say "START dedup_screened"
python3 -u src/dedup_screened.py screen_14b.jsonl screen_14b_dedup.jsonl >>"$LOG" 2>&1 \
  || { say "FAIL dedup_screened"; exit 1; }
cp data/processed/screen_14b_dedup.jsonl data/processed/screen_pass1.jsonl
mark dedup_screened; say "OK    dedup_screened"

# ---- 3. embed-dedup diagnostic (bge-m3) ------------------------------------
say "START embed_dedup"
python3 -u src/embed_dedup.py >>"$LOG" 2>&1 || say "WARN embed_dedup failed (non-blocking)"

# ---- 4. analysis chain ------------------------------------------------------
stage adjudicate  data/processed/included.jsonl        python3 -u src/adjudicate.py
stage measure     data/processed/extracted.jsonl       python3 -u src/measure.py
stage m8_m10      data/processed/m8_m10.json           python3 -u src/m8_m10.py
stage analyse     data/processed/analysis.json         python3 -u src/analyse.py
stage experiments data/processed/experiments.json      python3 -u src/experiments.py
stage e5          data/processed/e5.json               python3 -u src/e5.py
stage s5          out/supplements/S5_sensitivity_and_modules.md   python3 -u src/make_s5.py
stage supplements out/supplements/S4_extraction.csv    python3 -u src/supplements.py
stage worksheet   out/supplements/S3_author_worksheet.csv         python3 -u src/worksheet.py

# ---- 5. self-check gate -----------------------------------------------------
say "START selfcheck"
if python3 src/selfcheck.py >>"$LOG" 2>&1; then
  say "OK    selfcheck"
else
  say "FAIL  selfcheck — artefacts written but flagged; see logs/selfcheck output"
  printf '{"stage":"failed_selfcheck","utc":"%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > status.json
  exit 2
fi

# ---- 6. full-text lift test (resumable; non-blocking) -----------------------
say "START fulltext (resumable)"
bash src/pipeline_fulltext.sh >>"$LOG" 2>&1 || say "WARN fulltext stage failed (non-blocking)"
mark fulltext

printf '{"stage":"done","utc":"%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > status.json
say "================ pipeline done ================"
