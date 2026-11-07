# HPC run: LLM generation of the golden 5-port router

This page lists every command for the BITS Hyderabad HPC, in order. Copy each command exactly as shown.

- Cluster login: `soumyaj@hpc.bits-hyderabad.ac.in`
- Laptop repository: `D:\Projects\STITCH`
- Study folder on the cluster: `/scratch/soumyaj/STITCH_GEN/SiliconComparision/LLM_generation_study`
- Job logs on the cluster: `hpc_logs/` in the study folder

Phase 0 (sections 1 to 6, done 2026-11-05, smoke job 434111): cluster checks, both models, node choice, GPU smoke
test. Generation (section 7): one job per model, both at the same time.

| file in `hpc/` | runs on | what it does |
|---|---|---|
| `deploy_to_hpc.ps1` | laptop | ships the committed code to the cluster; never touches results |
| `hpc_env.sh` | cluster | paths, tools, model names, Ollama server; sourced by every other script |
| `step1_check_login.sh` | login node | read-only checks: tools, Ollama, qwen digest, disk, internet, GPU nodes |
| `step2_get_models.sh` | login node | qwen hard-linked from Phase 3; Gemma pulled; both digests recorded |
| `step3_pick_node.sh` | login node | start time on every H200/H100/A100 node; prints the sbatch line for the best one |
| `step4_smoke_test.slurm` | GPU node | GPU memory, golden checks on the cluster tools, both models answer |
| `model_check.py` | GPU node | one prompt to one model; digest, quantisation, tok/s (used by step 4) |
| `gen_job.slurm` | GPU node | generation for one model: freeze check, mock test, preflight, `pipeline/generate.py` |

Models:

| model | Ollama tag | quantisation | where it comes from |
|---|---|---|---|
| Qwen2.5-Coder 32B | `qwen2.5-coder:32b` | Q4_K_M | Phase 3 store, digest `b92d6a0bd47e...` (hard links, never re-pulled) |
| Gemma 4 31B, instruction-tuned | `gemma4:31b-it-q4_K_M` | Q4_K_M | pulled once by step 2 |

## Rules

1. **Paste one line at a time.** Pasting several lines at once can garble them.
2. **Never edit files on the HPC.** Change the repository on the laptop, commit, and deploy again (step 1).
3. **One job per model at a time.** The qwen job and the Gemma job may run together (each writes only to
   `results/<model>/` and has its own Ollama port), but never two jobs of the same model.
4. **The site allows 4 CPUs per GPU.** The job scripts ask for 4. Do not add `--cpus-per-task`.

## 1. Deploy (laptop, PowerShell)

```powershell
cd D:\Projects\STITCH
```

This must print nothing. If it prints anything, commit first; the deploy ships the last commit only:

```powershell
git status --short
```

Note the commit; step 2 compares it:

```powershell
git log -1 --oneline
```

Dry run. It builds and checks the package and sends nothing. It must end with `DryRun: ... nothing sent.`:

```powershell
powershell -ExecutionPolicy Bypass -File SiliconComparision\LLM_generation_study\hpc\deploy_to_hpc.ps1 -DryRun
```

Real deploy. It asks for the cluster password twice (once for `scp`, once for `ssh`):

```powershell
powershell -ExecutionPolicy Bypass -File SiliconComparision\LLM_generation_study\hpc\deploy_to_hpc.ps1
```

Expected at the end:

```
llmgen_deploy.tar: OK
result files on the cluster: before 0, after 0
deployed commit: <the hash from git log>
Deployed <hash> to soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/STITCH_GEN/SiliconComparision/LLM_generation_study. Next: HPC_RUN.md, step 2.
```

The two counts may be larger than 0 after the first job; the second must never be smaller than the first.

## 2. Log in and check the cluster (login node)

```bash
ssh soumyaj@hpc.bits-hyderabad.ac.in
```

Every command from here on runs in the study folder:

```bash
cd /scratch/soumyaj/STITCH_GEN/SiliconComparision/LLM_generation_study
```

It must show the hash from step 1:

```bash
cat DEPLOYED_COMMIT.txt
```

Read-only checks, about 30 seconds:

```bash
bash hpc/step1_check_login.sh
```

Expected: every line `ok` or `info`, then the GPU node table, then `STEP1: ALL OK`. Note the `[ollama]` version.
If it ends with `STEP1: PROBLEMS: ...`, stop and send the output to the team.

## 3. Get the models (login node, 10 to 30 minutes)

```bash
bash hpc/step2_get_models.sh
```

Expected: `qwen ok: digest b92d6a0b...`, the Gemma download progress, `ollama show` for Gemma (quantization
`Q4_K_M`), then two lines to record and `STEP2: ALL OK`. Copy the two digest lines into the
team notes; phase 1 freezes them.

If the pull fails with `requires a newer version of Ollama`, install the latest Ollama in user space and pull again.
From then on both models use the new Ollama:

```bash
bash hpc/step2_get_models.sh --new-ollama
```

The Ollama server in this step runs on the login node only to download; it listens on 127.0.0.1 and stops at the end.

## 4. Pick the node that starts first (login node, submits nothing)

```bash
bash hpc/step3_pick_node.sh
```

It prints one line per H200, H100 and A100 node with its expected start time, earliest first; at equal times the
faster GPU comes first (H200, H100, A100). `NEVER` means the node cannot take the job now (drained, reserved or
too small). The last line is the exact submit command for the best node, for example:

```
BEST: gpunode5 (H100, partition gpu_h100_4), start 2026-11-05T09:00:00. Submit with:
JOB=$(sbatch --parsable --partition=gpu_h100_4 --nodelist=gpunode5 hpc/step4_smoke_test.slurm); echo $JOB
```

## 5. Smoke test (GPU node, about 10 minutes)

Must show no `llmgen_` job:

```bash
squeue -u soumyaj
```

Paste the `JOB=$(sbatch ...)` line that step 3 printed. It prints the job number.

Save the job number:

```bash
echo "$JOB $(date '+%F %T') smoke $(squeue -h -j $JOB -o '%P %N')" >> hpc_logs/JOBIDS.txt
```

Expected start:

```bash
squeue --start -j $JOB
```

State (`PD` waiting, `R` running; the job is gone from the list when it ends):

```bash
squeue -u soumyaj -o "%.10i %.12P %.14j %.8T %.10M %.10L %.10N %R"
```

When it has ended, show the result lines:

```bash
grep -E "^\[|^MODEL|^SMOKE|^== " hpc_logs/smoke_$JOB.log
```

Expected:

- `[gpu] ok` with at least 40960 MiB
- `[golden] ok` (all 7 modules pass and are struct_clean on the cluster tools, the mesh test passes, routing proved)
- for each model: `[model] ...` with digest and quantisation `Q4_K_M`, `[speed] ok` (8 tok/s is the minimum; qwen ran at 61.4 tok/s on an H100 in
  the closed study),
  `MODEL ...: OK`
- `[offload] ok   both models fully on the GPU`
- last line `SMOKE: ALL PASSED`

Also note the `[thinking]` line of each model: a number above 0 means the model returns hidden reasoning; phase 2
must handle it the same way for every arm.

New terminal, or logged in again later? Set `$JOB` again from the saved list:

```bash
JOB=$(tail -1 hpc_logs/JOBIDS.txt | cut -d' ' -f1); echo $JOB
```

## 6. Copy the smoke-test logs back (laptop, PowerShell)

```powershell
cd D:\Projects\STITCH
```

```powershell
New-Item -ItemType Directory -Force SiliconComparision\LLM_generation_study\hpc_logs
```

```powershell
scp "soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/STITCH_GEN/SiliconComparision/LLM_generation_study/hpc_logs/*" SiliconComparision\LLM_generation_study\hpc_logs\
```

The folder then holds `smoke_<JOBID>.log`, `golden_checks_hpc_<JOBID>.md`, `MODELS.txt`, `JOBIDS.txt` and the
Ollama server logs. Phase 0 is done when `SMOKE: ALL PASSED`.

## 7. Generation: qwen and Gemma at the same time

Each job: freeze check (`FREEZE.sha256`), mock end-to-end test, Ollama, preflight (GPU, cluster tools, the golden of
every task through the pipeline's own checks, model digest), then `pipeline/generate.py`: one-shot, simloop and stitch
for 7 modules x 5 reps. Results go to `results/qwen2.5-coder_32b/` and `results/gemma4_31b-it-q4_K_M/`.

Deploy the frozen commit first (section 1), then on the HPC:

```bash
cd /scratch/soumyaj/STITCH_GEN/SiliconComparision/LLM_generation_study
```

It must show the commit you deployed:

```bash
cat DEPLOYED_COMMIT.txt
```

Must show no `llmgen_qwen` or `llmgen_gemma` job:

```bash
squeue -u soumyaj
```

Pick the node for qwen (24-hour limit):

```bash
bash hpc/step3_pick_node.sh hpc/gen_job.slurm --time=24:00:00 -J llmgen_qwen --export=ALL,GEN=qwen
```

Paste the `JOB=$(sbatch ...)` line it prints, then save it:

```bash
QJOB=$JOB; echo "$QJOB $(date '+%F %T') gen qwen $(squeue -h -j $QJOB -o '%P %N')" >> hpc_logs/JOBIDS.txt
```

Pick the node for Gemma. Slurm now counts the qwen job, so the answer may differ:

```bash
bash hpc/step3_pick_node.sh hpc/gen_job.slurm --time=24:00:00 -J llmgen_gemma --export=ALL,GEN=gemma
```

Paste the `JOB=$(sbatch ...)` line it prints, then save it:

```bash
GJOB=$JOB; echo "$GJOB $(date '+%F %T') gen gemma $(squeue -h -j $GJOB -o '%P %N')" >> hpc_logs/JOBIDS.txt
```

Expected starts:

```bash
squeue --start -u soumyaj
```

New terminal later? Set both job numbers again:

```bash
QJOB=$(grep ' gen qwen' hpc_logs/JOBIDS.txt | tail -1 | cut -d' ' -f1); GJOB=$(grep ' gen gemma' hpc_logs/JOBIDS.txt | tail -1 | cut -d' ' -f1); echo $QJOB $GJOB
```

### As actually run (2026-11-05 to 2026-11-07): 2-hour chunks

A 24-hour job would have waited until 2026-11-08 (an 8-hour one until 2026-11-16), and the cluster rejects a job
that names two partitions ("Multiple partition job request not supported"). The work therefore ran in 2-hour jobs
with the same job name and `--dependency=singleton`: Slurm runs them one at a time, each continues where the last
stopped (finished work is skipped), and a job with nothing left ends in a few minutes. From the study folder:

```bash
for i in 1 2 3; do sbatch --parsable --partition=gpu_h200_8 --time=2:00:00 -J llmgen_qwen --dependency=singleton --export=ALL,GEN=qwen hpc/gen_job.slurm; sbatch --parsable --partition=gpu_h100_4 --time=2:00:00 -J llmgen_qwen --dependency=singleton --export=ALL,GEN=qwen hpc/gen_job.slurm; done
```

(the same with `-J llmgen_gemma` and `GEN=gemma` for Gemma). When `results/<model>/outputs/*/rep*/*.v` holds 35
files per arm, cancel the jobs still waiting: `scancel -u soumyaj -t PENDING -n llmgen_qwen`. Jobs that ran: Gemma
434462 and 434463; qwen 434444, 436070 and 436071 (`hpc_logs/gen_llmgen_*.log`).

Pack the results from the study folder (`cd` first; a `tar` started elsewhere packs nothing).

### First check, about 15 minutes after a job shows `R`

```bash
grep -hE "^\[(freeze|gpu|tools|golden|digest|gpu offload|threads|speed)\]|MOCK E2E|PREFLIGHT|FAILED" hpc_logs/gen_llmgen_qwen_$QJOB.log hpc_logs/gen_llmgen_gemma_$GJOB.log
```

Expected for each job: `[freeze] ok`, `MOCK E2E: PASS`, `[gpu] ok`, 3 `[tools] ok`, 7 `[golden] ok`, `[digest] ok`,
`PREFLIGHT: ALL PASSED`, then `[gpu offload] offloaded N/N layers`, `[threads] ok`, `[speed] ok`.

### Monitor

```bash
squeue -u soumyaj -o "%.10i %.14j %.8T %.10M %.10L %.10N %R"
```

Finished outputs per model (oneshot, simloop, stitch; 35 35 35 when done):

```bash
for d in results/*/; do echo "$d $(ls $d/outputs/oneshot/rep*/*.v 2>/dev/null | wc -l) $(ls $d/outputs/simloop/rep*/*.v 2>/dev/null | wc -l) $(ls $d/outputs/stitch/rep*/*.v 2>/dev/null | wc -l)"; done
```

Last lines of both logs:

```bash
tail -3 hpc_logs/gen_llmgen_qwen_$QJOB.log hpc_logs/gen_llmgen_gemma_$GJOB.log
```

### When a job ends

```bash
sacct -j $QJOB,$GJOB -X -o JobID,JobName,State,ExitCode,Elapsed
```

| State / ExitCode | Meaning | What to do |
|---|---|---|
| `COMPLETED` `0:0` | `GENERATION DONE`: 35 outputs per arm. | Copy back (below). |
| `FAILED` `2:0` or `TIMEOUT` | Unfinished work (listed at the end of the log). | Resubmit the same model (pick a node again); finished work is skipped. |
| `FAILED` `1:0` | Freeze check, mock test or preflight failed; nothing generated. | Send `tail -40` of the log. |
| `FAILED` `3:0` | First-call check: wrong thread count or below 8 tok/s. | Do not resubmit; send `tail -40` of the log. |

### Copy the results back (both jobs ended)

On the HPC, in the study folder:

```bash
tar -czf /scratch/soumyaj/STITCH_GEN/llmgen_results.tgz results hpc_logs
```

```bash
sha256sum /scratch/soumyaj/STITCH_GEN/llmgen_results.tgz
```

On the laptop (PowerShell):

```powershell
cd D:\Projects\STITCH
```

```powershell
scp soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/STITCH_GEN/llmgen_results.tgz $env:TEMP\llmgen_results.tgz
```

It must equal the HPC hash (PowerShell prints capitals):

```powershell
Get-FileHash -Algorithm SHA256 $env:TEMP\llmgen_results.tgz
```

```powershell
tar -xzf $env:TEMP\llmgen_results.tgz -C SiliconComparision\LLM_generation_study
```

## Troubleshooting

| You see | Cause | Fix |
|---|---|---|
| `uncommitted changes, commit first` (deploy) | The deploy ships the last commit only. | Commit, then deploy again. |
| `sha256sum: WARNING: 1 computed checksum did NOT match` (deploy) | The upload was damaged. Nothing was unpacked. | Run the deploy again. |
| `bash: hpc/step1_check_login.sh: No such file or directory` | Not in the study folder, or not deployed. | `cd /scratch/soumyaj/STITCH_GEN/SiliconComparision/LLM_generation_study` |
| `[qwen_phase3] BAD` | The Phase 3 store changed or was purged. | Stop; do not re-pull qwen (that can change its digest). Tell the team. |
| `[same_fs] BAD` | Hard links cannot cross filesystems. | Tell the team; qwen would have to be copied (about 20 GB). |
| `requires a newer version of Ollama` (step 2) | Ollama is older than Gemma 4. | `bash hpc/step2_get_models.sh --new-ollama` |
| `zstd is not installed` (step 2 with `--new-ollama`) | The Ollama archive is zstd-compressed. | Ask the HPC team for zstd, or use the Hugging Face fallback below. |
| Every node `NEVER` (step 3) | All GPU nodes drained or reserved. | `sinfo -N -l`, then try again later. |
| `ReqNodeNotAvail`, `Priority` or `Resources` in squeue | The job waits for the node. | Nothing; or cancel (`scancel $JOB`) and pick again (step 4). |
| `[speed] BAD` or `[offload] BAD` | Model not fully on the GPU, or too few CPU threads. | Send `tail -60 hpc_logs/smoke_$JOB.log` to the team. |
| `[golden] BAD` | The cluster tools disagree with the laptop on the golden. | Compare `hpc_logs/golden_checks_hpc_<JOBID>.md` with `reports/GOLDEN_CHECKS.md`. |

Hugging Face fallback for Gemma (only if Ollama cannot pull it at all): download `google/gemma-4-31B-it` with a
Hugging Face token after accepting the licence, convert it to GGUF at Q4_K_M, and `ollama create` it. Never print or
commit the token. Ask the team before starting; it is not scripted.
