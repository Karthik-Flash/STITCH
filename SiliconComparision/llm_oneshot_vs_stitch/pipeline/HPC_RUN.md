# HPC run: LLM one-shot vs STITCH on the 2x2 mesh

One Slurm job (`pipeline/gen_job.slurm`, gpu_h200_8 on gpunode7, 1 GPU, 11 h) runs:
1. drift gate (`pipeline/gate.py`; the job exits non-zero if it fails),
2. preflight: `nvidia-smi -L`, `ollama serve` (models `/scratch/soumyaj/Phase3_HPC/ollama_models`, port
   11434 + job id mod 1000, up within 120 s or the job fails), then `pipeline/preflight.py` (runner imports, tool
   versions, qwen2.5-coder:32b digest equal to the Phase 3 digest, identical Ollama options for one-shot and arms;
   writes `runs/RUN_MANIFEST.json`),
3. one-shot generation with qwen2.5-coder:32b (T = 0.1, num_ctx 32768, all 34 modules plus the whole-router bonus),
4. the two feedback arms through the Phase 3 runner (`baseline` = simulation loop, `sem_esc_restart_v3` = STITCH;
   budget 6, N = 1),
5. the summary.

`ollama serve` is stopped on exit. Login: `soumyaj@hpc.bits-hyderabad.ac.in`. Base on the cluster:
`/scratch/soumyaj/STITCH_GEN`. Budget figures (options, token estimates, wall time): `reports/PREDEPLOY_BUDGET.md`.

## 1. Dependency checklist (login node; one check command each)

| Dependency | Expected | Check |
|---|---|---|
| oss-cad-suite: Yosys | `Yosys 0.69...` | `/scratch/soumyaj/oss-cad-suite/bin/yosys -V` |
| oss-cad-suite: Verilator | `Verilator 5.053...` | `/scratch/soumyaj/oss-cad-suite/bin/verilator --version` |
| oss-cad-suite: Icarus | `Icarus Verilog version 14...` | `/scratch/soumyaj/oss-cad-suite/bin/iverilog -V 2>&1 \| head -1` |
| Python 3.11 (oss-cad-suite) | `Python 3.11.x` | `/scratch/soumyaj/oss-cad-suite/py3bin/python3 --version` |
| Ollama binary (reused from Phase 3) | prints a client version | `/scratch/soumyaj/Phase3_HPC/bin/ollama --version` |
| qwen2.5-coder:32b in the models directory | lists `32b` | `ls /scratch/soumyaj/Phase3_HPC/ollama_models/manifests/registry.ollama.ai/library/qwen2.5-coder/` |

The job reuses the Phase 3 Ollama binary and models directory, so the model keeps the digest it had in Phase 3 (the
digest is recorded in every run). Other locations: set `OSS_CAD`, `GEN_OLLAMA_DIR` or `GEN_OLLAMA_MODELS` (see
`pipeline/hpc_env.sh`). If the model is missing, pull it with the Phase 3 script
(`P3_PULL_MODELS="qwen2.5-coder:32b" sbatch /scratch/soumyaj/Phase3_HPC/phase3/hpc/pull_ollama_models_phase3.slurm`);
a fresh pull may bring a newer digest.

If a check fails because the scratch purge removed something, restore it as in `docs/HPC_GUIDE.md` section 2.6.

## 2. Deploy (LAPTOP, PowerShell)

```powershell
cd D:\Projects\STITCH
powershell -ExecutionPolicy Bypass -File SiliconComparision\llm_oneshot_vs_stitch\pipeline\deploy_gen.ps1 -DryRun
powershell -ExecutionPolicy Bypass -File SiliconComparision\llm_oneshot_vs_stitch\pipeline\deploy_gen.ps1
```

Deploy from a clean, pushed commit: the script writes that commit to `DEPLOYED_COMMIT.txt` for the run manifest. It
prints local and remote SHA-256 of the runner, interpreter and pipeline files; the two lists must be equal. The runner
and interpreter hashes equal `phase3/evidence/FREEZE_FINAL.md`.

## 3. Submit (ssh)

```bash
ssh soumyaj@hpc.bits-hyderabad.ac.in
cd /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch
sbatch pipeline/gen_job.slurm
```

The log must show `GATE: ALL PASSED` and `PREFLIGHT: ALL PASSED` before the first generation line.

## 4. Monitor and resume (ssh)

```bash
squeue -u soumyaj
tail -f /scratch/soumyaj/STITCH_GEN/logs/gen_<JOBID>.log
grep -E "GATE:|PREFLIGHT:|\[digest\]|\[options\] (ok|BAD)" /scratch/soumyaj/STITCH_GEN/logs/gen_<JOBID>.log
cat /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch/runs/RUN_MANIFEST.json
ls /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch/runs/oneshot | wc -l      # 35 when one-shot is done
python3 -c "import json;d=json.load(open('/scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch/runs/arms/results/master_log.json'));print(len(d),'of 68 arm runs')"
```

If the job hits the 11-hour limit or fails, submit `sbatch pipeline/gen_job.slurm` again: finished one-shot modules and
arm runs are skipped. `GEN_MODULES="encoder mux" sbatch pipeline/gen_job.slurm` runs a subset (no bonus prompt).

## 5. Copy the results back

```bash
# ssh
cd /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch
tar -czf /scratch/soumyaj/STITCH_GEN/gen_results.tgz outputs prompts reports runs
sha256sum /scratch/soumyaj/STITCH_GEN/gen_results.tgz
```

```powershell
# LAPTOP
cd D:\Projects\STITCH
scp soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/STITCH_GEN/gen_results.tgz $env:TEMP\gen_results.tgz
Get-FileHash -Algorithm SHA256 $env:TEMP\gen_results.tgz
tar -xzf $env:TEMP\gen_results.tgz -C SiliconComparision\llm_oneshot_vs_stitch
```

`runs/` stays local (gitignored). `outputs/`, `prompts/` and `reports/` are the files to commit.
