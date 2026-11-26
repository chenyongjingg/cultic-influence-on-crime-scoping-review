#!/bin/bash
# Parallel ranged download with verification against a known sha256.
# Usage: pardl.sh <url> <outfile> <total_bytes> <sha256> [nparts]
set -u
URL="$1"; OUT="$2"; TOT="$3"; WANT="$4"; N="${5:-8}"
DIR=$(dirname "$OUT"); TMP="$DIR/.parts_$(basename "$OUT")"
mkdir -p "$TMP"; rm -f "$TMP"/*
CHUNK=$(( (TOT + N - 1) / N ))
pids=()
for i in $(seq 0 $((N-1))); do
  s=$(( i * CHUNK )); e=$(( s + CHUNK - 1 )); [ $e -ge $TOT ] && e=$((TOT-1))
  ( for try in 1 2 3 4 5; do
      curl -sS -L --max-time 1200 -r "$s-$e" -o "$TMP/part$(printf %02d $i)" "$URL" \
        && [ "$(stat -c%s "$TMP/part$(printf %02d $i)")" -eq "$((e-s+1))" ] && break
      sleep 4
    done ) &
  pids+=($!)
done
for p in "${pids[@]}"; do wait "$p"; done
cat "$TMP"/part* > "$OUT"
rm -rf "$TMP"
GOT=$(sha256sum "$OUT" | awk '{print $1}')
if [ "$GOT" = "$WANT" ]; then echo "VERIFIED $(stat -c%s "$OUT") $OUT"; else echo "HASH_MISMATCH got=$GOT want=$WANT"; exit 1; fi
