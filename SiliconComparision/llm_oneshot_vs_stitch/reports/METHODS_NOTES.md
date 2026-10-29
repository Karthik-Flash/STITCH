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

## Whole-router bonus prompt: not attempted

The whole router (top_module with all its descendants) as one one-shot prompt was not attempted. The prompt alone is
32,290 of 32,768 tokens (`pipeline/budget.py`), and a golden-sized answer is about 74,627 tokens. `GEN_FULL_ROUTER`
defaults to 0, so one-shot produces 34 files.
