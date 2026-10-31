# Pre-deploy budget (mesh3x3; pipeline/budget.py --tokens-only)

NEW modules only (reports/reuse.json); REUSED modules keep their 2x2 runs. num_ctx 32768 as in 2x2. Whole-router bonus off.

## Prompt tokens (estimate)

Estimate. Tokenizer: Qwen2.5 BPE (pre-tokenizer qwen2, n_vocab 152064), counted as Ollama prompt_eval_count with local model `qwen2.5-coder:latest` (same tokenizer family as qwen2.5-coder:32b); chat template and the Phase 3 system prompt included. Generation budget: num_predict is not sent, so output shares num_ctx = 32768 with the prompt; `golden out` (tokens of the golden module in a ```verilog block) stands in for the answer size. `arms prompt` = Phase 3 user_prompt(spec, golden as current RTL, no feedback), a lower bound for every feedback iteration.

| module | one-shot prompt | golden out | one-shot total | arms prompt | arms total | over num_ctx | over Phase 3 num_ctx 8192 |
|---|---|---|---|---|---|---|---|
| top_3x3_router | 1583 | 9679 | 11262 | 11240 | 20919 | - | one-shot total, arms total |

Single-module prompts above num_ctx - expected output (prompt + golden-size answer > num_ctx): none
