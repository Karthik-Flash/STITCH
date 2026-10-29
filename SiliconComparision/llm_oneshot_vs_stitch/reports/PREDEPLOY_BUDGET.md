# Pre-deploy budget (pipeline/budget.py)

## Ollama options

| field | phase3 production | runner via run_arms | oneshot_gen |
|---|---|---|---|
| client_http_timeout_s | 900 | 900 | 900 |
| model | qwen2.5-coder:32b | qwen2.5-coder:32b | qwen2.5-coder:32b |
| options.num_ctx | 8192 | 32768 | 32768 |
| options.temperature | 0.1 | 0.1 | 0.1 |
| stream | False | False | False |
| options.num_predict | not sent (Ollama/model default) | not sent (Ollama/model default) | not sent (Ollama/model default) |
| options.seed | not sent (Ollama/model default) | not sent (Ollama/model default) | not sent (Ollama/model default) |
| options.top_p | not sent (Ollama/model default) | not sent (Ollama/model default) | not sent (Ollama/model default) |
| options.top_k | not sent (Ollama/model default) | not sent (Ollama/model default) | not sent (Ollama/model default) |
| options.repeat_penalty | not sent (Ollama/model default) | not sent (Ollama/model default) | not sent (Ollama/model default) |

job argv: phase3_run.slurm -> runner --model qwen2.5-coder:32b --host http://x --reps 3 --temperature 0.1 --max-iters 6 --out $OUT; gen_job.slurm -> run_arms --model qwen2.5-coder:32b --host http://x --max-iters 6 --reps 1; oneshot_gen --model qwen2.5-coder:32b --host http://x --temperature 0.1
runner via run_arms == oneshot_gen: True

## Prompt tokens (estimate)

Estimate. Tokenizer: Qwen2.5 BPE (pre-tokenizer qwen2, n_vocab 152064), counted as Ollama prompt_eval_count with local model `qwen2.5-coder:latest` (same tokenizer family as qwen2.5-coder:32b); chat template and the Phase 3 system prompt included. Generation budget: num_predict is not sent, so output shares num_ctx = 32768 with the prompt; `golden out` (tokens of the golden module in a ```verilog block) stands in for the answer size. `arms prompt` = Phase 3 user_prompt(spec, golden as current RTL, no feedback), a lower bound for every feedback iteration.

| module | one-shot prompt | golden out | one-shot total | arms prompt | arms total | over num_ctx |
|---|---|---|---|---|---|---|
| dff_synch_reset | 462 | 56 | 518 | 525 | 581 | - |
| dff_synch_set | 462 | 53 | 515 | 522 | 575 | - |
| dff_asynch_clr | 450 | 71 | 521 | 528 | 599 | - |
| irs | 952 | 369 | 1321 | 1304 | 1673 | - |
| register_32bit | 551 | 109 | 660 | 531 | 640 | - |
| asynch_comparator | 650 | 1325 | 1975 | 1982 | 3307 | - |
| jk_ff | 521 | 381 | 902 | 911 | 1292 | - |
| gray_mod6 | 623 | 436 | 1059 | 1040 | 1476 | - |
| memory | 579 | 276 | 855 | 865 | 1141 | - |
| router_fifo | 845 | 368 | 1213 | 1195 | 1563 | - |
| routing_algo_mesh | 593 | 704 | 1297 | 1305 | 2009 | - |
| ip_chnl | 1395 | 804 | 2199 | 2179 | 2983 | - |
| ip_link | 1446 | 2458 | 3904 | 3886 | 6344 | - |
| mux | 505 | 288 | 793 | 803 | 1091 | - |
| register_1bit | 508 | 111 | 619 | 527 | 638 | - |
| register_4bit | 517 | 101 | 618 | 514 | 615 | - |
| allot_vc | 1277 | 2395 | 3672 | 3653 | 6048 | - |
| demux_16 | 497 | 612 | 1109 | 1115 | 1727 | - |
| encoder | 527 | 305 | 832 | 842 | 1147 | - |
| falling_edge_pulse_generator | 575 | 166 | 741 | 720 | 886 | - |
| priority_encoder | 579 | 219 | 798 | 807 | 1026 | - |
| rr_arbiter | 768 | 1202 | 1970 | 1950 | 3152 | - |
| round_robin_req | 1492 | 3877 | 5369 | 5349 | 9226 | - |
| dff_synch_clr | 451 | 67 | 518 | 525 | 592 | - |
| rr_comb_new | 1260 | 1003 | 2263 | 2244 | 3247 | - |
| op_core | 3051 | 6220 | 9271 | 9253 | 15473 | - |
| final_op_data | 558 | 694 | 1252 | 1260 | 1954 | - |
| op_data_path | 1296 | 3237 | 4533 | 4514 | 7751 | - |
| op_link1 | 3203 | 6240 | 9443 | 9424 | 15664 | - |
| op_link2 | 3022 | 6091 | 9113 | 9094 | 15185 | - |
| op_link3 | 3022 | 6105 | 9127 | 9108 | 15213 | - |
| op_link4 | 3022 | 6085 | 9107 | 9088 | 15173 | - |
| top_module | 7106 | 22364 | 29470 | 29452 | 51816 | arms total |
| top_2x2_router | 1379 | 4385 | 5764 | 5742 | 10127 | - |
| top_module_full | 32290 | 74627 | 106917 | - | - | one-shot total |

Single-module prompts above num_ctx - expected output (prompt + golden-size answer > num_ctx): top_module: arms total

## Wall time

Phase 3 qwen2.5-coder:32b (job 369810, H200 NVL):
- recorded model digest(s) in metrics.json: ['b92d6a0bd47ee79114298de0177bf920c05a706d12633950b3936778492bef41']; preflight.PHASE3_DIGEST matches: True
- serve log (ollama_serve_369810.log): 244 /api/chat calls (HTTP 200), LLM time only: mean 53.5 s, median 38.3 s, p95 159.0 s, max 183.0 s
- metrics.json: 198 runs, 244 LLM calls, 14456 s wall (LLM + tool evaluation): 59.2 s per call
- per-call wall time used = max of the two means = 59.2 s
- 59.2 s x 443 calls (35 one-shot + 68 x 6) x 1.5 = 39368 s = 10.94 h -> --time=11:00:00
