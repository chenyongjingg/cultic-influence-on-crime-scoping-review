#!/bin/bash
set -u
D=/root/cultcrime/models/Qwen2.5-7B-Instruct
B=https://www.modelscope.cn/models/Qwen/Qwen2.5-7B-Instruct/resolve/master
cd "$D" || exit 1
get(){ # file expected_size
  local f="$1" want="$2" i=0
  while :; do
    local have=$(stat -c%s "$D/$f" 2>/dev/null || echo 0)
    [ "$have" -ge "$want" ] && { echo "COMPLETE $f $have"; return 0; }
    i=$((i+1)); [ $i -gt 40 ] && { echo "GIVEUP $f $have/$want"; return 1; }
    curl -sS -L -C - --max-time 900 -o "$D/$f" "$B/$f" || sleep 3
  done
}
get model-00003-of-00004.safetensors 3864726424 &
P1=$!
get model-00004-of-00004.safetensors 3556377672 &
P2=$!
wait $P1 $P2
echo "FINISH_MODEL"
md5sum "$D"/*.safetensors
