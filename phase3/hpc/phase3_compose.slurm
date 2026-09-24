#!/bin/bash
#SBATCH --job-name=p3_compose
#SBATCH --partition=gpu_h100_4
#SBATCH --nodelist=gpunode5
#SBATCH --gres=gpu:0
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=24:00:00
#SBATCH --output=/scratch/soumyaj/Phase3_HPC/logs/p3_compose_%j.log
# CPU only. Splice every (model, condition, rep) set of repaired leaves into the real designs and re-synthesise.
# meshes ~10 s/group, MPSoC ~4 min/group (90 groups ~ 6 h). Then write SUMMARY.md.
set -euo pipefail
source "${PHASE3_BASE:-/scratch/soumyaj/Phase3_HPC}/phase3/hpc/common_env.sh"
cd $BASE
R=$BASE/results/phase3_run
python3 phase3/runner/compose.py --from-results $R --designs mesh2x2 mesh3x3 --out $R/compose_mesh.jsonl
python3 phase3/runner/compose.py --from-results $R --designs mpsoc --out $R/compose_mpsoc.jsonl
cat $R/compose_mesh.jsonl $R/compose_mpsoc.jsonl > $R/compose_results.jsonl
python3 phase3/runner/summarize_p3.py --results $R --compose $R/compose_results.jsonl --out $R/SUMMARY.md
echo "COMPOSE + SUMMARY DONE"
