# Phase 3 HPC Command Sheet

Same conventions as `HPC_COMMANDS.md`:
- **Host:** `<HPC_HOST>`, user `<HPC_USER>`.
- **Laptop repo:** `<REPO_ROOT>`.
- **Where each command runs:** commands marked `# LAPTOP (PowerShell)` run on the laptop; everything else runs in the
  HPC ssh shell.
- **Scratch dir:** `/scratch/<HPC_USER>/Phase3_HPC`, fresh. Scratch files are auto-deleted 30 days after their last
  modification, so do not rely on Set1/Set3 directories surviving.

| Part | What | Where | Time |
|---|---|---|---|
| A | Preflight: what survived on scratch | HPC login node | 2 min |
| B | Deploy code + ollama binary | laptop → HPC | 5 min |
| C | Gate job (tests, live drift check, smoke, dry-run) | CPU job | ~10 min |
| D | Pull the 6 models | CPU job | 15–40 min |
| E | Pilot: 1 model, 4 tasks, 20 runs; send to Claude before continuing | H100 | ~30 min |
| F | Full run: 990 runs | H100, 72 h cap | est. 10–30 h |
| G | Monitor / resubmit | HPC | — |
| H | Composition + summary | CPU job | ~6 h |
| I | Download results | laptop | 5 min |

**Go/no-go rules:**
- Nothing GPU-side is submitted before Part C prints `ALL GATES PASSED`.
- The full run (Part F) is not submitted before the pilot (Part E) has been reviewed.

---

## Part A: Preflight (HPC login node)

```bash
ssh <HPC_USER>@<HPC_HOST>
ls /scratch/<HPC_USER>/oss-cad-suite/bin/{iverilog,vvp,yosys,verilator} && echo "OSS-CAD OK" || echo "OSS-CAD GONE"
/scratch/<HPC_USER>/oss-cad-suite/bin/yosys -V ; /scratch/<HPC_USER>/oss-cad-suite/bin/verilator --version
ls /scratch/<HPC_USER>/Set3_HPC/bin/ollama /scratch/<HPC_USER>/Set3_HPC/lib/ollama 2>/dev/null && echo "OLLAMA OK (Set3)" || echo "OLLAMA GONE"
sinfo -p gpu_h100_4 ; squeue -u <HPC_USER>
```
If a check fails:
- **OSS-CAD GONE:** redo `HPC_COMMANDS.md` Part 5.3 (laptop download + scp; the tgz extracts to
  `/scratch/<HPC_USER>/oss-cad-suite`).
- **OLLAMA GONE:** redo Part 5.4, but extract into `/scratch/<HPC_USER>/Phase3_HPC/` instead of `Set3_HPC`. Part B's
  ollama step then becomes a no-op.

Write down the Yosys and Verilator versions. They will almost certainly be newer than the Yosys 0.33 / Verilator 5.020
the interpreter was verified on. That is exactly what the live drift check in Part C tests.

## Part B: Deploy

```powershell
# LAPTOP (PowerShell), from <REPO_ROOT>  (branch phase3-setup, after Claude Code finished T0-T10)
cd <REPO_ROOT>
powershell -ExecutionPolicy Bypass -File phase3\hpc\deploy_phase3.ps1
```
The deploy script does the following:
- creates `Phase3_HPC/{logs,results,src/interpreter,ollama_models,bin}`;
- copies the whole `phase3\` folder;
- copies the 3 interpreter files (production `stitch_interpreter.py` unchanged, plus the v3 layer);
- strips Windows `\r` line endings on arrival.

It must end with `LINE ENDINGS OK`.

Next, the ollama binary. **Copy `lib/` together with `bin/`:** the GPU (CUDA) libraries live in `lib/ollama`. With
only the binary, Ollama silently falls back to the CPU and the run crawls.
```bash
cp -r /scratch/<HPC_USER>/Set3_HPC/bin/ollama /scratch/<HPC_USER>/Phase3_HPC/bin/
cp -r /scratch/<HPC_USER>/Set3_HPC/lib /scratch/<HPC_USER>/Phase3_HPC/
ls -la /scratch/<HPC_USER>/Phase3_HPC/bin/ollama /scratch/<HPC_USER>/Phase3_HPC/lib/ollama | head
```
Then run the verification greps, in the same spirit as Sets 1–3:
```bash
cd /scratch/<HPC_USER>/Phase3_HPC
ls phase3/tasks | wc -l                                                   # 11
ls src/interpreter/                                                       # stitch_interpreter.py stitch_interpreter_v3.py _v3_parsers.py
python3 -c "import hashlib;print(hashlib.sha256(open('src/interpreter/stitch_interpreter.py','rb').read().replace(b'\r\n',b'\n')).hexdigest())"
#   -> 42f61a493e4544e027b880ba5ae16ef1677c52f9b328cce2e13c25028fb2abff  (production v2, unmodified)
grep -c "STITCH_INTERPRETER_DIR" phase3/hpc/common_env.sh                 # 1
ls phase3/runner/system_prompt.txt                                        # present (Claude Code T5); if absent the run uses the default prompt
```

## Part C: Gate (CPU job; nothing GPU-side before this passes)

```bash
cd /scratch/<HPC_USER>/Phase3_HPC
sbatch phase3/hpc/phase3_gate.slurm
squeue -u <HPC_USER>
tail -f logs/p3_gate_*.log
```
Expected, in order:
- `44 passed, 0 failed`
- 11 `OK` lines, then `GATE 1: PASS`
- `done: 55 new runs` and `summarize OK`
- `plan: ... = 990 runs`
- `ALL GATES PASSED`

**If a line reads `BAD <task> ... FAILED: ['drift_v3_classes']` (or `drift_v2_classes`):** the cluster's newer
Yosys/Verilator prints a message in a format the interpreter was not verified on. Stop here. Send the whole
`logs/p3_gate_<id>.log` to Claude. Do not run anything else, because a drifted interpreter would silently turn
sem conditions into baseline.

## Part D: Pull the models (CPU job, compute node has internet)

```bash
cd /scratch/<HPC_USER>/Phase3_HPC
sbatch phase3/hpc/pull_ollama_models_phase3.slurm
tail -f logs/ollama_pull_*.log                 # must end with ALL MODELS PRESENT
ls ollama_models/manifests/registry.ollama.ai/library/
#   expect: deepseek-coder gemma3 llama3.1 llama3.2 qwen2.5-coder
```
The ladder, as listed in `phase3/hpc/models_phase3.txt`, is: `llama3.2:3b`, `gemma3:4b`, `deepseek-coder:6.7b`,
`qwen2.5-coder:7b`, `llama3.1:latest` and `qwen2.5-coder:14b`. Edit that file to change it; the run script reads it
at start.

## Part E: Pilot (H100, ~30 min, 20 runs)

The pilot is the same run script, restricted with three environment variables:
```bash
cd /scratch/<HPC_USER>/Phase3_HPC
export P3_MODELS="llama3.1:latest"
export P3_EXTRA_ARGS="--tasks mux3 register_4bit register_1bit ni_flit_pack --reps 1"
export P3_OUT=/scratch/<HPC_USER>/Phase3_HPC/results/phase3_pilot
sbatch --export=ALL --time=02:00:00 phase3/hpc/phase3_run.slurm
unset P3_MODELS P3_EXTRA_ARGS P3_OUT
tail -f logs/p3_run_*.log
```
Check the following:
1. The log shows `ollama up after Ns`, then one line per run with `it=`, `func=`, `clean=`, `sf=`.
2. The GPU is actually in use:
   ```bash
   grep -i -E "cuda|library=" logs/ollama_serve_*.log | tail -3
   ```
   It must mention cuda. If it says cpu, fix Part B's `lib/` copy.
3. Progress:
   ```bash
   python3 -c "import json; d=json.load(open('results/phase3_pilot/master_log.json')); print(len(d),'/20 done,',sum(1 for e in d if e.get('error')),'errored')"
   ```
4. Download the pilot and send it to Claude for a prompt-level review before Part F:
   ```powershell
   # LAPTOP (PowerShell)
   scp -r <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/Phase3_HPC/results/phase3_pilot <REPO_ROOT>\phase3\results\
   ```

## Part F: Full run (H100, 990 runs)

```bash
cd /scratch/<HPC_USER>/Phase3_HPC
sbatch phase3/hpc/phase3_run.slurm            # <GPU_NODE>, gpu_h100_4, 72 h; models run in models_phase3.txt order
squeue -u <HPC_USER>
```
If <GPU_NODE> is busy but <GPU_NODE> is idle (same pattern as `HPC_COMMANDS.md` Part 7.2):
```bash
sbatch --nodelist=<GPU_NODE> phase3/hpc/phase3_run.slurm
```
To chain the run after the model pull so it starts hands-off:
```bash
sbatch --dependency=afterok:<PULL_JOB_ID> phase3/hpc/phase3_run.slurm
```

## Part G: Monitor / resubmit

```bash
tail -f /scratch/<HPC_USER>/Phase3_HPC/logs/p3_run_*.log
python3 -c "import json; d=json.load(open('/scratch/<HPC_USER>/Phase3_HPC/results/phase3_run/master_log.json')); print(len(d),'/990 done,',sum(1 for e in d if e.get('error')),'errored')"
sacct -j <jobid> --format=JobID,State,ExitCode,Elapsed,End,NodeList
```
- **Hit the 72 h cap:** `sbatch` the same script again. Every run with a `metrics.json` is skipped, so no flag is
  needed.
- **Errors:** the error rate should stay well below 1%, and errors should be transient Ollama timeouts, each recorded
  in an `error.json`. Delete the affected run folders and resubmit to retry them.

## Part H: Composition + summary (CPU job, after the run completes)

```bash
cd /scratch/<HPC_USER>/Phase3_HPC
sbatch --dependency=afterok:<RUN_JOB_ID> phase3/hpc/phase3_compose.slurm
tail -f logs/p3_compose_*.log                    # ends with COMPOSE + SUMMARY DONE
cat results/phase3_run/SUMMARY.md | head -60
```

## Part I: Download results

```powershell
# LAPTOP (PowerShell)
scp -r <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/Phase3_HPC/results/phase3_run <REPO_ROOT>\phase3\results\
```
`phase3/results/` is gitignored (Claude Code T2). Results stay local and are never committed.

---

## Part J: Final batch (baseline_gate control arm + qwen2.5-coder:32b), 2026-09-28

Pre-registered in `evidence/PREREG_FINAL.md` and frozen in `evidence/FREEZE_FINAL.md`. The batch has four jobs:

| job | what | runs | estimate |
|---|---|---|---|
| A `phase3_gate_ctrl` | baseline_gate, 6 original models | 198 | ~5 h (7 h worst case) |
| C `phase3_32b` | qwen2.5-coder:32b, all 6 conditions | 198 | ~3 h (5 h worst case) |
| D1 | compose A's groups into the three designs | 18 groups | ~1.5 h |
| D2 | compose C's groups into the three designs | 18 groups | ~1.5 h |

The estimates for A and C come from the 990-run wall times and from the Set 3 32B/14B call-time ratio. Each job
starts its own ollama server on its own port (`common_env.sh`), so A and C can share <GPU_NODE> when two GPUs are free.
If only one GPU is free, Slurm queues C behind A.

**1. Deploy (LAPTOP, PowerShell)**
```powershell
cd <REPO_ROOT>
powershell -ExecutionPolicy Bypass -File phase3\hpc\deploy_phase3.ps1
```
It must print `LINE ENDINGS OK`, and its sha256 lines must match `evidence/FREEZE_FINAL.md` section 2.

**2. HPC**
```bash
ssh <HPC_USER>@<HPC_HOST>
B=/scratch/<HPC_USER>/Phase3_HPC; cd $B
find /scratch/<HPC_USER>/oss-cad-suite $B/bin $B/lib $B/ollama_models -exec touch -h {} +   # reset the 30-day purge clock
df -h /scratch | tail -1                                   # 32B needs ~20 GB free
ls results/                                                # phase3_gate_ctrl and phase3_32b must NOT exist yet
sinfo -p gpu_h200_8 -o "%P %l %G"; scontrol show node <GPU_NODE> | grep -E "Gres|AllocTRES"
F="--partition=gpu_h200_8 --nodelist=<GPU_NODE> --cpus-per-task=4 --mem=32G"
M6="llama3.2:3b gemma3:4b deepseek-coder:6.7b qwen2.5-coder:7b llama3.1:latest qwen2.5-coder:14b"
C6="baseline raw_adv sem_adv_v2 sem_adv_v3 sem_esc_restart_v3 baseline_gate"
G=$(sbatch --parsable $F --gres=gpu:0 --time=01:00:00 phase3/hpc/phase3_gate.slurm)
P=$(P3_PULL_MODELS="qwen2.5-coder:32b" sbatch --parsable $F --gres=gpu:0 --time=03:00:00 --dependency=afterok:$G phase3/hpc/pull_ollama_models_phase3.slurm)
A=$(P3_OUT=$B/results/phase3_gate_ctrl P3_MODELS="$M6" P3_EXTRA_ARGS="--conditions baseline_gate" \
    sbatch --parsable $F --gres=gpu:1 --time=24:00:00 --job-name=phase3_gate_ctrl --dependency=afterok:$G phase3/hpc/phase3_run.slurm)
C=$(P3_OUT=$B/results/phase3_32b P3_MODELS="qwen2.5-coder:32b" P3_EXTRA_ARGS="--conditions $C6" \
    sbatch --parsable $F --mem=48G --gres=gpu:1 --time=24:00:00 --job-name=phase3_32b --dependency=afterok:$P phase3/hpc/phase3_run.slurm)
D1=$(P3_OUT=$B/results/phase3_gate_ctrl sbatch --parsable $F --gres=gpu:0 --time=08:00:00 --dependency=afterok:$A phase3/hpc/phase3_compose.slurm)
D2=$(P3_OUT=$B/results/phase3_32b sbatch --parsable $F --gres=gpu:0 --time=08:00:00 --dependency=afterok:$C phase3/hpc/phase3_compose.slurm)
echo "G=$G P=$P A=$A C=$C D1=$D1 D2=$D2" | tee -a $B/logs/final_batch_ids.txt; squeue -u <HPC_USER>
```
- `sbatch` passes the calling environment (`--export=ALL` is the default), so the `P3_*` prefixes reach the job.
- `logs/p3_gate_$G.log` must end with `ALL GATES PASSED`. It prints `G5 PASS` and `plan: ... x 7 model(s) = 1386
  runs`.
- `logs/ollama_pull_$P.log` must end with `ALL MODELS PRESENT`. Its `== before` and `== after` listings must show
  the same IDs for the six original models.
- If the pull fails for lack of internet on <GPU_NODE>, re-submit it on the Part D node instead:
  `P3_PULL_MODELS="qwen2.5-coder:32b" sbatch --parsable phase3/hpc/pull_ollama_models_phase3.slurm`. Then
  `scontrol update JobId=$C Dependency=afterok:<new pull id>`.
- Users can usually only lower a time limit: `scontrol update JobId=$A TimeLimit=12:00:00`. To raise one, resubmit
  (step 4).

**Status of the whole batch** (read-only; one PASS / FAIL / WAITING line per check: deploy hashes, gate, job
states, pull digests, gate-arm prompt, job C's port and GPU, progress and ETA):
```bash
cd /scratch/<HPC_USER>/Phase3_HPC && bash phase3/hpc/check_final_batch.sh $G $P $A $C $D1 $D2
```
Live logs (one per job):
```bash
tail -f logs/p3_gate_$G.log          # gate
tail -f logs/ollama_pull_$P.log      # pull
tail -f logs/p3_run_$A.log           # A  (baseline_gate)
tail -f logs/p3_run_$C.log           # C  (32B)
tail -f logs/p3_compose_$D1.log      # D1
tail -f logs/p3_compose_$D2.log      # D2
```

**3. Spot-check after A's first ~5 runs** (and again for C, with `phase3_32b`)
```bash
/scratch/<HPC_USER>/oss-cad-suite/py3bin/python3 - /scratch/<HPC_USER>/Phase3_HPC/results/phase3_gate_ctrl <<'PY'
import glob, json, os, sys
fs = sorted(glob.glob(sys.argv[1] + "/*/*/*/rep*/metrics.json"), key=os.path.getmtime)
print(len(fs), "runs done; conditions:", sorted({f.split(os.sep)[-4] for f in fs}))
ms = [(f, json.load(open(f))) for f in fs]
f, m = next(((f, m) for f, m in ms if m["per_iter"][0]["func_pass"] and m["llm_calls"]), ms[0])
print("=" * 30, "iter1 prompt of", m["model"], m["condition"], m["task"], "rep", m["rep"])
print(open(os.path.join(os.path.dirname(f), "iter1", "prompt.txt")).read())
print("=" * 30)
for k in ("llm_calls", "stop_reason", "func_pass", "clean_pass", "tool_feedback_iters", "semantic_fired",
          "escalated_at", "restarted", "would_fire", "would_class", "would_fire_final", "protocol", "temperature", "max_iters"):
    print(f"{k:>20}: {m.get(k)}")
p = m["provenance"]
for k in ("model_digest", "node", "v3_version", "base_interp_sha256_lf", "runner_sha256_lf", "tb_v_sha256_lf", "toolchain"):
    print(f"{k:>20}: {p[k]}")
PY
```
For baseline_gate, the feedback section must be the simulation line plus "The design simulates correctly but FAILS
SYNTHESIS SIGN-OFF. Re-check it for synthesis problems." and nothing else. `tool_feedback_iters` and
`semantic_fired` must be 0 or False, `escalated_at` None, `would_fire` present, `model_digest` a sha256 (not
`NOT_LISTED`), and `runner_sha256_lf` equal to FREEZE_FINAL.

**4. Resume if a job dies**

Resubmit the same line without `--dependency`: every run that has a `metrics.json` is skipped, and a run with only an
`error.json` is retried.
```bash
B=/scratch/<HPC_USER>/Phase3_HPC; cd $B; F="--partition=gpu_h200_8 --nodelist=<GPU_NODE> --cpus-per-task=4 --mem=32G"
P3_OUT=$B/results/phase3_gate_ctrl P3_MODELS="llama3.2:3b gemma3:4b deepseek-coder:6.7b qwen2.5-coder:7b llama3.1:latest qwen2.5-coder:14b" \
  P3_EXTRA_ARGS="--conditions baseline_gate" sbatch $F --gres=gpu:1 --time=24:00:00 --job-name=phase3_gate_ctrl phase3/hpc/phase3_run.slurm
P3_OUT=$B/results/phase3_32b P3_MODELS="qwen2.5-coder:32b" P3_EXTRA_ARGS="--conditions baseline raw_adv sem_adv_v2 sem_adv_v3 sem_esc_restart_v3 baseline_gate" \
  sbatch $F --mem=48G --gres=gpu:1 --time=24:00:00 --job-name=phase3_32b phase3/hpc/phase3_run.slurm
```
Then resubmit the matching compose job (`P3_OUT=... sbatch $F --gres=gpu:0 --time=08:00:00 phase3/hpc/phase3_compose.slurm`).
Progress: `python3 -c "import json;d=json.load(open('results/phase3_gate_ctrl/master_log.json'));print(len(d),'/198')"`.

**5. Download and analyse (LAPTOP)**
```powershell
scp -r <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/Phase3_HPC/results/phase3_gate_ctrl <REPO_ROOT>\phase3\results\
scp -r <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/Phase3_HPC/results/phase3_32b <REPO_ROOT>\phase3\results\
wsl bash -lc "cd $REPO_ROOT && python3 phase3/runner/analyze_phase3.py --score-signoff --results phase3/results/phase3_run --more-results phase3/results/phase3_gate_ctrl phase3/results/phase3_32b"
python phase3/runner/analyze_phase3.py --final --more-results phase3/results/phase3_gate_ctrl phase3/results/phase3_32b
```
The output goes to `phase3/evidence/phase3_final/PHASE3_FINAL.md` and `phase3_final.json`.

---

## Failure table

| Symptom | Cause | Fix |
|---|---|---|
| `sbatch: error: Batch script contains DOS line breaks` | CRLF scripts | re-run the deploy script (it strips `\r`), or `sed -i 's/\r$//' phase3/hpc/*` |
| Gate log stops right after `== toolchain` | a tool is missing from `PATH` | check `/scratch/<HPC_USER>/oss-cad-suite/bin` (Part A) |
| `BAD ... drift_v3_classes` | newer tool message format | stop and send the gate log to Claude |
| `ollama failed to start` | `bin/ollama` missing, or port busy | Part B ollama copy; `squeue`: another of your jobs may hold `:11434` on the same node |
| Runs extremely slow; serve log says cpu | `lib/ollama` not copied | Part B `lib/` copy |
| `WARNING: phase3/runner/system_prompt.txt absent` | Claude Code T5 not deployed | scp it, then resubmit (finished runs are kept) |
| `ModuleNotFoundError: stitch_interpreter` | interpreter files missing | re-run the deploy script |
| pull job `Invalid qos specification` | restricted partition | stay on `gpu_h100_4` / `gpu_a100_8` |
