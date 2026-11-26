#!/bin/bash
# Background stage: full-text lift test.  Resumable — records already fetched are
# skipped, so this can be re-run or interrupted at will.
set -u
cd /root/cultcrime || exit 1
LOG=logs/fulltext.log
say(){ echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

for round in 1 2 3; do
  say "round $round start (have $(wc -l < data/fulltext/fetch.jsonl 2>/dev/null || echo 0) rows)"
  python3 -u src/fulltext.py >>"$LOG" 2>&1
  rc=$?
  n=$(wc -l < data/fulltext/fetch.jsonl 2>/dev/null || echo 0)
  say "round $round end rc=$rc rows=$n"
  [ "$n" -ge "$(wc -l < data/processed/included.jsonl)" ] && break
  sleep 30
done

say "computing paired comparison"
python3 -u src/fulltext_compare.py >>"$LOG" 2>&1
say "FULLTEXT_PIPELINE_DONE"
