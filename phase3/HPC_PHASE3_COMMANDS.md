# Phase 3 HPC Command Sheet

Same conventions as `HPC_COMMANDS.md`:
- **Host:** `hpc.bits-hyderabad.ac.in`, user `soumyaj`.
- **Laptop repo:** `D:\Projects\STITCH`.
- **Where each command runs:** commands marked `# LAPTOP (PowerShell)` run on the laptop; everything else runs in the
  HPC ssh shell.
- **Scratch dir:** `/scratch/soumyaj/Phase3_HPC`, fresh. Scratch files are auto-deleted 30 days after their last
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
ssh soumyaj@hpc.bits-hyderabad.ac.in
ls /scratch/soumyaj/oss-cad-suite/bin/{iverilog,vvp,yosys,verilator} && echo "OSS-CAD OK" || echo "OSS-CAD GONE"
/scratch/soumyaj/oss-cad-suite/bin/yosys -V ; /scratch/soumyaj/oss-cad-suite/bin/verilator --version
ls /scratch/soumyaj/Set3_HPC/bin/ollama /scratch/soumyaj/Set3_HPC/lib/ollama 2>/dev/null && echo "OLLAMA OK (Set3)" || echo "OLLAMA GONE"
sinfo -p gpu_h100_4 ; squeue -u soumyaj
```
If a check fails:
- **OSS-CAD GONE:** redo `HPC_COMMANDS.md` Part 5.3 (laptop download + scp; the tgz extracts to
  `/scratch/soumyaj/oss-cad-suite`).
- **OLLAMA GONE:** redo Part 5.4, but extract into `/scratch/soumyaj/Phase3_HPC/` instead of `Set3_HPC`. Part B's
  ollama step then becomes a no-op.

Write down the Yosys and Verilator versions. They will almost certainly be newer than the Yosys 0.33 / Verilator 5.020
the interpreter was verified on. That is exactly what the live drift check in Part C tests.

## Part B: Deploy

```powershell
# LAPTOP (PowerShell), from D:\Projects\STITCH  (branch phase3-setup, after Claude Code finished T0-T10)
cd D:\Projects\STITCH
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
cp -r /scratch/soumyaj/Set3_HPC/bin/ollama /scratch/soumyaj/Phase3_HPC/bin/
cp -r /scratch/soumyaj/Set3_HPC/lib /scratch/soumyaj/Phase3_HPC/
ls -la /scratch/soumyaj/Phase3_HPC/bin/ollama /scratch/soumyaj/Phase3_HPC/lib/ollama | head
```
Then run the verification greps, in the same spirit as Sets 1–3:
```bash
cd /scratch/soumyaj/Phase3_HPC
ls phase3/tasks | wc -l                                                   # 11
ls src/interpreter/                                                       # stitch_interpreter.py stitch_interpreter_v3.py _v3_parsers.py
python3 -c "import hashlib;print(hashlib.sha256(open('src/interpreter/stitch_interpreter.py','rb').read().replace(b'\r\n',b'\n')).hexdigest())"
#   -> 42f61a493e4544e027b880ba5ae16ef1677c52f9b328cce2e13c25028fb2abff  (production v2, unmodified)
grep -c "STITCH_INTERPRETER_DIR" phase3/hpc/common_env.sh                 # 1
ls phase3/runner/system_prompt.txt                                        # present (Claude Code T5); if absent the run uses the default prompt
```

## Part C: Gate (CPU job; nothing GPU-side before this passes)

```bash
cd /scratch/soumyaj/Phase3_HPC
sbatch phase3/hpc/phase3_gate.slurm
squeue -u soumyaj
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
cd /scratch/soumyaj/Phase3_HPC
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
cd /scratch/soumyaj/Phase3_HPC
export P3_MODELS="llama3.1:latest"
export P3_EXTRA_ARGS="--tasks mux3 register_4bit register_1bit ni_flit_pack --reps 1"
export P3_OUT=/scratch/soumyaj/Phase3_HPC/results/phase3_pilot
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
   scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Phase3_HPC/results/phase3_pilot D:\Projects\STITCH\phase3\results\
   ```

## Part F: Full run (H100, 990 runs)

```bash
cd /scratch/soumyaj/Phase3_HPC
sbatch phase3/hpc/phase3_run.slurm            # gpunode5, gpu_h100_4, 72 h; models run in models_phase3.txt order
squeue -u soumyaj
```
If gpunode5 is busy but gpunode6 is idle (same pattern as `HPC_COMMANDS.md` Part 7.2):
```bash
sbatch --nodelist=gpunode6 phase3/hpc/phase3_run.slurm
```
To chain the run after the model pull so it starts hands-off:
```bash
sbatch --dependency=afterok:<PULL_JOB_ID> phase3/hpc/phase3_run.slurm
```

## Part G: Monitor / resubmit

```bash
tail -f /scratch/soumyaj/Phase3_HPC/logs/p3_run_*.log
python3 -c "import json; d=json.load(open('/scratch/soumyaj/Phase3_HPC/results/phase3_run/master_log.json')); print(len(d),'/990 done,',sum(1 for e in d if e.get('error')),'errored')"
sacct -j <jobid> --format=JobID,State,ExitCode,Elapsed,End,NodeList
```
- **Hit the 72 h cap:** `sbatch` the same script again. Every run with a `metrics.json` is skipped, so no flag is
  needed.
- **Errors:** the error rate should stay well below 1%, and errors should be transient Ollama timeouts, each recorded
  in an `error.json`. Delete the affected run folders and resubmit to retry them.

## Part H: Composition + summary (CPU job, after the run completes)

```bash
cd /scratch/soumyaj/Phase3_HPC
sbatch --dependency=afterok:<RUN_JOB_ID> phase3/hpc/phase3_compose.slurm
tail -f logs/p3_compose_*.log                    # ends with COMPOSE + SUMMARY DONE
cat results/phase3_run/SUMMARY.md | head -60
```

## Part I: Download results

```powershell
# LAPTOP (PowerShell)
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Phase3_HPC/results/phase3_run D:\Projects\STITCH\phase3\results\
```
`phase3/results/` is gitignored (Claude Code T2). Results stay local and are never committed.

---

## Failure table

| Symptom | Cause | Fix |
|---|---|---|
| `sbatch: error: Batch script contains DOS line breaks` | CRLF scripts | re-run the deploy script (it strips `\r`), or `sed -i 's/\r$//' phase3/hpc/*` |
| Gate log stops right after `== toolchain` | a tool is missing from `PATH` | check `/scratch/soumyaj/oss-cad-suite/bin` (Part A) |
| `BAD ... drift_v3_classes` | newer tool message format | stop and send the gate log to Claude |
| `ollama failed to start` | `bin/ollama` missing, or port busy | Part B ollama copy; `squeue`: another of your jobs may hold `:11434` on the same node |
| Runs extremely slow; serve log says cpu | `lib/ollama` not copied | Part B `lib/` copy |
| `WARNING: phase3/runner/system_prompt.txt absent` | Claude Code T5 not deployed | scp it, then resubmit (finished runs are kept) |
| `ModuleNotFoundError: stitch_interpreter` | interpreter files missing | re-run the deploy script |
| pull job `Invalid qos specification` | restricted partition | stay on `gpu_h100_4` / `gpu_a100_8` |
