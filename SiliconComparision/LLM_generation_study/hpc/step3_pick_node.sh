#!/bin/bash
# STEP 3 (login node, submits nothing): on which GPU node would a job finish first?
# Asks Slurm (sbatch --test-only) for the start time on every H200, H100 and A100 node that is not drained or down,
# sorts by start time, then by GPU speed (H200, H100, A100), and prints the exact sbatch command for the best node.
# Usage, from the study folder:  bash hpc/step3_pick_node.sh [job file, default hpc/step4_smoke_test.slurm] [sbatch options]
set -uo pipefail
cd "$(dirname "$0")/.."
JOBFILE=${1:-hpc/step4_smoke_test.slurm}; shift $(( $# > 0 ? 1 : 0 ))
speed() { case "${1,,}" in *h200*) echo 1 H200;; *h100*) echo 2 H100;; *a100*) echo 3 A100;; *) echo 9 other;; esac; }

rows=$(sinfo -h -N -t idle,mixed,allocated,completing -o "%N %R %G" | awk 'tolower($0) ~ /h200|h100|a100/' | sort -u |
  while read node part gres; do
    out=$(sbatch --test-only --partition=$part --nodelist=$node "$@" $JOBFILE 2>&1)
    start=$(sed -n 's/.* to start at \([^ ]*\) .*/\1/p' <<<"$out" | head -1)
    echo "${start:-NEVER} $(speed "$part $gres") $part $node"
  done | sort -k1,1 -k2,2n)

echo "Start times for $JOBFILE${*:+ $*} (now: $(date '+%FT%T')):"
printf "%-20s %-5s %-14s %s\n" START GPU PARTITION NODE
awk '{printf "%-20s %-5s %-14s %s\n", $1, $3, $4, $5}' <<<"$rows"
read -r start rank gpu part node <<<"$(head -1 <<<"$rows")"
if [ -z "${start:-}" ] || [ "$start" = NEVER ]; then
  echo "No usable node answered. Run  sinfo -N -l  and see HPC_RUN.md, troubleshooting."; exit 1
fi
echo
echo "BEST: $node ($gpu, partition $part), start $start. Submit with:"
echo "JOB=\$(sbatch --parsable --partition=$part --nodelist=$node${*:+ $*} $JOBFILE); echo \$JOB"
