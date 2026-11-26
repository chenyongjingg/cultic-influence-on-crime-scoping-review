#!/bin/bash
# Autonomous driver: wait for the OpenAlex credit window, harvest it, then run
# the whole downstream chain.  Each stage writes status.json, so progress is
# checkable from outside without reading the log.
set -u
cd /root/cultcrime || exit 1
LOG=logs/pipeline.log
say(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }
status(){ printf '{"stage":"%s","utc":"%s"}\n' "$1" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > status.json; }

status starting; say "driver started (pid $$)"

# ---- 1. wait for the OpenAlex quota window (measured reset ~2026-11-27 00:00 UTC)
RESET_EPOCH=1795737900          # 2026-11-27T00:05:00Z
while [ "$(date -u +%s)" -lt "$RESET_EPOCH" ]; do
  say "waiting for OpenAlex window ($(( (RESET_EPOCH - $(date -u +%s)) / 60 )) min left)"
  sleep 900
done

# ---- 2. OpenAlex harvest
status openalex; say "attempting OpenAlex harvest"
for i in 1 2 3 4 5 6; do
  if python3 -u src/run_sources.py openalex >>"$LOG" 2>&1; then
    say "OpenAlex harvest OK"; break
  fi
  say "OpenAlex attempt $i failed; sleeping 40 min"
  sleep 2400
done

# ---- 3. downstream chain on the merged corpus
status compose;    say compose;    python3 -u src/compose.py    >>"$LOG" 2>&1
status screen;     say screen;     python3 -u src/screen.py --concurrency 10 >>"$LOG" 2>&1
status perturb;    say perturb;    python3 -u src/screen.py --perturb --concurrency 10 \
                                   --out data/processed/screen_perturb.jsonl >>"$LOG" 2>&1
status adjudicate; say adjudicate; python3 -u src/adjudicate.py >>"$LOG" 2>&1
status measure;    say measure;    python3 -u src/measure.py    >>"$LOG" 2>&1
status analyse;    say analyse;    python3 -u src/analyse.py    >>"$LOG" 2>&1
status supplements; say supplements; python3 -u src/supplements.py >>"$LOG" 2>&1
status done;       say "PIPELINE_DONE"
