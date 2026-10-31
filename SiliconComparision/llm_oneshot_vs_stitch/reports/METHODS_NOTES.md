# Methods notes

## Context window: num_ctx 32768 (Phase 3 used 8192)

Every LLM call in this study, one-shot and both feedback arms, sends the same Ollama options: temperature 0.1 and
num_ctx 32768. Nothing else is sent; num_predict, seed, top_p and top_k stay at the Ollama and model defaults, as in
Phase 3. The Phase 3 runner sends the same two options, and its production run used num_ctx 8192. That was the runner
default, and the Phase 3 32b server log shows `n_ctx = 8192`. 32768 is the context qwen2.5-coder:32b was trained with
(`n_ctx_train = 32768` in the same log).

Phase 3 tasks were single leaf modules, and all of them fit in 8192 tokens. Several tasks here do not. num_predict is
not set, so the answer shares num_ctx with the prompt. The table lists every task whose prompt plus a golden-sized
answer is over 8192 tokens. Figures are estimates from `pipeline/budget.py` (`reports/PREDEPLOY_BUDGET.md`), counted
with the Qwen2.5 tokenizer. The arms prompt is measured with the golden module as the current RTL and no feedback, so
it is a lower bound for every feedback iteration.

| task | one-shot prompt + answer | arms prompt + answer | over 8192 | over 32768 |
|---|---|---|---|---|
| round_robin_req | 5,369 | 9,226 | arms | no |
| op_core | 9,271 | 15,473 | one-shot, arms | no |
| op_link1 | 9,443 | 15,664 | one-shot, arms | no |
| op_link2 | 9,113 | 15,185 | one-shot, arms | no |
| op_link3 | 9,127 | 15,213 | one-shot, arms | no |
| op_link4 | 9,107 | 15,173 | one-shot, arms | no |
| top_2x2_router | 5,764 | 10,127 | arms | no |
| top_module | 29,470 | 51,816 | one-shot, arms | arms |

The other 26 tasks fit in 8192 tokens in both one-shot and the arms. At 8192, the answers for the arms marked in the
"over 8192" column would be cut off. 32768 is the largest context the model was trained for, and it is used for all 34
tasks with no per-task setting.

top_module still does not fit in the arms. Its prompt there is about 29,452 tokens, which leaves about 3,300 tokens for
an answer of about 22,364. It is run as is, without special handling. Each call's `done_reason` and output token count
are recorded (`runs/arms/results/.../iter<k>/llm_meta.json`, `runs/oneshot/<m>/record.json`). `reports/SUMMARY.md`
lists every call that ended with `done_reason=length`.

## CPU threads: num_thread = the job's CPUs

Every /api/chat request in this study, one-shot and both arms, also carries `options.num_thread` = the job's CPU count
(`$SLURM_CPUS_PER_TASK`, 4). `pipeline/p3_bridge.py` adds it to the runner's request for both paths. The same value is
given to llama-server through `LLAMA_ARG_THREADS` and `LLAMA_ARG_THREADS_BATCH` (`pipeline/hpc_env.sh`).

num_thread is a CPU-thread setting, not a sampling option. Phase 3 sent no thread setting. Its llama-server ran 64
threads on 8 CPUs (`n_threads = 64 (n_threads_batch = 64) / 64` in the Phase 3 32b server log) and generated about
4.9 tokens/s. This study's first two jobs did the same: 5.3 tokens/s on an H200 and 4.4 tokens/s on an A100
(`reports/SPEED.md`, `pipeline/speed.py`). In every one of these jobs all 65 layers ran on the GPU
(`offloaded 65/65 layers to GPU`), so the thread count sets how many CPU threads drive the GPU, not the model.

The job checks the setting on the first call. It stops (exit 3) if llama-server's n_threads differs from the
configured value or generation is slower than 8 tokens/s, and warns below 15 tokens/s. The values are recorded in
`runs/RUN_MANIFEST.json`.

## Client timeout: 3600 s (Phase 3: 900 s)

Both paths use a client HTTP timeout of 3600 s per call (`p3_bridge.CLIENT_TIMEOUT_S`). Phase 3 used 900 s, which its
leaf answers never reached. Here, answers of 6,000-22,000 tokens at 4-5 tokens/s took longer than 900 s: op_core timed
out in job 423542. The timeout is a client setting, not sent to Ollama. A request body that has already timed out
fails at once on the runner's retries, so one slow call costs one timeout, not three. A module that still fails is
recorded as an infrastructure error and retried on the next submission.

## Whole-router bonus prompt: not attempted

The whole router (top_module with all its descendants) as one one-shot prompt was not attempted. The prompt alone is
32,290 of 32,768 tokens (`pipeline/budget.py`), and a golden-sized answer is about 74,627 tokens. `GEN_FULL_ROUTER`
defaults to 0, so one-shot produces 34 files.

## Run history

Per-job figures are in `reports/RUN_HISTORY.md` (`pipeline/run_history.py`, from the git-ignored `hpc_logs/`), and
which job produced each output is in `reports/INTEGRITY.md` (`pipeline/integrity.py`).

- **422841** (gpunode7, H200 NVL, deployed commit e77bf73): smoke run on 3 tasks (encoder, register_4bit, allot_vc),
  one-shot and both arms. llama-server ran 64 threads; generation 5.32 tok/s. JOB DONE after 1:09:40.
- **423542** (gpunode4, A100-SXM4-80GB, e77bf73): all tasks, 64 threads, 4.37 tok/s. The one-shot call for op_core
  hit the 900 s client timeout (`RuntimeError: ollama failed after retries: timed out`) and the job stopped. Its 22
  finished one-shot records are kept.
- **424063** (gpunode5, H100 80GB HBM3, deployed commit 62b4131): the remaining 9 one-shot modules and the remaining
  31 runs per arm. 4 threads; generation 64.91 tok/s pooled, 48.4-74.0 tok/s per call (median 67.9). JOB DONE
  4:21:38 after its first log line.

Settings common to the runs: num_ctx 32768; options.num_thread 4 from 62b4131 on (a CPU-thread setting, not a
sampling option); client timeout 3600 s from 62b4131 on (900 s before); `--cpus-per-task=4` (the site allows 4 CPUs
per GPU). Temperature 0.1 and no seed in every call. The whole-router bonus prompt was not attempted. The cluster
results were extracted from an archive with sha256 `93c24d50a0c7aa7e8733c60dbb1096df719828933e55d5a60c5d4954c2c10ace`
(`reports/INTEGRITY.md`).

## Evaluation caveats

- **No sampling seed.** With identical prompts, the two arms' first answers differed in 6 of 25 modules
  (`reports/STITCH_VS_RETRY.md`). A difference between the arms can come from sampling alone; every gain and
  regression in that report states whether the arms diverged after a different or an identical prompt.
- **The mesh tb is cycle-exact against a golden with simulation races.** The golden's blocking-assignment flops
  (q = d) make the comparison sensitive to event order. Five LLM modules that are formally equivalent to golden fail
  it (`reports/ASSEMBLY.md`).
- **The loop tb is cycle-exact even for timing-dependent modules.** Their sign-off verdict is the property checks,
  so the loop feedback is stricter than the sign-off verdict (`reports/FAILURE_AUDIT.md`).
