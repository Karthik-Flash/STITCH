# Integrity of the HPC results (pipeline/integrity.py)

Archive extracted into the study folder: sha256 `7cb51ed4bd3ca5fbf5215190f2752f3df72cca5d2e2185dedf91d064c5976aa3` (excludes *.vvp/*.vcd; value as recorded at download, the archive itself is not in the repository).

No gen log in hpc_logs/ (the job log stayed on the cluster): each one-shot record is attributed to the study's only run manifest. The manifest's git_commit is `UNKNOWN`: preflight.py looked for DEPLOYED_COMMIT.txt in the study sub-folder instead of the study root (fixed after this job). The deployed commit, 0fa68c9, was checked on the cluster (DEPLOYED_COMMIT.txt, reported by the user).

## Summary

- one-shot records: 1 of 1; arm runs with metrics.json: 2 of 2
- problems: 0 (nothing missing, errored or mismatched)

| part | job | GPU | deployed commit | count |
|---|---|---|---|---|
| one-shot | 426786 | NVIDIA H200 NVL | UNKNOWN | 1 |
| simloop | 426786 | NVIDIA H200 NVL | UNKNOWN | 1 |
| stitch | 426786 | NVIDIA H200 NVL | UNKNOWN | 1 |

Jobs (run manifests):

- 426786: gpunode7.sharanga.local, NVIDIA H200 NVL, commit UNKNOWN, GEN_TASKS all, threads {'SLURM_CPUS_PER_TASK': '4', 'LLAMA_ARG_THREADS': '4', 'LLAMA_ARG_THREADS_BATCH': '4', 'options.num_thread (p3_bridge)': 4}

Iteration testbench copies (runs/arms/results/**/iter*/tb*.v, git-ignored): 14 byte-identical to tasks/<m>/, 0 differ.

## One-shot records

| module | status | output sha256 = record | tokens out | done_reason | job | GPU | commit |
|---|---|---|---|---|---|---|---|
| top_3x3_router | ok | True | 14933 | stop | 426786 | NVIDIA H200 NVL | UNKNOWN |

## Arm runs

| module | arm | LLM calls | stop | final = outputs/<arm> | job | GPU | commit | earlier failed attempts |
|---|---|---|---|---|---|---|---|---|
| top_3x3_router | simloop | 6 | budget | True | 426786 | NVIDIA H200 NVL | UNKNOWN | 0 |
| top_3x3_router | stitch | 6 | budget | True | 426786 | NVIDIA H200 NVL | UNKNOWN | 0 |
