# Run history (pipeline/run_history.py)

The job log and serve log stayed on the cluster (not in the results archive), so the rates come from Ollama's own counters of every LLM call of this study (eval_count / eval_duration: generation only, prompt evaluation and model load excluded). mesh3x3 and ni ran in the same job.

| job | node | GPU | llama-server threads | calls (this study) | tok/s pooled | tok/s range per call | job end |
|---|---|---|---|---|---|---|---|
| 426786 | gpunode7 | NVIDIA H200 NVL | 4 | 52 | 66.07 | 59.0-68.6 (median 66.5) | exit 0, elapsed 01:08:57 (sacct, reported by the user) |
