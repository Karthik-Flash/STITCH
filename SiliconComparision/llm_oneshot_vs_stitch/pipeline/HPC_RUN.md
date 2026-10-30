# HPC run: LLM one-shot vs STITCH (2x2 mesh)

This page is for running the generation job on the BITS Hyderabad HPC. Copy each command exactly as shown.

- Cluster login: `soumyaj@hpc.bits-hyderabad.ac.in`
- Base folder on the cluster: `/scratch/soumyaj/STITCH_GEN`
- Study folder on the cluster: `/scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch`
- Job logs: `/scratch/soumyaj/STITCH_GEN/logs/gen_<JOBID>.log`
- Laptop repository: `D:\Projects\STITCH`

The job (`pipeline/gen_job.slurm`) uses 1 GPU, 4 CPUs, 48 GB of memory and up to 24 hours. It runs in this order:
the self-test gate, the preflight checks, one-shot generation for 34 modules, the two feedback arms (68 runs), then the
summary. Background on the settings: `reports/METHODS_NOTES.md` and `reports/SPEED.md`.

Three placeholders appear on this page. Replace each one before you press Enter:

| Placeholder | What to put there | Where it comes from |
|---|---|---|
| `<PART>` | a partition name, for example `gpu_h100_4` | step 3 output |
| `<NODE>` | a node name, for example `gpunode5` | step 3 output |
| `<JOBID>` | a job number, for example `424063` | step 4 output, or `/scratch/soumyaj/STITCH_GEN/logs/JOBIDS.txt` |

Most commands below use `$JOB` instead of `<JOBID>`. Step 4 sets `$JOB`.

## 0. Rules

1. **Run one generation job at a time.** Two jobs write to the same `runs/` folder and corrupt it. Before you submit,
   check that this shows no `stitch_gen` job:

   ```bash
   squeue -u soumyaj -n stitch_gen
   ```

2. **Paste one line at a time.** Pasting several lines at once can garble them in the terminal.
3. **The site allows 4 CPUs per GPU.** The job script already asks for 4. Do not add `--cpus-per-task` to `sbatch`.
4. **Never edit files on the HPC.** Change the repository on the laptop, commit, push, and redeploy (step 1).
5. **Do not deploy while a generation job is queued or running.** Wait until `squeue -u soumyaj -n stitch_gen` is
   empty.

## 1. Deploy from the laptop (PowerShell)

Go to the repository:

```powershell
cd D:\Projects\STITCH
```

Check for local changes. This must print nothing. If it prints anything, commit or discard it first:

```powershell
git status --short
```

Note the commit you are about to deploy. You will compare it in step 2:

```powershell
git log -1 --oneline
```

Dry run. This builds the package, sends nothing, and must end with `DryRun: ... nothing sent.`:

```powershell
powershell -ExecutionPolicy Bypass -File SiliconComparision\llm_oneshot_vs_stitch\pipeline\deploy_gen.ps1 -DryRun
```

Real deploy. It asks for the cluster password up to six times:

```powershell
powershell -ExecutionPolicy Bypass -File SiliconComparision\llm_oneshot_vs_stitch\pipeline\deploy_gen.ps1
```

The deploy prints two lines of counts, for example `remote results before (...): 25 6 25` and
`remote results after: 25 6 25`. The three numbers are:

1. one-shot record files,
2. finished arm runs (`metrics.json`),
3. one-shot Verilog outputs.

Each number must stay the same or go up. Results on the cluster are never shipped, overwritten or deleted. If any
number drops, the script stops with `remote result count dropped`. The deploy then runs the hash check from step 2 and
must end with `Deployed to ...`.

## 2. Verify the deploy on the HPC

Log in:

```bash
ssh soumyaj@hpc.bits-hyderabad.ac.in
```

Show the deployed commit. It must equal the hash from `git log -1` in step 1 and must not say `(dirty)`:

```bash
cat /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch/DEPLOYED_COMMIT.txt
```

Check the file hashes. Every line must end in `OK`:

```bash
cd /scratch/soumyaj/STITCH_GEN && sha256sum -c DEPLOY_HASHES.sha256
```

## 3. Pick a node

Go to the study folder. Every command from here on runs in this folder:

```bash
cd /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch
```

Ask Slurm when the job would start on each usable node. This submits nothing:

```bash
for P in gpu_h200_8:gpunode7 gpu_a100_8:gpunode4 gpu_h100_4:gpunode5 gpu_h100_4:gpunode6; do sbatch --test-only --partition=${P%:*} --nodelist=${P#*:} pipeline/gen_job.slurm 2>&1; done
```

Each answer looks like:

```
sbatch: Job 424100 to start at 2026-10-31T09:12:00 using 4 processors on nodes gpunode5 in partition gpu_h100_4
```

Pick the line with the earliest `to start at`. Its `partition` is your `<PART>` and its `nodes` value is your `<NODE>`.

To see the node states:

```bash
sinfo -N -l -p gpu_h200_8,gpu_a100_8,gpu_h100_4
```

How to read the STATE column:

- `idle` or `mixed`: usable now.
- `allocated`: full; the job waits.
- `mixed-` (trailing `-`): reserved for another job that will start soon.
- `drained` or `draining`: taken out of service. An admin must resume the node; do not pick it.

Nodes not in the list above:

- V100 nodes: excluded. They have 32 GB, and the preflight needs at least 40 GiB of GPU memory.
- The RTX partition: not usable for this job.

To see who is using a node:

```bash
squeue -w <NODE> -o "%.10i %.10u %.12P %.8T %.10L"
```

## 4. Submit

Check that no generation job is queued or running. This must show only the header line:

```bash
squeue -u soumyaj -n stitch_gen
```

Submit, replacing `<PART>` and `<NODE>` with the values from step 3. The job number goes into `$JOB`:

```bash
JOB=$(sbatch --parsable --partition=<PART> --nodelist=<NODE> pipeline/gen_job.slurm); echo $JOB
```

Save the job number, date, partition and node:

```bash
echo "$JOB $(date '+%F %T') $(squeue -h -j $JOB -o '%P %n')" >> /scratch/soumyaj/STITCH_GEN/logs/JOBIDS.txt
```

Show the expected start time:

```bash
squeue --start -j $JOB
```

New terminal, or logged in again later? Set `$JOB` again from the saved list:

```bash
JOB=$(tail -1 /scratch/soumyaj/STITCH_GEN/logs/JOBIDS.txt | cut -d' ' -f1); echo $JOB
```

## 5. First check, about 15 minutes after the job shows RUNNING

The gate and preflight must have passed:

```bash
grep -E "GATE:|PREFLIGHT:|^\[gpu\]|^\[digest\]|^\[options\]" /scratch/soumyaj/STITCH_GEN/logs/gen_$JOB.log
```

Expect `GATE: ALL PASSED`, `[gpu] ok`, `[digest] ok`, `[options] ok` and `PREFLIGHT: ALL PASSED`.

Then show the first-call checks. They come after `PREFLIGHT: ALL PASSED`:

```bash
sed -n '/PREFLIGHT: ALL PASSED/,$p' /scratch/soumyaj/STITCH_GEN/logs/gen_$JOB.log | grep -E "^\[(gpu offload|threads|speed)\]|FIRST-CALL"
```

These three lines must appear:

- `[gpu offload] offloaded 65/65 layers to GPU`
- `[threads] ok  llama-server n_threads = 4 (n_threads_batch = 4) ...`
- `[speed] ok  ... tok/s`, at 15 tok/s or more. Job 424063 ran at 61.4 tok/s on an H100. Between 8 and 15 the line
  says `WARNING`: the job continues, but tell the team.

If nothing shows yet, the model is still loading. Check again in 5 minutes.

Lines starting with `[selftest]` come from the gate's own tests with fake models. They are expected; ignore them.

## 6. Monitor

Your jobs, with time used (`TIME`) and time left (`TIME_LEFT`):

```bash
squeue -u soumyaj -o "%.10i %.12P %.10j %.8T %.10M %.10L %.10N %R"
```

Finished one-shot modules (34 when done):

```bash
grep -L '"infra_error"' runs/oneshot/*/record.json | wc -l
```

One-shot modules with an infrastructure error (should be 0; a resubmit retries them):

```bash
grep -l '"infra_error"' runs/oneshot/*/record.json | wc -l
```

Finished arm runs (68 when done):

```bash
find runs/arms/results -path '*/rep1/metrics.json' | wc -l
```

Follow the log live. Ctrl+C stops the viewing only; the job keeps running:

```bash
tail -f /scratch/soumyaj/STITCH_GEN/logs/gen_$JOB.log
```

## 7. When the job ends: exit codes

Show how the job ended:

```bash
sacct -j $JOB -X -o JobID,State,ExitCode,Elapsed
```

Show the end of the log:

```bash
tail -20 /scratch/soumyaj/STITCH_GEN/logs/gen_$JOB.log
```

| State / ExitCode | Meaning | What to do |
|---|---|---|
| `COMPLETED` `0:0` | All 34 one-shot modules and 68 arm runs finished; the summary is written. | Step 9. |
| `FAILED` `2:0` | Some modules hit a timeout or connection error. The log lists them under `INFRA ERRORS` or `ARMS NOT FINISHED`. | Resubmit (step 4); only the failed work runs again. |
| `FAILED` `3:0` | The first-call check failed: wrong thread count or slower than 8 tok/s. | Do not resubmit. Send the team the output of `tail -40` of the log. |
| `TIMEOUT` | The 24-hour limit was reached. | Resubmit (step 4); finished work is skipped. |
| `FAILED` `1:0` | Gate or preflight failed; nothing was generated. | Send the team the log tail. |

## 8. Move a queued job to another node

Use this when the job is still `PENDING` and another node would start sooner (step 3).

Remember the old job:

```bash
OLD=$JOB; echo $OLD
```

Hold it so it cannot start:

```bash
scontrol hold $OLD
```

Submit the new job with the new `<PART>` and `<NODE>`, using the three step-4 commands (`JOB=$(sbatch ...)`, `echo ... >> JOBIDS.txt`,
`squeue --start -j $JOB`).

Once the new job shows `RUNNING`, cancel the old one:

```bash
scancel $OLD
```

Changed your mind before the new job starts? Cancel the new job:

```bash
scancel $JOB
```

Then release the old job again:

```bash
scontrol release $OLD
```

Then point `$JOB` back at the old job:

```bash
JOB=$OLD; echo $JOB
```

Never release the old job while the new one is running (rule 1).

## 9. Copy the results back

Only after the job has ended (`squeue -u soumyaj -n stitch_gen` is empty).

On the HPC, go to the study folder:

```bash
cd /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch
```

Pack the results:

```bash
tar -czf /scratch/soumyaj/STITCH_GEN/gen_results.tgz outputs prompts reports runs
```

Print the hash of the package:

```bash
sha256sum /scratch/soumyaj/STITCH_GEN/gen_results.tgz
```

On the laptop (PowerShell), go to the repository:

```powershell
cd D:\Projects\STITCH
```

Download the package:

```powershell
scp soumyaj@hpc.bits-hyderabad.ac.in:/scratch/soumyaj/STITCH_GEN/gen_results.tgz $env:TEMP\gen_results.tgz
```

Print its hash. It must equal the HPC hash; PowerShell prints it in capitals:

```powershell
Get-FileHash -Algorithm SHA256 $env:TEMP\gen_results.tgz
```

Unpack it into the study folder:

```powershell
tar -xzf $env:TEMP\gen_results.tgz -C SiliconComparision\llm_oneshot_vs_stitch
```

`runs/` stays local (gitignored). `outputs/`, `prompts/` and `reports/` are the files to commit.

## 10. Troubleshooting

| You see | Cause | Fix |
|---|---|---|
| `sbatch: error: Unable to open file pipeline/gen_job.slurm` | You are not in the study folder. | `cd /scratch/soumyaj/STITCH_GEN/SiliconComparision/llm_oneshot_vs_stitch`, then submit again. |
| `-bash: PART: No such file or directory` | `<PART>` or `<NODE>` was pasted literally. | Replace both placeholders with the values from step 3. |
| `only 4 CPUs per H200 GPU` (or similar) | Site rule: at most 4 CPUs per GPU. | Use the job script as is; do not add `--cpus-per-task`. |
| A command that looks cut or merged with the next line | Several lines were pasted at once. | Press Ctrl+C, then paste one line at a time. |
| `[selftest] ... BAD 5.0 tok/s` before `GATE: ALL PASSED` | Gate self-test with a fake model, not the real job. | Ignore it; only lines after `PREFLIGHT: ALL PASSED` count (step 5). |
| `[threads] BAD` or `[speed] BAD` after `PREFLIGHT: ALL PASSED`, job ends with exit 3 | llama-server did not use 4 threads, or generation was below 8 tok/s. | Do not resubmit; send the team the log tail. |
| `ReqNodeNotAvail`, `Priority` or `Resources` in the squeue `REASON` column | The job is waiting for the node. | Nothing to fix. To move it, see step 8. |
| `JobHeldUser` in the squeue `REASON` column | The job was held (step 8). | `scontrol release <JOBID>` if it should run. |

History of the A100 failure: before commit `62b4131`, llama-server started 64 CPU threads on a 4-CPU job. Generation
ran at about 4-5 tok/s on both A100 and H200. In job 423542, op_core then hit the 900-second client timeout, and the
error stopped the job. Since `62b4131`:

- the job uses 4 threads and the first call checks this;
- the timeout is 3600 seconds;
- one failed module no longer stops the job.
