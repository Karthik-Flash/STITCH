# Run history (pipeline/run_history.py)

From hpc_logs/ (gen_<job>.log, ollama_serve_<job>.log). Times are the node's local clock (not comparable across nodes); a job without JOB DONE ended after its last stamp (no end time). tok/s = generation rate from the serve log (prompt evaluation and model load excluded).

| job | node | GPU | llama-server threads | calls | tok/s pooled | tok/s range per call | first / last `==` stamp | time between stamps | JOB DONE |
|---|---|---|---|---|---|---|---|---|---|
| 422841 | gpunode7.sharanga.local | NVIDIA H200 NVL | n_threads = 64 (n_threads_batch = 64) / 64 | 17 | 5.32 | 5.1-6.1 (median 5.3) | 08:32:12 / 09:41:52 IST | 1:09:40 | yes |
| 423542 | gpunode4.hpc.bits-hyderabad.ac.in | NVIDIA A100-SXM4-80GB | n_threads = 64 (n_threads_batch = 64) / 64 | 22 | 4.37 | 3.8-5.0 (median 4.4) | 12:38:06 / 12:41:25 IST | 0:03:19 | no |
| 424063 | gpunode5.hpc.bits-hyderabad.ac.in | NVIDIA H100 80GB HBM3 | n_threads = 4 (n_threads_batch = 4) / 64 | 248 | 64.91 | 48.4-74.0 (median 67.9) | 09:09:13 / 13:30:51 EDT | 4:21:38 | yes |
