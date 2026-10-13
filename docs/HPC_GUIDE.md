# HPC Guide

This guide covers every cluster run of the project: the RTLLM study (Set 2 / Twin, Set 1, Set 3) and the MPSoC case
study (Phase 3: the 990-run batch and the final batch of the control arm and qwen2.5-coder:32b). It merges three
earlier documents, which are kept in `docs/archive/`:
- the command reference (`HPC_COMMANDS.md`);
- the full-run runbook (`FULL_RUN_RUNBOOK.md`);
- the Phase 3 command sheet (`HPC_PHASE3_COMMANDS.md`).

The API study (Sets 4, 4b, 4c) ran on a laptop, not on the cluster: see `phase2/frontier/PENDING.md` and
`REPO_INDEX.md`.

## 0. Conventions

- **Placeholders.**
  - The login is `<HPC_USER>@<HPC_HOST>`, and a GPU node is `<GPU_NODE>`.
  - The laptop checkout is `<REPO_ROOT>`.
  - Scratch is `/scratch/<HPC_USER>/`. The Slurm scripts in the repository use `/scratch/$USER`, and
    `/scratch/%u` in `#SBATCH` lines, where Slurm does not expand variables.
  - Replace `<GPU_NODE>` in a script's `#SBATCH --nodelist` line before submitting it.
- **Where a command runs.** Commands marked `# LAPTOP (PowerShell)` run on the laptop. Everything else runs in the
  ssh shell on the cluster.
- **Partitions used and their time caps:**

| Partition | Cap | Used for |
|---|---|---|
| `gpu_a100_8` | 5 days | Set 1, Set 3 (one long job each) |
| `gpu_h100_4` | 3 days | Set 2 (Twin); the default in `phase3/hpc/phase3_run.slurm` |
| `gpu_h200_8` | 1 day | Phase 3: the 990 runs and the final batch ran on an H200 NVL node (`PHASE3_RESULTS.md` provenance, `PLANNER_BRIEF.md` section 1); Twin fallback |

Useful status commands:
```bash
sinfo -o "%P %l"              # partition time limits
sinfo                         # node states (idle / mix / alloc / drain)
squeue -u <HPC_USER>          # your jobs
squeue -u <HPC_USER> --start  # estimated start times
sacct -j <jobid> --format=JobID,State,ExitCode,Elapsed,End,NodeList   # after a job leaves the queue
```

## 1. Known pitfalls (read first)

Each of these cost real time at least once.

| Pitfall | What happens | What to do |
|---|---|---|
| **Scratch purge** | Scratch files are deleted 30 days after their last modification. Once, mid-project, everything project-specific (RTLLM, oss-cad-suite, the ollama binary, the models, the venv) disappeared. | Before a batch, reset the clock: `find /scratch/<HPC_USER>/oss-cad-suite $B/bin $B/lib $B/ollama_models -exec touch -h {} +`. After a wipe, follow section 2.6. |
| **Python 3.6 on compute nodes** | `/usr/bin/python3` on the compute nodes is 3.6, too old for the runners, and the purge broke `miniconda3`. | Phase 3 jobs use the Python 3.11 that ships with oss-cad-suite: `/scratch/<HPC_USER>/oss-cad-suite/py3bin/python3` (`phase3/hpc/common_env.sh` puts it first on `PATH`). |
| **Ollama on the CPU** | If only `bin/ollama` is copied, Ollama silently falls back to the CPU, and the run crawls. | Copy `lib/` with `bin/` (section 5.2). Check that the serve log mentions `cuda`. |
| **Vulkan fallback** | In the Phase 3 control-arm job, Ollama's CUDA discovery timed out and it ran on its Vulkan backend (same H200, all layers on the GPU). This made no detectable difference on byte-identical prompts (`phase3/evidence/phase3_final/PLANNER_BRIEF.md`, section 1). | Record the backend from the serve log (`grep -i -E "cuda|vulkan|library=" logs/ollama_serve_*.log`) and disclose it if it differs between arms. |
| **Time limits** | A job that reaches its `--time` cap is killed mid-run. Users can lower a running job's limit (`scontrol update JobId=<id> TimeLimit=12:00:00`) but usually not raise it. | Resubmit the same script. Every runner skips finished runs (section 7). |
| **CRLF line endings** | `sbatch: error: Batch script contains DOS line breaks`, or in WSL `set: pipefail: invalid option name`. | `.gitattributes` now forces LF for `*.sh` and `*.slurm`. The Phase 3 deploy script strips `\r` on arrival. On the cluster: `sed -i 's/\r$//' <script>`. |
| **Login node** | Ollama does not run there (exit 126 or "command not found"), and there is no outbound internet. | Run pulls, clones and downloads inside an sbatch job, or download on the laptop and `scp`. Check models by listing the manifest directory, not with `ollama list`. |
| **Old `tar`** | `tar: unrecognized option '--zstd'`. | `conda install -y -c conda-forge zstd`, then `zstd -d x.tar.zst -o x.tar && tar xf x.tar`. |
| **Restricted partition** | `Invalid qos specification`. | Use `gpu_a100_8`, `gpu_h100_4` or `gpu_h200_8`. |
| **Port clash** | `ollama failed to start` when two of your jobs share a node. | Phase 3 jobs pick one Ollama port per job (`common_env.sh`). For older scripts, do not run two jobs on one node. |
| **Stale `RTLLM_ROOT`** | A job fails within a minute with "RTLLM not found". | Re-point `RTLLM_ROOT` after every deploy (section 4.3). |

## 2. One-time setup on the cluster

### 2.1 Scratch layout

```
/scratch/<HPC_USER>/
  oss-cad-suite/bin/        iverilog, vvp, verilator, yosys (put on PATH by each Slurm script)
  oss-cad-suite/py3bin/     Python 3.11 used by the Phase 3 jobs
  RTLCoderHPC/              Set 2: shared venv, RTLLM checkout, HF cache, Ollama models for Sets 1-2, bin/ollama
  Set1_HPC/                 Set 1: venv and RTLLM are symlinks into RTLCoderHPC
  Set3_HPC/                 Set 3: self-contained (own venv, RTLLM, bin/ollama, models) after the wipe
  Phase3_HPC/               Phase 3: phase3/, src/interpreter/, bin/, lib/, ollama_models/, logs/, results/
```

### 2.2 Base directories and Python venv (Phase 2)

```bash
ssh <HPC_USER>@<HPC_HOST>
mkdir -p /scratch/<HPC_USER>/RTLCoderHPC/{logs,venv,hf_cache,RTLLM,results,src/interpreter,ollama_models,bin}
python3 -m venv /scratch/<HPC_USER>/RTLCoderHPC/venv
source /scratch/<HPC_USER>/RTLCoderHPC/venv/bin/activate
pip install torch==2.1.0 transformers==4.34.0 accelerate sentencepiece openai
```
`openai` is needed by every runner (Ollama client). The `torch`/`transformers` pins are only for RTLCoder in the Twin
run.

### 2.3 oss-cad-suite (the EDA tools)

The reliable path is a laptop download plus `scp`, because a compute-node `wget` failed on a stale release tag:
```powershell
# LAPTOP (PowerShell), after downloading oss-cad-suite-linux-x64-YYYYMMDD.tgz from the YosysHQ releases page
cd $env:USERPROFILE\Downloads
scp oss-cad-suite-linux-x64-YYYYMMDD.tgz <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/
```
```bash
cd /scratch/<HPC_USER> && tar xzf oss-cad-suite-linux-x64-YYYYMMDD.tgz
ls /scratch/<HPC_USER>/oss-cad-suite/bin/{iverilog,vvp,yosys,verilator} && echo "OSS-CAD OK"
/scratch/<HPC_USER>/oss-cad-suite/bin/yosys -V ; /scratch/<HPC_USER>/oss-cad-suite/bin/verilator --version
```
Write the versions down. The Phase 3 runs used Yosys 0.69+71 and Verilator 5.053. The API study matched exactly that
build on the laptop.

### 2.4 RTLLM checkout (inside a job: the login node has no internet)

```bash
sbatch --nodelist=<GPU_NODE> --gres=gpu:0 --time=00:20:00 --mem=8G --partition=gpu_a100_8 \
  --output=/scratch/<HPC_USER>/RTLCoderHPC/logs/rtllm_clone_%j.log \
  --wrap="git clone https://github.com/hkust-zhiyao/RTLLM.git /scratch/<HPC_USER>/RTLCoderHPC/RTLLM"
ls /scratch/<HPC_USER>/RTLCoderHPC/RTLLM/      # expect: Arithmetic Control Memory Miscellaneous
```
RTLLM is never copied into the repository. Runners read it from `$RTLLM_ROOT`.

### 2.5 Ollama binary

```powershell
# LAPTOP (PowerShell)
cd $env:USERPROFILE\Downloads
scp ollama-linux-amd64.tar.zst <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/RTLCoderHPC/
```
```bash
cd /scratch/<HPC_USER>/RTLCoderHPC
zstd -d ollama-linux-amd64.tar.zst -o ollama-linux-amd64.tar && tar xf ollama-linux-amd64.tar
chmod +x bin/ollama && ./bin/ollama --version   # "could not connect" is normal on the login node
```
The archive contains `bin/ollama` and `lib/ollama`. Keep both.

### 2.6 After a scratch wipe

```bash
ls -la /scratch/<HPC_USER>/
ls /scratch/<HPC_USER>/oss-cad-suite/bin/iverilog 2>/dev/null && echo "OSS-CAD OK" || echo "OSS-CAD GONE"
ls /scratch/<HPC_USER>/*/bin/ollama 2>/dev/null && echo "OLLAMA OK" || echo "OLLAMA GONE"
```
Then:
1. Rebuild only what is gone, following sections 2.2 to 2.5.
2. Set 3 was stood up this way, in its own directory: `Set3_HPC/{logs,results,src/interpreter,ollama_models,bin}`,
   its own venv with `pip install openai`, its own RTLLM clone and its own Ollama binary.

## 3. The gates (nothing runs before they pass)

### 3.1 Phase 2: pass detection, verification greps, dry run

1. **Pass-detection gate.** It proves the deployed harness reads pass and fail correctly.
   ```powershell
   # LAPTOP (PowerShell)
   scp phase2\verify_pass_detection.py <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/RTLCoderHPC/
   ```
   ```bash
   cd /scratch/<HPC_USER>/RTLCoderHPC
   sbatch --nodelist=<GPU_NODE> --gres=gpu:0 --time=00:20:00 --mem=8G --partition=gpu_a100_8 \
     --output=logs/verify_%j.log \
     --wrap="source venv/bin/activate && python verify_pass_detection.py --rtllm-root /scratch/<HPC_USER>/RTLCoderHPC/RTLLM"
   ```
   - **Pass condition:** the golden side must be **44/44 PASS**.
   - **Expected exceptions:** the broken side shows about 8 non-green rows. These are documented: handshake designs
     where stuck-at-0 never reaches a verdict, and the two excluded weak-oracle testbenches. The analysis is in
     `docs/archive/IMP_PHASE2_RUNNER_HARDENING_REPORT.md`, sections 4 and 6.
2. **Verification greps**, in each deployed directory:

| Check | Expected | Proves |
|---|---|---|
| `grep -c 'ALL TESTS PASSED" not in output' stitch_runner_hpc.py` | 0 | the old hard-coded pass check is gone |
| `grep -c "detect_outcome" stitch_runner_hpc.py` | 2 or more | the pass-detection registry is wired in |
| `grep -c "cwd=iter_dir" stitch_runner_hpc.py` | 2 or more | the simulator working-directory fix is present |
| `grep -c "square_wave" <runner>` | 1 or more | the exclusion list is deployed (Set 1, Twin) |
| `grep -c "detect_outcome" escalation_runner_hpc.py` | 1 or more | escalation uses the registry too |
| recoverable entries in `module_categories.json` | 17 | the Set 3 pool is right |

   A bare `grep -c '"PASS"'` returning about 6 is expected (bookkeeping labels). Gate on the first line, not on
   that.
3. **Dry run:** `python <runner> --dry-run` must print **630** (Twin), **1512** (Set 1) or **612** (Set 3). A
   different number means a wrong module pool. Stop.

### 3.2 Phase 3: the gate job (G0 to G5)

```bash
cd /scratch/<HPC_USER>/Phase3_HPC
sbatch phase3/hpc/phase3_gate.slurm
tail -f logs/p3_gate_*.log
```
Expected, in order:
1. `44 passed, 0 failed` (G0: interpreter tests on frozen real logs).
2. 11 `OK` lines and `GATE 1: PASS` (G1: every task's golden fix is clean, its input shows the defect, and a live
   drift check).
3. `done: ... new runs` and `summarize OK` (G2: a mock end-to-end run).
4. `G5 PASS` (the control arm feeds no tool detail).
5. `G4: PASS` (composition bounds on the 2x2 mesh).
6. `plan: ... runs` (G3: dry run).
7. `ALL GATES PASSED`.

**If any line reads `BAD <task> ... FAILED: ['drift_v3_classes']`, stop.** The cluster's tools print a message format
the interpreter was not verified on, and a drifted interpreter would silently turn the interpreted conditions into
baseline.

The same gates run on a laptop with WSL: `bash phase2/frontier/p3_api/p3_gate_local.sh`.

## 4. Laptop-side deploy

**Deploy only from a committed state**, so that what runs matches a commit you can cite. Never patch a file by hand
on the cluster.

### 4.1 Phase 2 (scp lists)

```powershell
# LAPTOP (PowerShell), from <REPO_ROOT>
# Set 2 (Twin)
scp phase2\twin_run.slurm phase2\twin_run_runner.py phase2\stitch_runner_hpc.py phase2\rtlcoder_adapter.py `
    phase2\pull_ollama_models.slurm phase1\results\rtllm_pilot\task_a_screen.json `
    <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/RTLCoderHPC/
# Set 1
scp phase2\set1_runner.py phase2\set1_run.slurm phase2\stitch_runner_hpc.py phase2\escalation_runner_hpc.py `
    phase1\error_signature.py phase1\escalation_state.py phase1\results\rtllm_pilot\task_a_screen.json `
    <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/Set1_HPC/
# Set 3 (adds the tier file and its own pull script)
scp phase2\set3_runner.py phase2\set3_run.slurm phase2\pull_ollama_models_set3.slurm phase2\stitch_runner_hpc.py `
    phase2\escalation_runner_hpc.py phase1\error_signature.py phase1\escalation_state.py `
    phase1\results\rtllm_pilot\task_a_screen.json phase2\twin_analysis_SET2\module_categories.json `
    <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/Set3_HPC/
# the interpreter and the pass-detection registry, always re-copied fresh (shown for Set 3)
scp src\interpreter\pass_detection.py src\interpreter\stitch_interpreter.py `
    <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/Set3_HPC/src/interpreter/
```
Why there are cluster ports of the laptop files:
- `phase2/stitch_runner_hpc.py` runs the tools natively, because compute nodes have no WSL;
- `phase2/escalation_runner_hpc.py` replaces a runner that imported the WSL runner;
- `phase2/rtlcoder_adapter.py` serves RTLCoder through Hugging Face `transformers`.

### 4.2 Phase 3 (deploy script)

```powershell
# LAPTOP (PowerShell), from <REPO_ROOT>
powershell -ExecutionPolicy Bypass -File phase3\hpc\deploy_phase3.ps1
```
The script:
- creates `Phase3_HPC/{logs,results,src/interpreter,ollama_models,bin}`;
- copies `phase3/` and the three interpreter files: the production `stitch_interpreter.py`, unchanged, and the v3
  layer;
- strips `\r`.

It must end with `LINE ENDINGS OK`. For the final batch, its sha256 lines must match
`phase3/evidence/FREEZE_FINAL.md`, section 2. The deploy script and the Phase 3 Slurm scripts are hash-frozen in that
file, so they still carry the original cluster paths. Edit a local copy before deploying to another cluster.

Then copy the Ollama binary **with its libraries**, and verify:
```bash
cp -r /scratch/<HPC_USER>/Set3_HPC/bin/ollama /scratch/<HPC_USER>/Phase3_HPC/bin/
cp -r /scratch/<HPC_USER>/Set3_HPC/lib /scratch/<HPC_USER>/Phase3_HPC/
cd /scratch/<HPC_USER>/Phase3_HPC
ls phase3/tasks | wc -l                                   # 11
python3 -c "import hashlib;print(hashlib.sha256(open('src/interpreter/stitch_interpreter.py','rb').read().replace(b'\r\n',b'\n')).hexdigest())"
# -> 42f61a493e4544e027b880ba5ae16ef1677c52f9b328cce2e13c25028fb2abff (production v2, unmodified)
```

### 4.3 Re-point `RTLLM_ROOT` after a deploy (Set 3)

The committed `set3_run.slurm` points at the wiped `RTLCoderHPC/RTLLM`:
```bash
cd /scratch/<HPC_USER>/Set3_HPC
sed -i 's|RTLCoderHPC/RTLLM|Set3_HPC/RTLLM|g' set3_run.slurm
grep RTLLM_ROOT set3_run.slurm                 # now Set3_HPC/RTLLM
```

## 5. Pull the models (inside a job)

### 5.1 Phase 2

```bash
sbatch /scratch/<HPC_USER>/RTLCoderHPC/pull_ollama_models.slurm      # deepseek-coder:6.7b, gemma3:4b, llama3.1:latest
sbatch /scratch/<HPC_USER>/Set3_HPC/pull_ollama_models_set3.slurm    # qwen2.5-coder:14b, qwen2.5-coder:32b, gemma3:27b (~50 GB)
ls /scratch/<HPC_USER>/Set3_HPC/ollama_models/manifests/registry.ollama.ai/library/   # login-node-safe check
```
Twin also needs the RTLCoder weights (about 13 GB):
```bash
sbatch --nodelist=<GPU_NODE> --gres=gpu:1 --time=01:00:00 --mem=32G --partition=gpu_a100_8 \
  --output=/scratch/<HPC_USER>/RTLCoderHPC/logs/download_%j.log \
  --wrap="source /scratch/<HPC_USER>/RTLCoderHPC/venv/bin/activate && export HF_HOME=/scratch/<HPC_USER>/RTLCoderHPC/hf_cache && python -c \"from transformers import AutoModelForCausalLM, AutoTokenizer; AutoTokenizer.from_pretrained('ishorn5/RTLCoder-Deepseek-v1.1'); AutoModelForCausalLM.from_pretrained('ishorn5/RTLCoder-Deepseek-v1.1')\""
```

### 5.2 Phase 3

```bash
cd /scratch/<HPC_USER>/Phase3_HPC
sbatch phase3/hpc/pull_ollama_models_phase3.slurm      # must end with ALL MODELS PRESENT
ls ollama_models/manifests/registry.ollama.ai/library/  # deepseek-coder gemma3 llama3.1 llama3.2 qwen2.5-coder
```
- **Which models:** they are listed in `phase3/hpc/models_phase3.txt`: llama3.2:3b, gemma3:4b, deepseek-coder:6.7b,
  qwen2.5-coder:7b, llama3.1:latest and qwen2.5-coder:14b.
- **Pulling other models:** `P3_PULL_MODELS="qwen2.5-coder:32b" sbatch phase3/hpc/pull_ollama_models_phase3.slurm`.
- **What the log shows:** the `== before` and `== after` listings, which must keep the same IDs for models already
  present.

## 6. Run

### 6.1 Phase 2 (RTLLM)

| Run | Scratch | Models | Conditions | Modules | N / T | Runs | Partition, time |
|---|---|---|---|---|---|---|---|
| Set 2 (Twin) | RTLCoderHPC | RTLCoder (native and shared prompt), deepseek-coder:6.7b, gemma3:4b, llama3.1 | baseline | 42 | 3 / 0.5 | 630 | gpu_h100_4, 72 h |
| Set 1 | Set1_HPC | gemma3:4b, llama3.1:8b, deepseek-coder:6.7b | 4 | 42 | 3 / 0.1 | 1,512 | gpu_a100_8, 120 h |
| Set 3 | Set3_HPC | qwen2.5-coder:14b and 32b, gemma3:27b | 4 | 17 | 3 / 0.1 | 612 | gpu_a100_8, 120 h |

```bash
export STITCH_INTERPRETER_DIR=/scratch/<HPC_USER>/Set3_HPC/src/interpreter
export TASK_A_SCREEN_JSON=/scratch/<HPC_USER>/Set3_HPC/task_a_screen.json
export MODULE_CATEGORIES_JSON=/scratch/<HPC_USER>/Set3_HPC/module_categories.json   # Set 3 only
export RTLLM_ROOT=/scratch/<HPC_USER>/Set3_HPC/RTLLM
source venv/bin/activate && python set3_runner.py --dry-run     # 612
sbatch /scratch/<HPC_USER>/Set3_HPC/set3_run.slurm
```
- **Running two sets at once:** Set 1 and Set 2 ran at the same time on two different nodes. Each node has its own
  loopback, so both can bind Ollama to `127.0.0.1:11434`. Launch Set 2 first, then Set 1 two minutes later.
- **Starting a run after a pull, hands-off:** `sbatch --dependency=afterok:<pull_job_id> set3_run.slurm`.

### 6.2 Phase 3: pilot, then the 990 runs

The pilot is 20 runs, reviewed before anything else:
```bash
cd /scratch/<HPC_USER>/Phase3_HPC
export P3_MODELS="llama3.1:latest"
export P3_EXTRA_ARGS="--tasks mux3 register_4bit register_1bit ni_flit_pack --reps 1"
export P3_OUT=/scratch/<HPC_USER>/Phase3_HPC/results/phase3_pilot
sbatch --export=ALL --time=02:00:00 phase3/hpc/phase3_run.slurm
unset P3_MODELS P3_EXTRA_ARGS P3_OUT
grep -i -E "cuda|library=" logs/ollama_serve_*.log | tail -3     # must mention cuda
```
Then the full run (6 models x 11 tasks x 5 conditions x N=3 = 990 runs, 6 model calls per run in every condition):
```bash
sbatch phase3/hpc/phase3_run.slurm                      # script default: gpu_h100_4, 72 h; override the node and partition at submit time
sbatch --nodelist=<GPU_NODE> phase3/hpc/phase3_run.slurm # if the default node is busy
```

### 6.3 Phase 3: the final batch (control arm and qwen2.5-coder:32b)

This batch was pre-registered in `phase3/evidence/PREREG_FINAL.md` and frozen in `phase3/evidence/FREEZE_FINAL.md`.
It is one chained submission:
1. G: the gate;
2. P: the 32B pull;
3. A: `baseline_gate` on the 6 models, 198 runs;
4. C: qwen2.5-coder:32b under all 6 conditions, 198 runs;
5. D1 and D2: composition of A's and C's repairs.

```bash
B=/scratch/<HPC_USER>/Phase3_HPC; cd $B
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
echo "G=$G P=$P A=$A C=$C D1=$D1 D2=$D2" | tee -a $B/logs/final_batch_ids.txt
bash phase3/hpc/check_final_batch.sh $G $P $A $C $D1 $D2   # one PASS / FAIL / WAITING line per check
```
- `sbatch` passes the calling environment by default, so the `P3_*` prefixes reach the job.
- **Spot-check the control arm after its first runs.** Its feedback must be the simulation line plus "The design
  simulates correctly but FAILS SYNTHESIS SIGN-OFF. Re-check it for synthesis problems." and nothing else.
  - `tool_feedback_iters` must be 0;
  - `semantic_fired` must be False;
  - `would_fire` must be present;
  - `runner_sha256_lf` must equal the freeze record.

  The ready-made spot-check script is in `docs/archive/HPC_PHASE3_COMMANDS.md`, Part J step 3.

## 7. Monitor and resume

```bash
tail -f logs/<run>_*.log
python3 -c "import json; d=json.load(open('results/<run>/master_log.json')); print(len(d),'done,',sum(1 for e in d if e.get('error')),'errored')"
```
- **Monitoring:** read progress from `master_log.json`, not from the console log, which can lag.
- **Resume:** when a job hits its cap or dies, resubmit the same script with the same environment prefixes and no
  `--dependency`.
  - Phase 2 runners skip finished `(module, model, condition, replicate)` keys.
  - Phase 3 skips every run that has a `metrics.json`, and retries runs that have only an `error.json`.
- **Errors:** they should be well below 1%, and transient (Ollama timeouts). The actual counts were Set 1: 6 of
  1,512, Set 3: 2 of 612, Twin: 0.

## 8. Compose (Phase 3)

Composition splices each (model, replicate) group of repaired leaves back into the 2x2 mesh, the 3x3 mesh and the
MPSoC top, then runs top-level synthesis:
```bash
cd /scratch/<HPC_USER>/Phase3_HPC
sbatch --dependency=afterok:<RUN_JOB_ID> phase3/hpc/phase3_compose.slurm   # ends with COMPOSE + SUMMARY DONE
head -60 results/phase3_run/SUMMARY.md
```
For a separate result tree, prefix with `P3_OUT=$B/results/<tree>`.

## 9. Download and analyse (laptop)

```powershell
# LAPTOP (PowerShell)
scp -r <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/Set3_HPC/results/set3_run <REPO_ROOT>\phase2\results\
scp -r <HPC_USER>@<HPC_HOST>:/scratch/<HPC_USER>/Phase3_HPC/results/phase3_run <REPO_ROOT>\phase3\results\
```
Result trees are gitignored and stay local.

The analysis commands for every table and figure are in `REPO_INDEX.md`. The Phase 3 final analysis, for example:
```powershell
wsl bash -lc "cd $REPO_ROOT && python3 phase3/runner/analyze_phase3.py --score-signoff --results phase3/results/phase3_run --more-results phase3/results/phase3_gate_ctrl phase3/results/phase3_32b"
python phase3/runner/analyze_phase3.py --final --more-results phase3/results/phase3_gate_ctrl phase3/results/phase3_32b
```

## 10. Failure table

| Symptom | Cause | Fix |
|---|---|---|
| `ollama: command not found` on the login node | Ollama runs only inside jobs | ignore; the Slurm script starts its own server |
| Job FAILED within a minute, "task_a_screen.json not found" or "RTLLM not found" | missing file or stale `RTLLM_ROOT` | re-`scp` the file; section 4.3 |
| `ModuleNotFoundError: stitch_interpreter` | `src/interpreter/` not deployed | re-copy the interpreter files (or re-run the deploy script) |
| dry run prints the wrong count | RTLLM path unresolved, so the pool is short | set `RTLLM_ROOT` and rerun on the cluster |
| `tar: unrecognized option '--zstd'` | old `tar` | conda `zstd` (section 1) |
| `Invalid qos specification` | restricted partition | use the partitions in section 0 |
| job pending `(Resources)` | node busy | wait, or `scancel` and resubmit with another `--nodelist` |
| `Batch script contains DOS line breaks` | CRLF | section 1, CRLF row |
| gate log stops after `== toolchain` | a tool missing from `PATH` | check `oss-cad-suite/bin` |
| `BAD ... drift_v3_classes` | new tool message format | stop; do not run anything else |
| runs very slow; the serve log says cpu | `lib/ollama` not copied | section 4.2 |
| `ollama failed to start` | `bin/ollama` missing, or port busy | copy the binary; check for another job on the node |

## 11. Run inventory

| Run | Runs | Errors | Hardware |
|---|---|---|---|
| Set 2 (Twin) | 630 | 0 | H100 |
| Set 1 | 1,512 | 6 (timeouts, excluded) | A100 |
| Set 3 | 612 | 2 (timeouts, excluded) | A100 |
| Phase 3, 990 runs | 990 | 0 excluded (198 per condition analysed) | H200 NVL |
| Phase 3 final batch (control arm and 32B) | 396 | 0 excluded | H200 NVL |
