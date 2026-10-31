# Pre-deploy budget (ni; pipeline/budget.py --tokens-only)

NEW modules only (reports/reuse.json); REUSED modules keep their 2x2 runs. num_ctx 32768 as in 2x2. Whole-router bonus off.

## Prompt tokens (estimate)

Estimate. Tokenizer: Qwen2.5 BPE (pre-tokenizer qwen2, n_vocab 152064), counted as Ollama prompt_eval_count with local model `qwen2.5-coder:latest` (same tokenizer family as qwen2.5-coder:32b); chat template and the Phase 3 system prompt included. Generation budget: num_predict is not sent, so output shares num_ctx = 32768 with the prompt; `golden out` (tokens of the golden module in a ```verilog block) stands in for the answer size. `arms prompt` = Phase 3 user_prompt(spec, golden as current RTL, no feedback), a lower bound for every feedback iteration.

| module | one-shot prompt | golden out | one-shot total | arms prompt | arms total | over num_ctx | over Phase 3 num_ctx 8192 |
|---|---|---|---|---|---|---|---|
| rp1 | 1091 | 527 | 1618 | 1627 | 2154 | - | - |
| new1 | 852 | 207 | 1059 | 1041 | 1248 | - | - |
| depack | 862 | 367 | 1229 | 1238 | 1605 | - | - |
| nidepack | 716 | 190 | 906 | 887 | 1077 | - | - |

Single-module prompts above num_ctx - expected output (prompt + golden-size answer > num_ctx): none
