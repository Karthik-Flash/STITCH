# Integrity of the HPC results (pipeline/integrity.py)

Archive extracted into the study folder: sha256 `7cb51ed4bd3ca5fbf5215190f2752f3df72cca5d2e2185dedf91d064c5976aa3` (excludes *.vvp/*.vcd; value as recorded at download, the archive itself is not in the repository).

No gen log in hpc_logs/ (the job log stayed on the cluster): each one-shot record is attributed to the study's only run manifest. The manifest's git_commit is `UNKNOWN`: preflight.py looked for DEPLOYED_COMMIT.txt in the study sub-folder instead of the study root (fixed after this job). The deployed commit, 0fa68c9, was checked on the cluster (DEPLOYED_COMMIT.txt, reported by the user).

## Summary

- one-shot records: 4 of 4; arm runs with metrics.json: 8 of 8
- problems: 0 (nothing missing, errored or mismatched)

| part | job | GPU | deployed commit | count |
|---|---|---|---|---|
| one-shot | 426786 | NVIDIA H200 NVL | UNKNOWN | 4 |
| simloop | 426786 | NVIDIA H200 NVL | UNKNOWN | 4 |
| stitch | 426786 | NVIDIA H200 NVL | UNKNOWN | 4 |

Jobs (run manifests):

- 426786: gpunode7.sharanga.local, NVIDIA H200 NVL, commit UNKNOWN, GEN_TASKS all, threads {'SLURM_CPUS_PER_TASK': '4', 'LLAMA_ARG_THREADS': '4', 'LLAMA_ARG_THREADS_BATCH': '4', 'options.num_thread (p3_bridge)': 4}

Iteration testbench copies (runs/arms/results/**/iter*/tb*.v, git-ignored): 56 byte-identical to tasks/<m>/, 0 differ.

## One-shot records

| module | status | output sha256 = record | tokens out | done_reason | job | GPU | commit |
|---|---|---|---|---|---|---|---|
| depack | ok | True | 526 | stop | 426786 | NVIDIA H200 NVL | UNKNOWN |
| new1 | ok | True | 378 | stop | 426786 | NVIDIA H200 NVL | UNKNOWN |
| nidepack | ok | True | 402 | stop | 426786 | NVIDIA H200 NVL | UNKNOWN |
| rp1 | ok | True | 765 | stop | 426786 | NVIDIA H200 NVL | UNKNOWN |

## Arm runs

| module | arm | LLM calls | stop | final = outputs/<arm> | job | GPU | commit | earlier failed attempts |
|---|---|---|---|---|---|---|---|---|
| depack | simloop | 6 | budget | True | 426786 | NVIDIA H200 NVL | UNKNOWN | 0 |
| new1 | simloop | 6 | budget | True | 426786 | NVIDIA H200 NVL | UNKNOWN | 0 |
| nidepack | simloop | 6 | budget | True | 426786 | NVIDIA H200 NVL | UNKNOWN | 0 |
| rp1 | simloop | 6 | budget | True | 426786 | NVIDIA H200 NVL | UNKNOWN | 0 |
| depack | stitch | 6 | budget | True | 426786 | NVIDIA H200 NVL | UNKNOWN | 0 |
| new1 | stitch | 6 | budget | True | 426786 | NVIDIA H200 NVL | UNKNOWN | 0 |
| nidepack | stitch | 6 | budget | True | 426786 | NVIDIA H200 NVL | UNKNOWN | 0 |
| rp1 | stitch | 6 | budget | True | 426786 | NVIDIA H200 NVL | UNKNOWN | 0 |
