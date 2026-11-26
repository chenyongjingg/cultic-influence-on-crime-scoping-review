#!/bin/bash
# Download Qwen2.5-14B-Instruct-AWQ (10 GB) with 12-way ranges + sha256 verify.
set -u
D=/root/cultcrime/models/Qwen2.5-14B-Instruct-AWQ
B=https://www.modelscope.cn/models/Qwen/Qwen2.5-14B-Instruct-AWQ/resolve/master
mkdir -p "$D"
SMALL="config.json generation_config.json merges.txt model.safetensors.index.json tokenizer.json tokenizer_config.json vocab.json LICENSE README.md"
for f in $SMALL; do
  curl -sSL --max-time 600 -o "$D/$f" "$B/$f" || echo "small fail $f"
done
bash /root/cultcrime/src/pardl.sh "$B/model-00001-of-00003.safetensors" "$D/model-00001-of-00003.safetensors" 3988804408 4e874dc3b1febb5b22fe74a8793066ae430d90cdbc51765d0a4eb44a82a1fbbd 12
bash /root/cultcrime/src/pardl.sh "$B/model-00002-of-00003.safetensors" "$D/model-00002-of-00003.safetensors" 3968309440 b3b25da74cc854cdc726956f8152f1dda8519c7bb7d4724ac12c1312463e61c8 12
bash /root/cultcrime/src/pardl.sh "$B/model-00003-of-00003.safetensors" "$D/model-00003-of-00003.safetensors" 2023056736 25b97bf28033ed4560387293ce76bd3dc55a22882fea005a10c137b6478dae85 12
echo "AWQ_DONE"
du -sh "$D"
