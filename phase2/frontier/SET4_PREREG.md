# Set 4 pre-registration: commercial non-reasoning API models on the Set 3 protocol

Written 2026-09-28, **before any paid API call**. The SHA-256 of this file is recorded in
the preparation report. Any later change needs a dated amendment section at the end, not an
edit above it.

## 1. Question

Does the Set 1 → Set 3 pattern (always-on interpretation `sem_adv` is harmful on small
models and fades with capability; escalation never shows the harm; tool cost falls with
escalation) extend to commercial API models above the 32B end of the ladder? Set 4 adds one
cost-efficient non-reasoning model per provider. It is the top rung of the paper's
capability ladder (Figure 5), measured with the identical protocol.

## 2. Design (identical to Set 3 except where §4 says otherwise)

| Item | Value |
|---|---|
| Modules | The 17 recoverable-band modules: `difficulty_tier == "recoverable"` in `phase2/twin_analysis_SET2/module_categories.json`, loaded by `set3_runner._load_module_pool()` unchanged. |
| Conditions | `baseline`, `sem_adv`, `sem_escalate`, `sem_escalate_restart` |
| Replicates | N = 3 |
| Runs per model | 17 × 4 × 3 = 204 |
| Engine | `phase2/set3_runner.py` → `stitch_runner_hpc.py` + `escalation_runner_hpc.py`, unmodified; only `call_llm` is rebound (the same mechanism Set 3 uses for Ollama) |
| System prompt, message construction, code extraction | the engine's, unchanged |
| Iteration caps | classic 6 (`MAX_RETRIES`), escalation 8 (`escalate_after=2`, `restart_after=3`, `signature_window=5`) |
| Pass detection | `detect_outcome(sim_log, benchmark="rtllm")` |
| Interpreter | production interpreter (`src/interpreter/stitch_interpreter.py`, unchanged) |
| Temperature | 0.1 (exception: Kimi, §4) |
| max_tokens | 25,088 = 2 × 12,501, the longest single completion in Set 3's saved candidates, rounded up to a multiple of 256 |

### Models (selected by the rule: most capable non-reasoning model per provider with projected 204-run cost ≤ INR 700 incl. 18% GST)

Prices are USD per 1M tokens (input / cached input / output), fetched 2026-09-28.

| Provider | Model ID | Price | Reasoning setting | Price source |
|---|---|---|---|---|
| OpenAI | `gpt-4.1-mini-2025-04-14` (pinned snapshot) | 0.40 / 0.10 / 1.60 | non-reasoning model; no reasoning parameter sent | developers.openai.com/api/docs/pricing |
| Anthropic | `claude-haiku-4-5-20251001` | 1.00 / 0.10 / 5.00 | no `thinking` field (extended thinking off) | platform.claude.com/docs/en/about-claude/pricing |
| Google | `gemini-2.5-flash` | 0.30 / 0.03 / 2.50 | `thinkingConfig.thinkingBudget = 0` | ai.google.dev/gemini-api/docs/pricing |
| Moonshot | `kimi-k2.6` (base URL `https://api.moonshot.ai/v1`) | 0.95 / 0.16 / 4.00 | `thinking: {"type": "disabled"}` | platform.kimi.ai/docs/pricing/chat |

Rejected by the rule (a priori Set-3-token projection at list price, INR 96/USD, incl. GST):
`gpt-4.1` (INR 866), `gpt-5-chat-latest` (INR 707, also a moving alias), `claude-sonnet-5`
(INR 932 before its ~30% larger tokenizer). Gemini 3.x Flash models cannot disable thinking
(3.5 Flash-Lite minimum is "minimal"); Kimi `k2.7-code` and `k3` always reason.

Every call is checked at run time: any reported reasoning tokens, or any
thinking/reasoning content in the response, stops the run (`ReasoningDetected`).

## 3. Budget and stopping rules

- Global hard cap USD 25, per-provider cap USD 7, enforced before every call using the
  worst case (input characters / 2 as a pessimistic token count × input price, plus
  max_tokens × output price). All smoke, pilot and full calls share one ledger per provider.
- At most 3 retries per call (429, 5xx, timeouts), then the run is recorded as errored and
  excluded, as in Set 3. A failed run is not re-run.
- Launch order: cheapest provider first (by the pilot projection). After each provider
  completes, compare actual spend with its projection. Continue only if actual ≤ 1.3 ×
  projected; otherwise stop and report.
- If the pilot projects over INR 3,000 in total, drop the most expensive model first.
  N, the conditions and the modules are never reduced.

## 4. Deviations from Set 3, decided now

1. **Kimi temperature 0.6.** With thinking disabled, `kimi-k2.6` accepts only
   temperature 0.6 (top_p fixed at 0.95); any other value is an error
   (platform.kimi.ai/docs/api/models-overview). Kimi runs at 0.6 and is flagged in
   every table and figure.
2. **Laptop WSL toolchain, not HPC oss-cad-suite.** Local: Icarus Verilog 12.0,
   Verilator 5.020, Yosys 0.33. Set 3 did not record its versions. Parity on 140 saved
   Set 3 candidates: pass/fail 140/140 identical. The interpreter class was identical in
   48/51 tool-run iterations. All 3 differences are MULTIDRIVEN directives that HPC's newer
   Verilator emitted and 5.020 does not reach, because it stops on earlier errors first.
   If a matching oss-cad-suite build is installed before the full run, that is recorded
   here as an amendment.
3. **Per-call retries instead of per-run retries.** Set 3 re-ran a whole run up to 3
   times on an exception. Set 4 retries each call up to 3 times and does not re-run the
   run, because re-running costs money. An exhausted call marks the run errored in both
   classic and escalation conditions (Set 3's classic path would have recorded it as a
   FAIL).
4. **max_tokens is set** (Set 3 used Ollama's default and sent none). 25,088 is twice the
   longest Set 3 completion. Truncations (`finish_reason` = length / max_tokens /
   MAX_TOKENS) are counted and reported.
5. **Token counts come from different tokenizers.** Set 3's counts are Ollama's
   `prompt_eval_count` / `eval_count` (exposed as `usage.prompt_tokens` /
   `completion_tokens`). All 309 multi-call Set 3 runs have non-decreasing prompt counts,
   so the full history was counted, as the APIs do. Counts are comparable in meaning but
   not in units: each provider tokenizes differently. Cross-set token comparisons are
   reported as ratios within a model (condition vs baseline), never as absolute
   differences between models.

## 5. Primary analysis (method identical to Set 3)

Unit: run = (module, model, condition, replicate). Cell = (module, model, condition), N = 3.
Errored runs are excluded and counted.

1. Recoverable-band pass rate per condition, pooled over the four API models and per
   model, with Wilson 95% intervals.
2. Each condition vs baseline, paired by (module, model) cell:
   - cell-level bootstrap of the difference in pass rate (10,000 resamples of cells, 95% CI);
   - two-sided sign-flip permutation p on the paired cell differences (exact if ≤ 2^16
     sign patterns, else 10,000 random flips).
   These are to be implemented exactly as the paper's Set 3 analysis defines them. This
   preparation could not read that implementation (`paper/`, `phase3/` were out of
   scope), so the definition must be confirmed against it before analysis.
3. Replicate trace, the project's mechanism gate: passes with and without
   `semantic_fired` per condition; escalation rate (share of escalation runs with
   `fired_escalate`); no win is attributed to the interpreter unless the winning
   replicates fired it.
4. Tool-invocation reduction sem_adv → sem_escalate on the recoverable band, reported next
   to Set 1 (16.6%) and Set 3 (27.6%).

## 6. Token, cost and latency analysis (new in Set 4)

- Tokens per run and per pass; INR per run and per pass, by condition and model (INR at the
  rate stated in the report, plus 18% GST).
- Token overhead of sem_adv vs baseline and of each escalation condition vs baseline.
- Latency per call and per run (provider-reported wall time of each request).
- Figure: INR per passing module by condition, per model.

## 7. Figure 5 update

Add the four API models' baseline bars (T = 0.1; Kimi marked 0.6) in one distinct colour
labelled "API, non-reasoning", ordered by baseline pass rate like the rest; relabel the
range "4B to API models".

## 8. Threats to validity

- **Contamination:** RTLLM has been public since 2024; API models may have seen it.
  This affects absolute pass rates, not the within-model condition contrasts.
- **Model drift:** API models change behind stable names. The exact returned model
  version string, request/response IDs, system_fingerprint (where given) and UTC time of
  every call are logged; OpenAI is pinned to a dated snapshot.
- **Temperature semantics differ between providers**, and Kimi is fixed at 0.6.
- **Toolchain:** laptop WSL vs HPC oss-cad-suite (§4.2, parity numbers above).
- **Tokenizers differ** (§4.5).
- **Prompt caching** is provider-side and automatic for OpenAI, Gemini 2.5 and Kimi. It
  lowers cost, not behaviour. Cached tokens are logged and priced at the cached rate.

---

## Amendment 1 (2026-09-28 18:25 UTC, before any paid call)

Original sections above are unchanged; the original file's SHA-256 was
`ED262B53E4BDA06C9994128846EC8C43DC1BD324396637B1E167044882AA9A4B`. Where this amendment
conflicts with them, this amendment wins.

**A1. max_tokens = 8192 for every model** (replaces §2's 25,088). `finish_reason` /
`stop_reason` is logged on every call. Truncated outputs (finish_reason `length`,
`max_tokens` or `MAX_TOKENS`) are counted per model and condition, scored exactly as the
harness scores them (no special handling), and the count is disclosed.

**A2. Kimi temperature.** `kimi-k2.6` (thinking disabled) runs at T=0.6, the only value it
accepts with thinking off; the other three run at T=0.1. The Kimi row is marked in every
table and figure, as Twin's T=0.5 is.

**A3. Toolchain.** Set 3 recorded no tool versions: its saved Yosys output keeps only
filtered lines (no version banner) and its Verilator output drops the `?v=` doc URLs, and
no manifest exists. Target = the HPC's current oss-cad-suite as printed on 2026-09-28:
Verilator 5.053 devel rev v5.052-103-g1aa87913c, Yosys 0.69+71 (git sha1 150c32b03),
Icarus Verilog 14.0 (devel) s20260301-451-gc9ed76463. At most 45 minutes are spent
installing the matching dated oss-cad-suite release into a separate WSL directory, selected
for Set 4 only by the env var `STITCH_SET4_OSSCAD` (prepended to PATH by the Set 4 scripts;
the system tools used by Phase 3 are not touched). If installed, the Step 2 parity check is
re-run on the same 140 candidates: pass/fail must be 140/140 and the interpreter count out
of 51 is reported (target 51/51), and that toolchain is used for everything after. If not
achievable, the local tools (Yosys 0.33, Verilator 5.020, Icarus 12.0) are used and the 48/51
MULTIDRIVEN difference is a disclosed threat. Tool versions go in every run's manifest.

**A4. Statistics.** The cell-level bootstrap and sign-flip functions are copied from
`phase3/runner/posthoc_checks.py` into `phase2/frontier/stats_set4.py` (no import from
phase3/). Before use, the copy must reproduce the Set 3 lines of
`phase3/evidence/phase3_run/POSTHOC_CHECKS.md` exactly: sem_adv − baseline −0.7
[−7.8, +6.5] p=1.000; sem_escalate − baseline +2.6 [−1.3, +7.2] p=0.404;
sem_escalate_restart − baseline +2.0 [−2.6, +7.2] p=0.596. If it does not, the analysis
step stops and is reported (the runs may still proceed). This replaces §5.2's own
definition.

**A5. Errored runs.** After each provider's full run, one resume pass over its errored
runs (budget permitting). Anything still errored is excluded and counted.

**A6. Money.** Every INR figure uses INR 96/USD plus 18% GST.

**A7. Caps (replace §3's).** Global cap USD 18 across all providers and all phases. Each
provider's full-run cap = 1.5 × its pilot projection (the higher of the two methods), never
above OpenAI 3.0 / Gemini 3.0 / Kimi 6.0 / Anthropic 6.5 USD, applied to the provider's
cumulative ledger (smoke + pilot + full). Smoke-test stop rules per provider: reasoning
tokens > 0, auth failure, wrong model ID, wrong pass detection or `semantic_fired`
logging, ledger not updating, or `scan_secrets` finding any key. A stopped provider does not
stop the others.

---

## Amendment 2 (2026-09-29 13:00 UTC, after Set 4 ran; before any Set 4b call)

Previous SHA-256 (after Amendment 1): `52DC7DEFD3D8434D1ACBCE88324B13BA631B6B0E866A2C60DB2BA8A5361520F9`.

**A8. Kimi dropped (deviation from §2).** `kimi-k2.6` was stopped at smoke test (i)
(`reasoning_tokens=1`, empty reasoning content). It is dropped from Set 4 by decision, not
because of that flag: Gemini 2.5 Flash and Claude Haiku 4.5 already pass 204/204, and a
third ceiling model at a different temperature (0.6) would add no information. Set 4 is
therefore three models. Its one smoke call ($0.0004) stays in the ledger.

**A9. Statistics source.** `signflip_p` and only the helpers it calls may be read from
`phase3/runner/analyze_phase3.py` and copied into `stats_set4.py`. `verify()` must reproduce
all six published bootstrap CIs and p-values (Set 1 and Set 3) before any contrast is
reported.

## Set 4b: floor tier (pre-registered 2026-09-29 13:00 UTC, before any Set 4b call)

**Why.** The paper states that floor modules sit outside the interpreter's reach but has
never tested it with models that can solve them; this run tests that and screens for oracle
(testbench) failures.

**Modules.** The 19 `difficulty_tier == "floor"` modules of
`phase2/twin_analysis_SET2/module_categories.json`: LIFObuffer, accu, adder_16bit,
adder_32bit, adder_bcd, adder_pipe_64bit, alu, barrel_shifter, counter_12, div_16bit,
float_multi, freq_divbyfrac, fsm, multi_pipe_4bit, multi_pipe_8bit, parallel2serial,
pulse_detect, serial2parallel, traffic_light.

**Protocol.** Identical to Set 4 except the module set: 4 conditions, N=3 (228 runs per
model), production interpreter, caps 6/8, `detect_outcome(benchmark="rtllm")`, T=0.1,
max_tokens 8192, the 0.69 toolchain via `STITCH_SET4_OSSCAD`, one retry pass over errored
runs. Separate ledger directory (`ledgers_4b/`) so the Set 4b cap is measured on Set 4b spend
only.

**Models.** `gpt-4.1-mini-2025-04-14`, `gemini-2.5-flash` (thinkingBudget 0);
`claude-haiku-4-5-20251001` only under the money rule below.

**Pilot.** Per model, 2 floor modules × 4 conditions × N=1: the lowest and the highest Twin
pooled pass rate among floor modules, ties broken by Set 1 pooled pass rate, then
alphabetically: lowest `LIFObuffer` (Twin 0/15, Set 1 0/35), highest `adder_16bit`
(Twin 2/15, Set 1 12/36). Projection per model for 228 runs: the higher of the two Set 4
methods (pilot USD per run per condition; Set 3 mean calls per run per condition × pilot
USD per call), plus the 90% bootstrap upper bound.

**Money.** Set 4b hard cap USD 14 in total, including the pilot (global cap on `ledgers_4b/`).
Haiku is included only if the three-model projected total is ≤ USD 12; otherwise
GPT-4.1 mini + Gemini if their total is ≤ USD 12; otherwise GPT-4.1 mini only. Per-provider
cap = 1.5 × its projection, never raised. Selected providers run in parallel; a provider that
hits its cap stops cleanly and reports its progress.

**Stop rules (per provider).** Reasoning tokens > 0; authentication failure or a returned
model ID that does not match the requested one; ledger not updating; `scan_secrets` > 0.
No change of model, temperature or protocol mid-run.

**Questions.**
- Q1. Which floor modules do API models pass at baseline (floor → recoverable/ceiling at this
  tier)? Reported per module and model: baseline passes out of 3.
- Q2. On floor failures, does the interpreter fire (`semantic_fired`), and do any passes
  occur only with it firing? Reported: runs with `semantic_fired` > 0 per condition; passes
  with vs without it firing.
- Q3. On modules still failing, do conditions differ? (model, module)-cell bootstrap CI and
  sign-flip p vs baseline, as in Set 3, restricted to cells whose baseline pass rate is < 1.
- Q4. Modules failed in every run, by every model, under every condition = oracle-audit
  candidates.

**Oracle audit (no paid calls).** For every Q4 module: does the RTLLM reference design pass
its testbench under this harness and toolchain; the dominant failure across models from the
sim logs; whether it looks like a spec/testbench mismatch. Every result is marked
"candidate, needs manual confirmation".

---

## Amendment 3: Gemini completion (2026-10-12 13:21 UTC, before any call it governs)

Previous SHA-256 (after Amendment 2 and the Set 4b section):
`8B376DF348F3A4732898A1706573F1DAED0778DF861E2F9824321D603FB52C7C`. Gemini only: no OpenAI,
Anthropic or Moonshot call is made under this amendment.

**Scope.**
- Smoke: one minimal `gemini-2.5-flash` call, then one full run (`counter_12`, `sem_adv`, N=1,
  tag `smoke_gc`) and a resume check on it.
- Part A: finish Set 4b for `gemini-2.5-flash`. The 8 missing runs are all `alu` (`sem_adv` rep2–3,
  `sem_escalate` rep1–3, `sem_escalate_restart` rep1–3). Resumed from
  `phase2/results/set4_api/floor_full/gemini/master_log.json`; a completed run is never re-run.
- Part B: `gemini-2.5-flash` as a third API ladder row on the Phase 3 MPSoC tasks, on the
  protocol of `p3_api/P3_API_PREREG.md` unchanged (11 tasks × 6 conditions × N=3 = 198 runs,
  same runner path, prompts and toolchain). Gates G0–G5 are re-run first on a `/tmp` copy
  (`p3_gate_local.sh`) and must all pass. Sign-off scoring is offline, with `apply_signoff()` from
  `phase3/runner/analyze_phase3.py` (read-only import) against `tb_signoff.v`, as for the other
  two API rows; the sign-off cache is a copy outside `phase3/`. Nothing under `phase3/` is written.

**Protocol unchanged.** T=0.1; max_tokens 8192; `thinkingConfig.thinkingBudget = 0`; Set 4b caps 6/8;
production interpreter; `detect_outcome(benchmark="rtllm")`; 4 conditions (Set 4b) and 6
conditions with a 6-call budget (Phase 3); oss-cad-suite 20260917 via `STITCH_SET4_OSSCAD`
(Yosys 0.69+71 150c32b03, Verilator 5.053, Icarus 14.0); prices as §2.

**Money.** All calls of this amendment go to one ledger,
`phase2/results/p3_api/ledgers/gemini_ledger.jsonl` (tags `smoke_gc`, `floor_full`, `p3_full`).
Runner caps: Part A USD 1.5 (applied to that ledger, so the smoke counts against it); Part B
USD 1.5 of its own spend; combined USD 3.0. Part B's runner cap on the cumulative ledger is
min(3.0, ledger spend when Part B starts + 1.5). Caps are never raised. Gemini total across all
batches must stay ≤ INR 1,500 incl. GST (USD × 96 × 1.18); before this amendment it is
USD 4.0506 (INR 458.9).

**Stop rules (stricter than before; backends.py error paths only).** The provider stops at once
on: HTTP 400 or 402 (billing, credit, invalid request), added to 401/403; HTTP 429 that persists
after the 3 retries; a truncated completion (finish_reason `MAX_TOKENS`), which replaces A1's
count-and-score for this run; reasoning tokens > 0; a returned `modelVersion` that does not start
with `gemini-2.5-flash`; a ledger not updating; `scan_secrets` > 0; a toolchain mismatch; a
gate failure; or a cap. A cap stops before the call that could cross it, so the run in progress
is not recorded (it is re-run in full on resume). A returned `modelVersion` that starts with
`gemini-2.5-flash` but differs from the value in the Set 4 / 4b ledgers (`gemini-2.5-flash`)
is recorded as a deviation and the run continues. No change of model, temperature, protocol or cap
mid-run.

**Wrapper-only changes (no protocol change).** `p3_api_runner.py` accepts `--api gemini`;
`backends.py` takes a `STITCH_GEMINI_BASE` override used only by the offline mock parity, which
now also covers Gemini; `p3_api_analysis.py` includes Gemini.

**Analysis.** `analysis_set4b.py` re-run on the completed data (Q1–Q4, per-model coverage, Q4
strict test on every module run by all three models; Haiku stays at 143/228, disclosed as pending);
`oracle_audit.py` re-run on alu and freq_divbyfrac; Phase 3 ladder row reported in the format of
Table 12 of `STITCH_EXT_v8.tex` (sign-off clean of 33, sim-silent of 18 / sim-visible of 15,
tokens per run), plus `p3_api_analysis.py`'s as-run tables. Descriptive at N=3, never pooled.

---

## Amendment 4: Set 4c (2026-10-12 14:38 UTC, before any call it governs)

Previous SHA-256 (after Amendment 3):
`62C1C0BEFE0487C639161A724FFC56E89A806E45AB644501A0BBFB2ADBE3216A`. Gemini only.

**Deviation from Set 4's design: a REASONING model.** Set 4 and 4b use non-reasoning models only.
Set 4c runs one Gemini Pro model with thinking on. It is descriptive only and is never pooled with
Set 4 or 4b.

**Questions.**
- Q5: does the model pass adder_pipe_64bit, alu or freq_divbyfrac at baseline?
- Q6: does sem_escalate_restart differ from baseline on these modules? Is any pass attributable to
  the interpreter, meaning semantic_fired with a directive delivered on an iteration before the pass?
- Q7: does freq_divbyfrac fail, and if so at check 3 ("clk_div=1, expected 0") like every Set 4b model?

**Model choice (free, 2026-10-12).** Pro models served on this key (list-models endpoint):
`gemini-3.1-pro-preview` (version 3.1-pro-preview-01-2026; the flagship, preview), `gemini-pro-latest`
(a moving alias) and `gemini-2.5-pro` (GA, version 2.5, no dated variant listed).

Prices from https://ai.google.dev/gemini-api/docs/pricing (page last updated 2026-10-09, fetched
2026-10-12), Standard tier, prompts ≤ 200k tokens, USD per 1M tokens (input / output including thinking):
3.1 Pro Preview 2.00 / 12.00; 2.5 Pro 1.25 / 10.00, cached input 0.125.

Worst case (`set4c.py project`): 18 runs × 8 calls, each call at the maxima observed for these modules
in Set 4b. Over 732 calls those maxima are 23,473 input tokens and 4,023 answer tokens, plus the full
2,048 thinking tokens.
- `gemini-3.1-pro-preview`: $17.25. That is over $7.5, so under the brief's rule the model is
  **`gemini-2.5-pro`**.
- `gemini-2.5-pro`: $12.97 ($0.0901 per call, $0.7204 per run). Also over $7.5. The run goes ahead, and
  the run order puts the most important runs first; the cap stops it.

**Settings.**
- `thinkingConfig.thinkingBudget = 2048`. For 2.5 Pro the docs give a range of 128–32,768; thinking
  cannot be turned off; and the budget is a "soft limit" whose actual use "might vary slightly".
- `includeThoughts` is not sent, so no thought text is returned or stored.
- `maxOutputTokens = 10240` (2,048 + 8,192). The docs state that the output limit includes thought
  tokens, so with thinking at or under its budget, an answer of up to 8,192 tokens cannot be truncated.
- T=0.1, which 2.5 Pro accepts; it carries no Gemini 3 temperature caveat. If the API rejects it, the
  value used is recorded.
- Ledger: thinking tokens are recorded (`reasoning_tokens`), included in `output_tokens` and billed at
  the output price.

**Scope.** Modules adder_pipe_64bit, alu and freq_divbyfrac. Conditions baseline and
sem_escalate_restart. N=3, so 18 runs. Everything else as in Set 4b: caps 6/8, the production
interpreter, `detect_outcome(benchmark="rtllm")`, oss-cad-suite 20260917, and the same runner, prompts and
code extraction. Tag `set4c`; results in `phase2/results/set4_api/set4c/gemini/`.

**Run order.**
1. Baseline rep1 on adder_pipe_64bit, alu and freq_divbyfrac.
2. Baseline reps 2–3, in the same module order. After step (1), the observed cost per run and an
   all-fail upper bound for the rest are computed (`set4c.py after1`) and reported; the run then continues
   automatically.
3. sem_escalate_restart reps 1–3, module by module: freq_divbyfrac first, then adder_pipe_64bit, then alu.

**Smoke test.**
- One minimal call: authentication, model ID, thinking tokens > 0 and ≤ 2,048, no truncation, and the
  ledger records the thinking tokens as billed output.
- One full run: counter_12, baseline, N=1, tag `set4c_smoke`. Check `detect_outcome`, the ledger and resume.
- `scan_secrets`.

**Money.** All calls, smoke included, go to `phase2/results/set4_api/ledgers_4c/gemini_ledger.jsonl`.
- Hard cap USD 7.5 (INR 850 incl. GST), applied as both the provider cap and the global cap on that
  directory. It is never raised.
- The runner does not start a run if its worst case ($0.7204) could cross the cap, so it stops between
  runs.
- The per-call worst-case check remains as the last guard.

**Stop rules.** The provider stops at once on:
- HTTP 400, 401, 402 or 403, or a 429 that persists after the retries;
- thinking tokens above 2,048 on any call;
- returned thought text;
- a truncation (finish_reason `MAX_TOKENS`);
- a returned modelVersion that does not start with `gemini-2.5-pro`;
- a ledger not updating;
- `scan_secrets` > 0;
- a toolchain mismatch.

Thinking tokens > 0 are expected in this run and are not a stop condition. No change of model, budget,
temperature, protocol or cap mid-run.

**Analysis** (`set4c.py analyze`, `set4c.py trace`).
- Per module × condition: passes, iterations to pass, semantic_fired runs, "directive before pass" (the
  interpreter fired on an iteration before the passing one), escalations. Tokens (input / answer / thinking)
  and INR per run and per pass.
- Q7: the first failing check on each run's final iteration, against the Set 4b models. Shifted-trace
  comparison: `clk_div` of every final candidate is sampled every 5 ns and compared with the testbench's
  expected sequence at shifts of −2 to +2 half-steps, together with its high/low run lengths.
- Verdict for freq_divbyfrac: "solvable: not an oracle defect" if any Set 4c run passes it; otherwise
  "consistent with an oracle/spec defect". Either way it is marked "needs manual confirmation".
- `phase2/frontier/FREQ_DIVBYFRAC_AUDIT.md` holds the spec text and the testbench check lines
  (file:line) for human review.

---

## Amendment 5: Set 4c closed (2026-10-12 16:12 UTC)

Previous SHA-256 (after Amendment 4):
`EDF26C7070366C565D7F93CA0D0AA45BC366843E2CCE0468AC9BA776DE1ABA02`.

- **Stopped by a pre-registered stop rule.** On run 1, iteration 2 (adder_pipe_64bit, baseline,
  rep1), `gemini-2.5-pro` returned 10,237 thinking tokens against a 2,048 budget. That used the whole
  10,240-token output limit, so the answer was cut off (finish `MAX_TOKENS`). Both "thinking above the
  budget" and "truncation" are Amendment 4 stop rules.
- **Closed by decision.** No setting is changed and the run is not resumed. There are no further paid
  calls of any kind under this pre-registration.
- **0 of 18 runs completed, so no Set 4c results are reported.** Q5 and Q6 are unanswered. Set 4c
  spend: USD 0.1723 (INR 19.5): smoke 0.0321, run 0.1401.
- **Q7 is answered instead by a free analysis** of the 36 existing Set 4b freq_divbyfrac runs
  (`set4c.py trace`). It is a shifted-trace comparison of every final candidate against the original
  testbench's checks, and is reported in the oracle-audit part of `SET4_REPORT.md`.
- The Set 4c code stays in the repository. `set4c_launch.sh` refuses to run without `--reopen`.
