# Wall time for STUDIES="mesh3x3 ni" (pipeline/walltime.py)

Generation 67.9 tok/s (2x2 job 424063, median per call, reports/RUN_HISTORY.md); prompt 1919 tok/s (job 424063 serve log); Phase 3 tool time per call 5.7 s; model load 100 s per process, 4 processes. Worst case: 6 LLM calls in each of the 2 arm runs per module. eval = measured p3_eval of the golden in its task (tool time per call is the larger of eval and the Phase 3 mean); signoff = one tb_signoff.v simulation (3 per module in summarize.py).

| study | module | one-shot in / out tokens | arms in tokens | eval s | signoff s | one-shot h | arms h (worst) | total h |
|---|---|---|---|---|---|---|---|---|
| mesh3x3 | top_3x3_router | 1583 / 9679 | 11240 | 7.5 | 67.9 | 0.04 | 0.52 | 0.62 |
| ni | depack | 862 / 367 | 1238 | 0.2 | 0.3 | 0.00 | 0.04 | 0.04 |
| ni | new1 | 852 / 207 | 1041 | 0.2 | 0.5 | 0.00 | 0.03 | 0.03 |
| ni | nidepack | 716 / 190 | 887 | 0.2 | 0.4 | 0.00 | 0.03 | 0.03 |
| ni | rp1 | 1091 / 527 | 1627 | 0.2 | 0.4 | 0.00 | 0.05 | 0.05 |

Total (worst case, loads included): 0.89 h; x 1.5 = 1.34 h; --time=2:00:00.
A run that ends early is resumed by resubmitting the same command.
