# STITCH — Handoff (Phase 1 complete, Phase 2 mid-flight)

Supersedes the previous version of this file (Phase 0→1 handoff, now
resolved — see git history if you need that archaeology; the short
version is folded into "Origin" at the bottom). Written 2026-08-24 for
a fresh chat picking this up.

## Orientation — read this paragraph first

Phase 0 proved the interpreter mechanism works on 2 illustrations.
Phase 1 built and benchmarked the `sem_escalate` conditional-escalation
architecture (255-run benchmark + an RTLLM pilot) and is **done,
committed, and consolidated** — the result is a cost/robustness story,
not a pass-rate win, and that's the honest, final Phase 1 verdict (see
Key Findings below). Phase 2 is building and validating an HPC-based
RTLCoder-vs-twin comparison. **Everything run so far in Phase 2 — the
4-check smoke test, the 64/75-run twin pilot — is validation/pilot
scale on a single HPC job, not the real study.** The real study is a
full HPC run that hasn't launched yet, and there's one concrete bug
blocking it (see "What's blocking the next launch").

---

## Key locations

**Canonical harness (Windows/WSL, still the source of truth for fixes):**
- `src/runner/stitch_runner.py` — the shared runner. Two real bugs found
  and fixed here in Phase 1 (see Findings) — commit `a047d78`.
- `src/interpreter/stitch_interpreter.py` — the semantic interpreter,
  platform-agnostic (no subprocess/WSL code), imported unchanged by both
  the Windows runner and the Phase 2 HPC port.

**Phase 1** (`phase1/`, all committed):
- `PHASE1_FINDINGS.md` — **read this first for Phase 1.** The
  consolidated, paper-citable record: cost axis as the real result, the
  4-cell mixed pass-rate sample, no RTLLM pass-rate advantage, the
  N=1→N=3 replication collapse, both harness bugs, and the
  capability-conditional hypothesis flagged for Phase 2 to test.
- `PHASE1_TASK3_ANALYSIS.md` — the 255-run escalation benchmark detail.
- `PILOT_INSIGHTS.md` / `PILOT_SUMMARY.md` — the RTLLM v2.1 pilot
  (laptop-scale) and its bug-fix validation re-run.
- `RUNBOOK.md` — one entry per `phase1/*.py`, purpose/command/requires/
  produced/runtime for all 11 scripts.
- `escalation_state.py`/`escalation_runner.py` — the `sem_escalate`/
  `sem_escalate_restart` state machine and runner.

**Phase 2** (`phase2/`, partially committed — see Git State below):
- `HPC_RTLCODER_COMMANDS.md` — **the HPC runbook, read this before
  touching HPC.** Copy-paste command reference: scratch layout, deploy,
  the two correctness-check greps, sbatch scripts, monitoring, collection.
- `rtlcoder_adapter.py` — RTLCoder-Deepseek-v1.1 adapter (HuggingFace
  `transformers`, not Ollama). **Validated end-to-end on real HPC
  hardware (H100)** via the 4-point smoke test — committed, working.
- `smoke_test.py` — the 4-check validator (model loads / generates /
  extracts a clean module / compiles). Already passed for real on HPC.
- `stitch_runner_hpc.py` — Linux-native port of `stitch_runner.py` (WSL
  has no equivalent on HPC compute nodes). Mechanically diffed against
  the Windows original to confirm both bug fixes are present and
  nothing else drifted. **Not yet committed.**
- `twin_run_runner.py` — the RTLCoder-vs-twin orchestrator. Bridges
  RTLCoder into the shared `call_llm()` dispatch via monkeypatch,
  handles native/shared prompt construction, matches T=0.5 across all
  5 model-conditions. **Not yet committed — and currently has the
  known pass-detection bug, see below.**
- `TWIN_RUN_PREREG.md` — the design doc for the twin comparison,
  written before any run (75 runs: RTLCoder native+shared, 3 Ollama
  models shared-only, matched T=0.5). **Not yet committed.**
- `TWIN_PILOT_ANALYSIS.md` — analysis of the first real HPC attempt
  (64/75 runs, cut short by an 8h wall-clock timeout). **Staged, not
  committed.** This is where the pass-detection bug was found.
- `graphs/` — 3 figures for the paper from the pilot analysis, all
  watermarked PILOT/NOT CONFIRMATORY. **Staged, not committed.**
- `twin_run.slurm` / `pull_ollama_models.slurm` — real sbatch scripts
  (not markdown heredocs — that distinction mattered, see Findings).
  **Not yet committed.**
- `results/` — gitignored. Raw run output (`twin_run_pilot/` has the
  64-run pilot's `master_log.json` + a `corrected_pass.json` built
  during analysis).

**HPC cluster** (BITS Hyderabad, `soumyaj@hpc.bits-hyderabad.ac.in`):
- Everything lives under `/scratch/soumyaj/RTLCoderHPC/` (40GB home
  quota, same reasoning as the existing `/scratch/soumyaj/AutoChipHPC/`
  project this borrows conventions from).
- `oss-cad-suite` (iverilog/verilator/yosys) at
  `/scratch/soumyaj/oss-cad-suite/bin`.
- `ollama` binary at `/scratch/soumyaj/AutoChipHPC/bin/ollama` (reused,
  not reinstalled) — not on PATH by default, must be exported.
- GPU nodes: `gpunode4` (A100 80GB, `gpu_a100_8`), `gpunode6` (H100
  80GB HBM3, `gpu_h100_4` — the one actually used and validated so
  far). `gpunode5` shows "draining," avoid it.
- Full command sequences (deploy, verify, pull models, submit, monitor,
  collect) are in `phase2/HPC_RTLCODER_COMMANDS.md` §0-10 — don't
  reconstruct these from memory, they're written out literally there.

---

## What's blocking the next launch — fix this first

**`stitch_runner_hpc.py`'s pass-detection checks for the case-sensitive
substring `"PASS"`/`"ALL TESTS PASSED"`. RTLLM's testbenches print
`"Your Design Passed"` — which contains neither.** Found during
`TWIN_PILOT_ANALYSIS.md`'s write-up: 20 of the pilot's 64 completed
runs (31%) actually passed and were recorded as failures, including
literally every `counter_12` cell. `phase1/rtllm_pilot_runner.py`
already has the fix for this exact problem
(`_rtlcoder_aware_run_iverilog_sim`, checking for the real RTLLM pass
string) — it was never carried into `twin_run_runner.py`. This also
corrupted run trajectories, not just labels: a cell that passed on
iteration 1 was told `"SIMULATION FAILED"` and burned its remaining
iterations "fixing" already-correct code.

**Before the next HPC launch**: patch `twin_run_runner.py` with the
same RTLLM-aware wrapper (mirror the pattern in
`phase1/rtllm_pilot_runner.py`), verify it the same way every other fix
in this project has been verified (golden-reference before/after, not
just "looks right"), then re-run — either a scoped re-pilot on just the
mismeasured cells, or roll straight into the real run, is an open
decision for whoever picks this up, not resolved here.

---

## Key findings so far (both phases)

**Phase 1 (`phase1/PHASE1_FINDINGS.md`, full detail):**
1. **The real result is cost, not pass rate**: `sem_escalate` invokes
   heavyweight tools ~35-45% less often than unconditional `sem_adv`,
   matching or beating its pass rate. Token cost moves the other way on
   some cells — report both axes, they diverge.
2. Pass-rate result on cells that actually replicate at N=3: **mixed**,
   2 wins (1 real, 1 structural) + 1 cost-no-change + 1 loss, reported
   at equal weight, not a clean win.
3. **No RTLLM pass-rate advantage for `sem_escalate`** — `alu` is
   genuinely hard post-fix (baseline 0), `calendar`'s apparent trend
   was ceiling+early-luck, not rescue, once decomposed.
4. **N=1→N=3 replication collapse**: most of Task 3's pre-registered
   17-cell run set didn't reproduce its N=1-based label at N=3. Always
   confirm at N≥3 before trusting a cell selection.
5. **Two harness bugs** found and fixed in `stitch_runner.py`: (a) `vvp`
   never had a working directory, breaking any file-I/O testbench
   ($readmemh); (b) an unclosed ` ```verilog ` fence corrupted
   extraction — confirmed to have corrupted 8.8% of Task 3's own
   generated files (re-audit against the fix is a named, still-open gap).
6. **Capability-conditional hypothesis, not a finding**: one trajectory
   (`llama3.1` on `alu`) suggests escalation may help models stuck in a
   narrow repeating failure mode more than models that already
   self-explore. Flagged for Phase 2's model ladder to actually test,
   not cited as evidence anywhere.

**Phase 2 (this session, chronological — each was a real bug caught
before it could contaminate results, not hypothetical):**
1. RTLCoder's postprocessing needed 3 rounds of fixes before the smoke
   test went green: (a) the prompt wasn't sliced out of the generation
   in token space, (b) the module-header stub the model *completes but
   doesn't re-emit* wasn't rejoined, (c) the extraction cut at the
   wrong `endmodule` when the model's overrun was separator-delimited
   rather than the documented `endmodulemodule`-glommed pattern. All
   three verified against real captured HPC output, not synthetic
   guesses, before being called fixed.
2. The smoke test itself had a bug: check (c) validated
   `postprocess(generate_raw(prompt))` — a path the real harness never
   takes — instead of the real `generate(prompt)` function. Fixed to
   validate the actual call path.
3. `twin_run.slurm` was designed and shown in chat but never actually
   deployed as a file — heredoc-in-markdown is fragile; real `.slurm`
   files that get `scp`'d directly are the fix, applied for both
   `twin_run.slurm` and `pull_ollama_models.slurm`.
4. Ollama-on-HPC needed real infrastructure the laptop never needed:
   the binary isn't on PATH, nothing listens by default, `OLLAMA_HOST`
   must be read by the client (not hardcoded), and models must be
   confirmed present before a job burns wall-clock assuming they are.
5. **The pass-detection bug above** — the most consequential one found
   so far, since it silently invalidated the entire first pilot's raw
   numbers.

---

## Next big phase — the real HPC run hasn't happened yet

Everything on HPC to date is validation: the smoke test (1 module,
proof-of-life) and the twin pilot (64/75 runs, cut short by an 8h
`--time` limit, and now known to need the pass-detection fix before its
numbers mean anything). **Treat every number produced so far as
pre-real-run.** The next phase, in order:

1. Fix and verify the pass-detection bug in `twin_run_runner.py`.
2. Decide, with the user: re-pilot just the affected/missing cells, or
   go straight to a full launch. `calendar` (11 cells never ran) is the
   one module where the only real RTLCoder-vs-twin differentiation
   might live — it's the open question the pilot couldn't answer.
3. The actual twin comparison run, complete this time (75 runs as
   pre-registered, or a revised scope if the user changes it).
4. Beyond the twin comparison: `PHASE1_FINDINGS.md`'s HPC readiness
   table has the full planned scope — 44-compatible-module pool,
   pass@5, model ladder 4B→32B, the RTLCoder-vs-deepseek-coder twin
   (this is that axis), frontier APIs deferred to a later phase. STITCH
   condition scope for the full run is explicitly listed there as
   "to decide together, not defaulted."

---

## Standing conventions (violate these and expect a correction)

- **RTLLM is never copied into this repo** — read live from
  `D:\Projects\RTLLM` locally / `$RTLLM_ROOT` on HPC, always.
- **N≥3 before any cell result is trusted** — N=1 is resampling noise,
  proven twice now (phase0, then Task 3's whole premise).
- **No `Co-Authored-By: Claude` trailer** in any commit message in this
  repo (project rule, stated explicitly 2026-08-22).
- **Stage and propose; the user runs `git commit`/`git push`** unless
  they explicitly say otherwise for that specific batch (they have,
  twice, for specific committed batches — it's not a standing override).
- **Verify every "fix" against real captured data before calling it
  fixed** — golden references, real HPC logs, real sim output. Every
  bug in the "Key findings" list above was caught this way, and every
  fix was verified this way before being trusted.
- **Never frame an RTLCoder/Phase-2 model-comparison result as a STITCH
  validation** — the twin run's `condition` is fixed at `baseline`
  throughout; the interpreter never runs in that design.

---

## Immediate next action

Fix `twin_run_runner.py`'s pass-detection (mirror
`phase1/rtllm_pilot_runner.py`'s `_rtlcoder_aware_run_iverilog_sim`),
verify it against a golden-reference RTLLM module before trusting it,
then take the re-pilot-vs-full-launch decision to the user. Everything
needed to do this — the runbook, the bug's exact location and fix
pattern, the HPC command sequences — is linked above; don't re-derive
it from scratch.

## Origin (condensed, for archaeology)

Phase 0 proved the interpreter on 2 illustrations
(`phase0/illustrations/proven/`), 50 interpreter tests,
`plans/research_plan_v4.md` is the plan of record. Phase 1's benchmark
decision (RTLLM v2, not VerilogEval-Human — SystemVerilog
incompatibility) and model set are resolved facts now, not open
questions — see `PHASE1_FINDINGS.md` rather than re-litigating. The
original Phase 0→1 version of this file is in git history if the
detailed reasoning is ever needed.
