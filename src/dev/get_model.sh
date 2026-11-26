#!/bin/bash
# Download Qwen2.5-7B-Instruct from ModelScope with resume + size verification.
set -u
DST=/root/cultcrime/models/Qwen2.5-7B-Instruct
BASE=https://www.modelscope.cn/models/Qwen/Qwen2.5-7B-Instruct/resolve/master
mkdir -p "$DST"
FILES="config.json configuration.json generation_config.json merges.txt model.safetensors.index.json
tokenizer.json tokenizer_config.json vocab.json README.md LICENSE
model-00001-of-00004.safetensors model-00002-of-00004.safetensors
model-00003-of-00004.safetensors model-00004-of-00004.safetensors"
for f in $FILES; do
  out="$DST/$f"
  for attempt in 1 2 3 4 5; do
    curl -sS -L -C - --retry 3 --retry-delay 3 --max-time 1800 -o "$out" "$BASE/$f" && break
    echo "retry $attempt for $f"; sleep 5
  done
  echo "$(stat -c%s "$out" 2>/dev/null) $f"
done
echo "MODEL_DOWNLOAD_DONE"
du -sh "$DST"
