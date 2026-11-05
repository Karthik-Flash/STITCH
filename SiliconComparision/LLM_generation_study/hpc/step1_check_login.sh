#!/bin/bash
# STEP 1 (login node, read only, about 30 s): is the cluster ready for this study? Changes nothing.
# Usage, from the study folder:  bash hpc/step1_check_login.sh
# Ends with "STEP1: ALL OK" or "STEP1: PROBLEMS: <names>". [info] lines are for the record and never fail.
set -uo pipefail
source "$(dirname "$0")/hpc_env.sh"
P=""
ok()   { echo "[$1] ok   $2"; }
bad()  { echo "[$1] BAD  $2"; P="$P $1"; }
info() { echo "[$1] info $2"; }

echo "== $(date '+%F %T') $(hostname) user $USER"
info deployed "$(cat $STUDY/DEPLOYED_COMMIT.txt 2>/dev/null || echo 'no DEPLOYED_COMMIT.txt: run the deploy first')"
info queue "$(squeue -h -u $USER -o '%i %j %T %P %N' | tr '\n' ';' | sed 's/;$//')"
[ -z "$(squeue -h -u $USER -n llmgen_smoke,llmgen_gen)" ] && ok jobs "no llmgen job queued or running" || bad jobs "an llmgen job is queued or running: wait"

echo "== tools"
py=$(python3 -c 'import sys;print("%d.%d.%d" % sys.version_info[:3])' 2>&1)
[[ $py == 3.1[1-9]* ]] && ok python3 "$py ($(command -v python3))" || bad python3 "$py: need 3.11+ from $OSS_CAD/py3bin"
for t in yosys verilator iverilog vvp; do command -v $t >/dev/null && ok $t "$($t -V 2>&1 | head -1 | cut -c1-70)" || bad $t "not on PATH ($OSS_CAD/bin)"; done
command -v zstd >/dev/null && info zstd "present (needed only if step 2 must install a newer Ollama)" || info zstd "absent (needed only if step 2 must install a newer Ollama)"

echo "== ollama"
[ -x $OLLAMA_DIR/bin/ollama ] && ok ollama "$OLLAMA_DIR/bin/ollama version $(ollama_version)" || bad ollama "no binary in $OLLAMA_DIR/bin"
q=$(sha256sum "$PHASE3_STORE/manifests/$MANIFESTS/qwen2.5-coder/32b" 2>/dev/null | cut -d' ' -f1)
[ "$q" = "$QWEN_DIGEST" ] && ok qwen_phase3 "$QWEN in the Phase 3 store, digest ${q:0:12} = Phase 3" || bad qwen_phase3 "Phase 3 store digest '${q:-missing}' != $QWEN_DIGEST"
info study_store "$OLLAMA_MODELS: qwen $(manifest_digest $QWEN | cut -c1-12 || true), gemma $(manifest_digest $GEMMA | cut -c1-12 || true) (empty = step 2 not run yet)"

echo "== disk"
[ "$(stat -c %d $PHASE3_STORE)" = "$(stat -c %d $BASE)" ] && ok same_fs "Phase 3 store and $BASE on one filesystem (hard links work)" || bad same_fs "different filesystems: step 2 cannot hard-link qwen"
free=$(df -BG --output=avail $BASE | tail -1 | tr -dc 0-9)
[ "${free:-0}" -ge 30 ] && ok disk "$free GB free on $(df --output=target $BASE | tail -1) (Gemma needs about 20 GB)" || bad disk "${free:-?} GB free, need 30"
info quota "$( (lfs quota -hu $USER /scratch 2>/dev/null || quota -s 2>/dev/null) | tail -2 | tr -s ' ' | tr '\n' ';')"

echo "== internet from the login node"
for u in https://registry.ollama.ai/v2/ https://ollama.com https://huggingface.co; do
  c=$(curl -sS -o /dev/null -m 20 -w '%{http_code}' $u 2>&1)
  [[ $c =~ ^[234] ]] && ok net "$u HTTP $c" || bad net "$u: $c"
done

echo "== GPU nodes (V100 and RTX are not usable: the models need 40 GiB of GPU memory)"
sinfo -N -O "NodeList:12,Partition:16,StateLong:14,Gres:28,GresUsed:36" | awk 'NR==1 || tolower($0) ~ /h200|h100|a100/'

echo
[ -z "$P" ] && echo "STEP1: ALL OK" || { echo "STEP1: PROBLEMS:$P"; exit 1; }
