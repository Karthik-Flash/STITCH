# reSTITCHing HPC Command Reference

Complete, copy-paste command reference for every HPC operation in the
reSTITCHing extension. Consolidates all three confirmatory runs (Set 1,
Set 2/Twin, Set 3) plus the full scratch re-provisioning that was needed after
a mid-project wipe.

This file is the **commands**. For the ordered procedure, the go/no-go gates,
and the reasoning behind each locked parameter, read
[`FULL_RUN_RUNBOOK.md`](FULL_RUN_RUNBOOK.md) first; it links back here by Part
number.

**Conventions used throughout**

- HPC host: `hpc.bits-hyderabad.ac.in`, username `soumyaj` (swap yours in).
- Scratch root: `/scratch/soumyaj/` (Lustre, 253T, survives across jobs but was
  wiped once mid-project, see Part 5).
- Laptop repo root: `d:\Projects\STITCH` (PowerShell `scp` examples).
- Commands run **on HPC** are plain bash. Commands run **on the laptop** are
  marked `# LAPTOP (PowerShell)`.
- GPU partitions and their `--time` caps on this cluster:

| Partition | Node | Cap | Used for |
|---|---|---|---|
| `gpu_a100_8` | gpunode4 | 5 days | Set 1, Set 3 (long single-sbatch runs) |
| `gpu_h100_4` | gpunode5/6 | 3 days | Set 2 / Twin |
| `gpu_h200_8` | gpunode7 | 1 day | Twin fallback (needs ~4 resubmits) |

Check current caps and availability any time with:

```bash
sinfo -o "%P %l"          # partition time limits
sinfo                     # node states (idle / mix / alloc / drain)
squeue -u soumyaj         # your jobs
squeue -u soumyaj --start # estimated start times for pending jobs
```

---

## Part 0: One-Time Environment Facts

These are the hard-won environment facts that every run depends on. If a run
fails, check these first.

- **Ollama does not run on the login node.** The `ollama` binary exits 126 or
  reports "command not found" on `hpc01`. It only runs inside an sbatch job on a
  compute node, where each run's slurm script starts its own `ollama serve`.
  Do not try to `ollama list` on the login node; check model presence by listing
  the manifest directory instead (Part 3.3).
- **The login node has no outbound internet.** Any `git clone`, `wget`, `curl`,
  or model pull must run inside an sbatch job on a compute node, or be downloaded
  on the laptop and `scp`'d up.
- **iverilog / vvp / yosys** come from `oss-cad-suite`, not a module. They live at
  `/scratch/soumyaj/oss-cad-suite/bin` and are put on `PATH` by each slurm script.
- **`tar` on this cluster is too old for `--zstd`.** Use conda's `zstd` (Part 5.4)
  to unpack `.tar.zst` archives.
- Every runner reads pass/fail through the hardened `detect_outcome(sim_log,
  benchmark)` registry. The old-bug signature `'ALL TESTS PASSED" not in output'`
  must return 0 in `stitch_runner_hpc.py`; a bare `'"PASS"'` grep returning ~6 is
  expected (bookkeeping labels, not the old check).

---

## Part 1: Shared Provisioning (needed once, before any run)

### 1.1 Connect and create the base layout

```bash
ssh soumyaj@hpc.bits-hyderabad.ac.in
mkdir -p /scratch/soumyaj/RTLCoderHPC/{logs,venv,hf_cache,RTLLM,results,src/interpreter,ollama_models,bin}
```

### 1.2 Python venv (shared by all runs)

```bash
python3 -m venv /scratch/soumyaj/RTLCoderHPC/venv
source /scratch/soumyaj/RTLCoderHPC/venv/bin/activate
pip install torch==2.1.0 transformers==4.34.0 accelerate sentencepiece openai
```

`openai` is required by every runner for the Ollama client dispatch. The
`torch`/`transformers` pins are only needed for the RTLCoder (Hugging Face
`transformers`) path in Twin; Set 1 and Set 3 are Ollama-only and need just
`openai`.

### 1.3 oss-cad-suite (iverilog / vvp / yosys)

Try a compute-node download first; fall back to laptop + scp (Part 5.3 has the
exact fallback, which is what actually worked after the wipe).

```bash
# compute-node attempt
sbatch --nodelist=gpunode4 --gres=gpu:0 --time=00:30:00 --mem=8G \
  --partition=gpu_a100_8 \
  --output=/scratch/soumyaj/RTLCoderHPC/logs/osscad_%j.log \
  --wrap="cd /scratch/soumyaj && wget -q <LATEST_OSS_CAD_URL> -O oss-cad.tgz && tar xzf oss-cad.tgz && echo DONE"

# verify
ls /scratch/soumyaj/oss-cad-suite/bin/iverilog && echo "OSS-CAD OK"
```

Get `<LATEST_OSS_CAD_URL>` from
`https://github.com/YosysHQ/oss-cad-suite-build/releases/latest` (the
`oss-cad-suite-linux-x64-YYYYMMDD.tgz` asset).

### 1.4 RTLLM benchmark checkout

```bash
sbatch --nodelist=gpunode4 --gres=gpu:0 --time=00:20:00 --mem=8G \
  --partition=gpu_a100_8 \
  --output=/scratch/soumyaj/RTLCoderHPC/logs/rtllm_clone_%j.log \
  --wrap="git clone https://github.com/hkust-zhiyao/RTLLM.git /scratch/soumyaj/RTLCoderHPC/RTLLM"

# verify
ls /scratch/soumyaj/RTLCoderHPC/RTLLM/ | head
# expect: Arithmetic Control Memory Miscellaneous (plus files)
```

RTLLM is never copied into the STITCH repo. It is read live from
`$RTLLM_ROOT` on HPC (and `D:\Projects\RTLLM` on the laptop).

### 1.5 Ollama binary

```bash
# LAPTOP (PowerShell) if compute-node download is blocked (ollama.com not in allowlist)
cd C:\Users\karth\Downloads
scp ollama-linux-amd64.tar.zst soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/

# HPC: unpack .tar.zst (see Part 5.4 for the zstd install if needed)
cd /scratch/soumyaj/RTLCoderHPC
zstd -d ollama-linux-amd64.tar.zst -o ollama-linux-amd64.tar
tar xf ollama-linux-amd64.tar
chmod +x bin/ollama
./bin/ollama --version    # prints client version; "could not connect" warning is normal on login node
```

---

## Part 2: Set 2 (Twin Comparison) Deployment and Run

**Scope:** 5 model-conditions x 42 modules x N=3 = 630 runs, T=0.5, baseline
only. RTLCoder (HF transformers) + 3 Ollama models. Node: gpunode6 (H100),
`--time=72:00:00`, ~2 sbatches.

### 2.1 Deploy code

```bash
# LAPTOP (PowerShell), from d:\Projects\STITCH
scp phase2\twin_run.slurm phase2\twin_run_runner.py phase2\stitch_runner_hpc.py `
    phase2\rtlcoder_adapter.py phase2\pull_ollama_models.slurm `
    phase1\results\rtllm_pilot\task_a_screen.json `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/

scp src\interpreter\pass_detection.py src\interpreter\stitch_interpreter.py `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/src/interpreter/
```

### 2.2 Download RTLCoder weights (~13GB, HF transformers)

```bash
export HF_HOME=/scratch/soumyaj/RTLCoderHPC/hf_cache
sbatch --nodelist=gpunode4 --gres=gpu:1 --time=01:00:00 --mem=32G \
  --partition=gpu_a100_8 \
  --output=/scratch/soumyaj/RTLCoderHPC/logs/download_%j.log \
  --wrap="source /scratch/soumyaj/RTLCoderHPC/venv/bin/activate && export HF_HOME=/scratch/soumyaj/RTLCoderHPC/hf_cache && python -c \"from transformers import AutoModelForCausalLM, AutoTokenizer; AutoTokenizer.from_pretrained('ishorn5/RTLCoder-Deepseek-v1.1'); AutoModelForCausalLM.from_pretrained('ishorn5/RTLCoder-Deepseek-v1.1')\""

# verify
find /scratch/soumyaj/RTLCoderHPC/hf_cache -iname "*.safetensors" -o -iname "*.bin" | head
du -sh /scratch/soumyaj/RTLCoderHPC/hf_cache   # expect ~13GB
```

### 2.3 Pull the 3 Ollama models (shared with Set 1)

```bash
sbatch /scratch/soumyaj/RTLCoderHPC/pull_ollama_models.slurm
tail -f /scratch/soumyaj/RTLCoderHPC/logs/ollama_pull_*.log
# pulls deepseek-coder:6.7b, gemma3:4b, llama3.1:latest into RTLCoderHPC/ollama_models
```

### 2.4 Verify + dry-run

```bash
cd /scratch/soumyaj/RTLCoderHPC
grep -c "detect_outcome" stitch_runner_hpc.py                     # >= 2
grep -c 'ALL TESTS PASSED" not in output' stitch_runner_hpc.py    # 0
grep -c "cwd=iter_dir" stitch_runner_hpc.py                       # >= 2
grep -c "square_wave" twin_run_runner.py                          # >= 1

export STITCH_INTERPRETER_DIR=/scratch/soumyaj/RTLCoderHPC/src/interpreter
export TASK_A_SCREEN_JSON=/scratch/soumyaj/RTLCoderHPC/task_a_screen.json
export RTLLM_ROOT=/scratch/soumyaj/RTLCoderHPC/RTLLM
source venv/bin/activate
python twin_run_runner.py --dry-run    # expect 630
```

### 2.5 Launch + monitor

```bash
sbatch /scratch/soumyaj/RTLCoderHPC/twin_run.slurm
squeue -u soumyaj
tail -f /scratch/soumyaj/RTLCoderHPC/logs/twin_*.log

python3 -c "import json; d=json.load(open('/scratch/soumyaj/RTLCoderHPC/results/twin_run/master_log.json')); print(len(d),'/630 done,',sum(1 for e in d if e.get('error')),'errored')"
```

Resubmit the same script if it hits the time cap (runner skips completed cells).

---

## Part 3: Set 1 (STITCH Conditions, Small Models) Deployment and Run

**Scope:** 3 small models (`gemma3:4b`, `llama3.1:latest` (8B), `deepseek-coder:6.7b`)
x 4 conditions x 42 modules x N=3 = 1,512 runs, T=0.1. Node: gpunode4 (A100),
`--time=120:00:00`, ~2 sbatches. Ollama-only, reuses Set 2's pulled models.

### 3.1 Scratch dir (separate from RTLCoderHPC)

```bash
mkdir -p /scratch/soumyaj/Set1_HPC/{logs,results,src/interpreter}
ln -s /scratch/soumyaj/RTLCoderHPC/venv /scratch/soumyaj/Set1_HPC/venv
ln -s /scratch/soumyaj/RTLCoderHPC/RTLLM /scratch/soumyaj/Set1_HPC/RTLLM
```

### 3.2 Deploy code

`sem_escalate`/`sem_escalate_restart` depend on `escalation_runner_hpc.py`, an
HPC port of the Windows/WSL `escalation_runner.py` (which hardcodes a WSL import
and would crash on a compute node). It pulls in `error_signature.py` and
`escalation_state.py`.

```bash
# LAPTOP (PowerShell), from d:\Projects\STITCH
scp phase2\set1_runner.py phase2\set1_run.slurm phase2\stitch_runner_hpc.py `
    phase2\escalation_runner_hpc.py `
    phase1\error_signature.py phase1\escalation_state.py `
    phase1\results\rtllm_pilot\task_a_screen.json `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set1_HPC/

scp src\interpreter\pass_detection.py src\interpreter\stitch_interpreter.py `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set1_HPC/src/interpreter/
```

### 3.3 Confirm Ollama models present (login-node-safe check)

```bash
ls /scratch/soumyaj/RTLCoderHPC/ollama_models/manifests/registry.ollama.ai/library/
# expect: deepseek-coder gemma3 llama3.1
```

### 3.4 Verify + dry-run

```bash
cd /scratch/soumyaj/Set1_HPC
grep -c "detect_outcome" stitch_runner_hpc.py                     # >= 2
grep -c 'ALL TESTS PASSED" not in output' stitch_runner_hpc.py    # 0
grep -c "cwd=iter_dir" stitch_runner_hpc.py                       # >= 2
grep -c "square_wave" set1_runner.py                              # >= 1
grep -c "detect_outcome" escalation_runner_hpc.py                 # >= 1

export STITCH_INTERPRETER_DIR=/scratch/soumyaj/Set1_HPC/src/interpreter
export TASK_A_SCREEN_JSON=/scratch/soumyaj/Set1_HPC/task_a_screen.json
export RTLLM_ROOT=/scratch/soumyaj/Set1_HPC/RTLLM
source venv/bin/activate
python set1_runner.py --dry-run    # expect 1512
```

### 3.5 Launch + monitor

```bash
sbatch /scratch/soumyaj/Set1_HPC/set1_run.slurm
squeue -u soumyaj
tail -f /scratch/soumyaj/Set1_HPC/logs/set1_*.log

python3 -c "import json; d=json.load(open('/scratch/soumyaj/Set1_HPC/results/set1_run/master_log.json')); print(len(d),'/1512 done,',sum(1 for e in d if e.get('error')),'errored')"
```

### 3.6 Two-node parallelism note

Set 1 (gpunode4) and Set 2 (gpunode6) run concurrently on different physical
nodes. Both bind Ollama to `127.0.0.1:11434`, which is safe because each node has
its own loopback. Scratch dirs, log names, and venvs are disjoint or symlinked to
one source. Launch Set 2 first, wait ~2 min, then Set 1.

---

## Part 4: Golden-Reference Pass-Detection Verification (before any full run)

This is the gate that proves the deployed harness reads pass/fail correctly. Run
it on HPC, not just locally.

```bash
# LAPTOP (PowerShell)
scp phase2\verify_pass_detection.py soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/

# HPC
cd /scratch/soumyaj/RTLCoderHPC
sbatch --nodelist=gpunode4 --gres=gpu:0 --time=00:20:00 --mem=8G \
  --partition=gpu_a100_8 \
  --output=/scratch/soumyaj/RTLCoderHPC/logs/verify_%j.log \
  --wrap="source env.sh 2>/dev/null; source venv/bin/activate && export RTLLM_ROOT=/scratch/soumyaj/RTLCoderHPC/RTLLM && python verify_pass_detection.py --rtllm-root \$RTLLM_ROOT"

tail -f /scratch/soumyaj/RTLCoderHPC/logs/verify_*.log
```

Expected: golden side 44/44 PASS (the Bug #3 regression guard). The broken side
shows ~8 non-green rows that are documented, expected stragglers (handshake
designs where stuck-at-0 never reaches a verdict, plus the 2 weak-oracle
testbenches edge_detect/square_wave that are excluded from the runs anyway). None
are `detect_outcome` defects. The full per-row explanation is in
[`IMP_PHASE2_RUNNER_HARDENING_REPORT.md`](IMP_PHASE2_RUNNER_HARDENING_REPORT.md) §4/§6.

---

## Part 5: Scratch Re-Provisioning (after a mid-project wipe)

The cluster purged everything project-specific mid-project (RTLLM, oss-cad-suite,
ollama binary, all models, the venv). Only `hf_cache`, `miniconda3`, and unrelated
dirs survived. This is the full recovery sequence, used to stand up Set 3.

### 5.1 Diagnose what survived

```bash
ls -la /scratch/soumyaj/
ls /scratch/soumyaj/Set3_HPC/RTLLM/Arithmetic 2>/dev/null && echo "RTLLM OK" || echo "RTLLM GONE"
ls /scratch/soumyaj/oss-cad-suite/bin/iverilog 2>/dev/null && echo "OSS-CAD OK" || echo "OSS-CAD GONE"
ls /scratch/soumyaj/*/bin/ollama 2>/dev/null && echo "OLLAMA BIN OK" || echo "OLLAMA BIN GONE"
```

### 5.2 Rebuild dirs + venv

```bash
mkdir -p /scratch/soumyaj/Set3_HPC/{logs,results,src/interpreter,ollama_models,bin}
python3 -m venv /scratch/soumyaj/Set3_HPC/venv
source /scratch/soumyaj/Set3_HPC/venv/bin/activate
pip install openai
```

### 5.3 Re-clone RTLLM + re-fetch oss-cad-suite

```bash
# RTLLM (compute node)
sbatch --nodelist=gpunode4 --gres=gpu:0 --time=00:20:00 --mem=8G \
  --partition=gpu_a100_8 \
  --output=/scratch/soumyaj/Set3_HPC/logs/rtllm_clone_%j.log \
  --wrap="git clone https://github.com/hkust-zhiyao/RTLLM.git /scratch/soumyaj/Set3_HPC/RTLLM"

# oss-cad-suite: LAPTOP download + scp is the reliable path (compute-node wget 404'd on stale tag)
# LAPTOP (PowerShell), after downloading from the GitHub releases/latest page:
cd C:\Users\karth\Downloads
scp oss-cad-suite-linux-x64-YYYYMMDD.tgz soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/
# HPC
cd /scratch/soumyaj && tar xzf oss-cad-suite-linux-x64-YYYYMMDD.tgz
ls /scratch/soumyaj/oss-cad-suite/bin/iverilog && echo "OSS-CAD OK"
```

### 5.4 Re-fetch ollama binary (.tar.zst needs conda zstd)

```bash
# LAPTOP (PowerShell)
cd C:\Users\karth\Downloads
scp ollama-linux-amd64.tar.zst soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set3_HPC/

# HPC: the cluster tar has no --zstd, use conda's zstd
conda install -y -c conda-forge zstd
cd /scratch/soumyaj/Set3_HPC
zstd -d ollama-linux-amd64.tar.zst -o ollama-linux-amd64.tar
tar xf ollama-linux-amd64.tar
chmod +x bin/ollama
find /scratch/soumyaj/Set3_HPC -name ollama -type f    # confirm at Set3_HPC/bin/ollama
./bin/ollama --version

# cleanup
rm ollama-linux-amd64.tar ollama-linux-amd64.tar.zst
```

---

## Part 6: Set 3 (STITCH Conditions, Large Models) Deployment and Run

**Scope:** 3 larger models (`qwen2.5-coder:14b`, `qwen2.5-coder:32b`, `gemma3:27b`) x 4
conditions x 17 recoverable-band modules x N=3 = 612 runs, T=0.1. Node: gpunode4
(A100), `--time=120:00:00`, fits in ~1 sbatch. Recoverable band only, no
ceilings/floors.

### 6.1 Pull the 3 larger Ollama models (~50GB, ONE TIME)

Point `OLLAMA_MODELS` at `Set3_HPC/ollama_models` and the ollama binary at
`Set3_HPC/bin`. Chain-free; run before the main run (or dependency-chain, Part 7).

```bash
sbatch /scratch/soumyaj/Set3_HPC/pull_ollama_models_set3.slurm
tail -f /scratch/soumyaj/Set3_HPC/logs/ollama_pull_*.log
# ends with ollama list showing qwen2.5-coder:14b, qwen2.5-coder:32b, gemma3:27b

# login-node-safe confirmation
ls /scratch/soumyaj/Set3_HPC/ollama_models/manifests/registry.ollama.ai/library/
# expect: gemma3 qwen2.5-coder
```

### 6.2 Deploy code (11 files, 2 destinations)

Full transitive dependency set: set3_runner imports stitch_runner_hpc,
escalation_runner_hpc, escalation_state; escalation_runner_hpc imports
error_signature, escalation_state; stitch_runner_hpc imports stitch_interpreter,
pass_detection. `module_categories.json` is the SET2 copy (recoverable-tier
source). RTLLM already on HPC.

```bash
# LAPTOP (PowerShell), from d:\Projects\STITCH
ssh soumyaj@hpc.bits-hyderabad.ac.in "mkdir -p /scratch/soumyaj/Set3_HPC/{logs,results,src/interpreter,ollama_models}"

scp phase2\set3_runner.py phase2\set3_run.slurm phase2\pull_ollama_models_set3.slurm `
    phase2\stitch_runner_hpc.py phase2\escalation_runner_hpc.py `
    phase1\error_signature.py phase1\escalation_state.py `
    phase1\results\rtllm_pilot\task_a_screen.json `
    phase2\twin_analysis_SET2\module_categories.json `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set3_HPC/

scp src\interpreter\pass_detection.py src\interpreter\stitch_interpreter.py `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set3_HPC/src/interpreter/
```

### 6.3 Fix the RTLLM path in the slurm (scp overwrites it with the laptop copy)

The laptop `set3_run.slurm` points `RTLLM_ROOT` at the old `RTLCoderHPC/RTLLM`,
which no longer exists after the wipe. Re-point it to `Set3_HPC/RTLLM` after every
deploy.

```bash
cd /scratch/soumyaj/Set3_HPC
grep RTLLM_ROOT set3_run.slurm
sed -i 's|/scratch/soumyaj/RTLCoderHPC/RTLLM|/scratch/soumyaj/Set3_HPC/RTLLM|g' set3_run.slurm
grep RTLLM_ROOT set3_run.slurm    # confirm now Set3_HPC/RTLLM
grep -r "RTLCoderHPC/RTLLM" *.slurm set3_runner.py   # expect no output
```

### 6.4 Verify + dry-run

```bash
cd /scratch/soumyaj/Set3_HPC
grep -c 'ALL TESTS PASSED" not in output' stitch_runner_hpc.py    # 0
grep -c "detect_outcome" stitch_runner_hpc.py                     # >= 2
python3 -c "import json; d=json.load(open('module_categories.json')); print(len([m for m,i in d.items() if i['difficulty_tier']=='recoverable']))"   # expect 17

export STITCH_INTERPRETER_DIR=/scratch/soumyaj/Set3_HPC/src/interpreter
export TASK_A_SCREEN_JSON=/scratch/soumyaj/Set3_HPC/task_a_screen.json
export MODULE_CATEGORIES_JSON=/scratch/soumyaj/Set3_HPC/module_categories.json
export RTLLM_ROOT=/scratch/soumyaj/Set3_HPC/RTLLM
source venv/bin/activate
python set3_runner.py --dry-run    # expect 612
```

### 6.5 Launch + monitor

```bash
sbatch /scratch/soumyaj/Set3_HPC/set3_run.slurm
squeue -u soumyaj
tail -f /scratch/soumyaj/Set3_HPC/logs/set3_*.log

python3 -c "import json; d=json.load(open('/scratch/soumyaj/Set3_HPC/results/set3_run/master_log.json')); print(len(d),'/612 done,',sum(1 for e in d if e.get('error')),'errored')"
```

---

## Part 7: Useful Patterns

### 7.1 Chaining a run to start after a pull (hands-off overnight)

```bash
squeue -u soumyaj                              # note the pull job id, e.g. 350622
sbatch --dependency=afterok:350622 set3_run.slurm
squeue -u soumyaj                              # run shows PD (Dependency) until pull succeeds
```

`afterok` means the run only starts if the pull exits 0 (all models verified). A
failed pull holds the run rather than launching it with missing models.

### 7.2 Overriding node/partition at submit time

```bash
# move a queued job to a free node without editing the slurm
scancel <jobid>
sbatch --nodelist=gpunode5 --partition=gpu_h100_4 --time=72:00:00 <script>.slurm
# for the ollama pull (no GPU needed), request zero GPUs to slot into spare capacity
sbatch --nodelist=gpunode5 --partition=gpu_h100_4 --gres=gpu:0 pull_ollama_models_set3.slurm
```

Note: `gpu_rtx_pro_6000_6_csis_hyd` rejects jobs without a group-specific QOS
("Invalid qos specification"); skip it.

### 7.3 Reading job outcome after it leaves the queue

```bash
sacct -j <jobid> --format=JobID,State,ExitCode,Elapsed,End,NodeList
# COMPLETED = ran to end; FAILED + short Elapsed = crashed early (check the log tail)
```

### 7.4 Resubmit-to-resume

Every runner checkpoints via `master_log.json` and skips completed
`(module, model, condition, replicate)` keys. When a job hits its `--time` cap,
just `sbatch` the same script again. No flag, no "part 2" script.

### 7.5 Download results to laptop

```bash
# LAPTOP (PowerShell)
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/results/twin_run d:\Projects\STITCH\phase2\results\
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set1_HPC/results/set1_run   d:\Projects\STITCH\phase2\results\
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/Set3_HPC/results/set3_run   d:\Projects\STITCH\phase2\results\
```

`phase2/results/` is gitignored; these land locally and are never committed.

---

## Part 8: Run Inventory (what each run produced)

| Run | Scratch dir | Models | Conditions | Modules | N | Temp | Runs | Errors | Node |
|---|---|---|---|---|---|---|---|---|---|
| Set 2 (Twin) | RTLCoderHPC | 5 model-conditions | baseline | 42 | 3 | 0.5 | 630 | 0 | gpunode6 H100 |
| Set 1 | Set1_HPC | 3 small (4B–8B) | 4 | 42 | 3 | 0.1 | 1512 | 6 | gpunode4 A100 |
| Set 3 | Set3_HPC | 3 large (14B–32B) | 4 | 17 | 3 | 0.1 | 612 | 2 | gpunode4 A100 |
| Phase 3 (planned) | Phase3_HPC | 6 small-to-medium (3B–14B) | 5 | 11 tasks | 3 | 0.1 | 990 | – | gpunode5 H100 |

Total: 2,754 confirmatory runs. All error rates < 0.5%, all transient Ollama
timeouts, none structural. Every pass/fail routed through the hardened
`detect_outcome` registry, regression-verified against 64 manually-adjudicated
cells before launch.

### Common failure modes and fixes

| Symptom | Cause | Fix |
|---|---|---|
| `ollama: command not found` on login node | Ollama only runs in sbatch jobs | Ignore; the slurm starts its own server |
| Job `FAILED` in <60s, log ends `task_a_screen.json not found` or `RTLLM not found` | Missing file or stale `RTLLM_ROOT` | scp the file / re-point RTLLM_ROOT (Part 6.3) |
| `ModuleNotFoundError: stitch_interpreter` | `src/interpreter/` not deployed | scp `pass_detection.py` + `stitch_interpreter.py` to `src/interpreter/` |
| dry-run asserts 0 != 42/17 | RTLLM path unresolved locally | run dry-run on HPC with `RTLLM_ROOT` set (runners read the env var; only `verify_pass_detection.py` has a `--rtllm-root` flag) |
| `tar: unrecognized option '--zstd'` | old cluster tar | `conda install -c conda-forge zstd`, then `zstd -d` + `tar xf` |
| pull job `Invalid qos specification` | restricted partition | use gpunode4/5, not the csis_hyd partition |
| run PD `(Resources)` | GPU node busy | wait (you are first in line) or override to a free node (Part 7.2) |

---

## Part 9: Phase 3 (MPSoC composition + interpreter v3)

Status: **planned**. The integration is finished on branch `phase3-setup` (2026-09-24); nothing has been run on the
HPC yet, so the Part 8 row for it carries no error count.

- **Scratch dir:** `/scratch/soumyaj/Phase3_HPC` (fresh; do not rely on `Set1_HPC` / `Set3_HPC` still existing).
- **Node:** `gpunode5`, partition `gpu_h100_4` (`phase3/hpc/phase3_run.slurm`; `--nodelist=gpunode6` is the fallback, same
  pattern as Part 7.2).
- **Size:** 6 models x 11 tasks x 5 conditions x N=3 = **990 runs**, T=0.1, 6 iterations per run in every condition.
- **Commands:** `phase3/HPC_PHASE3_COMMANDS.md`, Parts A-I. It replaces the per-Set command blocks above for this run.
