#!/bin/bash
# Run the analysis chain on the 14B screening output and write every artefact.
set -u
cd /root/cultcrime || exit 1
LOG=logs/finalize.log
say(){ echo "[$(date -u +%H:%M:%SZ)] $*" | tee -a "$LOG"; }

[ -f data/processed/screen_14b.jsonl ] || { say "no 14B output"; exit 1; }
cp data/processed/screen_14b.jsonl data/processed/screen_pass1.jsonl
say "adjudicate";  python3 -u src/adjudicate.py  >>"$LOG" 2>&1
say "measure";     python3 -u src/measure.py     >>"$LOG" 2>&1
say "m8_m10";      python3 -u src/m8_m10.py      >>"$LOG" 2>&1
say "analyse";     python3 -u src/analyse.py     >>"$LOG" 2>&1
say "experiments"; python3 -u src/experiments.py >>"$LOG" 2>&1
say "e5";          python3 -u src/e5.py          >>"$LOG" 2>&1
say "s5";          python3 -u src/make_s5.py     >>"$LOG" 2>&1
say "supplements"; python3 -u src/supplements.py >>"$LOG" 2>&1
say "FINALIZE_DONE"
