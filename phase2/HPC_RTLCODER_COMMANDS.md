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

## 6. Find iverilog on the target GPU node — BEFORE submitting the smoke test

GPU nodes often don't carry `iverilog` on `PATH` by default (this doc's
own troubleshooting table flags it) — check (d) of the smoke test needs
it, so find it now rather than discovering the gap from a failed job
log. Quick interactive session, no need to wait in the batch queue:

```
srun --nodelist=gpunode4 --gres=gpu:0 --time=00:05:00 --pty bash -c '
  echo "--- module avail matches ---"
  module avail 2>&1 | grep -i "iverilog\|icarus\|verilog"
  echo "--- which iverilog (no module loaded) ---"
  which iverilog
'
```

Three possible outcomes:

1. **`module avail` lists something** (e.g. `icarus-verilog/12.0`,
   naming will vary by cluster) — note the exact name. That's what goes
   into `smoke_test.slurm` below as `module load <name>`.
2. **`which iverilog` already resolves with no module needed** — rare
   (system-wide install), but if so, skip the `module load` line
   entirely in Section 7's script.
3. **Neither** — no iverilog anywhere on this node. Two fallbacks, in
   order of effort:
   - **Point the smoke test at a different node.** Check the others
     the same way (`srun --nodelist=gpunode6 ...`, etc.) — iverilog is
     a CPU-only tool, so it doesn't need to be on a GPU-carrying node's
     default image specifically; whichever node has it, run check (d)
     there (the model-loading/generation checks still need the GPU
     node — this would mean splitting the smoke test's compile check
     onto a second node, a real complication, only worth it if no GPU
     node has iverilog at all).
   - **Install a portable iverilog into scratch and PATH it in.**
     Mirrors AutoChip's own pattern of keeping a self-contained binary
     under `bin/` instead of depending on the cluster image:
     ```
     # On a node WITH internet (or laptop-download + scp, same fallback
     # pattern as Sections 3-4), build or fetch a static iverilog build,
     # then:
     mkdir -p /scratch/soumyaj/RTLCoderHPC/bin
     # ...place the iverilog/vvp binaries there...
     export PATH=/scratch/soumyaj/RTLCoderHPC/bin:$PATH   # add to env.sh too
     ```

Do not leave this as "load whatever the module is" — write the actual
name (or the fallback you used) into `smoke_test.slurm` before
submitting, and note it here for the next person:

```
# Discovered on <date>: module name = ______________
# (or: fallback used = ______________)
```

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

# From Section 6's discovery step -- REPLACE <ICARUS_MODULE_NAME> with
# the real name found there. Delete this line entirely if outcome 2
# applied (iverilog already resolves with no module load), or replace
# it with the PATH export from outcome 3's fallback if no module exists
# on this node at all.
module load <ICARUS_MODULE_NAME>

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

(and re-run Section 6's discovery step against `gpunode6` specifically
— module availability isn't guaranteed to match `gpunode4`.)

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

## Troubleshooting

| Problem                                                         | Fix                                                                                                                                                                                                                  |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RuntimeError: FAILED to load ishorn5/RTLCoder-Deepseek-v1.1` | Almost always means Section 4's download never completed or`HF_HOME` isn't set to where it landed. Re-run the `find`/`du` check in Section 4.                                                                  |
| `HF_HOME is not set` warning                                  | `source /scratch/soumyaj/RTLCoderHPC/env.sh` before running anything.                                                                                                                                              |
| `FATAL: .../design_description.txt not found`                 | RTLLM isn't at`$RTLLM_ROOT` — check Section 3, or pass `--rtllm-root` explicitly.                                                                                                                               |
| `iverilog: command not found` in check (d)                    | Section 6's discovery step wasn't run, or `smoke_test.slurm`'s `module load` line wasn't filled in with what it found. Run Section 6 against the node named in your `#SBATCH --nodelist`, then update the script — don't guess a module name. |
| Job stuck in`PD`                                              | `QOSMaxJobsPerUserLimit` — same as AutoChip, cluster caps simultaneous GPU jobs; it starts once another finishes.                                                                                                 |
| `curl`/`git clone` gets a tiny file or hangs on login node  | Login node blocks outbound internet, same as AutoChip's ollama binary problem — use the sbatch-node path (Sections 3/4) or laptop+SCP fallback.                                                                     |
| Check (b) generation produces empty output but no exception     | Model loaded onto CPU with no error (rare, but possible if`device_map="auto"` picked CPU due to a GPU allocation issue) — check `device=` in check (a)'s log line; should say `cuda:0`, not `cpu`.          |

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
