# Generation speed and wall time (pipeline/speed.py)

Generation rate = output tokens / generation time (llama-server print_timing `eval time`, or Ollama eval_duration); model load and prompt evaluation excluded. Wall rate = output tokens / wall seconds of the one-shot call (gen log), prompt evaluation included.

| source | GPU | llama-server threads | calls | generation tok/s (pooled) | median per call | prompt tok/s |
|---|---|---|---|---|---|---|
| Phase 3 32b (job 369810) serve log | NVIDIA H200 NVL | n_threads = 64 (n_threads_batch = 64) / 64 | 244 | 4.90 | 4.87 | 256 |
| job 422841 serve log | NVIDIA H200 NVL | n_threads = 64 (n_threads_batch = 64) / 64 | 17 | 5.32 | 5.29 | 484 |
| job 423542 serve log | NVIDIA A100-SXM4-80GB | n_threads = 64 (n_threads_batch = 64) / 64 | 22 | 4.37 | 4.40 | 619 |
| job 422841 gen log, one-shot wall rate (first call excluded) | NVIDIA H200 NVL | - | 2 | 5.32 (wall) | 5.52 (wall) | - |
| job 423542 gen log, one-shot wall rate (first call excluded) | NVIDIA A100-SXM4-80GB | - | 21 | 4.33 (wall) | 4.33 (wall) | - |
| oneshot_records (HPC record.json) | - | - | 25 | 4.43 | 4.41 | - |

## Remaining work (inputs to --time)

- one-shot: 9 modules left (final_op_data, op_core, op_data_path, op_link1, op_link2, op_link3, op_link4, top_2x2_router, top_module); output tokens 61421 (HPC records where finished, otherwise golden-size estimates from PREDEPLOY_BUDGET.md), input 25659
- arms: 62 of 68 runs left (smoke finished 6); LLM calls per run from the smoke log: [1, 1, 0, 0, 6, 6] -> mean 2.33 (worst case 6)
- per arm call: output = the module's one-shot output size, input = arms prompt (PREDEPLOY_BUDGET.md); summed over the remaining runs at 1 call each: output 157520, input 235496 tokens
- tool time per call 5.7 s (Phase 3: metrics wall per call minus serve-log LLM time per call); prompt rate 256 tok/s (slowest measured); model load 100 s per process, 2 processes

| generation tok/s | one-shot h | arms h (expected) | arms h (worst, 6 calls) | total h expected | x 1.5 |
|---|---|---|---|---|---|
| 4.37 (measured, job 423542, before the fix) | 3.95 | 24.21 | 62.27 | 28.22 | 42.33 |
| 8 | 2.17 | 13.59 | 34.94 | 15.82 | 23.73 |
| 15 | 1.18 | 7.63 | 19.63 | 8.87 | 13.30 |
| 30 | 0.61 | 4.23 | 10.88 | 4.90 | 7.34 |

Formula per row: one-shot = out/tg + in/pp + calls x tool; arms = (out/tg + in/pp + runs x tool) x calls per run; total = one-shot + arms + 2 x load; x 1.5 margin.
--time is set for the slowest speed the job accepts (8 tok/s; below it the first call exits 3): --time=24:00:00. A run that ends early is resumed by resubmitting.
