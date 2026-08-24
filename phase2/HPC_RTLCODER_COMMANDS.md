# RTLCoder HPC Command Reference

Copy-paste runbook, same style as `AutoChip_HPC_Reference.docx`. Every
command below is literal and runnable as written, except where your
username differs from `soumyaj` (used throughout — swap it if needed).
**You run these commands yourself on HPC.** Nothing here is executed by
Claude.

Scope: get RTLCoder-Deepseek-v1.1 (HuggingFace `transformers`, not
Ollama) loading on a GPU node and pass `phase2/smoke_test.py`'s 4-point
checklist on one golden RTLLM module. This is setup + proof-of-life —
**not** a benchmark run.

---

## 0. Scratch directory layout

Mirrors AutoChip's layout (`/scratch/soumyaj/AutoChipHPC/`), same reason:
avoid the 40GB home quota.

```
/scratch/soumyaj/RTLCoderHPC/
├── logs/              ← SLURM job logs
├── venv/              ← Python virtual environment
├── hf_cache/           ← HF_HOME (model weights land here, NOT home)
├── RTLLM/              ← RTLLM v2.1 checkout (design specs + testbenches;
│                          never committed into STITCH — same policy as
│                          local phase1/phase2 work)
├── rtlcoder_adapter.py ← scp'd from phase2/
├── smoke_test.py        ← scp'd from phase2/
├── smoke_test.slurm    ← sbatch wrapper (Section 4)
└── results/            ← smoke test output
```

Create it:

```
ssh soumyaj@hpc.bits-hyderabad.ac.in
mkdir -p /scratch/soumyaj/RTLCoderHPC/{logs,venv,hf_cache,RTLLM,results}
```

---

## 1. HF_HOME — keep weights off the home quota

RTLCoder-Deepseek-v1.1 is ~13GB (7B params, fp16). Same 40GB-home-quota
problem as AutoChip's Ollama models — point `HF_HOME` at scratch, always,
before touching `transformers`:

```
export HF_HOME=/scratch/soumyaj/RTLCoderHPC/hf_cache
```

Add this to a small `env.sh` so you don't retype it (same pattern as
AutoChip's `env.sh`):

```
cat > /scratch/soumyaj/RTLCoderHPC/env.sh << 'EOF'
export HF_HOME=/scratch/soumyaj/RTLCoderHPC/hf_cache
export RTLLM_ROOT=/scratch/soumyaj/RTLCoderHPC/RTLLM
EOF

source /scratch/soumyaj/RTLCoderHPC/env.sh
```

`phase2/rtlcoder_adapter.py` warns loudly (not fatally) if `HF_HOME` is
unset when you load the model — source `env.sh` first to avoid the warning.

---

## 2. Python virtual environment

```
python3 -m venv /scratch/soumyaj/RTLCoderHPC/venv
source /scratch/soumyaj/RTLCoderHPC/venv/bin/activate
```

Version pins taken from RTL-Coder's own `requirements.txt`
(`github.com/hkust-zhiyao/RTL-Coder`, confirmed 2026-08-22) — `torch`
and `transformers` pinned exactly as they specify, since a version drift
on either can silently change generation output for a checkpoint this
old. `accelerate` is added beyond their list — it's required for
`device_map="auto"` in current `transformers`, which their own script
(written against an older single-GPU-index convention) didn't need.
`Deepspeed`/`scikit-learn`/`openai==0.28.0` from their requirements.txt
are for their *training/eval* pipeline, not inference — deliberately
left out here to keep the install fast and low-risk for what this
adapter actually needs.

```
pip install torch==2.1.0 transformers==4.34.0 accelerate sentencepiece
```

Verify:

```
python -c "import torch, transformers, accelerate; print('torch', torch.__version__, 'transformers', transformers.__version__, 'cuda available:', torch.cuda.is_available())"
```

`cuda available: False` here is expected and fine — you're still on the
login node. It becomes `True` once this runs inside an sbatch job on a
GPU node.

Deactivate when done poking around interactively:

```
deactivate
```

(`venv` is activated automatically inside the `.slurm` script below —
manual activation is only for interactive testing, same note as AutoChip.)

---

## 3. Getting RTLLM onto HPC

`smoke_test.py` reads `design_description.txt` + `testbench.v` for one
RTLLM module live off disk — same "never copy RTLLM into STITCH" policy
as the local Windows setup, just now it needs to exist *somewhere* on
the HPC filesystem too.

**Try a compute-node `git clone` first** (login node blocks outbound
internet; compute nodes reached via `sbatch` have it — same reasoning
AutoChip's troubleshooting table gives for "Model pull stalls / slow on
login node"):

```
sbatch --nodelist=gpunode4 --gres=gpu:0 --time=00:20:00 --mem=8G \
  --partition=gpu_a100_8 \
  --output=/scratch/soumyaj/RTLCoderHPC/logs/rtllm_clone_%j.log \
  --wrap="git clone https://github.com/hkust-zhiyao/RTLLM.git /scratch/soumyaj/RTLCoderHPC/RTLLM"

tail -f /scratch/soumyaj/RTLCoderHPC/logs/rtllm_clone_*.log
```

If that fails (no internet from compute nodes either), fall back to
laptop-download + SCP, same as the ollama binary in AutoChip:

```
# On your laptop, after `git clone` or downloading a ZIP of RTLLM locally
scp -r ./RTLLM soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/
```

Verify the one module the smoke test needs is present:

```
ls /scratch/soumyaj/RTLCoderHPC/RTLLM/Arithmetic/Accumulator/accu/
# expect: design_description.txt  makefile  testbench.v  verified_accu.v
```

---

## 4. Model download — RTLCoder-Deepseek-v1.1 (~13GB)

**Try the sbatch-node path first**, same as AutoChip's ollama pulls
(login node has no internet; a compute node reached via `sbatch` might):

```
sbatch --nodelist=gpunode4 --gres=gpu:1 --time=01:00:00 --mem=32G \
  --partition=gpu_a100_8 \
  --output=/scratch/soumyaj/RTLCoderHPC/logs/download_%j.log \
  --wrap="source /scratch/soumyaj/RTLCoderHPC/env.sh && \
          source /scratch/soumyaj/RTLCoderHPC/venv/bin/activate && \
          python -c \"from transformers import AutoModelForCausalLM, AutoTokenizer; \
          AutoTokenizer.from_pretrained('ishorn5/RTLCoder-Deepseek-v1.1'); \
          AutoModelForCausalLM.from_pretrained('ishorn5/RTLCoder-Deepseek-v1.1')\""

tail -f /scratch/soumyaj/RTLCoderHPC/logs/download_*.log
```

**If the compute node also can't reach huggingface.co**, download on
your laptop first, then SCP the whole `HF_HOME` cache up (same
"download on laptop, SCP up" fallback AutoChip uses for the ollama
binary):

```
# On your laptop (needs Python + `pip install transformers torch` locally)
$env:HF_HOME = "$PWD\hf_cache_local"
python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; AutoTokenizer.from_pretrained('ishorn5/RTLCoder-Deepseek-v1.1'); AutoModelForCausalLM.from_pretrained('ishorn5/RTLCoder-Deepseek-v1.1')"

# then SCP the whole cache directory up
scp -r ./hf_cache_local/* soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/hf_cache/
```

**Verify weights are actually present** before trusting either path
worked (this is exactly the check `rtlcoder_adapter.load_model()` relies
on failing loudly if it's missing — but confirm by hand too):

```
find /scratch/soumyaj/RTLCoderHPC/hf_cache -iname "*rtlcoder*" -o -iname "*.safetensors" -o -iname "*.bin" | head -20
du -sh /scratch/soumyaj/RTLCoderHPC/hf_cache
# expect roughly 13GB total
```

---

## 5. SCP the adapter + smoke test up

From your laptop:

```
scp d:\Projects\STITCH\phase2\rtlcoder_adapter.py d:\Projects\STITCH\phase2\smoke_test.py `
  soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/
```

---

## 6. iverilog on the target GPU node — CONFIRMED ANSWER

Resolved 2026-08-22 via the real smoke test run: this cluster's GPU
nodes don't carry `iverilog` on `PATH` by default, and there's no
`module load` for it either — it comes from **oss-cad-suite**, already
present at `/scratch/soumyaj/oss-cad-suite/bin` (bundles iverilog,
verilator, and yosys together). Fix is a PATH export, not a module load:

```
export PATH=/scratch/soumyaj/oss-cad-suite/bin:$PATH
```

Add this to `env.sh` too, so every script that sources it gets it:

```
cat >> /scratch/soumyaj/RTLCoderHPC/env.sh << 'EOF'
export PATH=/scratch/soumyaj/oss-cad-suite/bin:$PATH
EOF
```

If a future node or a fresh cluster doesn't have oss-cad-suite at that
path, re-run the discovery this section used to describe
(`module avail 2>&1 | grep -i "iverilog\|icarus\|verilog"` /
`which iverilog` via a quick `srun`) before assuming the same path —
don't hardcode blindly onto a different cluster.

---

## 7. sbatch script — run the smoke test on a GPU node

`gpunode4` (A100 80GB, `gpu_a100_8`) or `gpunode6` (H100 80GB HBM3,
`gpu_h100_4` — `gpunode5` shows "draining" in the cluster inventory,
avoid it). Either has plenty of VRAM for one 7B fp16 model.

```
cat > /scratch/soumyaj/RTLCoderHPC/smoke_test.slurm << 'EOF'
#!/bin/bash
#SBATCH --job-name=rtlcoder_smoke
#SBATCH --partition=gpu_a100_8
#SBATCH --nodelist=gpunode4
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/soumyaj/RTLCoderHPC/logs/smoke_%j.log
#SBATCH --error=/scratch/soumyaj/RTLCoderHPC/logs/smoke_%j.err

source /scratch/soumyaj/RTLCoderHPC/env.sh
source /scratch/soumyaj/RTLCoderHPC/venv/bin/activate
export PATH=/scratch/soumyaj/oss-cad-suite/bin:$PATH

cd /scratch/soumyaj/RTLCoderHPC
python smoke_test.py --module accu --rtllm-root "$RTLLM_ROOT"
EOF

sbatch /scratch/soumyaj/RTLCoderHPC/smoke_test.slurm
```

For an H100 node instead, swap the two directives:

```
#SBATCH --partition=gpu_h100_4
#SBATCH --nodelist=gpunode6
```

**Status: this already ran for real and passed all 4 checks on H100.**
Kept here as the reference invocation for the twin run below, which
reuses the same PATH/env pattern. (`/scratch/soumyaj/oss-cad-suite` is a
scratch path, not node-local, so the PATH export in Section 6 applies
the same way regardless of which node runs the job.)

---

## 8. Monitoring

`smoke_test.py` prints a `[N/4] <check> — <status>` line as it moves
through the four checks (model load → generation → postprocessing →
compile), matching the pattern AutoChip's runner uses. Watch it live:

```
squeue -u soumyaj
tail -f /scratch/soumyaj/RTLCoderHPC/logs/smoke_*.log
```

The final block of the log is a `=== CHECKLIST ===` with `[PASS]`/`[FAIL]`
against all four checks — that's the thing to read once the job finishes.
If step (c) shows `[FAIL]`, the log's raw-vs-postprocessed side-by-side
dump right above the checklist is where to look first.

```
# Cancel if it hangs
scancel JOBID

# Your job history
sacct -u soumyaj --format=JobID,JobName,State,Elapsed,Start,End
```

---

## 9. Download results back

```
# On your laptop
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/logs/smoke_*.log ./phase2_smoke_logs/
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/results ./phase2_smoke_results
```

(`phase2/results/` is gitignored locally — these land there or wherever
you point the SCP, not committed either way.)

---

## 10. Twin-comparison run (RTLCoder vs. deepseek-coder:6.7b + ladder)

**Design doc: `phase2/TWIN_RUN_PREREG.md` — read that first.** Revised
2026-08-23: **75 runs** (5 model-conditions x 5 modules x N=3 — RTLCoder
native+shared, the 3 Ollama models shared-only, since native/shared are
procedurally identical for them), Pass@8, `baseline` STITCH condition
only (NOT an interpreter test), **T=0.5/top_p=0.9 matched across every
model-condition** (overrides the harness's usual T=0.1 for the Ollama
side — see the prereg doc's temperature section for why, and why this
run isn't iteration-count-comparable to this project's other, T=0.1,
results). Estimated ~2.7-6.5h wall-clock, real uncertainty on RTLCoder's
HPC generation pace — see the prereg doc's estimate table. **Not
launched by this doc — you launch it yourself after reviewing the
prereg doc, the run count, and the estimate.**

### 10.1 What's new here vs. the smoke test, and the two real gaps this section fixes

The smoke test validated only the RTLCoder/transformers path. This run
ALSO drives 3 models through Ollama, and **on HPC Ollama is not like the
laptop** — found 2026-08-23 when `twin_run.slurm` turned out to not
exist on HPC at all (it had only ever been shown as a heredoc in this
doc, never actually created) and the Ollama path had never been
scripted or tested:

- the `ollama` binary is at `/scratch/soumyaj/AutoChipHPC/bin/ollama`,
  not on `PATH`;
- it must be **started as a server** (`ollama serve &`) *inside* the
  slurm job on the GPU node — nothing is listening by default, unlike a
  laptop where Ollama commonly runs as a standing background service;
- the 3 models must already be pulled into an `OLLAMA_MODELS` location
  the job can read;
- `twin_run_runner.py` must point its Ollama client at whatever
  `host:port` that job's server actually bound to, not a hardcoded
  default that might not match.

**Fixed properly, not papered over**: `phase2/twin_run.slurm` and
`phase2/pull_ollama_models.slurm` are now real files (not
copy-paste-from-markdown heredocs — that's likely why the first one
never got created) that you `scp` up directly. `twin_run_runner.py` now
reads `$OLLAMA_HOST` itself and builds its own client from it (see that
file's `OLLAMA_HOST`/`_ollama_client`), rather than reusing
`stitch_runner_hpc.py`'s hardcoded-localhost:11434 client — the server
and the client are now structurally bound to the same value, not just
hoped to match. `twin_run_runner.py` also fails loudly at startup
(`_verify_ollama_models()`) if any of the 3 models aren't present on the
server it connects to, as a second check independent of `twin_run.slurm`'s
own bash-level check.

**Which of the 3 needed models already exist on HPC**: per
`AutoChip_HPC_Reference.docx`'s own documented pull list
(`qwen2.5-coder:32b`, `gemma3:27b`, `qwen2.5-coder:14b`), **none** of
`deepseek-coder:6.7b`, `gemma3:4b`, `llama3.1:latest` were pulled for
that project — different names, different sizes entirely. All 3 need a
fresh pull. Confirm this yourself too, in case something changed since
that doc was written:

```
export PATH=/scratch/soumyaj/AutoChipHPC/bin:$PATH
export OLLAMA_MODELS=/scratch/soumyaj/AutoChipHPC/ollama_models  # AutoChip's own dir, read-only check
ollama list
```

Also install the `openai` pip package — `stitch_runner_hpc.py` and
`twin_run_runner.py` both import it for their LLM dispatch, unchanged
from the original harness, and the smoke test's venv never needed it:

```
source /scratch/soumyaj/RTLCoderHPC/venv/bin/activate
pip install openai
```

### 10.2 Deploy everything, and VERIFY the harness fixes

```
# On your laptop, from the STITCH repo root
scp d:\Projects\STITCH\phase2\stitch_runner_hpc.py `
    d:\Projects\STITCH\phase2\twin_run_runner.py `
    d:\Projects\STITCH\phase2\twin_run.slurm `
    d:\Projects\STITCH\phase2\pull_ollama_models.slurm `
    soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/
```

**Independent post-deploy confirmation that both harness fixes are on
the file that will actually run** (correctness check #1 -- STILL step 1
before launch, unchanged by this revision):

```
# On HPC
cd /scratch/soumyaj/RTLCoderHPC
grep -n "cwd=iter_dir" stitch_runner_hpc.py        # bug #2 fix -- expect 2+ matches
grep -n 'sub(r"\^```' stitch_runner_hpc.py         # bug #1 fix -- expect 1 match
grep -c "wsl\b" stitch_runner_hpc.py               # expect 0 real invocations
                                                     # (comments mentioning "WSL" for
                                                     # context are fine and expected)
```

If either grep comes back empty, STOP — do not launch. Re-scp the file
and re-check; do not patch it by hand on the cluster.

### 10.3 Pull the Ollama models — ONE TIME, before ever submitting the run

```
sbatch /scratch/soumyaj/RTLCoderHPC/pull_ollama_models.slurm
tail -f /scratch/soumyaj/RTLCoderHPC/logs/ollama_pull_*.log
```

Waits for readiness, pulls all 3, prints `ollama list` to confirm, exits
clean. Only needs to be run once — re-run only if a model ever goes
missing (`OLLAMA_MODELS` gets cleared, cluster storage issue, etc.).

### 10.4 Submit the twin run

```
sbatch /scratch/soumyaj/RTLCoderHPC/twin_run.slurm
```

Targets `gpunode6` (H100 80GB HBM3, `gpu_h100_4`), `--time=08:00:00` —
real margin over the ~2.7-6.5h estimate (see the prereg doc) given
RTLCoder's HPC pace is unvalidated. In order: sets `PATH` for both
`ollama` and `iverilog`/`verilator`/`yosys`, starts its own `ollama
serve` bound to `OLLAMA_HOST=127.0.0.1:11434`, waits for readiness,
confirms all 3 models present (**fails loudly and exits — does not pull
inline** — if Section 10.3 was skipped), then runs
`twin_run_runner.py`. A `trap ... EXIT` guarantees the Ollama server
gets killed on any exit path (success, an early failure, or `set -e`
aborting) — not just a `kill` at the bottom that could get skipped.
Detached and resumable by construction (same incremental-checkpoint
pattern as every other runner in this project) — if the job is killed
or times out, re-submitting the same script picks up from
`master_log.json`'s already-done cells rather than restarting.

### 10.5 Monitoring

```
squeue -u soumyaj
tail -f /scratch/soumyaj/RTLCoderHPC/logs/twin_*.log
```

`twin_run_runner.py` prints a `[N/75] <module> / <model> /
<prompt_condition> / replicate <k>` line per cell, same progress format
as every other runner in this project -- use entry count in
`master_log.json` (not just the console log, which can lag when
redirected) to judge real progress, same lesson as every prior overnight
run in this project.

```
python3 -c "import json; d=json.load(open('/scratch/soumyaj/RTLCoderHPC/results/twin_run/master_log.json')); print(len(d), '/ 75 done;', sum(1 for e in d if e.get('error')), 'errored')"
```

### 10.6 Download results back

```
# On your laptop
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/logs/twin_*.log ./phase2_twin_logs/
scp -r soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/RTLCoderHPC/results/twin_run ./phase2_twin_results
```

---

## Troubleshooting

| Problem                                                         | Fix                                                                                                                                                                                                                  |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RuntimeError: FAILED to load ishorn5/RTLCoder-Deepseek-v1.1` | Almost always means Section 4's download never completed or`HF_HOME` isn't set to where it landed. Re-run the `find`/`du` check in Section 4.                                                                  |
| `HF_HOME is not set` warning                                  | `source /scratch/soumyaj/RTLCoderHPC/env.sh` before running anything.                                                                                                                                              |
| `FATAL: .../design_description.txt not found`                 | RTLLM isn't at`$RTLLM_ROOT` — check Section 3, or pass `--rtllm-root` explicitly.                                                                                                                               |
| `iverilog: command not found` in check (d)                    | The `export PATH=.../oss-cad-suite/bin:$PATH` line (Section 6) is missing from the script, or `env.sh` wasn't sourced first. Confirm with `which iverilog` after sourcing both. |
| Job stuck in`PD`                                              | `QOSMaxJobsPerUserLimit` — same as AutoChip, cluster caps simultaneous GPU jobs; it starts once another finishes.                                                                                                 |
| `curl`/`git clone` gets a tiny file or hangs on login node  | Login node blocks outbound internet, same as AutoChip's ollama binary problem — use the sbatch-node path (Sections 3/4) or laptop+SCP fallback.                                                                     |
| Check (b) generation produces empty output but no exception     | Model loaded onto CPU with no error (rare, but possible if`device_map="auto"` picked CPU due to a GPU allocation issue) — check `device=` in check (a)'s log line; should say `cuda:0`, not `cpu`.          |
| Twin run: `openai.APIConnectionError` on any of the 3 Ollama models | Ollama server isn't up yet, or died. Check `ollama_twin_*.log`; `twin_run.slurm`'s readiness loop (up to 30s, polling `ollama list`) may need lengthening on a slow node. |
| Twin run: `FATAL: ollama server never became ready` | Same as above, but the job's own readiness loop already gave up and exited — check `ollama_twin_JOBID.log` for why `ollama serve` itself failed to start (port already in use from a stale process, disk issue under `OLLAMA_MODELS`, etc). |
| Twin run: `FATAL: ... is missing: [...]` (from `twin_run.slurm` or `twin_run_runner.py`'s own `_verify_ollama_models()`) | Section 10.3 (`pull_ollama_models.slurm`) wasn't run, or was run against a different `OLLAMA_MODELS` path than this job uses. Run it, confirm with `ollama list`, then resubmit — don't let either script pull inline (see the comment in `twin_run.slurm`). |
| Twin run: `grep` in Section 10.2 comes back empty for either fix | Do NOT launch. Re-scp `stitch_runner_hpc.py` and re-check — this means the deployed file is not the verified one. |
| Twin run: `alu`/`calendar` failing 100% again, `$readmemh` errors in `sim_log.txt` | The exact symptom bug #2 caused before it was fixed. Means Section 10.2's grep check was skipped or the wrong file got deployed — go back and verify. |

---

## Quick reference card

| Command                      | Description                                |
| ---------------------------- | ------------------------------------------ |
| `squeue -u soumyaj`        | Check your running/queued jobs             |
| `scancel JOBID`            | Cancel a specific job                      |
| `sinfo -o "%n %G %t"`      | List all nodes with GPU info               |
| `tail -f logs/smoke_*.log` | Live log of the running smoke test         |
| `source env.sh`            | Load`HF_HOME`/`RTLLM_ROOT`             |
| `sbatch smoke_test.slurm`  | Submit the smoke test job                  |
| `du -sh hf_cache`          | Check how much of scratch the weights used |
| `df -h /scratch/soumyaj`   | Check overall scratch disk usage           |
| `sbatch pull_ollama_models.slurm` | One-time: pull the 3 Ollama models this run needs |
| `sbatch twin_run.slurm`    | Submit the twin-comparison run (75 runs)  |
| `tail -f logs/twin_*.log`  | Live log of the twin run                   |
