#!/bin/bash
# Parallel download of Qwen2.5-7B-Instruct from ModelScope (aria2c, 16 conns).
set -u
DST=/root/cultcrime/models/Qwen2.5-7B-Instruct
BASE=https://www.modelscope.cn/models/Qwen/Qwen2.5-7B-Instruct/resolve/master
mkdir -p "$DST"
cd "$DST" || exit 1
LIST="model-00002-of-00004.safetensors model-00003-of-00004.safetensors model-00004-of-00004.safetensors"
for f in $LIST; do
  aria2c -x16 -s16 -k2M --continue --file-allocation=none --allow-overwrite=false \
         --auto-file-renaming=false --max-tries=20 --retry-wait=5 \
         -d "$DST" -o "$f" "$BASE/$f" && echo "OK $f"
done
echo "ARIA_DONE"
ls -l "$DST"/*.safetensors | awk '{print $5, $9}'
