# HPC run: LLM one-shot vs STITCH on the 2x2 mesh

One Slurm job (`pipeline/gen_job.slurm`: 1 GPU, 4 CPUs, 48 GB, 24 h; partition and node chosen on the sbatch line) runs:
1. drift gate (`pipeline/gate.py`, including the failure-handling tests; the job exits 1 if it fails),
2. preflight: `nvidia-smi -L`, `ollama serve` (models `/scratch/soumyaj/Phase3_HPC/ollama_models`, port
   11434 + job id mod 1000, `LLAMA_ARG_THREADS` = `LLAMA_ARG_THREADS_BATCH` = CPUs; up within 120 s or the job fails),
   then `pipeline/preflight.py` (runner imports, tool versions, thread settings, GPU name and memory (fails below
   40 GiB), GEN_TASKS names, qwen2.5-coder:32b digest equal to the Phase 3 digest, identical Ollama options for
   one-shot and arms including `num_thread`; writes `runs/RUN_MANIFEST.json`),
3. one-shot generation with qwen2.5-coder:32b (T = 0.1, num_ctx 32768, num_thread = CPUs, 34 modules). After the first
   call: GPU layer-offload line, llama-server `n_threads` and generation speed. The job exits 3 if n_threads differs
   from the CPU count or the speed is below 8 tokens/s, and warns below 15,
4. the two feedback arms through the Phase 3 runner (`baseline` = simulation loop, `sem_esc_restart_v3` = STITCH;
   budget 6, N = 1),
5. the summary.

A timeout or connection error on one module does not stop the job: the module is recorded as `infra_error`, the rest
continue, and the job ends with exit 2 and the list. Resubmitting retries those modules and any incomplete folder;
finished modules and arm runs are skipped. The client timeout is 3600 s per call, and a request that timed out once
fails at once on the runner's retries.

Each LLM call's `done_reason` and output tokens are recorded (`runs/oneshot/<m>/record.json`,
`runs/arms/results/.../iter<k>/llm_meta.json`) and counted in `reports/SUMMARY.md`. The whole-router bonus is off
(`GEN_FULL_ROUTER=0`): not attempted, its prompt alone is 32,290 of 32,768 tokens (`pipeline/budget.py`). num_ctx,
num_thread and timeout versus Phase 3: `reports/METHODS_NOTES.md`. Speed and the --time arithmetic:
`reports/SPEED.md`. `ollama serve` is stopped on exit. Login: `soumyaj@hpc.bits-hyderabad.ac.in`. Base on the
cluster: `/scratch/soumyaj/STITCH_GEN`.

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
digest is recorded in every run). Other locations: set `OSS_CAD` or `GEN_OLLAMA_DIR` (see `pipeline/hpc_env.sh`;
the models directory is fixed to `/scratch/soumyaj/Phase3_HPC/ollama_models`). If the model is missing, pull it with
the Phase 3 script (`P3_PULL_MODELS="qwen2.5-coder:32b" sbatch
/scratch/soumyaj/Phase3_HPC/phase3/hpc/pull_ollama_models_phase3.slurm`); a fresh pull may bring a newer digest.

If a check fails because the scratch purge removed something, restore it as in `docs/HPC_GUIDE.md` section 2.6.

## 2. Deploy (LAPTOP, PowerShell)

```powershell
cd D:\Projects\STITCH
powershell -ExecutionPolicy Bypass -File SiliconComparision\llm_oneshot_vs_stitch\pipeline\deploy_gen.ps1 -DryRun
powershell -ExecutionPolicy Bypass -File SiliconComparision\llm_oneshot_vs_stitch\pipeline\deploy_gen.ps1
```

Deploy from a clean, pushed commit: the script writes that commit to `DEPLOYED_COMMIT.txt` for the run manifest. The
tar never holds `runs/`, `outputs/`, `prompts/` or `hpc_logs/` (the script checks and refuses otherwise), and `tar -xf`
deletes nothing, so results on the cluster survive. The script prints the remote counts of one-shot records, arm
`metrics.json` files and one-shot outputs before and after the untar, and stops if one drops. It also prints local and
remote SHA-256 of the runner, interpreter and pipeline files; the two lists must be equal. The runner and interpreter
hashes equal `phase3/evidence/FREEZE_FINAL.md`.

## 3. Submit (ssh)

```bash
ssh soumyaj@hpc.bits-hyderabad.ac.in
cd /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch
sbatch --partition=<PART> --nodelist=<NODE> pipeline/gen_job.slurm
```

The log must show `GATE: ALL PASSED`, `[gpu] ok`, `[threads] ok`, `PREFLIGHT: ALL PASSED`, then after the first call
`[gpu offload] offloaded 65/65 layers to GPU`, `[threads] ok  llama-server n_threads = 4 (n_threads_batch = 4)` and
`[speed] ok` (or `WARNING` between 8 and 15 tokens/s). `GEN_TASKS=a,b` before `sbatch` limits the run to those tasks;
an unknown name fails the preflight before any generation.

## 4. Monitor and resume (ssh)

```bash
squeue -u soumyaj
tail -f /scratch/soumyaj/STITCH_GEN/logs/gen_<JOBID>.log
grep -E "GATE:|PREFLIGHT:|\[gpu|\[threads\]|\[speed\]|\[tasks\]|\[digest\]|\[options\] (ok|BAD)|INFRA|NOT FINISHED|FIRST-CALL" /scratch/soumyaj/STITCH_GEN/logs/gen_<JOBID>.log
cat /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch/runs/RUN_MANIFEST.json
cd /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch
python3 -c "import json,glob;r=[json.load(open(p)) for p in glob.glob('runs/oneshot/*/record.json')];print(sum(x.get('status','ok')=='ok' for x in r),'of 34 one-shot finished;',sum(x.get('status')=='infra_error' for x in r),'infra_error')"
find runs/arms/results -path '*/rep1/metrics.json' | wc -l      # 68 when the arms are done
```

Exit 2 (infra errors) or a time-out: submit the same command again; only unfinished work runs. Exit 3: llama-server did
not take the thread setting or generation was slower than 8 tokens/s; look at the `[threads]` and `[speed]` lines
before resubmitting.

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

`runs/` and `hpc_logs/` stay local (gitignored). `outputs/`, `prompts/` and `reports/` are the files to commit.
