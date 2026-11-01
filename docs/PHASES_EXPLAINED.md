# The phases, explained

This document walks through every phase of the reSTITCHing work, from Phase 0 to Phase 3, plus the API study (Sets 4,
4b and 4c). Each phase gets the same six headings:
1. the question it asked;
2. the design;
3. the runs;
4. the results;
5. what changed in the paper;
6. the canonical evidence files.

Phases 2 and 3 carry most of the paper and are covered in full depth.

**Note (2026-10-30).** This document was written against paper v10 (`paper/overleaf/main.tex`, 15 pages, with a
supplement), and its page, figure, table and Supplementary Material numbers refer to that build, now archived (local,
`paper/archive/v10/`; in git history at `e77bf73`). The current paper is `paper/main.tex` (v11, 14 pages, no
supplement); its names for the conditions and studies are mapped at the top of `docs/reSTITCH.md`, and the former
supplement's tables are in `docs/reSTITCH.md`, Part 15. The results themselves are unchanged. For the full narrative, with every decision and its reason, read `docs/reSTITCH.md`. For
questions and answers, read `docs/reSTITCH_REVISITED_QA.md`. For cluster commands, read `docs/HPC_GUIDE.md`.

**Vocabulary used throughout.**
- **RTL:** register-transfer level, the hardware description a synthesis tool turns into gates.
- **Verilog:** the language the RTL is written in.
- **The loop:**
  1. a language model writes RTL;
  2. Icarus Verilog simulates it against a testbench;
  3. on failure, feedback goes back to the model, up to a fixed number of iterations.
- **Lint and synthesis:** Verilator (lint) and Yosys (synthesis) find structural defects that simulation cannot see.
- **The interpreter:** STITCH's deterministic rule set that turns their messages into short repair directives. It
  calls no model.
- **Conditions:**
  - `baseline`: simulation log only;
  - `raw_adv`: plus raw tool text;
  - `sem_adv`: plus the interpreter's directives on every iteration;
  - `sem_escalate`: directives only after two same-signature failures;
  - `sem_escalate_restart`: as `sem_escalate`, plus one blank-slate restart;
  - `baseline_gate` (Phase 3 control arm): simulation plus a bare "fails sign-off" alarm.
- **Runs:** N=3 replicates per (model, module, condition) cell, at temperature T=0.1 unless stated.

---

## Phase 0: does the conference result replicate?

**Question.** The conference paper (MLCAD '26) showed four outcome regimes, each with one module, one model and one
run: enabling, protective, harmful and irrelevant. Do its illustrations survive replication at N=3?

**Design.**
- Re-run the gated-input illustrations at N=3, T=0.1, under `baseline`, `raw_adv` and `sem_adv`.
- Build output-omission candidates (`adder_with_overflow`, `fsm_next_state_error`) to test the mirror-image defect.
- Build three larger candidates (`datapath_mux_alu`, its redesign `alu_with_enable`, `instr_decode_unit`) to test
  whether the mechanism scales.

**Runs.** Small hand-built modules on gemma3:4b and llama3.1, plus a pre-migration sweep whose aggregate is in
`phase0/evidence/combined_results.csv`.

**Results.**
- **Two illustrations replicate 3/3:** `decoder_3to8` and `mux4_oe`.
  - On gemma3:4b both controls fail all six iterations, and `sem_adv` passes in two (Table 2, page 4).
  - `raw_adv` tracks `baseline` exactly, so the effect is the interpretation, not the presence of the tools.
- **The input/output asymmetry.**
  - A forgotten gating input reliably occurs and is reachable through Verilator's `UNUSEDSIGNAL`.
  - A forgotten output does not occur: the model assigned every declared output unprompted on iteration 1, so the
    interpreter correctly had nothing to fire on.
  - Driving an output is a local obligation the model closes itself; reading an input is non-local.
- **What replication retired.** None of the three larger candidates replicated:
  - `datapath_mux_alu`: llama3.1 passed 2 of 3 with `semantic_fired`=0 in all three, which is sampling variance;
  - `instr_decode_unit`: gemma3:4b got the correct directive and still failed, falling into a syntax loop;
  - `alu_with_enable` became too easy after its redesign.
- The interpreter and runner were hardened along the way (simulator working directory, code-fence extraction).

**What changed in the paper.**
- Section 4 (page 3 to 4) reports the two replications, the asymmetry and the retirements at equal weight.
- The conference's four regimes became testable claims rather than single anecdotes.

**Evidence.**
- `phase0/evidence/phase0_illustration_hunt_findings.md`;
- `phase0/illustrations/proven/` (frozen) and `phase0/illustrations/retired/`;
- `phase0/README.md`.

---

## Phase 1: escalation and the in-house benchmark

**Question.** Firing the interpreter on every iteration can derail a run that was converging (the conference's
harmful regime). Can it be fired only when a run is stuck, and what does that save?

**Design.**
- **The escalation state machine** (`phase1/escalation_state.py`, unit-tested; Figure 3, page 5):
  - start in the baseline state;
  - after N=2 consecutive failures with the same normalised error signature (the first 5 lines of the log), switch
    permanently to the escalated state, which gives `sem_adv` feedback;
  - the restart variant: after M=3 further same-signature failures, one blank-slate prompt.
- **Budgets:** `baseline` and `sem_adv` 6 iterations; escalation 8.
- **The 255-run in-house benchmark:** 17 (module, model) cells x 5 conditions x N=3.
- **An RTLLM pilot and a compatibility screen** of the external benchmark.

**Results.**
- **Cost.** Escalation invokes Verilator and Yosys 35 to 45% less often than always-on interpretation and raw text,
  at a matching or better pass rate: 1.53 and 1.37 calls per run against 2.37 and 2.61 (Table 3, page 5).
- **The two cost axes diverge:** escalated runs execute extra iterations, so tokens can rise (5,151 against 4,883 per
  run) while tool calls fall. The paper scopes every efficiency claim to tool calls.
- **Benchmark-premise collapse.** Re-measured at N=3, 4 of 5 "real-test" cells and 2 of 3 "enabling" cells did not
  reproduce the behaviour their category was defined by. Benchmarks labelled from single runs encode noise.
- **RTLLM compatibility screen:** 44 of 50 designs are compatible with the Icarus flow (one exclusion is a defect in
  RTLLM's own reference).

**What changed in the paper.** Section 5 (Cost-Controlled Escalation, page 4 to 5) and Table 3.

**Evidence.**
- `phase1/PHASE1_FINDINGS.md`, `phase1/PHASE1_TASK3_ANALYSIS.md`, `phase1/RTLLM_PILOT_PREREG.md`;
- `phase1/escalation_state.py`, `phase1/tests/`.

---

## Phase 2: RTLLM at scale (in full depth)

### 2.1 The question

Do the interpreter's effects hold on an external benchmark the group did not build, at replicated scale, across model
sizes? And where exactly can an effect even be measured?

### 2.2 Harness hardening (before any confirmatory run)

Three silent defects in the shared runner were found and fixed, each verified against golden references (Section 6,
page 5; Supplementary Material S3):
- **A. No simulator working directory.** A testbench that loads a data file with `$readmemh` could never pass.
- **B. Unclosed code fence.** The opening marker stayed in the extracted code: 58 of 659 generated files (8.8%) were
  corrupted.
- **C. Pass string.** The check looked for `"PASS"`, while RTLLM testbenches print `"Your Design Passed"`. A re-scan
  found 20 of 64 completed runs (31%) misclassified as failures. Those runs then spent their remaining iterations
  "fixing" correct code.
  - **How it was found:** a near-trivial module, `counter_12`, scored 0/3.

**The structural fix.** Every confirmatory result routes pass detection through `detect_outcome(log, benchmark)`
(`src/interpreter/pass_detection.py`):
- it is backed by a per-benchmark registry with no default, so an unregistered benchmark fails at import;
- it was regression-verified against 64 manually adjudicated cells;
- a cluster gate requires 44/44 golden designs to pass.

### 2.3 The pool and the difficulty tiers

- **The pool.** 44 compatible designs, minus `edge_detect` and `square_wave`, whose testbenches pass outputs stuck at
  0 (weak oracles). That leaves 42 modules.
- **The tiers.** A module's tier is its **pooled** baseline pass count over all 15 Twin runs (five model-conditions,
  N=3), not a per-model maximum:
  - **ceiling:** 6 modules, 12 to 15 of 15 (80% or more);
  - **recoverable:** 17 modules, 3 to 11 of 15;
  - **floor:** 19 modules, 0 to 2 of 15 (under 20%).
- **Why tiers.** STITCH's effect can only show where baseline sometimes fails but can recover. Pooling the
  ceilings and floors flattens any signal.
- **How they are used.** Computed once (`phase2/twin_analysis_SET2/categorize.py`) and inherited by every later set.

### 2.4 The runs

| Set | Purpose | Models | Conditions | Modules | N / T | Runs | Errors |
|---|---|---|---|---|---|---|---|
| 2 (Twin) | model comparison, tiers | RTLCoder (native and shared prompt), deepseek-coder:6.7b, gemma3:4b, llama3.1 | baseline | 42 | 3 / 0.5 | 630 | 0 |
| 1 | STITCH on small models | gemma3:4b, llama3.1:8b, deepseek-coder:6.7b | 4 | 42 | 3 / 0.1 | 1,512 | 6 timeouts |
| 3 | STITCH on large models | qwen2.5-coder:14b and 32b, gemma3:27b | 4 | 17 | 3 / 0.1 | 612 | 2 timeouts |

All ran on the institutional GPU cluster with Ollama serving (`docs/HPC_GUIDE.md`).

**Why the temperatures differ.**
- **Twin, T=0.5:** it compares models, so it used one temperature matched across all five model-conditions.
- **Sets 1 and 3, T=0.1:** they compare conditions, at the conference setting.
- **Consequence:** the capability ladder that mixes them (Figure 5a) is ordinal across shades.

**Budgets.** `baseline` and `sem_adv` were capped at 6 iterations and escalation at 8. At an equal cap of 6 no
conclusion changes: one pass in each escalation condition moves (Supplementary Material S5).

### 2.5 Statistics

A (model, module) cell has three correlated replicates, so a general claim needs more than run-level counting:
- each contrast is the mean over cells of the within-cell difference in pass rate;
- its interval is a cell bootstrap: 10,000 resamples, percentile interval;
- its p-value is a two-sided sign-flip test over cells: 20,000 random sign patterns, seeded per label.

Rates carry Wilson intervals. The deficit figure uses Newcombe intervals for a difference of proportions. The code is
`phase3/runner/posthoc_checks.py` (section "phase2"), and the API study's copy (`phase2/frontier/stats_set4.py`)
reproduces all twelve published Set 1 and Set 3 values before any contrast is reported (Supplementary Material S9).

### 2.6 Results: the Twin (Set 2)

- **The question:** does fine-tuning help? RTLCoder-Deepseek-v1.1 is fine-tuned from the same weights as
  deepseek-coder:6.7b, so the pair isolates fine-tuning.
- **At the shared prompt,** on the 17 recoverable modules:
  - RTLCoder passes 21/51 against the base model's 32/51;
  - **0 module wins, 13 ties, 4 losses** (a tie is a difference of at most 1 in 3).
- **At RTLCoder's native prompt** it is a wash: 29/51; 5 wins, 6 ties, 6 losses.
- **The four losses fail at compilation every iteration,** for four different reasons:
  1. a submodule that is never defined;
  2. SystemVerilog-only syntax;
  3. parameter binding;
  4. a memorised folder name used as the module name.
- **Per-class exception:** RTLCoder (native) clears every recoverable signal-processing module (9/9) and the memory
  module (3/3).
- **Prompt format alone:** native wins 3 modules, shared 2, and 12 tie.
- **Reading:** a negative result on this external benchmark, with a per-class exception (Section 7, page 5;
  Supplementary Material S4, Figure S1).

### 2.7 Results: Set 1 (small models, Section 8.1, Figure 4, page 6)

- **Pooled over 42 modules,** the four conditions lie within 1.6 points (28.8, 27.2, 27.7 and 28.8%).
- **On the recoverable band, `sem_adv` is about four points below baseline** (47/153 against 54/153):
  - worse in 7 of 51 cells, better in 3;
  - cell CI -10.5 to +0.7, sign-flip p=0.199.
  - This is the direction of the conference's harmful regime, but it is not significant. It is also not separable
    from raw tool text, which Set 1 did not run.
- **`sem_escalate_restart` matches baseline:** 54/151 against 54/153; 0.0 points, CI -4.6 to +4.6.
- **Plain `sem_escalate` trails:** 47/150; -4.7, CI -10.7 to 0.0.
- **Ceilings and floors coincide** across conditions.
- **Tool calls, escalation against always-on, by tier:**
  - cut 75.1% on ceilings (4.02 to 1.00 per run);
  - cut 16.6% on the recoverable band;
  - cut 10.1% on floors.

### 2.8 Results: Set 3 (large models, Section 8.2, Figure 5, page 7)

- **No contrast differs from baseline:**
  - `sem_adv` -0.7 (CI -7.8 to +6.5);
  - `sem_escalate` +2.6;
  - `sem_escalate_restart` +2.0;
  - all p 0.40 or higher.
- **The nominal escalation lead is not a fired mechanism.** Of 153 `sem_escalate` runs:
  - 88 passed without escalating, and 65 escalated;
  - the 2 escalated runs that passed did so with `semantic_fired`=0.
- **Per model, the deficit is not monotonic in size:** gemma3:27b +7.8, qwen2.5-coder:32b -5.9; every interval
  crosses zero.
- **The tool-call cut grows:** 27.6% on the recoverable band (5.31 to 3.85 per run), because capable models get stuck
  less often.

### 2.9 The API study (Sets 4, 4b, 4c; Section 8.3 to 8.4, pages 7 to 8)

- **Question.** Do the patterns extend to commercial non-reasoning models? And is the floor tier beyond the models or
  beyond the tools?
- **Design.**
  - **Pre-registered** in `phase2/frontier/SET4_PREREG.md`, with five dated, hashed amendments.
  - **Models:**
    - `gpt-4.1-mini-2025-04-14`;
    - `gemini-2.5-flash` with thinking budget 0;
    - `claude-haiku-4-5-20251001`.
  - **Protocol:** the Set 3 protocol with only the model call replaced. T=0.1. Any reasoning token stops the provider.
  - **Toolchain:** a laptop toolchain matched to the cluster build (Yosys 0.69, Verilator 5.053, Icarus 14.0). It
    reproduces saved Set 3 verdicts: 140/140 pass/fail and 51/51 interpreter outputs.
- **Set 4 (recoverable band, 612 runs): a ceiling.**
  - Pooled pass rates are 99.3, 98.7, 98.0 and 98.0%.
  - No contrast is significant (every p=1.000).
  - Escalation rarely triggers, so its tool-call cut reaches 88.6% (2.29 to 0.26 per run).
  - The trend up the ladder: 16.6 to 27.6 to 88.6%.
- **Set 4b (floor, 599 valid runs).**
  - 16 of 19 floor modules leave the floor at baseline for at least one API model, so the floor belongs mostly to
    the 4B to 32B models.
  - `adder_pipe_64bit`, `alu` and `freq_divbyfrac` stay at the floor for every model that ran them.
  - On the remaining failures the interpreter fires in 55% (103/188) of failing tool-condition runs, but no pass is
    attributable to it.
  - Claude Haiku 4.5 is incomplete (143/228). The paper projects its 7 missing modules in two marked places only
    (`paper/V10_CHANGES.md`, section 6).
- **`freq_divbyfrac`:**
  - all three models fail it (0/36);
  - the reference's counter wraps every 14 half steps (two output periods per wrap), while the specification says the
    counter "cycles through 7 half clock steps";
  - so it is not a testbench defect: the specification's description of the counter does not match its reference
    design (our reading), and the models fail on period and duty cycle (`phase2/frontier/FREQ_DIVBYFRAC_AUDIT.md`).
- **Set 4c** (Gemini 2.5 Pro, reasoning) stopped on its pre-registered rule at run 1: 10,237 thinking tokens against
  a 2,048 budget. It has no results (Amendment 5).
- **Spend over all API work:** $13.70 (INR 1,552) (`phase2/frontier/evidence/spend_summary.txt`).

### 2.10 What changed in the paper

- **The harmful regime.** The conference called it a regime. It survives only as a non-significant four-point deficit
  on small models, not separable from raw tool text.
- **The escalation guarantee is narrowed.** Escalation equals baseline only on runs that converge before the trigger.
  Beyond it, only the restart variant matches baseline on small models.
- **The early Set 3 reading is withdrawn.** It said "escalation wins outright on large models"; the replicate trace
  above showed the wins were not interpreter-driven.
- **The floor** is re-read as mostly beyond small open models, not beyond the tools.
- **Sections:** these are Sections 6 to 8 and Figures 4 to 6.

### 2.11 Evidence

- **Reports:** `phase2/TWIN_RUN_ANALYSIS.md`, `phase2/SET1_ANALYSIS.md`, `phase2/SET3_ANALYSIS.md`.
- **Analysis directories and contrasts:** `phase2/set1_analysis/`, `phase2/set3_analysis/`;
  `phase3/evidence/phase3_run/POSTHOC_CHECKS.md` (cell bootstrap contrasts).
- **Harness:** `docs/archive/IMP_PHASE2_RUNNER_HARDENING_REPORT.md`.
- **API study:** `phase2/frontier/SET4_REPORT.md`, `phase2/frontier/evidence/` (snapshots of every analysis output),
  `phase2/frontier/FREQ_DIVBYFRAC_AUDIT.md`.

---

## Phase 3: a real MPSoC case study (in full depth)

### 3.1 The question

RTLLM scores a module by its testbench alone, but STITCH was built for defects that pass the testbench, break
synthesis, and multiply when a module is instantiated across a design. Does it help on real hardware that already
contains such defects? Is the improvement the detail of the feedback, or only the alarm that something failed?

### 3.2 The substrate

- **The design.** A RISC-V MPSoC developed within the group, independently of this study:
  - a five-stage RV32 core;
  - a network interface;
  - a virtual-channel wormhole mesh router, built as a 2x2 mesh (4 routers) and a 3x3 mesh (9 routers).
- **Source.** It comes from the `p20230031/RISC-V` repository. Only compile-level changes were made for the open-source
  flow (nested comments, duplicate declarations, implicit trailing ports), and each is listed in
  `phase3/designs/SANITISATION.md`.
- **Defects already present.**
  - The MPSoC top reports 63 latch inferences across 12 module definitions.
  - Synthesis then aborts on a one-bit register that tests `clr | reset` inside an asynchronous-reset block.
  - These defects are **simulation-silent**: the circuits simulate correctly on their intended inputs.
- **The latch defect at scale** (Figure 7a, page 9).
  - Each router instantiates two latching register definitions 20 times. They hold 36 latched bits in all: 32 in
    `register_32bit` and 4 in `register_4bit`.
  - That gives 36 x 20 x 4 = 2,880 latch cells in the 2x2 mesh and 6,480 in the 3x3 mesh.
  - Yosys prints one message per module definition, so the feedback is the same two messages at both sizes.
  - With the task leaves repaired, both meshes synthesise with 0 latch cells. The MPSoC top keeps 122 latch cells, in
    five modules outside the repair set.

### 3.3 Keeping the interpreter robust: the v3 layer

Running the production interpreter (v2) on the real logs exposed wrong or missing advice:
- an unused clock got the generic gating template, which builds a clock-gated latch;
- the asynchronous-reset abort and an expression truncation produced no directive.

The v3 layer (`src/interpreter/stitch_interpreter_v3.py`):
- imports v2 unchanged and reproduces it byte for byte wherever no new rule applies;
- adds rules only where a real log showed v2 wrong or silent: `MISSING_CLOCK` (a fusion of a Yosys latch and a
  Verilator unused clock), `ASYNC_RESET`, `WIDTH_EXPR` and `COMB_LOOP` (Table 1, page 3).

A live drift gate runs the interpreter on fresh tool output before any GPU time. It caught a latch-message format
change between Yosys 0.33 and 0.69.

### 3.4 The experiment

- **Eleven tasks** (Table 4, page 10): eight real defective leaves and three seeded modules for classes absent from
  the design.
  - Six are sim-silent: the defective input already passes its loop testbench.
  - Each task has `input.v`, `spec.md` (purely behavioural, because hints made it too easy), `tb.v` (the loop
    testbench), `tb_signoff.v` and `golden.v`.
- **Conditions.** Every condition shares one budget of 6 model calls, the same prompt and the same filtered raw tool
  text, and every candidate is fully evaluated.
  - `baseline` stops at the first simulation pass, as AutoChip does, so on a sim-silent task it stops at the input.
  - `raw_adv` adds raw tool text.
  - `sem_adv` (v2 or v3) adds directives.
  - `sem_esc_restart` (v3) starts like baseline behind a generic "fails synthesis sign-off" message, escalates to v3
    after two identical signatures, and restarts once.
  - `baseline_gate` (the control arm) gives simulation plus exactly that message, never escalates, and logs (never
    feeds back) what v3 would have said.
- **Models and runs.**
  - Six local models from 3B to 14B, N=3, T=0.1: 990 runs.
  - The final batch, pre-registered before any of its runs and frozen with the runner, interpreter and task files:
    the control arm (198 runs) and qwen2.5-coder:32b under all six conditions (198 runs). That makes 1,386 cluster
    runs in all.
  - Three API models (198 runs each) ran the same runner as descriptive ladder rows.
- **Two oracles.**
  - The loop testbench drives feedback and stopping.
  - A specification-complete sign-off testbench scores the returned RTL offline and never reaches the loop.
  - The sign-off testbench was added after a formal-equivalence audit found two testbench gaps (`mem_wb_mux`,
    `Address_select`). On the other nine tasks the two testbenches are identical.
  - Re-scoring the 990 runs is exact, because the loop never saw the new oracle. It is post hoc for them and
    pre-registered for the new arms.
- **The primary metric: sign-off clean.** The sign-off testbench passes, Yosys reports no latch or loop, and Verilator
  reports no hard structural warning.

### 3.5 Results (pages 10 to 13)

1. **Latches.** On the latch-bearing tasks, runs that end latch-free with a clean synthesis rise from 24% (35/144)
   under simulation-only repair to 88% (127/144) under v3 and escalation (Figure 1b).
   - Simulation-only repair signs off 63% of its runs as defective, including all 108 sim-silent runs (Figure 1a,
     Table 5).
2. **The detail, not the alarm** (pre-registered contrasts, Table 6).
   - **Escalation minus the alarm:** +19.7 points (CI +11.1 to +29.3, p<0.001).
   - **v3 minus the alarm:** +14.6 (CI +3.0 to +26.3, p=0.021).
   - **The alarm minus raw text:** -0.5. **The alarm minus baseline, on sim-visible tasks:** -1.1.
   - **Multiplicity:** as pre-registered, these are uncorrected. Under Holm only contrast 1 survives.
3. **Interpretation beats raw text, sooner and cheaper.**
   - v3 minus raw text: +14.1 (CI +3.5 to +24.7). v2, the out-of-sample estimate: +10.1.
   - v3 needs about 23% fewer calls and tokens.
4. **Escalation reaches 72% sign-off clean,** with 47.5% fewer tool rounds than always-on v3. On sim-visible tasks it
   beats simulation-only repair by +14.4.
5. **Leaves compose.** Simulation-only repair never restores top-level synthesis. v3 does in 16/18 groups in each
   design, and escalation in 18/18 in both meshes (Figure 7b).
6. **Up the ladder** (Table 7). At 32B and for the API models, any tool feedback repairs every sim-silent defect.
   Simulation-only repair still signs off all 18 sim-silent runs as defective for every model.
7. **The upgrade closes vocabulary gaps.** On the async-reset register, interpreter-credited wins rise from 3/18 to
   15/18.
8. **Oracle integrity.** 41 loop-clean `Address_select` repairs set `J_addr` to 0 where the specification defines
   `X + PC`. The production latch advice ("one unconditional assignment ... `<safe value>`") appears in every such run
   under v2, v3 and escalation. That is a count, not a causal claim.

### 3.6 What changed in the paper

- **Section 9 was rebuilt on the sign-off oracle** (paper v8). Every ordering and direction survived, and absolute
  rates fell:
  - escalation sign-off clean went from 80% as run to 72%;
  - escalation minus baseline on sim-visible tasks went from +23.3 to +14.4.
- **The control arm became the central result,** stated as "the detail, not the alarm".
- **The latch result** became the teaser (Figure 1) and Result 1's lead.

### 3.7 Evidence

- **Pre-registration and freeze:** `phase3/evidence/PREREG_FINAL.md` (SHA-256 `1b6eb915...cc63`),
  `phase3/evidence/FREEZE_FINAL.md`.
- **The reference for every interval:** `phase3/evidence/phase3_final/PHASE3_FINAL.md`, with `PAPER_NUMBERS.md` and
  `PLANNER_BRIEF.md` beside it.
- **The 990 runs:** `phase3/evidence/phase3_run/PHASE3_RESULTS.md` (as run), `POSTHOC_SIGNOFF.md`, `POSTHOC_CHECKS.md`.
- **The code:** `phase3/tasks/`, `phase3/runner/`, `phase3/designs/SANITISATION.md`.
- **Plain-language explainer:** `phase3/docs/PHASE3_EXPLAINED.md`.
- **API ladder rows:** `phase2/frontier/p3_api/P3_API_REPORT.md` and
  `phase2/frontier/evidence/p3_ladder_signoff_stdout.txt`.
