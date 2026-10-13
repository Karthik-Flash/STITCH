# reSTITCH: the complete record of the journal extension

**What this is.** The whole story of the reSTITCHing work in one place: from the conference paper (STITCH, MLCAD '26)
to the final journal draft, `paper/overleaf/main.tex` (v10). It covers:
- the motivation, every phase, and every decision with its reason;
- what replication retired, and what was corrected, with the before and after numbers;
- what it cost, and what we learned.

It assumes no prior familiarity with the project. Read it top to bottom.

**Companion documents.**
- `docs/PHASES_EXPLAINED.md`: each phase in a fixed format (question, design, runs, results, paper changes,
  evidence).
- `docs/reSTITCH_REVISITED_QA.md`: questions and answers, in paper order.
- `docs/HPC_GUIDE.md`: the cluster procedure.
- `REPO_INDEX.md`: where every file lives and how to regenerate every number.

Every number here appears in the paper or in an evidence file named next to it.

---

## Part 0. The problem and the vocabulary

Hardware is described in code. **RTL** (register-transfer level) is a description of what a circuit does at each clock
tick, written in a hardware description language such as **Verilog**. A synthesis tool turns RTL into gates.

Large language models can write Verilog from an English specification, but they make mistakes. The standard remedy is
a **repair loop**:
1. ask the model for RTL;
2. simulate it against a **testbench** (a program that drives inputs and checks outputs);
3. if it fails, feed the failure back and ask again, up to a fixed number of iterations.

**AutoChip** established that such a loop works.

A simulator, however, only sees what the testbench drives. Some defects simulate correctly and still break the real
design:
- **inferred latches**: accidental memory, created when a combinational block leaves a signal unassigned on some
  path;
- **multi-driven nets**: two pieces of logic driving one wire;
- **resets a synthesis tool cannot map.**

They are caught by two other kinds of tool:
- **lint**, here Verilator, which reads the code for suspicious patterns;
- **synthesis**, here Yosys, which builds the gates and reports latches, loops and unmappable constructs.

**STITCH** (the conference paper) adds Verilator and Yosys to the loop. It also places a deterministic
**interpreter** between the tools and the model: a fixed rule set that turns a raw message into a short, specific
repair **directive**. For example, "a declared input is never read; gate the output on it". The interpreter calls no
model, so it adds no inference cost.

**Conditions** (what is fed back after a failure):

| Condition | Feedback |
|---|---|
| `baseline` | simulation log only (the AutoChip loop) |
| `raw_adv` | plus the raw Verilator and Yosys text |
| `sem_adv` | plus the interpreter's directives, on every iteration (the conference design) |
| `sem_escalate` | baseline until the run is stuck, then `sem_adv` feedback for the rest of the run |
| `sem_escalate_restart` | as `sem_escalate`, plus one blank-slate restart if it stays stuck |
| `baseline_gate` | Phase 3 control arm: simulation plus a bare "fails synthesis sign-off" alarm |

In Phase 3 the interpreted conditions come in two versions: v2 (production) and v3 (an additive layer). Escalation
there is `sem_esc_restart` (v3).

---

## Part 1. Why an extension was needed

The conference paper described four **outcome regimes** of the interpreter:
- **enabling:** a weak model succeeds only with the directive;
- **protective:** interpretation shields a model from confusing raw text;
- **harmful:** firing the interpreter derails a run that was converging;
- **irrelevant:** a failure no tool can see.

Each was shown by **one module, one model, one run (N=1)**.

**The N=1 problem.** Language models sample. Even at a low temperature (T=0.1), the same prompt can pass on one run
and fail on the next. One run cannot separate a real mechanism from luck. The conference paper's own limitations said
so.

**The discipline adopted for the whole extension**, never broken: no interpreter claim without N of at least 3
replicates, and without a check that the interpreter actually fired in the runs credited to it. That check is the
per-run flag `semantic_fired`. A run can pass without the interpreter ever speaking. Crediting such a pass to the
interpreter would be wrong.

**Why N=3 and not more.**
- At N=3, a unanimous 3/3 or 0/3 differs meaningfully from a split.
- Cost grows linearly with N.
- The study ran thousands of runs.

The price is that several per-model effects stay undecided. The paper says so (Threats to Validity, page 13).

---

## Part 2. Phase 0: what replicated, and what replication retired

**Two illustrations replicate 3/3** (Table 2, page 4). In `decoder_3to8` and `mux4_oe`, gemma3:4b omits a declared
gating input on iteration 1.
- Verilator fires `UNUSEDSIGNAL`, and the directive names the port.
- The model passes in two iterations, where `baseline` and `raw_adv` fail all six.
- `raw_adv` tracks `baseline` exactly. That control is what isolates the effect to interpretation rather than to the
  mere presence of the tools.

**The input/output reachability asymmetry.** We built the mirror-image defect, a forgotten output, in
`adder_with_overflow` and `fsm_next_state_error`. It never occurred: gemma3:4b assigned every declared output
unprompted on iteration 1, so the interpreter correctly had nothing to fire on.
- **Why:** an unassigned output looks visibly unfinished, a local gap the model closes as it writes. An unread input
  looks complete: the code compiles and nothing dangles, and noticing the omission requires reasoning about the whole
  module.
- **The rule this gives:** reachability is a joint property of the tool and of the generator's failure distribution,
  and it must be measured per defect class.

**What replication retired.** Three larger candidates were built to show the mechanism at scale. None survived:
- `datapath_mux_alu`: llama3.1 passed `sem_adv` in 2 of 3 replicates, with `semantic_fired`=0 in all three. At N=1
  this would have been an interpreter win; it was sampling variance.
- `instr_decode_unit`: gemma3:4b received the correct directive and still failed, falling into a syntax loop the
  interpreter has no vocabulary for. Reaching a defect is not the same as repairing it.
- `alu_with_enable`: too easy after its redesign.

**Decision.** Report the retirements at equal weight with the replications. A boundary defines a mechanism as sharply
as a win.

Evidence: `phase0/evidence/phase0_illustration_hunt_findings.md`, `phase0/illustrations/`.

---

## Part 3. Phase 1: escalation

**The problem.** Always-on interpretation (`sem_adv`) intervenes even when nothing is wrong yet, which is the
conference's harmful regime.

**The design** (`phase1/escalation_state.py`, unit-tested; Figure 3, page 5):
1. Start in the baseline state.
2. On each failure, compute a normalised error signature from the first 5 lines of the log.
3. After N=2 consecutive failures with the same signature, the run is "demonstrably stuck". Switch permanently to the
   escalated state from the next iteration, which feeds back the tool text and the directives.
4. Restart variant only: after M=3 further same-signature failures, issue one blank-slate prompt that discards the
   current RTL, and stay escalated.

**Budgets.** On RTLLM, `baseline` and `sem_adv` were capped at 6 iterations and escalation at 8. The extra headroom
let an escalated run use its directives after the two probe failures. The paper discloses the equal-cap check: at a cap
of 6 no Set 1 or Set 3 conclusion changes; one pass in each escalation condition moves (Supplementary Material S5). In
Phase 3 every condition shared one budget of 6 model calls.

**The guarantee, and its correction.**
- **First stated:** "escalation's worst case is bounded below by baseline", as a structural guarantee.
- **What is true:** until the trigger, an escalation run receives exactly the prompts and feedback a baseline run
  receives. So **on runs that converge before the trigger, escalation is the baseline policy.** Beyond the trigger it
  diverges, and nothing guarantees it does as well as baseline from there.
- **What the data then show:** on the Set 1 recoverable band the restart variant matches baseline (0.0 points, CI
  -4.6 to +4.6), while plain escalation trails like always-on interpretation (-4.7, CI -10.7 to 0.0).
- **The correction:** v9 rewrote every place the guarantee appeared (`paper/archive/V9_CHANGES.md`, section F).

**Cost on the 255-run in-house benchmark** (17 cells x 5 conditions x N=3; Table 3, page 5):
- Verilator and Yosys calls per run: `baseline` 0.00, `raw_adv` 2.61, `sem_adv` 2.37, `sem_escalate` 1.53,
  `sem_escalate_restart` 1.37. That is 35 to 45% fewer.
- **The token axis moves the other way:** `sem_escalate` used 5,151 tokens per run against `sem_adv`'s 4,883,
  because escalated runs execute extra iterations.
- **Decision:** every efficiency claim is scoped to tool calls, and the token column stays visible.

**The benchmark-premise collapse.** The in-house benchmark's categories came from single runs. Re-measured at N=3, 4 of
its 5 "real-test" cells and 2 of its 3 "enabling" cells did not reproduce the behaviour they were defined by.
Single-run benchmark labels can encode noise as structure.

Evidence: `phase1/PHASE1_FINDINGS.md`, `phase1/PHASE1_TASK3_ANALYSIS.md`.

---

## Part 4. Three silent harness defects

All three were found in the shared runner. Each was verified before and after against golden references (Section 6,
page 5; Supplementary Material S3).

- **A. No working directory for the simulator.** Testbenches that load data with `$readmemh` could never find their
  file, whatever the logic. Fix: run the simulator in the iteration's directory.
- **B. Unclosed code fences.** When a model left a markdown fence open, the opening marker stayed in the extracted
  code: 58 of 659 generated files (8.8%) were corrupted.
- **C. The pass string.** The harness looked for `"PASS"`, while RTLLM testbenches print `"Your Design Passed"`.
  - **How it was found:** a near-trivial module, `counter_12`, scored 0/3.
  - **The damage:** a re-scan found 20 of 64 completed runs (31%) misclassified as failures. Worse, their trajectories
    were corrupted: a run that passed on iteration 1 was told it failed and spent its remaining iterations "fixing"
    correct code.

**The structural fix.** All three were the same fragility: an assumption about a benchmark's output format, buried
in shared code, producing plausible wrong numbers. So instead of patching one more string, every pass or fail decision
now goes through one function, `detect_outcome(log, benchmark)` (`src/interpreter/pass_detection.py`):
- it is backed by a per-benchmark registry;
- the benchmark argument has no default, so an unregistered benchmark fails at import, not silently;
- it was regression-verified against 64 manually adjudicated cells;
- a cluster gate requires 44/44 golden designs to pass.

**Why it matters beyond this project.** A 31% silent misclassification rate is large enough to invert a published
comparison.

---

## Part 5. The RTLLM study design

**Why an external benchmark.** Reviewers ask whether results hold on a benchmark you did not build. RTLLM v2.1 has 50
designs from another group.

**The pool.**
- A compatibility screen kept 44 of 50 designs. One exclusion is a defect in RTLLM's own reference.
- `edge_detect` and `square_wave` were dropped because their testbenches pass outputs stuck at 0. Such a weak oracle
  would reward a model that does nothing.
- That leaves **42 modules**.

**Difficulty tiers, the organising idea.** Think of testing whether a tutor helps students. On trivial questions
everyone passes; on impossible ones everyone fails. The tutor's effect is only visible on medium questions.
- **How a tier is set:** by each module's **maximum** baseline pass rate across the five Twin model-conditions:
  - **ceiling:** 6 modules, 80% or more;
  - **recoverable:** 17 modules, 20 to 80%;
  - **floor:** 19 modules, under 20%.
- **How they are used:** computed once and reused by every later set.
- **Why it matters:** pooled over all 42 modules, the four Set 1 conditions lie within 1.6 points, and any signal
  vanishes.

**Is defining tiers from the Twin circular?** No, for three reasons:
- the tiers use only `baseline` runs, never a STITCH condition;
- they come from a different run (Set 2, T=0.5) than the ones they organise (Sets 1, 3 and 4, T=0.1);
- they are fixed before those runs.

What they do define is where an effect can be measured, not its sign.

**Temperatures.**
- **Twin, T=0.5:** it compares models, so one temperature was matched across all five model-conditions.
- **Sets 1, 3 and 4, T=0.1:** they compare conditions, at the conference setting.
- **Consequence:** the capability ladder that mixes them (Figure 5a) is ordinal across shades.

**Statistics.** The three replicates of a (model, module) cell share a model and a module, so they are correlated.
- **Pass rates** carry **Wilson** 95% intervals.
- **Contrasts** use the mean over cells of the within-cell difference, with:
  - a **cell bootstrap** interval (10,000 resamples);
  - a two-sided **sign-flip test** over cells (20,000 random sign patterns, seeded per label, so reruns reproduce
    byte for byte).
- **The deficit figure** uses **Newcombe** intervals for a difference of two independent proportions.
- **Code:** `phase3/runner/posthoc_checks.py`. The API study's copy reproduces all twelve published Set 1 and Set 3
  values before any contrast is reported.

---

## Part 6. The fine-tuning twin (Set 2)

**The natural experiment.** RTLCoder-Deepseek-v1.1 is deepseek-coder-6.7b fine-tuned on curated Verilog, so the pair
differs only by the fine-tuning.
- RTLCoder ran under both its native stub-completion prompt and the shared harness prompt, so prompt format is
  measured rather than confounded.
- gemma3:4b and llama3.1 were added as ladder context.
- Scale: 630 runs, baseline only, T=0.5.

**Result: a negative result with a per-class exception** (Section 7, page 5; Figure S1).
- **At the shared prompt,** on the 17 recoverable modules:
  - RTLCoder 21/51, base model 32/51;
  - 0 module wins, 13 ties, 4 losses.
- **At the native prompt:** 29/51; 5 wins, 6 ties, 6 losses.
- **The four losses fail at compilation, every iteration,** for four different reasons:
  1. a submodule that is never defined;
  2. SystemVerilog-only syntax;
  3. a parameter binding;
  4. the module named after RTLLM's folder (`fixed_point_substractor`) instead of the name the specification gives,
     identically under both prompts. That is memorisation overriding the prompt.
- **The exception:** RTLCoder (native) clears every recoverable signal-processing module (9/9) and the memory module
  (3/3).
- **Prompt format alone** is a modest, inconsistent effect: native 3 wins, shared 2, 12 ties.

**What it contributes.**
- The tiers.
- An external negative result against a published positive claim.
- The bottom rungs of the capability ladder.

---

## Part 7. Set 1: small models (and a correction)

1,512 runs: gemma3:4b, llama3.1:8b and deepseek-coder:6.7b, four conditions, 42 modules, T=0.1. Six timeouts, all
transient, were excluded and counted.

**First reading:** "the harmful regime replicates at scale". On the recoverable band, `sem_adv` sits about four points
below baseline (47/153 against 54/153).

**What the cell bootstrap showed (the final reading; Section 8.1, page 6):**
- the deficit has CI -10.5 to +0.7 and sign-flip p=0.199: worse in 7 of 51 cells, better in 3, equal in 41;
- it is consistent in direction but not significant;
- it is not uniform across models;
- Set 1 has no `raw_adv` condition, so the deficit cannot be separated from the raw tool text that accompanies the
  directives.

The paper therefore says the harmful regime "survives only as a non-significant deficit on small models".

**Escalation.** `sem_escalate_restart` matches baseline (54/151 against 54/153; 0.0, CI -4.6 to +4.6). Plain
`sem_escalate` trails (47/150; -4.7, CI -10.7 to 0.0).

**Cost by tier** (Figure 4b). Escalation's cut in Verilator and Yosys calls against `sem_adv`:
- 75.1% on ceilings (4.02 to 1.00 per run);
- 16.6% on the recoverable band;
- 10.1% on floors.

On ceilings, 44 of 54 escalation runs passed before the trigger and made no tool call at all
(`phase2/set1_analysis/ceiling_tool_call_distribution.txt`).

---

## Part 8. Set 3: larger models (and a retracted reading)

612 runs: qwen2.5-coder:14b, qwen2.5-coder:32b and gemma3:27b, four conditions, the 17 recoverable modules. Two
timeouts.

**First reading:** "escalation wins outright on large models". The pooled pass rates were 90/153 for `sem_escalate`
against 86/153 for baseline.

**What tracing the replicates showed:**
- of 153 `sem_escalate` runs, 88 passed without escalating and 65 escalated;
- the 2 escalated runs that passed had `semantic_fired`=0, rescued by raw tool feedback;
- the lead came from a handful of single-replicate flips, ordinary resampling noise at N=3.

**The final reading** (Section 8.2, page 6 to 7):
- no contrast differs from baseline (`sem_adv` -0.7, `sem_escalate` +2.6, `sem_escalate_restart` +2.0; all p 0.40 or
  higher);
- the mean deficit shrinks from -4.6 (Set 1) to -0.65 points;
- per model it is not monotonic: gemma3:27b reverses it (+7.8) and qwen2.5-coder:32b keeps it (-5.9), with every
  interval crossing zero.

**gemma3:27b, traced.**
- The reversal sits in `freq_div` and `freq_divbyeven`. gemma3:27b declares an output port and then redeclares it as
  `reg`, which the tools reject.
- Under baseline's terse feedback it repeats the same line. Under `sem_adv`'s longer, labelled template, with no
  interpreted directive firing, it finds the fix.
- Our hypothesis, stated as a hypothesis: the disposition comes from post-training (instruction tuning), not from model
  size.

**The cost advantage grows:** 27.6% on the recoverable band (5.31 to 3.85 calls per run), because capable models get
stuck less often.

---

## Part 9. The API study (Sets 4, 4b, 4c)

**Question.** Do the patterns extend to commercial non-reasoning models, and is the floor beyond the models or beyond
the tools?

**Design.**
- Pre-registered in `phase2/frontier/SET4_PREREG.md`, with five dated amendments, each hashed before the calls it
  governs.
- **Models:** `gpt-4.1-mini-2025-04-14`, `gemini-2.5-flash` (thinking budget 0) and `claude-haiku-4-5-20251001`.
- **Protocol:** the Set 3 runner with only the model call replaced, at T=0.1. Any reasoning token on any call stops the
  provider; there were none.
- **Toolchain:** a laptop toolchain matched to the cluster build. It reproduces saved Set 3 verdicts exactly (140/140
  pass/fail, 51/51 interpreter outputs).
- **Logging:** every call logs tokens, the returned model version, request identifiers and cost.
- **A fourth model, Kimi K2.6,** stopped at its smoke test with one reasoning token and was dropped.

**Set 4, the recoverable band (612 runs).**
- **A ceiling:** pooled pass rates of 99.3, 98.7, 98.0 and 98.0%. Gemini and Haiku pass every run.
- **No contrast is significant.**
- **Escalation rarely triggers,** so its tool-call cut reaches 88.6% (2.29 to 0.26 calls per run). The trend up the
  ladder is 16.6 to 27.6 to 88.6%.
- **Cost:** each passing module cost INR 0.11 to 0.51.

**Set 4b, the floor (599 valid runs).**
- 16 of the 19 floor modules leave the floor at baseline for at least one API model, so the floor belongs mostly to
  the 4B to 32B models, not to the modules.
- `adder_pipe_64bit`, `alu` and `freq_divbyfrac` stay at the floor for every model that ran them.
- **On the remaining failures, the interpreter fires but credits no pass.** It fires in 55% (103/188) of failing
  tool-condition runs. Only 3 passes followed a directive in a cell whose baseline was 0/3, and each, traced, is not
  attributable to it.

**Haiku is incomplete.**
- 143/228 runs: 85 failed on an exhausted account credit, cost nothing, and are excluded.
- v10 projects Haiku's missing cells in two marked places only: the floor heat map and one count. They are typeset in
  italics with a dagger, and the method is in `paper/V10_CHANGES.md`, section 6.
- A `\finaltrue` switch makes any remaining projection a compile error, and `--no-projection` removes them all.

**`freq_divbyfrac`, the one module every model fails** (0/36).
- **What it is:** a 3.5x clock divider.
- **What the reference does:** its counter advances once per rising edge, wraps every 14 half steps and emits two
  output periods per wrap.
- **What the specification says:** the counter "cycles through 7 half clock steps".
- **What the candidates do:** none is a phase-shifted copy of the expected waveform. They have roughly twice the
  period.
- **The final statement:** not a testbench defect; the specification's own description of the counter does not match
  its reference design (our reading); and the models fail on period and duty cycle.

**Set 4c (Gemini 2.5 Pro, reasoning).** Its pre-registered stop rule fired on run 1: 10,237 thinking tokens against a
2,048 budget, with the answer cut off. It was closed with 0 of 18 runs and no results.

**Spend over all API work:** $13.70, INR 1,552 at USD x 96 x 1.18 (`phase2/frontier/evidence/spend_summary.txt`).

---

## Part 10. Phase 3: a real MPSoC

**Why.** RTLLM scores a module by its testbench alone. On the recoverable band the interpreter had something to say in
only about a third of always-on runs (52 of 153 in Set 1). The defects STITCH was built for pass the testbench, break
synthesis, and multiply across a design.

**The substrate** (Section 9.1, page 9).
- **The design:** a RISC-V MPSoC developed within our group, independently of this study, from the `p20230031/RISC-V`
  repository:
  - a five-stage RV32 core;
  - a network interface;
  - a virtual-channel wormhole mesh router (a network-on-chip), built as a 2x2 and a 3x3 mesh.
- **Changes made:** compile-level only, each listed in `phase3/designs/SANITISATION.md` (nested comments, duplicate
  declarations, implicit ports that Vivado accepts and the open-source tools reject).
- **Defects already present:**
  - the top reports 63 latch inferences across 12 module definitions;
  - synthesis then aborts on a one-bit register that tests `clr | reset` inside an asynchronous-reset block;
  - both are **simulation-silent**: the circuits behave correctly on the inputs the testbench drives.
- **The defect at scale** (Figure 7a):
  - each router holds 20 instances of `register_32bit` and 20 of `register_4bit`, which both latch, so there are 36
    latched bits per pair;
  - so 36 x 20 x 4 = 2,880 latch cells in the 2x2 mesh and 6,480 in the 3x3 mesh;
  - Yosys prints one message per module definition, so the model sees the same two messages at both sizes;
  - with the task leaves repaired, both meshes synthesise with 0 latch cells, and the MPSoC top with 122, left in five
    modules outside the repair set.

**v3: keeping the interpreter robust.** Running the production interpreter (v2) on real logs exposed three problems:
- **wrong advice:** an unused clock got the gating template, which builds a clock-gated latch;
- **silences:** the async-reset abort and an expression truncation produced no directive.

The v3 layer:
- imports v2 unchanged and reproduces it byte for byte wherever no new rule applies;
- adds `MISSING_CLOCK` (a fusion of a Yosys latch with a Verilator unused clock), `ASYNC_RESET`, `WIDTH_EXPR` and
  `COMB_LOOP`.

A live drift gate caught a latch-message format change between Yosys 0.33 and 0.69. That change would otherwise have
silently disabled the new rules.

**The experiment** (Section 9.2, page 10).
- **Eleven tasks:** eight real defective leaves and three seeded ones; six are sim-silent.
  - Specifications are purely behavioural: a pilot with hints let an 8B model fix everything on the first call.
- **Conditions:** all share 6 model calls, one prompt and identically filtered raw text.
  - `baseline` stops at the first simulation pass, as AutoChip does, so on a sim-silent task it stops at the input.
  - That is not a strawman. It is exactly what a simulation-only loop does. The like-for-like comparison is the
    sim-visible stratum.
- **Runs:** six models from 3B to 14B, N=3, T=0.1, 990 runs on the cluster.

**The equivalence audit, and the sign-off oracle.**
- **The audit:** every clean repair of the 990 runs was checked against its golden fix with Yosys formal equivalence.
  Where a candidate was not proven equivalent, the check was repeated with the inputs the specification declares
  illegal mapped to a legal value; that is "equivalent on legal inputs".
- **Two testbench gaps:**
  - in `mem_wb_mux`, the testbench never drove the cases where a latch holds a stale store operand;
  - in `Address_select`, the testbench checks `J_addr` only on a non-flushed jump, though the specification defines
    it on every input.
- **The fix:** a specification-complete **sign-off testbench** that scores the returned RTL offline and never reaches
  the loop. On the other nine tasks it is identical to the loop testbench.
- **Why re-scoring is exact:** the loop never saw the new oracle, so the 990 runs can be re-scored without re-running.
  The paper labels that post hoc.

**The numbers moved** (`phase3/evidence/phase3_final/PLANNER_BRIEF.md`, section 3). Every ordering and direction
survived, and the absolute rates for the tool conditions fell 5 to 8 points, mostly from `Address_select`:

| Claim | As run (loop testbench) | Under the sign-off oracle |
|---|---|---|
| clean rate: baseline / raw / v2 / v3 / escalation | 23 / 59 / 68 / 74 / 80% | 22 / 53 / 63 / 67 / 72% |
| baseline signed off defective | 62% (old "silent structural pass") | 63% (125/198) |
| v3 minus raw text | +14.6 | +14.1 (CI +3.5 to +24.7) |
| v2 minus raw text | +9.1 | +10.1 (CI +2.0 to +18.7) |
| escalation minus baseline, sim-visible | +23.3 | +14.4 (CI +3.3 to +27.8) |

This is a strength, not an embarrassment. We built a stricter oracle, applied it to our own results, and reported
every number it lowered.

**The control arm: the single most important run.**
- **The worry:** escalation opens with a generic message ("the design simulates correctly but fails synthesis
  sign-off"). Its advantage might come from that alarm alone, not from the interpreter's detail.
- **The test:** `baseline_gate` gives simulation plus exactly that message, never escalates, and logs (never feeds
  back) what v3 would have said.
- **How it was run:** it was pre-registered before any of its runs, together with qwen2.5-coder:32b under all six
  conditions:
  - `phase3/evidence/PREREG_FINAL.md`, SHA-256 `1b6eb915...cc63`;
  - four primary contrasts and their readings;
  - frozen with the runner, interpreter and task files in `FREEZE_FINAL.md`.
- **Results** (Table 6, page 11):
  - **escalation minus the alarm:** +19.7 (CI +11.1 to +29.3, p<0.001);
  - **v3 minus the alarm:** +14.6 (CI +3.0 to +26.3, p=0.021);
  - **the alarm minus raw text:** -0.5. **The alarm minus baseline, on sim-visible tasks:** -1.1.
- **The pre-registered reading, R1:** the detail in the feedback adds value beyond the verdict.
- **If the alarm had matched escalation,** the reading would have been R2 or R3: that the gain is the stop-on-clean
  rule plus a nudge, and that the interpreter adds nothing measurable. The paper would have had to say so.
- **Multiplicity** (added in v10): the contrasts are uncorrected by design. Under Holm across the four, contrast 1
  survives and contrast 2 (adjusted 0.063) does not.

**The other Phase 3 findings** (Results 1 to 8, pages 10 to 13).
- **Latches.** Latch-free clean synthesis on the latch-bearing tasks rises from 24% (35/144) to 88% (127/144). This
  count uses Yosys only.
- **The alarm alone breaks working logic.**
  - Of 108 sim-silent alarm-only runs, 80 still pass simulation at the end, against 97 under escalation.
  - From call 3 to call 6 the alarm adds two points, while escalation climbs from 56 to 72% once it hands over to v3.
- **Interpretation beats raw text, sooner and cheaper.**
  - v3 minus raw text is +14.1, and v2's out-of-sample +10.1 is the honest estimate.
  - v3 needs about 23% fewer calls and tokens.
  - 55% of v3 runs are sign-off clean after the first call.
- **Escalation reaches 72%** with 47.5% fewer tool rounds than always-on v3.
- **Leaves compose.** Simulation-only repair never restores top-level synthesis. v3 does in 16/18 groups per design,
  and escalation in 18/18 for both meshes.
- **Up the ladder:**
  - at 32B and for the three API models, any tool feedback repairs every sim-silent defect;
  - simulation-only repair still signs off all 18 sim-silent runs as defective for every model;
  - the pass-rate benefit is a small-model effect, but the guard is needed at every size.
- **A limitation of structural advice.**
  - 41 loop-clean `Address_select` repairs set `J_addr` to 0 where the specification defines `X + PC`.
  - The production latch advice ("one unconditional assignment ... `<safe value>`") appears in every such run under
    v2, v3 and escalation. Runs without the advice also produce violations, so this is a count, not a causal claim.
  - The violation is invisible at processor level, because the consumer reads `J_addr` only on a jump.

---

## Part 11. How the paper evolved

| Version | What changed, and why |
|---|---|
| Conference (MLCAD '26) | four regimes, N=1 illustrations, in-house benchmark |
| v7 | the extension: replication, escalation, harness, the RTLLM study, Phase 3 as run (loop testbench) |
| v8 | Phase 3 rebuilt on the sign-off oracle; the control arm and 32B added; the API ladder rows; the alarm-versus-detail result as the headline |
| v9 | condensed to 16 pages plus a supplement; the escalation guarantee corrected everywhere; the Gemini column; the `freq_divbyfrac` analysis; bibliography checked against Crossref and arXiv (one wrong author list fixed, two unverifiable venues removed); the deficit figure's intervals correctly labelled Newcombe, not Wilson |
| v10 | Overleaf-ready, self-contained build (15 pages); a unified figure style; the teaser figure; the latch result as Result 1's lead; one consistent `freq_divbyfrac` statement; the MPSoC described as "developed within our group, independently of this study"; the multiplicity note; Haiku's projections marked and removable |

Every change and number source is listed in the change logs: `paper/V10_CHANGES.md`, and
`paper/archive/V9_CHANGES.md` and `V8_CHANGES.md`.

---

## Part 12. What it cost

**Cluster runs** (Ollama serving on the institutional GPU cluster):

| Set | Runs | Hardware |
|---|---|---|
| Set 2 (Twin) | 630 | H100 |
| Set 1 | 1,512 | A100 |
| Set 3 | 612 | A100 |
| Phase 3, 990-run batch | 990 | H200 NVL |
| Phase 3, final batch | 396 | H200 NVL |
| **Total** | **4,140** | |

- **Excluded:** 8 transient timeouts (6 in Set 1, 2 in Set 3).
- **Wall time:** each run records its own wall time, but no total GPU-hour figure was compiled.

**Laptop runs:**
- the 255-run in-house benchmark (Phase 1);
- the Phase 0 hunt;
- every API run.

**API spend:** $13.70 (INR 1,552) over Sets 4, 4b and 4c, the Phase 3 API ladder rows and the completion runs. That
counts every paid call, including smoke tests and pilots. By provider:
- Anthropic $6.69;
- Google $4.72;
- OpenAI $2.29;
- Moonshot $0.0004.

---

## Part 13. Lessons

1. **Replicate before you claim.** Two of the conference-era readings ("the harmful regime replicates", "escalation
   wins on large models") did not survive N=3 with a cell-level test and a replicate trace.
2. **Gate every mechanism claim on `semantic_fired`.** A pass is not a win for the interpreter unless the interpreter
   spoke.
3. **Report by difficulty tier.** Pooling ceilings and floors hides any effect.
4. **Put pass detection in one place, with no defaults.** Silent harness bugs produce plausible wrong numbers.
5. **Separate the alarm from the detail.** Without the control arm, escalation's gain could not be attributed to the
   interpreter.
6. **Use an oracle the loop never sees.** A loop testbench is also a training signal. A specification-complete
   sign-off testbench caught repairs that were structurally clean and functionally wrong.
7. **Pre-register and hash.** The final batch and the API study were fixed before their runs, so their readings cannot
   drift after the fact.
8. **Scope efficiency claims to the axis that holds.** Tool calls fall with escalation; tokens can rise.
9. **State limitations as findings.** The `Address_select` advice result became a direction for the next interpreter,
   not something to hide.

---

## Part 14. Directions (from the paper's conclusion, page 14)

1. **Held-out real defects,** to test the v3 rules out of sample. They were written from these designs' logs.
2. **A specification-valued latch default:** "assign the value the specification defines", not a constant. This
   targets the `Address_select` violations.
3. **Integration-level feedback,** for defects that only exist once modules are connected. Two examples:
   - a one-bit program-counter port driven with 32 bits;
   - a FIFO instantiated by position with a missing port.
4. **Reasoning models,** and why the deficit depends on post-training rather than size.
5. **Specification-level robustness:** `freq_divbyfrac` shows a specification defect that no interpreter can see.

Two commitments carry into any future work:
- every interpreter claim stays N=3-replicated and `semantic_fired`-gated;
- every pass rate is reported against the difficulty tier that decides whether the mechanism could even be measured.
