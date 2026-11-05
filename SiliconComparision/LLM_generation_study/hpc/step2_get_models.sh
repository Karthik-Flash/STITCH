#!/bin/bash
# STEP 2 (login node, about 10-30 min, mostly the 20 GB download): build this study's model store.
#   1. qwen2.5-coder:32b: hard links from the Phase 3 store (no copy, no download, the digest cannot change).
#   2. gemma4:31b-it-q4_K_M: pulled through a temporary Ollama server on this login node (127.0.0.1 only).
# The Phase 3 store is only read. Safe to rerun: what is already there is kept, a broken download resumes.
# Usage, from the study folder:  bash hpc/step2_get_models.sh
# If the pull says the model needs a newer Ollama:  bash hpc/step2_get_models.sh --new-ollama
#   installs the latest Ollama into $BASE/ollama (user space); from then on hpc_env.sh uses it for both models.
# Ends with "STEP2: ALL OK" and the two digests to record.
set -euo pipefail
source "$(dirname "$0")/hpc_env.sh"

if [ "${1:-}" = "--new-ollama" ]; then
  command -v zstd >/dev/null || { echo "zstd is not installed: ask the HPC team, or use the Hugging Face fallback (HPC_RUN.md)"; exit 1; }
  rm -rf $BASE/ollama.new && mkdir -p $BASE/ollama.new
  curl -fL https://ollama.com/download/ollama-linux-amd64.tar.zst | zstd -d | tar -xf - -C $BASE/ollama.new
  rm -rf $BASE/ollama && mv $BASE/ollama.new $BASE/ollama
  source "$(dirname "$0")/hpc_env.sh"
  echo "installed $(command -v ollama) version $(ollama_version)"
fi

echo "== 1/2 qwen: hard links from the Phase 3 store"
M=manifests/$MANIFESTS/qwen2.5-coder/32b
mkdir -p $OLLAMA_MODELS/blobs $(dirname $OLLAMA_MODELS/$M)
for d in $(grep -o 'sha256:[0-9a-f]\{64\}' $PHASE3_STORE/$M | sort -u); do
  b=blobs/${d/:/-}
  [ -e $OLLAMA_MODELS/$b ] || ln $PHASE3_STORE/$b $OLLAMA_MODELS/$b
done
[ -e $OLLAMA_MODELS/$M ] || ln $PHASE3_STORE/$M $OLLAMA_MODELS/$M
[ "$(manifest_digest $QWEN)" = "$QWEN_DIGEST" ] || { echo "qwen digest $(manifest_digest $QWEN) != $QWEN_DIGEST: stop"; exit 1; }
echo "qwen ok: digest $QWEN_DIGEST, $(du -sh $OLLAMA_MODELS/blobs | cut -f1) in the store"

echo "== 2/2 gemma: pull $GEMMA with $(command -v ollama) $(ollama_version)"
start_ollama; trap stop_ollama EXIT
df -h $BASE | tail -1
for t in 1 2 3; do ollama pull $GEMMA && break; echo "pull failed (try $t of 3)"; [ $t = 3 ] && exit 1; sleep 30; done
ollama list
ollama show $GEMMA | head -25 || true
df -h $BASE | tail -1

g=$(manifest_digest $GEMMA)
[ -n "$g" ] || { echo "no manifest for $GEMMA"; exit 1; }
echo "$(date '+%F %T') ollama $(ollama_version) $QWEN $(manifest_digest $QWEN) $GEMMA $g" >> $LOGS/MODELS.txt
echo
echo "record these two lines:"
echo "  $QWEN  $(manifest_digest $QWEN)"
echo "  $GEMMA  $g"
echo "STEP2: ALL OK"
