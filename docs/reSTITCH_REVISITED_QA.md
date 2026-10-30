# reSTITCH Revisited: Questions and Answers

## How to use this document

This is the authors' reference for the journal paper. Use it to onboard a newcomer, to answer a fellow author, or to
prepare for a reviewer.

**Note (2026-10-30).** The answers were written against paper v10 (`paper/overleaf/main.pdf`, 15 pages, and its
supplement, "S1" to "S9"), now archived (local, `paper/archive/v10/`; in git history at `e77bf73`). The current paper
is `paper/main.tex` (v11, 14 pages, no supplement), with readable condition and study names (mapping at the top of
`docs/reSTITCH.md`), and the supplement's tables are in `docs/reSTITCH.md`, Part 15. Every number is unchanged;
section, page and "S" references below are v10's.

**Order.** The questions follow the v10 paper section by section, in the order a reader meets them.

**Format.** Every answer has three parts:

- **Short answer:** for a beginner;
- **In depth:** the full explanation, with every term defined on first use;
- **If a reviewer asks:** a defensible reply that includes the honest limitation.

**Numbers.** Every number is from the paper or from an evidence file named in the answer. Where a question asks how
something is computed, the answer cites the code (file and function).

**Start here.** If you are new, read the glossary and "The paper in 10 sentences" first.

**Related documents:**

- `docs/reSTITCH.md`: the full story;
- `docs/PHASES_EXPLAINED.md`: every phase;
- `docs/HPC_GUIDE.md`: the cluster runs;
- `REPO_INDEX.md`: where every file lives.

---

## Glossary

| Term                               | Meaning                                                                                                                                                                                       |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **RTL**                      | Register-transfer level: a description of a digital circuit in terms of registers (memory updated on a clock tick) and the logic between them. Synthesis turns it into gates.                 |
| **Verilog**                  | The hardware description language the RTL is written in. Its unit is a*module* with input and output *ports*.                                                                             |
| **Testbench**                | A Verilog program that drives a module's inputs and checks its outputs, printing pass or fail.                                                                                                |
| **Simulation**               | Running the design against a testbench in a simulator (here Icarus Verilog). It only checks what the testbench drives.                                                                        |
| **Lint**                     | Static checking of code for suspicious patterns without running it (here Verilator). Each warning has a code such as`UNUSEDSIGNAL`.                                                         |
| **Synthesis**                | Translating RTL into a netlist of gates and memory cells (here Yosys). It reports latches, loops, and constructs it cannot map.                                                               |
| **Latch**                    | A level-sensitive memory element. In combinational code it appears by accident when a signal is not assigned on every path, so the hardware must "remember" the old value.                    |
| **Multi-driven net**         | A wire driven by two pieces of logic at once. In silicon the drivers fight; in simulation the value can be`x`.                                                                              |
| **Sign-off**                 | The engineering check that a design is ready to build: it is functionally correct by a complete testbench and structurally clean (synthesisable, no latches or loops).                        |
| **LLM repair loop**          | A loop in which a language model writes RTL, tools check it, and the result is fed back for another attempt, up to a budget.                                                                  |
| **Interpreter**              | STITCH's deterministic rule set (no model) that turns a tool message into a short repair instruction.                                                                                         |
| **Directive**                | The interpreter's output: a short instruction that names the signal and the fix.                                                                                                              |
| `baseline`                       | Feedback is the simulation log only (the AutoChip-style loop).                                                                                                                                |
| `raw_adv`                        | Simulation log plus the raw Verilator and Yosys text.                                                                                                                                         |
| `sem_adv`                        | Simulation log, raw tool text and the interpreter's directives, on every iteration. In RTLLM this is the production interpreter (v2).                                                         |
| `sem_adv (v2)`, `sem_adv (v3)` | Phase 3 versions: v2 is the production interpreter, v3 the additive layer with four new rules.                                                                                                |
| `sem_escalate`                   | Behaves as`baseline` until two consecutive failures share an error signature, then gives `sem_adv` feedback for the rest of the run.                                                      |
| `sem_escalate_restart`           | As`sem_escalate`, plus one blank-slate restart if it stays stuck.                                                                                                                           |
| `sem_esc_restart (v3)`           | Phase 3 escalation: starts behind a generic "fails synthesis sign-off" message, escalates to v3 after two identical signatures, and restarts once.                                            |
| `baseline_gate`                  | Phase 3 control arm: simulation plus exactly that generic message; never escalates.                                                                                                           |
| **N**                        | The number of replicates per configuration. Here N=3.                                                                                                                                         |
| **Temperature (T)**          | The model's randomness setting. 0.1 is nearly deterministic; 0.5 is more varied.                                                                                                              |
| **Replicate**                | One independent run of the same (model, module, condition).                                                                                                                                   |
| **Cell**                     | All replicates of one (model, module) pair, or (model, task) in Phase 3, under one condition. Contrasts compare cells.                                                                        |
| **Tier**                     | RTLLM difficulty band (ceiling, recoverable, floor), set by the maximum baseline pass rate in the twin run.                                                                                   |
| **Wilson CI**                | A 95% confidence interval for a proportion, well behaved for small counts and for rates near 0% or 100%.                                                                                      |
| **Bootstrap**                | Estimating the uncertainty of a statistic by resampling the data with replacement many times. Here cells are resampled.                                                                       |
| **Sign-flip test**           | A permutation test: under "no effect", each cell's difference is equally likely to be positive or negative, so signs are flipped at random to see how often a mean as large arises by chance. |
| **p-value**                  | The probability, if there were no true effect, of a result at least as extreme as the one observed.                                                                                           |
| **Holm**                     | A correction for testing several hypotheses: sort the p-values, then multiply the smallest by the number of tests, the next by one fewer, and so on.                                          |
| **Newcombe interval**        | A confidence interval for the difference of two independent proportions, built from their two Wilson intervals.                                                                               |
| **Discordant pairs**         | In matched runs of A and B, the runs where only A succeeded or only B succeeded ("A/B only"). Ties carry no information about the difference.                                                 |
| **Pre-registration**         | Writing the hypotheses, metrics, contrasts and readings down, and hashing the file, before running.                                                                                           |
| **Oracle**                   | The judge of correctness. Here a testbench: the loop testbench guides repair, and the sign-off testbench scores the result.                                                                   |
| **Formal equivalence**       | A proof by a tool (here Yosys`equiv_*`) that two circuits produce the same outputs for every input.                                                                                         |
| **MPSoC**                    | Multi-processor system-on-chip: several processors, memories and a communication network on one chip.                                                                                         |
| **NoC**                      | Network-on-chip: a small packet network on the chip that connects the processors.                                                                                                             |
| **Router**                   | A crossroads of the NoC that forwards packets between neighbours.                                                                                                                             |
| **Leaf module**              | A module that instantiates no other module: the bottom of the design hierarchy.                                                                                                               |
| **Composition**              | Splicing repaired leaf modules back into the full design and synthesising the top.                                                                                                            |

---

## The paper in 10 sentences

1. STITCH adds Verilator lint and Yosys synthesis to a language-model repair loop for Verilog, plus a deterministic
   interpreter that turns their messages into short directives at no inference cost.
2. The conference version showed its effects one run at a time. This extension replicates everything at N=3 and checks
   that the interpreter actually fired in every run it is credited with.
3. Two gated-input illustrations replicate 3/3, and an input/output asymmetry explains which defects the interpreter
   can reach. Three larger candidates did not survive and are reported as retired.
4. Escalation fires the interpreter only once a run is stuck. Its tool-call savings grow with model capability (16.6,
   27.6, 88.6%), and its guarantee holds only for runs that converge before the trigger.
5. On RTLLM, always-on interpretation trails baseline by about four points on small models, which is not
   significant. The restart variant matches baseline, and API models are at ceiling.
6. The RTLLM floor is mostly beyond small open models, not beyond the tools. Where API models still fail, the
   interpreter fires but no pass is attributable to it.
7. On a real RISC-V MPSoC, simulation-only repair signs off 63% of its runs as defective, including every
   simulation-silent defect at every model size. With the tools, latch-free clean synthesis rises from 24% to 88%.
8. A pre-registered control arm shows that the detail of the feedback, not the alarm that sign-off failed, drives
   repair: escalation adds 19.7 points over the alarm. Interpretation beats raw text by 14.1 points with 23% fewer
   calls.
9. Repaired leaves restore synthesis of the 4- and 9-router meshes, which simulation-only repair never does. A
   specification-complete sign-off oracle catches structurally clean repairs that violate the specification.
10. STITCH is best read as a deterministic sign-off guard and translator. It matters most for small models and for
    defects simulation cannot see, and the guard is needed at every size.

---

## Part A. Title and abstract (page 1)

### Q1. Why is the title "reSTITCHing: Replicated, Cost-Controlled, and Sign-off-Aware Repair of LLM-Generated RTL"? What does each word mean, and what is "sign-off-aware"?

**Short answer:** "reSTITCHing" means revisiting the conference system STITCH. The three adjectives name the three
things the extension adds: replication, control of tool cost, and awareness of sign-off.

**In depth:**

- **"reSTITCHing"** is a play on the original name. We re-examine STITCH (MLCAD '26) rather than propose a new system.
- **"Replicated":** every claim is re-run at N=3 replicates per configuration. No interpreter claim is made without a
  check that the interpreter fired (`semantic_fired`) in the runs it is credited with.
- **"Cost-Controlled":** the escalation policies run the expensive tools (Verilator and Yosys) only once a run is
  stuck. They are measured in tool calls per run (Section 5, page 4; Section 8, pages 6 to 7).
- **"Sign-off-Aware":** the repair is judged by sign-off, not by "the loop testbench passed". Engineers sign off a
  design when it is both functionally correct and structurally clean.
  - In Phase 3, a run counts as **sign-off clean** only if three things hold:
    1. a specification-complete sign-off testbench passes;
    2. Yosys reports no latch or loop;
    3. Verilator reports no hard structural warning.
  - The loop never sees that testbench (Section 9.2, page 10).
- **"Repair of LLM-Generated RTL":** the task, fixing Verilog that a language model wrote.

**If a reviewer asks:** "The title states the three axes on which the extension changes the conference work: the claims
are replicated, tool cost is measured and controlled, and success is judged by a sign-off oracle the loop never sees.
It does not claim a new architecture, and the paper says so in 'Relation to the conference version' (page 2)."

### Q2. What is RTL, and what is Verilog?

**Short answer:** RTL is a description of a digital circuit as registers plus the logic between them. Verilog is the
text language it is written in. A synthesis tool turns Verilog RTL into real gates.

**In depth:**

- Hardware is not drawn gate by gate; it is described in a hardware description language. In Verilog, the unit is a
  **module**, like a function, with **ports** (inputs and outputs).
- **Two kinds of logic:**
  - **combinational** logic (`always @(*)` or `assign`) computes outputs from current inputs, like a calculator;
  - **sequential** logic (`always @(posedge clk)`) stores values in flip-flops that update on the clock tick, like a
    camera taking one photo per tick.
- **The key difference from software:** every part of the circuit exists physically and works at the same time.
  Verilog describes wiring, not a sequence of steps.
- **Why a model's Verilog can be wrong in ways a test misses:** a line that is harmless in software, such as "leave
  this variable unchanged in some case", becomes physical memory (a latch) in hardware.

**If a reviewer asks:** this is background, but the paper keeps it short on purpose. `phase3/docs/PHASE3_EXPLAINED.md`
gives a plain-language primer, with real examples from the MPSoC.

### Q3. What is an LLM repair loop? What did AutoChip do, and what did the conference version of STITCH add?

**Short answer:** In the loop, a model writes RTL, a tool checks it, and the failure is fed back for another try.
AutoChip used compiler errors and simulation mismatches. STITCH added lint and synthesis, and an interpreter that
rewrites their messages as instructions.

**In depth:**

- **AutoChip** (reference [2]): generate, compile, simulate, feed back, retry. It stops at the first simulation pass.
- **What a simulation-only loop cannot see:** latches, multi-driven nets and resets a synthesis tool cannot map, all
  of which simulate correctly on the inputs a testbench drives (Introduction, page 1).
- **What STITCH (reference [1]) adds:**
  1. **Verilator** (lint) and **Yosys** (synthesis) in the loop, so structural defects become visible;
  2. a **deterministic interpreter** between the tools and the model. It maps each recognised message to a directive
     that names the signal and the fix, for example "a declared input is never read: use it" (Table 1, page 3). It
     calls no model, so it adds no inference cost.
- **The conference paper** characterised the interpreter through four outcome regimes, each with one module and one
  run (page 1).

**If a reviewer asks:** "STITCH's contribution is not the loop, which AutoChip established, but what is fed back:
synthesis and lint diagnostics, translated deterministically, with no extra model call (Related Work, page 2)."

### Q4. What is a 95% CI? What is a Wilson interval, how can it work with N=3, what does it measure, and why is it needed?

**Short answer:** A 95% confidence interval (CI) is the range of values a rate or effect could plausibly have, given
the data. The Wilson interval is a good CI for a pass rate. With N=3 it is computed on pooled counts (for example
54/153 runs), where it is meaningful. On a single cell of 3 runs it is very wide, which is honest.

**In depth:**

- **What a CI is.** If we repeated the whole experiment many times, about 95% of the intervals computed this way
  would contain the true value. It answers "how sure are we?", not "how big is the effect?".
- **The Wilson interval for a proportion k/n.** Write p = k/n and z = 1.96. The centre is
  (p + z^2/2n) / (1 + z^2/n), and the half-width is z/(1 + z^2/n) x sqrt(p(1-p)/n + z^2/4n^2).
  - Unlike the textbook "p plus or minus 1.96 standard errors", it never leaves the range 0 to 1, and it behaves well
    for small n and for rates near 0 or 100%.
  - The code is `statsmodels`' `proportion_confint(method="wilson")`, used in `paper/make_v10_figures.py` (`_wilson`).
- **With N=3.**
  - N is the number of replicates per configuration, not the size of a rate's denominator. The paper's rates pool
    many cells. Table 5 (page 11) has 198 runs per condition: 6 models x 11 tasks x 3 replicates.
  - For a single cell, 3/3 gives a Wilson interval of about 44 to 100%. That is exactly why the paper never draws a
    conclusion from one cell.
- **What it measures and does not measure.** Uncertainty from sampling: the model's randomness across runs, at a fixed
  temperature. It does not cover choosing other modules, or a different benchmark or toolchain. Those are threats to
  validity (page 13).
- **Why it is needed.** Without an interval, 52% against 53% looks like a difference. With one, the reader sees that
  the alarm and raw text are level (Table 5: 45 to 59 against 46 to 59).

**If a reviewer asks:** "Wilson intervals are used for rates. Because the three replicates of a cell are correlated,
every contrast uses a cell-level bootstrap instead. That interval is about 1.7 times wider than a per-run Wilson
interval (Section 9.2, page 10; `phase3/evidence/phase3_run/PHASE3_RESULTS.md`, limitations, item 1)."

### Q5. What do N=3 and T=0.1 mean?

**Short answer:** N=3 means each (model, module, condition) is run three times independently. T=0.1 is the model's
temperature: low randomness, so runs are mostly, but not always, the same.

**In depth:**

- **Why replicate.** Language models sample their output. At T=0.1 the same prompt usually gives the same answer, but
  not always, and a single run cannot separate a real mechanism from a lucky draw.
  - The conference paper's evidence was N=1. Replication retired a would-be win, `datapath_mux_alu`, which passed in
    2 of 3 runs with the interpreter never firing (Section 4, page 4).
- **Why N=3 and not more.**
  - Three is the smallest N at which a unanimous result (3/3 or 0/3) differs meaningfully from a split.
  - Cost grows linearly with N: the study ran 4,140 cluster runs, plus API and laptop runs.
  - The price is low power for per-model effects, which the paper states (Threats, page 13).
- **Why T=0.1.** It matches the conference setting and keeps runs comparable. The twin run used T=0.5 (Q42).

**If a reviewer asks:** "N=3 is a deliberate trade-off between breadth (seven models, 42 modules, an MPSoC case study)
and depth per cell. General claims rest on cell-level statistics, and per-model effects are reported as undecided
where they are."

### Q6. Why are replicates correlated, and why is the cell bootstrap about 1.7 times wider than Wilson?

**Short answer:** The three runs of a cell share the same model, module and prompt, so they tend to agree. Treating
them as independent overstates the evidence. Resampling whole cells accounts for that, so its interval is wider.

**In depth:**

- **Most cells are unanimous.** At T=0.1 a model that solves a task tends to solve it three times, and one that fails
  tends to fail three times. In Phase 3, 990 runs form 330 (model, task, condition) cells of 3 correlated replicates,
  and most are unanimous (`PHASE3_RESULTS.md`, limitation 1).
- **So the effective sample size is closer to the number of cells than to the number of runs.**
- **The cell bootstrap** (`phase3/runner/posthoc_checks.py`):
  1. compute each cell's within-cell difference in pass rate between two conditions;
  2. resample the cells with replacement 10,000 times;
  3. take the 2.5th and 97.5th percentiles of the mean difference.
- **The result.** The interval is about 1.7 times wider than a per-run Wilson interval on the same data (Section 9.2,
  page 10).

**If a reviewer asks:** "We use the conservative interval for every claim. This costs significance on some per-model
effects, and we report those as undecided rather than switch to the optimistic interval."

---

## Part B. Introduction and Figure 1 (pages 1 to 2)

### Q7. What does "signed off defective RTL" mean?

**Short answer:** A run that the repair loop declared done (its testbench passed) but that is not sign-off clean.
It is either structurally dirty (a latch, loop or hard lint warning) or fails the specification-complete sign-off
testbench.

**In depth:**

- The definition is in Section 9.2 (page 10): a run is **signed off defective** when the loop testbench passed it but
  it is not sign-off clean. In other words, the loop would have shipped it, and sign-off would have rejected it.
- **Simulation-only repair (`baseline`)** signs off 63% of its runs as defective (125/198). That includes all 108
  runs on the six sim-silent tasks, where it stops at the unmodified defective input (Figure 1a, page 2; Table 5,
  page 11).
- **With the lint and synthesis layer,** the rate falls to 8% (v2 and v3), 12% (raw text), 13% (escalation) and 15%
  (the alarm).

**If a reviewer asks:** "The metric is defined against an oracle the loop never sees, so a condition cannot optimise
for it. It counts exactly the runs a simulation-only loop would wrongly accept."

### Q8. Do lint and synthesis "do harm"? What do latches, multi-driven nets and unmappable resets do to real silicon, and how does that affect real designs?

**Short answer:** No. Lint and synthesis do not cause defects; they detect them. The defects are real hardware
problems: timing and glitch risk, extra area, wires in contention, and designs that cannot be synthesised at all.

**In depth:**

- **The tools only report.** When the paper says simulation-only repair "signs off defective RTL", the defect was
  already in the RTL. Lint and synthesis make it visible.
- **An inferred latch** is memory where combinational logic was intended:
  - **timing:** a latch is transparent for a whole clock phase, which makes static timing analysis harder, because
    the tools reason about clock edges;
  - **glitches:** brief wrong values pass straight through an open latch;
  - **area:** each latched bit is an extra storage cell. The MPSoC's two latching register definitions become 2,880
    latch cells in the 4-router mesh and 6,480 in the 9-router mesh (Figure 7a, page 9).
- **A multi-driven net** has two drivers fighting over one wire. In silicon that is contention: an undefined value,
  extra current, and a functional failure. Simulation may show `x`, or nothing at all if the testbench never drives
  both sides.
- **An unmappable reset.** The MPSoC's one-bit register tests `clr | reset` inside an asynchronous-reset block. Yosys
  cannot build that as a standard reset flip-flop and aborts. The whole MPSoC top cannot be synthesised until it is
  fixed (page 9).
- **The effect on real designs.** Defects in small leaf modules multiply with every instance. The same two Yosys
  messages stand for 2,880 or 6,480 latch cells, depending on router count.

**If a reviewer asks:** "The paper uses structural cleanliness as one part of sign-off because these defects break
timing closure, area budgets or synthesis itself. Simulation alone cannot see them."

### Q9. What are the three panels of Figure 1?

**Short answer:** (a) How often each condition ships defective RTL; (b) how often latches are removed on the
latch-bearing tasks; (c) whether repaired leaves let the full designs synthesise.

**In depth (Figure 1, page 2; six models, 198 runs per condition, Wilson 95% CI):**

- **(a) Signed off defective, by condition.** Simulation-only repair 63%; with tools 8% (v2, v3), 12% (raw text), 13%
  (escalation) and 15% (the alarm).
- **(b) Latch-bearing tasks.** Runs that end latch-free with a clean synthesis:

| Condition  | Rate | Runs    |
| ---------- | ---- | ------- |
| baseline   | 24%  | 35/144  |
| alarm      | 65%  | 94/144  |
| raw text   | 72%  | 104/144 |
| v2         | 85%  | 122/144 |
| v3         | 88%  | 127/144 |
| escalation | 88%  | 127/144 |

  Source: `phase3/evidence/phase3_final/PAPER_NUMBERS.md`, latch line. The count comes from Yosys alone, so it does
  not depend on either testbench.

- **(c) Top-level synthesis restored.** Each condition's repaired leaves are spliced back into the 2x2 mesh, the 3x3
  mesh and the MPSoC top.
  - Simulation-only repair never yields a design that synthesises (marked "aborts").
  - v3 does in 16 of 18 (model, replicate) groups in each design.
  - Escalation does in 18/18, 18/18 and 15/18.

**If a reviewer asks:** "Figure 1 previews the case-study result; every number in it is repeated with its source in
Section 9."

### Q10. What is sem_adv (v3), and what improvement is it?

**Short answer:** v3 is an additive layer on top of the unchanged production interpreter (v2). It reproduces v2
exactly, except where real MPSoC logs showed v2 giving wrong advice or none, and there it adds four rules.

**In depth:**

- **Why it was needed.** Running v2 on the real MPSoC logs exposed gaps (Section 9.1, page 9):
  - **wrong advice:** an unused clock got the generic "gate the output on this input" template, which builds a
    clock-gated latch, the opposite of the fix;
  - **no advice:** the asynchronous-reset abort and a truncation whose operand is an expression produced no directive.
- **What v3 adds** (`src/interpreter/stitch_interpreter_v3.py`; Table 1, page 3): `MISSING_CLOCK`, `ASYNC_RESET`,
  `WIDTH_EXPR` and `COMB_LOOP` (Q22).
  - It also caps its output at three directives, and stops suggesting gating on clock ports and on partly used buses
    (S1).
- **The guarantee:** with `version="v2"`, v3 reproduces v2 byte for byte, and tests enforce it.
- **The measured gain:**
  - v3 reaches 67% sign-off clean against v2's 63% (Table 5). The v3 minus v2 contrast is +4.0, CI -4.0 to +12.1, not
    significant (Table S22).
  - On the async-reset register, interpreter-credited wins rise from 3/18 to 15/18 (Result 7, page 12).

**If a reviewer asks:** "v3's rules were written from these designs' logs, so its gain is in-sample. We report v2's
+10.1 over raw text as the out-of-sample estimate of what interpretation is worth (Result 3, page 11)."

### Q11. Why does sem_esc_restart look "worse" than v3 in places in Figure 1?

**Short answer:**

- **Signed off defective, 13% against 8%:** escalation keeps more runs passing simulation, so more of them can end as
  "passes the loop but is not clean". It still has the highest sign-off clean rate, 72%.
- **MPSoC top, 15/18 against 16/18:** one group out of 18, well within noise.

**In depth:**

- **Signed off defective = loop pass minus sign-off clean.** From `phase3/evidence/phase3_final/PHASE3_FINAL.md`
  (pooled):
  - escalation: loop pass 168/198, sign-off clean 142/198, so 26 signed off defective (13%);
  - v3: loop pass 147/198, sign-off clean 132/198, so 15 (8%).
- **Escalation has more runs in both buckets:**
  - 10 more sign-off clean runs than v3 (142 against 132);
  - 21 more loop-passing runs (168 against 147), so 11 more of them end in the "passes, not clean" bucket.
- **The stratum tables show where:**
  - on the sim-silent tasks both reach 86/108 sign-off clean, but escalation keeps 97/108 runs passing simulation
    against v3's 88/108, so 11 runs against 2 end defective;
  - escalation opens behind the generic alarm and only hands over to v3 after two identical signatures, so some runs
    keep working logic but reach the budget before finishing the structural repair.
- **MPSoC top composition: 15/18 against 16/18.** The Wilson intervals overlap almost completely (83%, 61 to 94,
  against 89%, 67 to 97; `PHASE3_FINAL.md`, Composition). Escalation reaches 18/18 in both meshes.

**If a reviewer asks:** "Escalation has the highest sign-off clean rate (72%, Table 5) and the highest loop pass rate
(85%). Its higher signed-off-defective share is the other side of preserving more working logic, not a quality
regression. The one-group difference at the MPSoC top is within noise."

### Q12. What is semantic_fired, and why do we refuse to credit the interpreter without it?

**Short answer:** A per-run flag saying whether the interpreter actually produced a directive in that run. A pass
without it is the model succeeding on its own, so it is never counted as an interpreter win.

**In depth:**

- Every runner records `semantic_fired`. In Phase 3 it is set from the directives actually fed back
  (`phase3/runner/stitch_runner_p3.py`, `semantic_fired: bool(sem_iters)`).
- **Why it matters, three times:**
  1. **Phase 0:** `datapath_mux_alu` passed `sem_adv` in 2 of 3 replicates with the flag at 0 in all three (page 4).
  2. **Set 3:** the two escalated runs that passed did so with the flag at 0, rescued by raw tool feedback (page 6).
  3. **Set 4b:** the interpreter fires on 55% of failing floor runs, but no pass is attributable to it (page 7).
- **The rule** (Introduction, page 2): no interpreter claim without N of at least 3 and a `semantic_fired` check in
  the runs it is credited with.

**If a reviewer asks:** "The flag separates 'the condition passed' from 'the interpreter caused the pass'. Without it,
pooled pass-rate gaps from sampling variance would be misread as mechanism."

### Q13. What are all the conditions? (a table)

**Short answer:** They differ only in what is fed back after a failure.

**In depth:**

| Condition                          | Where                     | Feedback                                                                                | Stops at                          |
| ---------------------------------- | ------------------------- | --------------------------------------------------------------------------------------- | --------------------------------- |
| `baseline`                       | all phases                | simulation log only                                                                     | the first simulation pass         |
| `raw_adv`                        | Phase 0, Phase 1, Phase 3 | plus raw Verilator and Yosys text                                                       | Phase 3: the first clean pass     |
| `sem_adv`                        | Phases 0 to 2 (v2)        | plus directives on every iteration                                                      | the first simulation pass (RTLLM) |
| `sem_adv (v2)`, `sem_adv (v3)` | Phase 3                   | plus v2 or v3 directives on every call                                                  | the first clean pass              |
| `sem_escalate`                   | Phase 1, RTLLM            | baseline until 2 same-signature failures, then`sem_adv`                               | the first simulation pass         |
| `sem_escalate_restart`           | Phase 1, RTLLM            | as above, plus one blank-slate restart after 3 more                                     | the first simulation pass         |
| `sem_esc_restart (v3)`           | Phase 3                   | the generic "fails sign-off" message, then v3 after 2 identical signatures, one restart | the first clean pass              |
| `baseline_gate`                  | Phase 3 control           | simulation plus exactly that message; never escalates                                   | the first clean pass              |

- **Budgets:**
  - RTLLM: 6 iterations for `baseline` and `sem_adv`, 8 for escalation (Q36);
  - Phase 3: 6 model calls for every condition.
- **"Clean pass"** means the loop testbench passes and the design is structurally clean.

**If a reviewer asks:** "In Phase 3 all conditions share the budget, the prompt and the identically filtered raw text,
and every candidate is fully evaluated. They differ only in what is fed back (Section 9.2, page 10)."

### Q14. The four conference regimes (enabling, protective, harmful, irrelevant): what survived replication?

**Short answer:**

- **Enabling** survives, in two replicated illustrations.
- **Harmful** survives only as a non-significant deficit on small models.
- **Irrelevant** gains a measured counterpart, the RTLLM floor tier, which is mostly beyond small models rather than
  beyond the tools.
- **Protective** is not claimed as a separate result.

**In depth:**

- **Enabling:** `decoder_3to8` and `mux4_oe` replicate 3/3 on gemma3:4b. The model passes in 2 iterations where both
  controls fail all 6 (Table 2, page 4).
- **Harmful:**
  - on the small models' recoverable band, always-on interpretation is about four points below baseline, with CI
    -10.5 to +0.7 and p=0.199 (page 6);
  - it is not separable from the raw tool text that accompanies the directives, and it fades on large models.
- **Irrelevant:** the floor tier, failures no tool sees, turns out to be passable by API models on 16 of 19 modules
  (page 7). Where they still fail, the interpreter fires but credits no pass.
- **Protective:** the escalation results cover the idea of shielding a model from intervention. The paper does not
  claim protective as a separate replicated regime.

**If a reviewer asks:** "The paper revises two conference readings explicitly ('Relation to the conference version',
page 2): harmful survives only as a non-significant deficit, and irrelevant gains a measured counterpart."

### Q15. What does the twin run (RTLCoder against its base model) contribute? Does it come out of the blue? What can we infer, and what does it predict?

**Short answer:** It does three jobs:

1. it defines the difficulty tiers every later set uses;
2. it is a negative result on fine-tuning;
3. it anchors the bottom of the capability ladder.

It is not out of the blue: the tiers could not exist without it.

**In depth (Section 7, page 5; S4, Figure S1):**

- **The natural experiment.** RTLCoder-Deepseek-v1.1 is deepseek-coder:6.7b fine-tuned on Verilog: same weights,
  differing only by the fine-tuning. Five model-conditions, 42 modules, N=3, T=0.5, baseline only: 630 runs.
- **Job 1, the tiers.** A module's tier is its maximum baseline pass rate across these five model-conditions:
  ceiling 6, recoverable 17, floor 19. Sets 1, 3 and 4 inherit them, so Set 3 and Set 4 run only on the recoverable
  band.
- **Job 2, the negative result.**
  - At the shared prompt RTLCoder passes 21/51 against 32/51 on the recoverable band: 0 wins, 13 ties, 4 losses.
  - At its native prompt it is a wash: 29/51; 5 wins, 6 ties, 6 losses.
  - The four losses fail at compilation on every iteration: an undefined submodule, SystemVerilog syntax, parameter
    binding, and a memorised folder name.
  - The exception: signal processing (9/9) and memory (3/3).
- **Job 3, the ladder.** Its bars sit at the bottom of Figure 5a (page 7), ordinal because of T=0.5.
- **What it predicts.** Fine-tuning on RTL text alone does not teach repair from feedback: RTLCoder repeated the same
  compile error for 8 iterations. A repair loop and its feedback matter more than the fine-tuned generator.

**If a reviewer asks:** "It is one model pair on one benchmark at one temperature, so it is a lean, not a verdict. It
is reported because a published positive claim exists, and with its per-class exception."

---

## Part C. Related work (pages 2 to 3)

### Q16. How does STITCH compare with agentic systems (VerilogCoder, MAGE, MEIC)? What is orthogonal about it?

**Short answer:** Agentic systems add model calls or agents to reach higher pass rates. STITCH adds no model call: it
changes what the loop feeds back. The two can be combined.

**In depth (Related Work, page 2):**

- **VerilogCoder** plans with several agents and traces waveforms with an AST-based tool.
- **MAGE** samples high-temperature candidates and debugs them with Verilog-state checkpoints.
- **MEIC** iterates language-model debugging over syntax and functional errors.
- **AIvril and UVLLM** add verification agents.
- **STITCH is a zero-inference-cost translation layer for lint and synthesis diagnostics.** It is evaluated with
  replication, tier decomposition, a sign-off oracle the loop never sees, and a control arm that separates "told that"
  from "told what". Any of those agents could consume STITCH's directives as one more input.

**If a reviewer asks:** "We do not compare pass rates with agentic systems: different models, budgets and benchmarks
would make the comparison meaningless. The paper's claim is orthogonal. It is about which feedback helps, at what
cost, and how to evaluate it honestly."

### Q17. Is STITCH "just regex"? Why deterministic, and why no extra model call?

**Short answer:** Partly regex, yes, and that is deliberate. It is a fixed, auditable rule set that costs nothing per
call, behaves the same every time, and cannot hallucinate.

**In depth:**

- **v2** parses Verilator and Yosys messages with regular expressions and fills directive templates
  (`src/interpreter/stitch_interpreter.py`).
- **v3** adds source-aware logic. It reads the RTL to:
  - find the offending block for the async-reset abort, whose message names no signal;
  - fuse two tools' messages into one diagnosis (`MISSING_CLOCK`);
  - route advice to the right module in multi-module files.
- **Why deterministic:**
  1. **Reproducibility:** the same log always gives the same directive. The production file's hash is recorded in
     every Phase 3 run.
  2. **Zero inference cost.**
  3. **Auditability:** every directive can be traced to a rule.
  4. **No hallucination:** a second model explaining errors (as in Qiu et al., reference [9]) can be wrong in new ways.
- **The cost of this design:**
  - rules must be maintained as tool formats change, which the live drift gate catches;
  - they only cover known classes, and v3's rules are in-sample.

**If a reviewer asks:** "The simplicity is the point: the paper shows what a deterministic translator buys, and where it
stops. The control arm shows that its detail, not a bare alarm, drives the repair."

---

## Part D. Section 3, STITCH in brief (page 3: Figure 2, Table 1)

### Q18. Walk me through Figure 2.

**Short answer:** Specification, then model, then RTL, then simulation. On failure, the feedback prompt collects the
simulation log, and, depending on the condition, the raw tool text and the interpreter's directives, and goes back
to the model. A sign-off testbench scores the returned RTL offline.

**In depth (Figure 2, page 3):**

- **The top row:** specification, LLM, RTL candidate, Icarus simulation (loop testbench), then Verilator lint and
  Yosys synthesis.
- **The feedback prompt** stacks three layers:
  1. the simulation log, for every condition;
  2. the raw tool text, for `raw_adv`, `sem_adv` and escalated runs;
  3. the interpreter's directives, for `sem_adv` and escalated runs.
- **The STITCH layer** is the tools plus the interpreter. The interpreter calls no model.
- **The offline sign-off testbench** (dashed box) only scores the final RTL and never feeds back. That separation is
  what makes the sign-off oracle fair.

**If a reviewer asks:** "In Phase 3 every candidate is fully evaluated in every condition, so the tools run
regardless. The conditions differ only in what reaches the prompt."

### Q19. In Table 1 (you wrote Table 3; it is Table 1 on page 3), what is "fusion"?

**Short answer:** "Fusion" means the directive comes from combining two tools' messages, not one. `MISSING_CLOCK` fuses
a Yosys latch report with a Verilator "clock is unused" warning.

**In depth:**

- **Read separately, the messages mislead.** On `register_4bit` the real messages are:

  - Yosys: "Latch inferred for signal `dout`";
  - Verilator: "Signal is not used: `clk`".

  v2 handles each alone. For the unused `clk` it applies the generic unused-input template ("condition on `clk`:
  `if (clk) ... else ...`"), which builds a clock-gated latch.
- **v3 reads the two together:** a latch in a level-sensitive block, plus an unused clock, means a register that is
  missing its clock edge. Its directive says: "change that block's header to `always @(posedge clk)` ... Do NOT add
  `if (clk)` anywhere" (`phase3/docs/PHASE3_EXPLAINED.md`, section 5.3).

**If a reviewer asks:** "Fusion is the one place where combining tools changes the diagnosis. It was written from a
real log that showed v2's advice was wrong (`phase3/evidence/PROD_V2_ON_REAL_LOGS.md`)."

### Q20. Table 1, the v2 rows: what does the tool say, and what does the directive tell the model?

**Short answer:** Each row pairs a tool message with a short instruction that names the signal and the fix.

**In depth** (templates in `src/interpreter/stitch_interpreter.py`, `_VERILATOR_INTERP` and the latch and loop
functions):

| Class                               | The tool says                                                                                            | The directive says                                                                                                                           |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `UNUSEDSIGNAL` (Verilator)        | a declared signal is never read                                                                          | "Port 'X' is declared but NEVER USED ... You MUST condition on 'X'", with an`if (X) ... else out = 0` template. Right for an enable input. |
| `MULTIDRIVEN` (Verilator)         | a signal has several drivers                                                                             | "Only ONE always block may drive a given signal. Merge all assignments."                                                                     |
| `UNDRIVEN` (Verilator)            | an output is never assigned, or a name is used but never declared (v2 tells these apart from the source) | assign the output, or declare the identifier                                                                                                 |
| `WIDTHTRUNC/EXPAND` (Verilator)   | an assignment's widths differ                                                                            | slice explicitly (`signal[N-1:0] = value[N-1:0]`), or check the declared widths                                                            |
| `BLKSEQ`, `COMBDLY` (Verilator) | a blocking`=` in a clocked block; a delay or non-blocking assignment in a combinational block          | use`<=` in clocked blocks; remove `#` delays from `always @(*)`                                                                        |
| Latch inferred (Yosys)              | a signal is not assigned on every path of a combinational block                                          | "assign every output on every path", for example one unconditional default at the top of the block                                           |
| Combinational loop (Yosys)          | a signal depends on itself with no register                                                              | break the feedback path                                                                                                                      |

**If a reviewer asks:** "S1 (Table S1) lists each class's verification status on real tool output, including where v2
was wrong. Two examples: `COMBDLY` assumes a `#` delay, while Verilator 5 uses the code for `<=` in a combinational
block; `BLKSEQ`'s signal extraction yields a prose word on Verilator 5."

### Q21. Table 1, the v3 rows: what are MISSING_CLOCK, ASYNC_RESET, WIDTH_EXPR and COMB_LOOP?

**Short answer:** Four rules, each added because a real MPSoC log showed v2 wrong or silent. They cover a missing clock
edge, an unmappable asynchronous reset, a truncation of a whole expression, and a loop only Verilator sees.

**In depth** (`src/interpreter/stitch_interpreter_v3.py`):

| Rule              | When it fires                                                                                                                           | What it says                                                                                                                                                              |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MISSING_CLOCK` | fusion (Q19), on`register_4bit` and `register_32bit`                                                                                | "MISSING CLOCK ... EXACT FIX: change that block's header to`always @(posedge clk)`"                                                                                     |
| `ASYNC_RESET`   | Yosys aborts with "Multiple edge sensitive events found for this signal!", which names no signal; v3 reads the source to find the block | "In an edge-triggered block with an asynchronous reset the FIRST if must test ONLY the reset signal", with a corrected template that moves the clear into an`else if`   |
| `WIDTH_EXPR`    | Verilator's width warning on an expression, such as a too-wide concatenation, which v2 dropped                                          | the right-hand expression is G bits but the destination is E, so the top bits are silently dropped; make it exactly E bits, slicing wider operands and sizing the padding |
| `COMB_LOOP`     | Verilator`UNOPTFLAT` when Yosys reports no loop                                                                                       | "Combinational loop ... depends on itself with no register in between"; move the held value into a clocked block, or compute it only from inputs                          |

On `ASYNC_RESET`: the MPSoC's `register_1bit` tests `clr | reset` first.

**If a reviewer asks:** "On the tasks where v2 was silent (the async-reset register and the flit packer), v3 fires the
intended class in 18/18 runs (Result 7, page 12). The rules are in-sample by construction, and Directions (i) asks for
held-out defects."

### Q22. Where does the offline sign-off testbench fit, and why is it drawn outside the loop?

**Short answer:** It scores the RTL the loop returns, after the loop has stopped. It never sends anything back, so no
condition can learn from it.

**In depth:**

- The loop's own testbench drives feedback and decides when to stop. Anything a loop can see, it can also overfit.
- **The two testbenches differ on two tasks only:**
  - on `mem_wb_mux` and `Address_select` the sign-off testbench is specification-complete, while the loop testbench
    missed cases (Result 8, page 13);
  - on the other nine tasks they are identical (Section 9.2, page 10).
- Keeping it offline is what allows the exact re-scoring of the 990 runs that predate it (Q71).

**If a reviewer asks:** "It is a held-out oracle in the usual machine-learning sense: the loop never sees it."

---

## Part E. Section 4, replicated cases (pages 3 to 4; Table 2)

### Q23. How do I read Table 2?

**Short answer:** Each cell shows the outcome and the number of iterations, identical in all three replicates.
"FAIL, 6" means it failed all six iterations; "PASS, 2" means it passed on iteration 2.

**In depth (Table 2, page 4):**

- **On gemma3:4b, in both modules,** `baseline` and `raw_adv` fail all 6 iterations, and `sem_adv` passes in 2.
- **On llama3.1 every condition passes.** On `mux4_oe`, `sem_adv` is faster (2 iterations against 4).
- **The `raw_adv` column is the key control:** it tracks `baseline` exactly. Adding the raw tool text did nothing for
  gemma3:4b; only the interpreted directive helped.

**If a reviewer asks:** "These are two small modules and one mechanism, deliberately. The paper retires the larger
candidates rather than overclaim (page 4)."

### Q24. Explain the input/output asymmetry to a complete beginner, with an everyday analogy.

**Short answer:** Models remember to give every output a value, because a missing output looks unfinished. They
sometimes forget to use an input, because ignoring an input still looks finished. So "forgotten input" defects happen
and can be fixed; "forgotten output" defects rarely happen at all.

**In depth:**

- **An analogy.** You are filling in a form. Every answer box (an output) that is still empty stares at you, and you
  fill it before you hand the form in. A sentence in the instructions you never read (an input) leaves no visible gap.
  The form looks complete, and only someone checking it against the instructions notices.
- **In Verilog:**
  - an output declared and never assigned leaves a dangling declaration, which the model closes as it writes;
  - an input declared and never read leaves code that compiles and looks complete.
- **The data** (page 4; Table S2): on the two modules built to elicit a forgotten output, gemma3:4b assigned every
  declared output unprompted on iteration 1. The interpreter therefore correctly had nothing to fire on
  (`semantic_fired`=0). The forgotten gating input did occur and was fixed.
- **The general lesson:** reachability is a joint property of the tool (can it see the defect?) and of the generator
  (does it make that mistake?). It must be measured per defect class.

**If a reviewer asks:** "It is an observation on two models and hand-built modules, offered as a mechanism that
predicts where a repair layer can act. We do not claim it as a law."

### Q25. What did replication retire, and why report it?

**Short answer:** Three larger candidates that looked like wins or were meant to show scale. Reporting them shows
which single-run results would have been false.

**In depth (page 4; S2):**

- **`datapath_mux_alu`:** llama3.1 passed in 2 of 3 replicates with the interpreter never firing. That is sampling
  variance.
- **`instr_decode_unit`:** gemma3:4b received the correct directive and still failed, falling into a syntax loop the
  interpreter has no vocabulary for. A correct directive does not guarantee recovery.
- **`alu_with_enable`:** too easy after its redesign.
- **Several further candidates** were discarded because the specification gave the answer away, or because the system
  prompt already forced the missing default.

**If a reviewer asks:** "Negative and null results are reported at equal weight. The retirements define the mechanism's
boundary as sharply as the successes define its reach."

### Q26. What are the 255 runs (the Phase 1 in-house benchmark), and what is the "benchmark-premise collapse"?

**Short answer:** 17 (module, model) cells x 5 conditions x 3 replicates = 255 runs, on the group's in-house
benchmark. When re-measured at N=3, many cells did not behave the way their single-run labels said.

**In depth:**

- **The benchmark.** It was built from the conference's 20-module suite and historical single-run labels
  (`phase1/PHASE1_TASK3_ANALYSIS.md`; S2).
- **Table 3 (page 5) gives its cost result:** escalation calls the tools 35 to 45% less often.
- **The collapse.** 4 of its 5 "real-test" cells and 2 of its 3 "enabling" cells did not reproduce the baseline
  behaviour that defined their category (page 4).
- **The lesson.** Benchmark categories built from single runs can encode noise as structure.

**If a reviewer asks:** "This is why the paper moved to RTLLM, an external benchmark, and to tiers computed from
replicated runs."

---

## Part F. Section 5, cost-controlled escalation (pages 4 to 5; Figure 3, Table 3)

### Q27. How does the escalation state machine (Figure 3) work?

**Short answer:** Start as plain baseline. If two failures in a row have the same error, switch to full interpreted
feedback for the rest of the run. The restart variant also starts over once if it stays stuck.

**In depth** (Section 5, page 4; `phase1/escalation_state.py`, a pure, unit-tested class):

1. Each iteration generates RTL and simulates it. A pass stops the run in any state.
2. A failure yields a normalised error signature: the first 5 lines of the log.
3. In the **baseline** state, only the simulation log is fed back.
4. After **N=2** consecutive failures with the same signature, the run switches permanently to **escalated** from the
   next iteration. That state feeds back the log, the tool text and the directives.
5. **Restart variant:** after **M=3** further same-signature failures, one blank-slate prompt discards the current RTL.
   The run stays escalated. The triggering failure is not counted, and the streak then resets (S1).

The state for iteration i is decided from iterations 1 to i-1 only, so the iteration that triggers escalation itself
ran under baseline tooling (S1).

**If a reviewer asks:** "The thresholds N=2 and M=3 were fixed before the RTLLM runs and never tuned on them."

### Q28. Why was the escalation "guarantee" narrowed?

**Short answer:** It was first stated as "escalation can never do worse than baseline". That is only true before the
trigger. After it, escalation is a different policy, and only the data can say whether it helps.

**In depth (Section 5, page 5):**

- **What is guaranteed.** Until the trigger, an escalation run receives exactly the prompts and feedback a baseline
  run receives. So on runs that converge before the trigger, it is the baseline policy.
- **What is not.** Beyond the trigger it diverges, and it may help or hurt.
- **The measurement.** On the Set 1 recoverable band:
  - `sem_escalate_restart` matches baseline (0.0 points, CI -4.6 to +4.6, p=1.000);
  - plain `sem_escalate` trails like always-on interpretation (-4.7, CI -10.7 to 0.0, p=0.148).
- **The record.** v9 corrected every sentence that had stated a structural worst-case guarantee
  (`paper/archive/V9_CHANGES.md`, section F).

**If a reviewer asks:** "We state the guarantee at its true scope and measure the rest. Overstating it would be easy to
refute with the plain-escalation numbers."

### Q29. Why does the restart variant match baseline while plain escalation does not?

**Short answer:** When an escalated run stays stuck, plain escalation keeps editing the same broken RTL. The restart
variant throws it away once and starts fresh, which recovers runs that the always-on feedback had trapped.

**In depth:**

- **Set 1 recoverable band:**
  - plain escalation: 47/150, about as low as `sem_adv` (47/153);
  - restart: 54/151, equal to baseline's 54/153.
- **The difference** is the blank-slate prompt after M=3 further same-signature failures.
- **The likely mechanism.** It is consistent with the derailing behind the always-on deficit: once a small model is
  locked into a bad edit, more feedback on the same RTL does not help, and a restart can.
- **No significance.** The paper does not claim a significant difference between the two escalation variants.

**If a reviewer asks:** "It is an observed difference, with intervals: 0.0 (CI -4.6 to +4.6) against -4.7 (CI -10.7 to
0.0). The paper recommends the restart variant on that basis and does not claim a proven mechanism."

### Q30. What do intervals like "-4.7, CI -10.7 to 0.0" mean? Which statistic is it? What is a p-value, what is a sign-flip test, and why "cell-level"?

**Short answer:** -4.7 is the average, over (model, module) cells, of the difference in pass rate between two
conditions, in percentage points. The CI comes from resampling cells. The p-value comes from randomly flipping the
signs of the cell differences.

**In depth** (S9; `phase3/runner/posthoc_checks.py`, reproduced by `phase2/frontier/stats_set4.py`):

1. **Per cell.** For each (model, module) cell, compute the difference in pass rate, for example `sem_escalate`
   minus `baseline`. With 3 replicates each, a cell's difference is a multiple of 1/3 (33.3 points).
2. **The point estimate.** The mean of those differences over cells: -4.7 points.
3. **The CI, a cell bootstrap.** Resample the cells with replacement 10,000 times, recompute the mean each time, and
   take the 2.5th and 97.5th percentiles: -10.7 to 0.0.
4. **The p-value, a sign-flip test.**
   - If the conditions were equivalent, each cell's difference would be equally likely positive or negative.
   - Flip the signs at random 20,000 times and count how often the mean is at least as far from zero as the observed
     one: p = (1 + count) / 20,001.
   - Here p=0.148: such a result is not rare under "no effect".
   - The random seeds are fixed per label (20260925 plus the CRC of the label), so reruns reproduce byte for byte.
5. **Why cell-level.** The replicates of a cell are correlated (Q6). The cell is the unit that varies independently,
   so it is the unit to resample.

**If a reviewer asks:** "An interval touching zero, together with p=0.148, means no detectable difference at this N. We
say 'trails', and report the interval."

### Q31. How is the tool cost computed? What exactly is counted, and how is it normalised?

**Short answer:** It counts Verilator and Yosys invocations per run (not the simulator), then averages over runs.
For the escalation policies the counts are logged per iteration. For `sem_adv` they are reconstructed exactly from
the runner's gating logic.

**In depth** (`phase2/set1_analysis/_data.py`, function `load_run_cost`):

- **Escalation policies** (`sem_escalate`, `sem_escalate_restart`):
  - the runner `phase2/escalation_runner_hpc.py` writes `run_log.json` with a per-iteration `tool_invocations`
    record;
  - Verilator is counted 1 if the run was in the escalated state that iteration;
  - Yosys is counted 1 if escalated and the code compiled;
  - in the baseline state both are 0;
  - the cost is the sum over iterations.
- **`sem_adv`** (`phase2/stitch_runner_hpc.py`):
  - its `metrics.json` has no per-iteration field;
  - the runner calls Verilator on every iteration when tools are on, so Verilator calls = total iterations;
  - it calls Yosys only when the code compiled, so Yosys calls = total iterations minus compile errors;
  - the comment block above `_warn` documents why this reconstruction is exact.
- **`baseline`:** 0.
- **Normalisation:** the mean over valid runs in the group, a tier or the pool. For example, 4.02 calls per run for
  `sem_adv` on the 54 ceiling runs is 217 calls / 54 runs.
- **Phase 1 (Table 3)** used a rough proxy: Verilator on every iteration with tools on, without itemising the Yosys
  skip on compile failure (`phase1/PHASE1_TASK3_ANALYSIS.md`, section 3).
- **Phase 3** counts "tool rounds" instead, because every candidate is evaluated in every condition. A tool round is
  a model call whose prompt carried tool feedback (`tool_feedback_iters` in `phase3/runner/stitch_runner_p3.py`).

**If a reviewer asks:** "Tool calls measure the heavyweight external processes the loop spawns. Tokens are a separate
axis and are reported beside them. Escalation saves tool calls and can spend tokens (Q33)."

### Q32. Why is escalation at about 1.00 call per run on ceiling modules?

**Short answer:** It is an average. 44 of the 54 ceiling runs passed before escalating and made no tool call. The 10
that got stuck made 3 to 10 calls each, for 54 calls in all, so the mean comes to exactly 1.00.

**In depth** (`phase2/set1_analysis/ceiling_tool_call_distribution.txt`, generated with `load_run_cost`):

| Condition                | Runs | Calls | Mean | Runs by calls                                                                                        |
| ------------------------ | ---- | ----- | ---- | ---------------------------------------------------------------------------------------------------- |
| `sem_adv`              | 54   | 217   | 4.02 | 29 runs at 2 (a pass on iteration 1 still costs one Verilator and one Yosys call); the rest up to 12 |
| `sem_escalate`         | 54   | 54    | 1.00 | 44 at 0; 3 at 3, 3 at 5, 2 at 6, 1 at 8, 1 at 10                                                     |
| `sem_escalate_restart` | 54   | 84    | 1.56 | 42 at 0                                                                                              |

The cut against always-on interpretation is 75.1% (Figure 4b, page 6).

**If a reviewer asks:** "The 1.00 is a mean, not a per-run cost. Escalation is free on runs that never get stuck, which
is most runs on easy modules."

### Q33. Why can tokens rise while tool calls fall?

**Short answer:** Escalation saves tool calls by not running the tools until a run is stuck. A stuck run that escalates
then uses extra iterations (budget 8 rather than 6), and each iteration costs tokens.

**In depth (page 5; Table 3):**

- On the in-house benchmark, `sem_escalate` uses 5,151 tokens per run against `sem_adv`'s 4,883, while its tool calls
  fall from 2.37 to 1.53.
- The two costs are separate axes: tokens are model input and output; tool calls are external processes.
- The paper scopes every efficiency claim to the tool-call axis, and keeps the token column visible.

**If a reviewer asks:** "We do not claim token savings for escalation on RTLLM. In Phase 3, where every condition has
6 calls, v3 does need about 23% fewer calls and tokens than raw text (Result 3)."

### Q34. Why does the tool-call saving grow with model capability (16.6 to 27.6 to 88.6%)?

**Short answer:** Escalation only pays for tools when a run gets stuck. Stronger models get stuck less often, so more
of their runs never trigger, and the saving against always-on interpretation grows.

**In depth (Sections 8.1 to 8.3, pages 6 to 7):**

| Models        | Tier        | Saving | Calls per run |
| ------------- | ----------- | ------ | ------------- |
| small (Set 1) | recoverable | 16.6%  | 6.74 to 5.62  |
| large (Set 3) | recoverable | 27.6%  | 5.31 to 3.85  |
| API (Set 4)   | recoverable | 88.6%  | 2.29 to 0.26  |

- **Set 4:** escalation rarely triggers, because the API models are near ceiling.
- **The same logic** explains the tier gradient within Set 1: 75.1% on ceilings, 16.6% on the recoverable band, 10.1%
  on floors, where runs get stuck most.

**If a reviewer asks:** "It is a mechanical count, not a statistical claim. It follows directly from the trigger
design and holds at every rung measured."

### Q35. What does "Table 3" show, and why is escalation bold there?

**Short answer:** Cost per run on the 255 in-house runs. The escalation rows are bold because they have the fewest
heavyweight tool calls.

**In depth (Table 3, page 5):**

| Condition           | Tokens per run | Tool calls per run |
| ------------------- | -------------- | ------------------ |
| `baseline`        | 4,891          | 0.00               |
| `raw_adv`         | 5,354          | 2.61               |
| `sem_adv`         | 4,883          | 2.37               |
| `sem_escalate`    | 5,151          | **1.53**     |
| `sem_esc_restart` | 4,719          | **1.37**     |

The pass rate matched or exceeded always-on interpretation and raw text (page 5; `phase1/PHASE1_FINDINGS.md`).

**If a reviewer asks:** "The bold marks the column the claim is about, tool calls, and the token column sits beside it
so the trade-off stays visible."

### Q36. Why 8 iterations for escalation on RTLLM and 6 for baseline? Is that justified?

**Short answer:**

- **The reason:** the 8-iteration cap came from the original escalation specification (Phase 1). It gives an escalated
  run room to use its directives after its baseline probes.
- **The disclosure:** the paper states it, and an equal-cap check at 6 changes no conclusion.
- **Phase 3:** every condition had one budget of 6 calls.

**In depth:**

- **The two caps.** `baseline` and `sem_adv` were capped at 6 iterations, the cap of the locked conference
  configuration. The escalation policies ran at Pass@8, per the original Task 1 specification. Phase 1 flags this as
  "not cap-equivalent" (`phase1/PHASE1_TASK3_ANALYSIS.md`).
- **The equal-cap check** (Section 7, page 5; S5):
  - on the Set 1 recoverable band, one `sem_escalate` pass and one `sem_escalate_restart` pass arrived only in
    iteration 7 or 8, so at a cap of 6 they would be 46/150 and 53/151;
  - none did in Set 3;
  - at an equal cap of 6, `sem_esc_restart` is 53/151 (35.1%) against baseline's 54/153 (35.3%);
  - no Set 1 or Set 3 conclusion changes.
- **Phase 3 removed the asymmetry entirely:** one shared budget of 6 model calls for every condition (page 10).

**If a reviewer asks:** "The unequal cap is disclosed and checked. The case study, which carries the paper's main
claims, uses one equal budget for all conditions."

---

## Part G. Section 6, harness hardening (page 5)

### Q37. What exactly was hardened (defects A, B and C)? How were they found and verified, and why do they matter for the whole field?

**Short answer:** Three silent bugs in the shared runner:

- **A:** the simulator had no working directory;
- **B:** broken code-fence extraction;
- **C:** the wrong pass string.

Each produced plausible but wrong numbers. All three were fixed and verified, and pass detection now lives in one
registry with no defaults.

**In depth (Section 6, page 5; S3; `docs/archive/IMP_PHASE2_RUNNER_HARDENING_REPORT.md`):**

- **A. Simulator working directory.**
  - The simulator ran without its working directory set, so a testbench loading data with `$readmemh` could never
    find its file. Every file-I/O design failed, whatever its logic.
  - Fixed by running in the iteration's directory. It was confirmed not to affect the conference benchmark.
- **B. Unclosed code fence.**
  - When a model left a markdown code fence open, the opening marker stayed in the extracted code.
  - An audit found 58 of 659 generated files (8.8%) corrupted.
- **C. Pass string.**
  - The check looked for `"PASS"` or `"ALL TESTS PASSED"`, but RTLLM testbenches print `"Your Design Passed"`.
  - **Found** because a near-trivial module (`counter_12`) scored 0/3.
  - **Scale:** a re-scan of 64 completed runs found 20 (31%) misclassified as failures.
  - **Damage:** those runs then spent their remaining iterations changing correct code.
- **Verification.**
  - Each fix was checked against golden references before and after.
  - The pass-detection registry was regression-verified on 64 manually adjudicated cells.
  - Before any cluster run, a gate requires 44/44 golden designs to pass.
- **Why it matters for the field.** All three are one fragility: an assumption about a benchmark's output format,
  buried in shared code. A 31% silent misclassification can invert a published comparison.

**If a reviewer asks:** "We report the defects because any RTL-repair harness can carry them. The registry design (one
function, a required benchmark argument, no default) makes the class fail loudly."

### Q38. What is `detect_outcome`, and why "no default"?

**Short answer:** The single function every runner uses to decide pass or fail from a simulation log. The benchmark
must be named explicitly, so a new benchmark cannot silently inherit the wrong pass string.

**In depth:**

- `detect_outcome(log, benchmark)` (`src/interpreter/pass_detection.py`) looks up the benchmark's pass and fail
  patterns in a registry and returns PASS, FAIL or UNKNOWN.
- The `benchmark` argument is required. An unregistered benchmark fails at import.
- UNKNOWN is never treated as a pass. It is surfaced.

**If a reviewer asks:** "The design turns a silent misclassification into a loud error, which is the right failure
mode for evaluation code."

---

## Part H. Section 7, study design and the twin (pages 5 to 6)

### Q39. Which sets did we run, and what is each for?

**Short answer:**

- **Set 2 (Twin):** model comparison and the tiers.
- **Set 1:** STITCH on small models.
- **Set 3:** STITCH on large models.
- **Sets 4 and 4b:** API models on the recoverable band and the floor.
- **Set 4c:** a reasoning model, closed without results.
- **Phase 3:** the MPSoC.

**In depth (Section 7, page 5):**

| Set      | Question                                                  | Models                                                         | Conditions | Modules        | N / T           | Runs      |
| -------- | --------------------------------------------------------- | -------------------------------------------------------------- | ---------- | -------------- | --------------- | --------- |
| 2 (Twin) | does RTL fine-tuning help; where are the tiers            | RTLCoder (2 prompts), deepseek-coder:6.7b, gemma3:4b, llama3.1 | baseline   | 42             | 3 / 0.5         | 630       |
| 1        | where does always-on interpretation stand on small models | gemma3:4b, llama3.1:8b, deepseek-coder:6.7b                    | 4          | 42             | 3 / 0.1         | 1,512     |
| 3        | does the picture change on larger models                  | qwen2.5-coder:14b and 32b, gemma3:27b                          | 4          | 17 recoverable | 3 / 0.1         | 612       |
| 4        | API models, recoverable band                              | GPT-4.1 mini, Gemini 2.5 Flash, Claude Haiku 4.5               | 4          | 17             | 3 / 0.1         | 612       |
| 4b       | API models, floor                                         | the same three                                                 | 4          | 19 floor       | 3 / 0.1         | 599 valid |
| 4c       | a reasoning model on the residual floor                   | Gemini 2.5 Pro                                                 | 2          | 3              | closed at run 1 | 0 results |

The "4 conditions" are `baseline`, `sem_adv`, `sem_escalate` and `sem_escalate_restart`. Set 4c's two conditions are
`baseline` and `sem_escalate_restart`.

Phase 3 is separate: 1,386 cluster runs plus 3 x 198 API runs (Section 9.2, page 10).

**If a reviewer asks:** "Set 3 runs only the recoverable band because Set 1 showed all conditions coincide on ceilings
and floors, so larger models would buy no discriminating power there."

### Q40. Why were RTLLM designs excluded? What is a "weak oracle"?

**Short answer:** 6 of 50 designs were incompatible with the Icarus flow, one of them because of a defect in RTLLM's
own reference. Two more were dropped because their testbenches pass a design whose outputs are stuck at 0. A testbench
that accepts a do-nothing design is a weak oracle.

**In depth (page 5; S4):**

- A compatibility screen kept 44 of 50 designs. Each exclusion has a documented cause
  (`phase1/rtllm_task_a_screen.py`).
- **`edge_detect` and `square_wave`** pass with every output stuck at a constant. Their check logic never fails such
  a design, so a model that writes nothing useful would "pass". They were excluded before the runs, leaving 42
  modules.
- This mirrors RTLLM's own exclusion of designs with defective references.
- **Why this matters for this paper:** a weak oracle rewards doing nothing. The same concern, at a higher level,
  motivated the sign-off testbench in Phase 3.

**If a reviewer asks:** "The exclusions were made before the confirmatory runs, are listed by name, and follow RTLLM's
own precedent."

### Q41. What are the ceiling, recoverable and floor tiers? Is defining them from the twin run circular?

**Short answer:** Tiers sort modules by how hard they were for the twin run's models: ceiling (easy), recoverable
(sometimes solved), floor (almost never solved). It is not circular. The tiers use only baseline runs from a different
set, fixed before the STITCH runs.

**In depth:**

- **Definition** (page 5): a module's maximum baseline pass rate across the five twin model-conditions:

  - ceiling, 80% or more: 6 modules;
  - recoverable, 20 to 80%: 17 modules;
  - floor, under 20%: 19 modules.

  Computed once by `phase2/twin_analysis_SET2/categorize.py` into `module_categories.json`, and reused verbatim.
- **Why tiers.** An effect can only show where baseline sometimes fails and could recover. Pooled over 42 modules,
  the four Set 1 conditions differ by at most 1.6 points (page 6).
- **Why it is not circular:**

  1. no STITCH condition enters the definition;
  2. it comes from a different run (T=0.5) and different model-conditions than the sets it organises;
  3. it was fixed before Sets 1, 3 and 4 ran;
  4. it chooses where an effect can be measured, never its direction.

**If a reviewer asks:** "Ceilings and floors are still reported (Figure 4a): all conditions coincide there, as
expected. The tiers move no data out of view."

### Q42. Why T=0.5 for the twin and T=0.1 elsewhere, and what does that mean for comparisons?

**Short answer:** The twin compares models, so it used one temperature matched across all five model-conditions. The
other sets compare conditions, at the conference's T=0.1. Rates from the two temperatures can be ranked, but not
compared directly.

**In depth:**

- **A higher temperature** makes outputs more varied, which can raise or lower pass rates.
- **Within each set** the temperature is fixed, so every comparison inside a set is fair.
- **Across sets,** Figure 5a (page 7) mixes twin bars (T=0.5) with Set 3 and API bars (T=0.1). The caption says the
  ladder is "ordinal across shades": the order is meaningful, the exact gaps are not.

**If a reviewer asks:** "No conclusion depends on comparing a T=0.5 rate with a T=0.1 rate. The ladder only places the
models on a rough capability axis."

### Q43. What is the "prompt effect" (native against shared prompt), and what did it show?

**Short answer:** RTLCoder was run with its own stub-completion prompt (native) and with the harness's chat prompt
(shared), so prompt format is measured rather than confounded. The effect is modest and inconsistent.

**In depth (page 5; Figure S1b):**

- **Native against shared, on the 17 recoverable modules:** native wins 3, shared wins 2, and 12 tie.
- **In total:** native passes 29/51 against shared's 21/51.
- **Native is better aligned** with how RTLCoder was trained, which helps on some modules.
- **The fine-tuning comparison still holds:** at native it is a wash against the base model (5 wins, 6 ties, 6
  losses), and at shared it is 0 wins, 13 ties, 4 losses.

**If a reviewer asks:** "We report both prompts so the negative fine-tuning result cannot be blamed on prompt format."

### Q44. What are the supplementary materials S1 to S9? A one-line summary of each, and when to read it.

**Short answer:** Nine sections holding the details the 15-page paper cannot.

**In depth** (`paper/overleaf/supplement.pdf`):

| Section | Contents                                                                                                        | Read it when                                     |
| ------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| S1      | interpreter classes and verification status (Table S1), the v3 layer, the exact conditions and escalation rules | you need the precise rules or a class's limits   |
| S2      | replication details: the reachability table and the retirements                                                 | a reviewer questions the illustrations           |
| S3      | the three harness defects in full                                                                               | you implement or audit a harness                 |
| S4      | the RTLLM pool, the pilot, the twin design and its verdict (Figure S1)                                          | you question the tiers or the fine-tuning result |
| S5      | Sets 1 and 3: timeouts, the iteration budget, the per-tier tables, the replicate trace, contrasts               | you check the RTLLM numbers                      |
| S6      | the API study: design, deviations, every Set 4 and 4b table, and the Haiku projection                           | you check API numbers or the projection          |
| S7      | `freq_divbyfrac`: the specification text, the testbench lines, the reference trace, every candidate           | you question the floor case                      |
| S8      | the MPSoC case study in full: substrate, v3, every Phase 3 table, the equivalence audit, the ladder             | you check any Section 9 number                   |
| S9      | statistics and reproducibility                                                                                  | you rerun or audit a contrast                    |

**If a reviewer asks:** "Every number in the supplement comes from a generated evidence file listed in `REPO_INDEX.md`."

---

## Part I. Section 8, STITCH at RTLLM scale (pages 6 to 9)

### Q45. What does Set 1 show (Figure 4a), and why are the pooled numbers flat?

**Short answer:** Pooled over all 42 modules the four conditions differ by at most 1.6 points, because 25 of the
modules are ceilings or floors where nothing can change. Split by tier, a small, non-significant deficit for always-on
interpretation appears on the recoverable band, and escalation with restart matches baseline.

**In depth (Section 8.1, page 6; Figure 4a; Table S3):**

- **Pooled pass rates:** 28.8% (baseline), 27.2% (`sem_adv`), 27.7% (`sem_escalate`), 28.8%
  (`sem_escalate_restart`).
- **Recoverable band:**
  - `sem_adv`: 47/153 against baseline's 54/153. Worse in 7 of 51 cells, better in 3, equal in 41; CI -10.5 to +0.7,
    p=0.199.
  - `sem_escalate_restart`: 54/151, matching baseline.
  - `sem_escalate`: 47/150.
- **Ceilings** coincide at 80 to 85%, and **floors** at 6 to 7%.

**If a reviewer asks:** "The deficit is consistent in direction with the conference's harmful regime, but it is not
significant at N=3, is not uniform across models, and is not separable from raw tool text, which Set 1 did not run.
The paper says all three things."

### Q46. What does Figure 4b show?

**Short answer:** Verilator and Yosys calls per run, by tier. Escalation saves most on easy modules (75.1%) and least on
hard ones (10.1%), because it only spends when a run is stuck.

**In depth (page 6; Table S4):**

| Tier        | `sem_adv` calls per run | `sem_escalate` calls per run | Cut   |
| ----------- | ------------------------- | ------------------------------ | ----- |
| ceiling     | 4.02                      | 1.00                           | 75.1% |
| recoverable | 6.74                      | 5.62                           | 16.6% |
| floor       | 7.28                      | 6.54                           | 10.1% |
| pooled      |                           |                                | 18.5% |

For how the counts are computed, see Q31 and Q32.

**If a reviewer asks:** "The gradient follows from the two-strike trigger: easy modules rarely trigger it, and hard ones
trigger it on most runs."

### Q47. Set 3: why is the "escalation lead" on larger models not a mechanism?

**Short answer:** Escalation scored 90/153 against baseline's 86/153, but almost all of its passes came before it ever
escalated. The two escalated runs that passed had the interpreter silent. The lead is resampling noise.

**In depth (Section 8.2, pages 6 to 7; S5):**

- **The replicate trace.** Of 153 `sem_escalate` runs:
  - 88 passed without escalating;
  - 65 escalated, and only 2 of those passed, both with `semantic_fired`=0, rescued by raw tool feedback.
- **The pooled lead** (+4 runs) comes from six cells gaining seven runs in total, against three cells losing one each.
- **No contrast differs from baseline:**
  - `sem_adv`: -0.7, CI -7.8 to +6.5;
  - `sem_escalate`: +2.6, CI -1.3 to +7.2;
  - `sem_escalate_restart`: +2.0, CI -2.6 to +7.2;
  - all p 0.40 or higher.
- **The withdrawn reading.** An early reading, "escalation wins outright on large models", was withdrawn after this
  trace.

**If a reviewer asks:** "This is the `semantic_fired` discipline at work: a pooled edge without a fired mechanism is not
credited to the interpreter."

### Q48. What does Figure 5a (the capability ladder) show?

**Short answer:** The baseline pass rate on the 17 recoverable modules for every model, from gemma3:4b at the bottom to
the three API models at the top. It places each model on a rough capability axis.

**In depth (page 7):**

- **Hatched light-grey bars** are twin runs (T=0.5). **Grey bars** are Set 3 (T=0.1). **Dark bars** are the API models
  (T=0.1).
- Because the temperatures differ, the ladder is ordinal across shades: the order means something, the exact gaps do
  not.
- **The extremes:** gemma3:4b (shared prompt) is at 4/51; the API models are at 50/51 or 51/51 (`set4_analysis.json`).
- **Error bars** are Wilson intervals.

**If a reviewer asks:** "The ladder is scaffolding, not a finding. Larger models passing more is expected. It locates
each model for Figure 5b."

### Q49. Figure 5b: does it mean STITCH was only useful on gemma3:27b? Why are most bars negative, and what does "minus baseline" mean?

**Short answer:** No. Each bar is always-on interpretation (`sem_adv`) minus `baseline`, in percentage points, on
RTLLM's recoverable band. A negative bar means slightly below baseline. Every interval crosses zero, so no model,
gemma3:27b's +7.8 included, shows a detectable effect either way. And RTLLM measures functional passes, not the
structural defects STITCH targets.

**In depth (page 7):**

- **The values:**

| Model               | `sem_adv` minus baseline (points) |
| ------------------- | ----------------------------------- |
| gemma3:4b           | -7.8                                |
| llama3.1:8b         | -5.9                                |
| deepseek-coder:6.7b | 0.0                                 |
| gemma3:27b          | +7.8                                |
| qwen2.5-coder:14b   | -3.9                                |
| qwen2.5-coder:32b   | -5.9                                |
| GPT-4.1 mini        | -2.0                                |
| Gemini 2.5 Flash    | 0.0                                 |
| Claude Haiku 4.5    | 0.0                                 |

  Error bars are Newcombe 95% intervals for a difference of two proportions.

- **Why most bars are negative.** Always-on interpretation intervenes even when nothing is wrong yet, which can derail
  a converging run. That is the conference's harmful regime, here small and not significant.
- **Why gemma3:27b is positive.** Its gain sits in `freq_div` and `freq_divbyeven`, where it repeats a
  declaration-style error under terse feedback. It finds the fix under `sem_adv`'s longer, labelled template, with no
  interpreted directive firing in the winning run (`docs/reSTITCH.md`, Part 8). It is a feedback-format effect, not
  the interpreter's mechanism.
- **Where usefulness is actually measured.**
  - Escalation, not always-on interpretation, is the recommended design.
  - Phase 3 measures what STITCH was built for: structural defects and sign-off.

**If a reviewer asks:** "Figure 5b's message is that the always-on deficit is small, not monotonic in size, and never
significant. It is not where STITCH's value is claimed."

### Q50. What can we infer from the RTLLM results exactly? Is STITCH useful there?

**Short answer:** The simple version: on RTLLM, STITCH neither helps nor hurts pass rates detectably, and escalation saves tool
calls, more so for stronger models. RTLLM checks function, not structure, so it cannot show STITCH's main value.

**In depth (the detailed version: Section 8.5's six claims, pages 8 to 9):**

1. **The mechanism generalises to a per-tier prediction:** the interpreter acts where it can reach a real defect and
   stays silent elsewhere.
2. **Always-on interpretation trails baseline by about four points** on small models: consistent in direction, not
   significant, and not separable from raw text.
3. **Escalation is the baseline policy** on every run that converges before its trigger. Beyond it, only the restart
   variant matches baseline on small models. On large and API models every condition matches baseline within noise.
4. **The deficit is a small-model effect** at group level, and not monotonic per model.
5. **The tool-call cut is tier-shaped and grows with capability:** 16.6, 27.6 and 88.6%.
6. **The floor is mostly beyond small open models,** not beyond the tools.

Why RTLLM cannot show more: on the recoverable band the interpreter had something to say in only about a third of
always-on runs (52 of 153 in Set 1). The defects STITCH targets pass the testbench and break synthesis.

**If a reviewer asks:** "We report RTLLM as a null-to-small result for pass rate and a clear result for cost. The
positive claims are made on the MPSoC, where the defects are structural."

### Q51. Why are the API models at ceiling? What is training contamination? Why was Kimi dropped? What happened to the reasoning run (Set 4c)?

**Short answer:**

- **Ceiling:** the recoverable band is easy for current commercial models.
- **Contamination:** RTLLM is public, so these models may have seen it in training.
- **Kimi:** it emitted a reasoning token in its smoke test, which the protocol forbids.
- **Set 4c:** the reasoning model overflowed its thinking budget on run 1, and the stop rule closed it.

**In depth (Section 8.3, pages 7 to 8; S6):**

- **Ceiling.** Pooled pass rates are 99.3, 98.7, 98.0 and 98.0%. Gemini and Haiku pass every run. The comparison of
  conditions rests on GPT-4.1 mini alone (differences -2.0, -3.9 and -3.9 points, all on one module, every p=1.000).
- **Training contamination.** A model trained on public text after 2024 may have seen RTLLM's designs and testbenches.
  That can inflate absolute pass rates. It does not affect comparisons between conditions within one model.
- **Kimi K2.6.** Its smoke test returned `reasoning_tokens`=1. Any reasoning token stops a provider under the
  pre-registration, so it was dropped by decision. A third ceiling model at a forced T=0.6 would add no information.
- **Set 4c (Gemini 2.5 Pro).** On the residual floor modules, its pre-registered stop rule fired on run 1: 10,237
  thinking tokens against a 2,048 budget, with the answer cut off (`phase2/frontier/PENDING.md`, section 1b). It was
  closed with 0 of 18 runs and no results (Amendment 5).
- **One more disclosure.** OpenAI's serving fingerprint changed during the run (256 and 7 calls) for the same pinned
  snapshot.

**If a reviewer asks:** "The API rows are disclosed as non-reasoning models with every call logged. Reasoning models
are listed as a direction (iv), because our budgeted protocol could not run them."

### Q52. What did the API study cost (INR), and what is "INR per passing module"?

**Short answer:** About $13.70 (INR 1,552) across all API work. On the recoverable band, each passing run cost INR 0.11
to 0.51, depending on model and condition.

**In depth:**

- **Exchange rate:** INR = USD x 96 x 1.18 (18% GST).
- **Totals** (`phase2/frontier/evidence/spend_summary.txt`):

| Batch                                           | USD             | INR               |
| ----------------------------------------------- | --------------- | ----------------- |
| Set 4                                           | 1.59            | 180.2             |
| Set 4b                                          | 8.05            | 912.2             |
| Completion runs and the Phase 3 API ladder rows | 3.89            | 440.4             |
| Set 4c                                          | 0.17            | 19.5              |
| **Total**                                 | **13.70** | **1,552.3** |

  By provider: Anthropic $6.69, Google $4.72, OpenAI $2.29, Moonshot $0.0004.

- **"INR per passing module"** (`inr_per_pass` in `phase2/frontier/analysis_set4.py`): a model-condition's total spend
  in INR divided by its number of passing runs. For example, GPT-4.1 mini at baseline: $0.0503 x 113.28 / 50 passes =
  INR 0.114 (Table S10).

**If a reviewer asks:** "The cost is reported to show that a full replicated API study of this kind is affordable. No
cost claim about STITCH depends on API prices."

### Q53. What is the heat map (Figure 6)? What are modules like freq_divbyfrac? What do the numbers, daggers and hatching mean? Why are some values decimals?

**Short answer:**

- **What it shows:** each cell is how many of 3 baseline runs passed, for one floor module (column) and one API model
  (row).
- **Daggers and hatching** mark Claude Haiku 4.5's projected values: the modules it did not run.
- **Decimals:** those projections are expected counts, not observed ones.

**In depth (page 8):**

- **The floor modules** are the 19 RTLLM designs that the twin run's models almost never passed (under 20%). They
  include adders, an ALU, FIFOs (`LIFObuffer`), a traffic light, serial converters, and clock dividers such as
  `freq_divbyfrac` (Q55).
- **Columns** are ordered by GPT-4.1 mini plus Gemini 2.5 Flash passes. Dark means 3 of 3; light means 0.
- **The reading:** most modules the open models could not pass are passed by at least one API model (16 of 19), and
  three stay at the floor for every model.
- **Daggers and hatching.** Haiku is measured on 12 of 19 modules. Its 7 missing modules are projected:

  1. take the mean rate of the other two models on that cell;
  2. shift it by Haiku's average logit difference from them on the cells all three ran (+0.72);
  3. multiply by 3 to get an expected pass count, for example 2.4.

  Those cells are italic, carry a dagger and are hatched. The caption says "values marked † are projections, to be
  replaced". The method is in S6 (Table S15) and `paper/V10_CHANGES.md`, section 6.
- **Observed conclusions use measured runs only.**

**If a reviewer asks:** "The projection is marked everywhere it appears, is used only where a trend needs a complete
column, and can be removed with one command (`make_numbers_set4.py --no-projection`). Under `\finaltrue` the paper will
not compile if one remains."

### Q54. What does "no pass is attributable to the interpreter" mean on the floor?

**Short answer:** On the hard modules where API models still fail, the interpreter does produce directives. But when
we trace every pass that followed a directive, none can be credited to it.

**In depth (page 8; S6, Table S13):**

- **The interpreter fires** in 55% (103/188) of failing tool-condition runs.
- **Only 3 passes** followed a directive in a cell whose baseline was 0/3. They fall in two cells:
  - in one, the same gain appears in runs that received no directive;
  - in the other, the directive was followed by several compile-error iterations before the pass.
- **No condition contrast is significant:** the smallest p is 0.062, of 12 contrasts.

**If a reviewer asks:** "Firing is not fixing. We credit a pass only when the directive plausibly caused it, and on the
floor none qualifies."

### Q55. freq_divbyfrac in depth: what is a fractional clock divider, what is double-edge clocking, and what did we find?

**Short answer:**

- **The module:** a divider that produces a clock 3.5 times slower than its input. A half-cycle period needs both
  clock edges.
- **The failure:** every API model failed it, with roughly twice the specified period.
- **The cause:** the reference counter wraps every 14 half steps, while the specification says 7. That is a
  specification-wording mismatch (our reading), not a testbench defect.

**In depth (Section 8.4, page 8; S7; `phase2/frontier/FREQ_DIVBYFRAC_AUDIT.md`):**

- **A clock divider** turns a fast clock into a slower one. Dividing by 3.5 means one output period lasts 3.5 input
  periods, which is 7 half periods. The specification asks for the output to be high for 3 half steps and low for 4.
- **Double-edge clocking.** A design that only acts on rising edges can only make whole-period steps. To get a
  half-period step, the reference makes one pulse on the rising edge and one adjusted pulse on the falling edge, and
  combines them.
- **What we found.**
  - The reference passes its testbench, and the testbench's expected waveform (`11100001110000111000`) matches the
    "3 high, 4 low" sentence.
  - Running all 36 final candidates through the original testbench: 34 compile, none matches, and none is a
    phase-shifted copy of the expected waveform.
  - Most have about twice the period (typical traces "H6 L7 H7"), and 32 fail first at check 3.
  - Simulating the reference with its counter exposed: the counter advances once per rising edge, so it wraps every
    14 half steps, with two output periods per wrap.
  - The specification says the counter "cycles through 7 half clock steps".
- **The statement:** not a testbench defect; the specification's own description of the counter does not match its
  reference design (our reading); the models fail on period and duty cycle, roughly doubling the period.
- **A minor robustness weakness, not the cause:** the testbench releases reset in the same time step as a clock edge.
  No candidate fails by a phase offset, so this did not cause the failures.

**If a reviewer asks:** "We state the specification mismatch as our reading, give every trace in S7, and list
specification-level robustness as direction (v): an interpreter cannot see a specification defect."

### Q56. What do the Set 4b disclosures mean for the conclusions?

**Short answer:** Haiku is incomplete, so every floor conclusion uses each model's completed runs, and the
"fails everywhere" test uses only the modules all three models ran.

**In depth (page 8):**

- **Haiku:** 143/228 runs. 85 failed on an exhausted account credit, cost nothing, and are excluded.
- **The fails-everywhere test** uses the 12 modules every model ran. Only `freq_divbyfrac` fails in all 36 runs.
- **The Q1 count** "8† of 19 at ceiling for all three" uses the projection and is marked. The observed count is 4 of
  the 12 modules all three ran.

**If a reviewer asks:** "The completion procedure is documented (`phase2/frontier/PENDING.md`). Re-running the
generator replaces every projection with the measured value."

---

## Part J. Section 9, the MPSoC case study (pages 9 to 13)

### Q57. Explain the MPSoC case study from zero. What are an MPSoC, a RISC-V core, a NoC, a mesh and a router?

**Short answer:** We took a real multiprocessor chip design that already contained the kind of defects STITCH
targets. We asked models to repair its defective parts, then put the repaired parts back and checked that the whole
chip could be built.

**In depth (Section 9.1, page 9; `phase3/docs/PHASE3_EXPLAINED.md`):**

- **A RISC-V core** is a processor that follows the open RISC-V instruction set. This one is a 32-bit (RV32) core with
  a five-stage pipeline (fetch, decode, execute, memory, write-back), like an assembly line. Forwarding multiplexers
  such as `mux3` pick the freshest copy of a value still in the pipeline.
- **An MPSoC** (multi-processor system-on-chip) puts several processors and memories on one chip.
- **A NoC** (network-on-chip) is a road network etched into the chip, so the processors can exchange packets without
  a shared bus becoming a traffic jam:
  - a **router** is a crossroads: it receives packets on its ports (north, south, east, west, local) and forwards each
    one toward its destination (XY routing), one at a time per output (round-robin arbitration);
  - **virtual channels** are extra lanes, so one stuck packet does not block the rest;
  - a **mesh** is the grid of routers: 2x2 has 4 routers, 3x3 has 9;
  - the **network interface** chops messages into flits (flow-control units) and reassembles them.
- **This design** was developed within our group, independently of this study: a five-stage RV32 core, a network
  interface, and a virtual-channel wormhole mesh router.
- **Why it matters.** The design already contains latches and an unmappable reset that simulate correctly, which is
  exactly what a simulation-only loop cannot see.

**If a reviewer asks:** "It is one design from one group. It was chosen because its defects were already there, not
seeded, and it is an external design in the sense that it was not written for this study."

### Q58. What did the source repository (p20230031/RISC-V) contain, what was sanitised, and why?

**Short answer:** The core, the router (as a 2x2 mesh), the network interface, a top module, and a 3x3 mesh built from
the same router pieces. Only compile-level problems that the open-source tools reject were fixed; no logic defect was
touched.

**In depth (`phase3/designs/SANITISATION.md`; S8.1):**

- **Contents:**

  - `processor/`: the core;
  - `router/`: a 2x2 mesh;
  - `NI/`: the network interface;
  - a top `main.v` connecting one core, one network interface, the mesh and a depacketiser;
  - an `Automation Code` folder with a 3x3 mesh that shares 28 of its 33 router leaf files.
- **What was sanitised.** Vivado, where the design was written, accepts constructs the open-source flow rejects:

  - nested comments;
  - wires declared twice;
  - module instances with an implicit trailing port, reproduced with identical binding.

  These were fixed, and each change is listed.
- **Why.** Without the fixes, Icarus, Verilator and Yosys could not read the design at all. The defects under study
  (latches, the reset) were left exactly as written.
- **A related observation.** At the `main` top, the network is optimised away because its outputs do not reach a chip
  pin. That is why the network is measured on the mesh tops directly.

**If a reviewer asks:** "Sanitisation is compile-level only and fully listed. The 63 latch inferences and the synthesis
abort are the design's own."

### Q59. How were the 11 tasks extracted (8 real leaves, 3 seeded)? What does "sim-silent" mean?

**Short answer:** Eight defective leaf modules were taken from the real design, and three more were written to cover
defect classes the design lacked. Six of the eleven are "sim-silent": the defective input already passes its loop
testbench.

**In depth (Section 9.2, page 10; Table 4):**

- **Real leaves (R):**
  - `MuxPC`, `execute_mux`, `mux3`, `mem_wb_mux`: latches;
  - `register_1bit`: an unmappable async reset;
  - `Address_select`: a latch and a width-mismatched port;
  - `register_32bit`, `register_4bit`: a missing clock edge.
- **Seeded (S):**
  - `riscv_alu_flags`: latches on the ALU flags;
  - `noc_xbar4`: a multi-driven output;
  - `ni_flit_pack`: width truncation.
- **Each task** has `input.v` (the defect), `spec.md` (purely behavioural), the loop testbench `tb.v`, the sign-off
  testbench `tb_signoff.v`, and `golden.v` (a correct fix, never shown to the model).
- **Why the specifications are behavioural.** A pilot with hint-bearing specifications let an 8B model fix every
  defect on its first call under every condition, so the hints were removed.
- **Sim-silent:** the defect does not show in simulation, because the testbench only drives the intended inputs.
  `mux3`'s specification declares `sel` = 11 unused, so its 32 latched bits are invisible to the test.

**If a reviewer asks:** "The seeded tasks are labelled S in Table 4. Results are reported by stratum (sim-silent and
sim-visible), and the like-for-like comparison with simulation-only repair is the sim-visible stratum."

### Q60. How were the runs done?

**Short answer:** Six local models from 3B to 14B, five conditions, 11 tasks, 3 replicates: 990 runs on the cluster.
Then a pre-registered final batch: the control arm and a 32B model, 396 runs. Three API models ran the same runner as
ladder rows.

**In depth (pages 10 and 13; `docs/HPC_GUIDE.md`):**

- **Models:** llama3.2:3b, gemma3:4b, deepseek-coder:6.7b, qwen2.5-coder:7b, llama3.1:8b and qwen2.5-coder:14b. N=3,
  T=0.1, served by Ollama on an H200 NVL node.
- **The runner** (`phase3/runner/stitch_runner_p3.py`):
  - evaluates the defective input first (iteration 0);
  - then gives up to 6 model calls;
  - evaluates every candidate with simulation, lint and synthesis;
  - feeds back according to the condition;
  - stops at a clean pass (`baseline`: at a simulation pass).
- **Before any GPU time,** a gate job ran interpreter tests on frozen real logs, task validation with a live drift
  check, a mock end-to-end run and a dry run.
- **Final batch:** pre-registered and frozen before its runs.
- **Ladder rows:** GPT-4.1 mini, Claude Haiku 4.5 and Gemini 2.5 Flash, 198 runs each, with the same runner code
  (SHA-256 `119611fe...6a36`) and a mock check that the prompts are byte-identical to the Ollama path (96/96 per
  provider; S8).

**If a reviewer asks:** "Every run records the hashes of its runner, interpreter, testbench and model digest, plus its
node and toolchain. Protocol fields are identical across all 1,386 cluster runs."

### Q61. How was composition done, and why does it matter?

**Short answer:** For each model and replicate, the repaired versions of the leaves are swapped into the real design,
and the top level is synthesised. It shows whether fixing small parts fixes the whole chip.

**In depth (Result 5, page 12; `phase3/runner/compose.py`):**

- A **group** is one (model, replicate). There are 18 per condition: 6 models x 3 replicates.
- **Each group's** final repaired leaves replace the defective ones in the 2x2 mesh, the 3x3 mesh and the MPSoC top.
  Yosys then synthesises each top and counts latch cells.
- **The golden bound:** 0 latch cells for the meshes, 122 for the MPSoC (Table S17).
- **Results** (Figure 7b, page 9):
  - simulation-only repair never yields a design that synthesises, because it never touches the sim-silent register
    that aborts synthesis;
  - v3 succeeds in 16/18 groups in each design, and escalation in 18/18 in both meshes;
  - raw text 15, 15 and 13; the alarm 11/18.
- **Why it matters.** It is the step from "the leaf passes" to "the design can be built", and the only top-level claim
  the paper makes. The top-level testbench is weak, so composed designs are checked by synthesis only.

**If a reviewer asks:** "Composition is synthesis-only, and the paper says so. The 2x2 and 3x3 meshes share the same
leaves, so their identical results are one observation, not two (`PHASE3_RESULTS.md`, limitation 8)."

### Q62. Why 2,880 and 6,480 latch cells? Why does Yosys print the same 2 messages at 4 and 9 routers? Why do 122 cells remain at the MPSoC top?

**Short answer:**

- **The counts:** each router contains 20 copies of each of two latching registers, 36 latched bits per pair, so
  36 x 20 x 4 = 2,880 and 36 x 20 x 9 = 6,480.
- **The messages:** Yosys reports once per module definition, not per copy, hence 2 at both sizes.
- **The 122:** latch cells in five modules outside the repair set.

**In depth (Section 9.1, page 9; Figure 7a; Table S17; `PHASE3_EXPLAINED.md`, section 4.4):**

- `register_32bit` latches 32 bits and `register_4bit` latches 4: 36 bits per pair. Each router instantiates 20 of
  each.
- **Messages against cells:**
  - the latch message comes from Yosys's `proc_dlatch` pass, which processes each module definition once;
  - the cells come from the flattened netlist, so they scale with every instance.
- **Consequence for repair.** A model repairing the leaf sees the same two short messages whether the chip has 4
  routers or 400. Fixing one definition fixes every copy, and with the task leaves repaired both meshes have 0 latch
  cells.
- **The MPSoC top's 122 cells** sit in five modules not in the task set, so its bound is "restored synthesis", not
  "latch-free".
- **The abort-causing file is excluded** from these counts (the 1-bit register stops synthesis otherwise).

**If a reviewer asks:** "The growth is linear in the number of routers (6,480/2,880 = 9/4), not exponential, and the
paper says only that."

### Q63. What does "keeping the interpreter robust" mean (the v3 layer and the drift gate)?

**Short answer:** Running the production interpreter on real logs showed wrong or missing advice. v3 fixes those cases
without changing anything else, and a gate checks, before each batch, that the cluster's tool versions still print
messages the interpreter understands.

**In depth (page 9; S1, S8.2):**

- **Ten findings** about v2 on real logs (`phase3/evidence/PROD_V2_ON_REAL_LOGS.md`), for example:
  - clocks treated as enables;
  - partly used buses turned into "gate on this bus";
  - advice for the wrong module;
  - silence on the async-reset abort and on expression truncation.
- **v3** imports v2 unchanged, reproduces it byte for byte where no new rule applies, and adds the four rules of
  Table 1.
- **The drift gate** runs the interpreter on fresh tool output on the cluster. It caught a latch-message format change
  between Yosys 0.33 and 0.69 that would otherwise have silently disabled the new rules, turning interpreted
  conditions into baseline.

**If a reviewer asks:** "Tool-format drift is a real threat to any message-parsing layer. Ours is gated, and the gate's
catch is reported."

### Q64. Is baseline a strawman on the sim-silent tasks, given that it makes 0 model calls?

**Short answer:** No. That is the point: it is exactly what a simulation-only loop does. The input passes simulation, so
the loop stops and ships the defect. The like-for-like comparison is the sim-visible stratum.

**In depth (pages 10 to 12):**

- **Baseline follows AutoChip.** It stops at the first simulation pass. On a sim-silent task that is the unmodified
  input, so it makes 0 calls and ends signed off defective in 108/108 runs.
- **What this measures:** not model quality, but whether a structural check exists at all. The paper states this
  scope (`PHASE3_RESULTS.md`, limitation 2).
- **The fair comparisons:**
  - on sim-visible tasks, where baseline does run the model, escalation beats it by +14.4 points (56/90 against 43/90,
    CI +3.3 to +27.8, p=0.048);
  - the control arm (Q66) compares tool detail with an alarm at an equal budget.

**If a reviewer asks:** "The sim-silent result is a property of simulation-only loops, which the paper reports as such.
Every quality claim uses the sim-visible stratum or the control arm."

### Q65. What is pre-registration, what were the readings, and why do the hashes matter?

**Short answer:** Before the final batch ran, we wrote down the contrasts, the metric and what each possible outcome
would mean, then hashed the file. The result could then only be read the way we had committed to in advance.

**In depth (`phase3/evidence/PREREG_FINAL.md`, sections 4 and 5; SHA-256 `1b6eb915...cc63`):**

- **The four primary contrasts** (sign-off clean, six models):
  1. escalation minus the alarm;
  2. v3 minus the alarm;
  3. the alarm minus raw text;
  4. the alarm minus baseline (sim-visible only).
- **The pre-registered readings, verbatim in spirit:**
  - **R1:** contrasts 1 and 2 exclude 0 with the alarm lower, so "the detail in the feedback adds value beyond the
    verdict".
  - **R2:** contrast 1 includes 0, so "the verdict carries most of escalation's gain". The interpreter's value would
    then rest on v2 and v3 against raw text, cost, first-call speed, and the tasks where the alarm fails.
  - **R3:** the alarm above always-on v3, so "terse beats verbose on some models", and escalation is the recommended
    design.
  - If none holds, the result is reported as observed, with no interpretation.
- **The outcome:** R1 held (Table 6, page 11).
- **Why the hashes matter.**
  - The prereg file's hash, and the hashes of the runner, interpreter and task files frozen with it
    (`FREEZE_FINAL.md`), are recorded in every new run.
  - Anyone can verify that the analysis plan and the code were fixed before the data.
  - The API study did the same, with five dated amendments, each hashed before the calls it governs.

**If a reviewer asks:** "The readings, the operational rule that decides them and the no-correction choice were all
written before the runs. That is why the multiplicity note (Q68) states them as pre-registered."

### Q66. The control arm in depth: why was it the single most important run? What if the alarm had matched escalation?

**Short answer:** Escalation opens with a generic "fails sign-off" message. Without a control, its advantage could have
come from that alarm, not from the interpreter. The control arm gives the alarm alone. Escalation beat it by 19.7
points, so the interpreter's detail is what helps.

**In depth (Results 2, page 11; `PLANNER_BRIEF.md`, section 2):**

- **Where the worry came from.** The analysis of the 990 runs flagged it: escalation's gate message is more
  information than baseline receives, and 110 of its 158 clean passes (as run) came with no interpreter output. The
  990 runs could not separate the message from the interpreter (`PHASE3_RESULTS.md`, limitation 3).
- **The control, `baseline_gate`:**
  - simulation feedback plus exactly the same message;
  - stops at a clean pass and never escalates;
  - it logs what v3 would have said, without feeding it back.
- **Results:**
  - escalation minus the alarm: +19.7 points (CI +11.1 to +29.3);
  - v3 minus the alarm: +14.6 (CI +3.0 to +26.3);
  - the alarm equals raw text (-0.5) and equals simulation alone on sim-visible tasks (-1.1).
  - Of the 95 alarm-only runs that were not sign-off clean, 38 returned RTL that still carries a defect v3 names.
- **If the alarm had matched escalation** (reading R2), the honest conclusion would have been that escalation's gain is
  mostly the stop-on-clean rule plus a nudge, and that the interpreter adds little beyond it. The paper's headline
  would have changed.

**If a reviewer asks:** "The control was pre-registered, run on the same models and budget, and verified on real
prompts: 0 of its prompts contain tool text. It turned 'escalation works' into 'the interpreter's detail works'."

### Q67. How do I read Table 6 (the primary contrasts), including "A/B only"?

**Short answer:** Each row is a pre-registered comparison: the difference in sign-off clean rate (points), its
cell-bootstrap CI, its sign-flip p, and how many matched runs only A or only B got right.

**In depth (Table 6, page 11):**

| Contrast                                 | Difference | CI             | p      | A/B only |
| ---------------------------------------- | ---------- | -------------- | ------ | -------- |
| 1. escalation minus the alarm            | +19.7      | +11.1 to +29.3 | <0.001 | 42/3     |
| sim-silent                               | +23.1      |                |        |          |
| sim-visible                              | +15.6      |                |        |          |
| 2. v3 minus the alarm                    | +14.6      | +3.0 to +26.3  | 0.021  | 43/14    |
| sim-silent                               | +23.1      |                |        |          |
| sim-visible                              | +4.4       | crosses 0      |        |          |
| 3. the alarm minus raw text              | -0.5       |                | 1.000  |          |
| 4. the alarm minus baseline, sim-visible | -1.1       |                | 1.000  |          |

- **"A/B only"** are the discordant pairs. Runs are matched on (model, task, replicate). 42/3 means 42 runs where only
  escalation was clean and 3 where only the alarm was. Matched runs where both or neither succeeded do not inform the
  difference.

**If a reviewer asks:** "Discordant counts show the direction is not driven by a few runs: 42 against 3 is lopsided."

### Q68. The multiplicity note: why does contrast 2 not survive Holm, and why does the headline still stand?

**Short answer:** With four tests, Holm multiplies the second-smallest p by 3: 0.021 x 3 = 0.063, above 0.05. Contrast 1
survives (p<0.001 x 4 is still below 0.004). The headline rests on contrast 1. The pre-registered reading used each
contrast's own CI, as planned.

**In depth (Result 2 and Threats, pages 11 and 13):**

- **Holm's procedure:** sort the p-values (<0.001, 0.021, 1.000, 1.000), multiply the smallest by 4, the next by 3, and
  stop at the first that is not significant.
- **What the paper states:** "As pre-registered, the four primary contrasts are not corrected for multiplicity;
  contrast 1 (p<0.001) survives a Holm correction across the four, contrast 2 (p=0.021) does not."
- **The pre-registration** explicitly applies no correction across the four (`PREREG_FINAL.md`, section 5).
- **Why the headline stands.** The headline, that the detail and not the alarm drives repair, is carried by escalation
  (contrast 1). v3's gain over the alarm is concentrated in the sim-silent tasks.

**If a reviewer asks:** "We report the uncorrected, pre-registered result and the Holm result side by side. The
conclusion that survives correction is the escalation one, and the abstract quotes that number."

### Q69. Why does the alarm alone break working logic? Why does v3 front-load its repairs while escalation keeps climbing (Figure 8b)?

**Short answer:**

- **The alarm:** told only "something is wrong", models rewrite logic that was fine.
- **v3** names the defect from the first call, so most of its wins come early.
- **Escalation** starts behind the same bare alarm and only gets v3's detail after two identical failures, so its wins
  come later and keep coming.

**In depth (Result 2, page 11; Figure 8b, page 12):**

- **Breaking working logic.** Every sim-silent input already simulates correctly. Of 108 alarm-only runs on those
  tasks, only 80 still pass simulation at the end, against 97 under escalation. Without knowing what to fix, models
  change the wrong thing.
- **Front-loading.** 55% of v3 runs are sign-off clean after the first call, against 41% with raw text and 15% with
  simulation only (Result 3).
- **The alarm's plateau.** From the third call to the sixth it adds two points (50 to 52%).
- **Escalation's climb.** It climbs from 56 to 72% over the same calls, once it hands over to v3.

**If a reviewer asks:** "The cumulative-by-call curves come from the logged trajectories
(`PHASE3_FINAL.md`, 'Cumulative signoff_clean by LLM call'). Both escalation and the alarm start from the same
message; they diverge only when escalation hands over to v3."

### Q70. What does Figure 8a show?

**Short answer:** Sign-off clean by condition, split into sim-silent tasks (solid) and sim-visible tasks (hatched).
Simulation-only repair scores 0 on sim-silent tasks. Interpretation and escalation lead there, and escalation also
leads on sim-visible tasks.

**In depth (page 12):**

- **Sim-silent** (n=108): baseline 0, the alarm 56%, raw text 59%, v2 77%, v3 80%, escalation 80%.
- **Sim-visible** (n=90): baseline 48%, the alarm 47%, raw text 44%, v2 46%, v3 51%, escalation 62%.

  Source: `PHASE3_FINAL.md`, stratum tables. The counts are 86/108 and 56/90 for escalation.

**If a reviewer asks:** "Always-on v3's advantage over the alarm is carried by the sim-silent tasks (+23.1 against
+4.4). Escalation's holds in both strata."

### Q71. The two oracles: loop testbench against sign-off testbench. Why could the 990 runs be re-scored exactly, and why is that post hoc?

**Short answer:** The loop testbench guides repair; the sign-off testbench judges it. Because the loop never saw the
sign-off testbench, each run's final RTL can simply be scored again under it, with no re-run. It is post hoc because
the oracle was written after those runs.

**In depth (Section 9.2, page 10):**

- **Why a second oracle.** The equivalence audit (Q72) found two tasks whose loop testbench does not check what the
  specification states. The sign-off testbench closes those gaps. On the other nine tasks it is identical.
- **Why re-scoring is exact.** The loop's behaviour depended only on the loop testbench and the tools. Scoring the
  returned RTL under a different testbench changes the label, not the run.
- **Post hoc for the 990 runs, pre-registered for the final batch.** The as-run metric, "loop-clean", is kept beside it
  as a sensitivity.

**If a reviewer asks:** "A post hoc oracle can be suspected of tuning, so we report both metrics. Every ordering and
direction is the same under both (Q73)."

### Q72. What is the formal-equivalence audit, and what does "equivalent on legal inputs" mean?

**Short answer:** A tool proof that each clean repair behaves exactly like the reference fix. "Equivalent on legal
inputs" means identical for every input the specification allows, differing only on inputs it declares illegal.

**In depth (S8.5, Tables S27 and S28):**

- **How.** Every clean repair of the 990 runs was compared with its golden fix in Yosys (`equiv_make`,
  `equiv_simple -seq 5`, `equiv_induct`). Each golden fix is equivalent to itself.
- **Legal inputs.** Where a repair was not proven equivalent, the check was repeated with inputs the specification
  declares illegal mapped to a legal value. A repair that differs only on, say, an unused select code is still
  correct.
- **Findings:**
  - on `MuxPC`, `execute_mux`, `mux3`, `register_1bit` and `riscv_alu_flags`, every clean repair is equivalent, or
    equivalent on legal inputs;
  - `noc_xbar4`'s 47 clean repairs are equivalent on legal inputs;
  - two tasks had "class (i)" repairs that differ from the golden fix on behaviour the specification defines and the
    loop testbench does not check: 41 on `Address_select` and 16 on `mem_wb_mux`.
- **For each gap,** the new sign-off testbench passes the golden fix, fails every class (i) repair, passes every other
  clean repair, and fails a golden mutant that differs only in the unchecked cases.

**If a reviewer asks:** "The audit is what turned a suspicion about the loop testbench into a measured gap. The
sign-off testbench was validated against the golden fix and a mutant before use."

### Q73. Why did numbers change between drafts (80% to 72%, +23.3 to +14.4), and why is that a strength?

**Short answer:** Earlier drafts scored Phase 3 with the loop testbench. When we applied the stricter sign-off oracle
to our own results, the absolute rates fell by 5 to 8 points for the tool conditions, mostly because of
`Address_select`. Every ordering and direction survived.

**In depth (`PLANNER_BRIEF.md`, section 3; `paper/archive/V8_CHANGES.md`):**

| Claim                                  | As run | Sign-off                    |
| -------------------------------------- | ------ | --------------------------- |
| escalation clean                       | 80%    | 72%                         |
| v3 clean                               | 74%    | 67%                         |
| raw text clean                         | 59%    | 53%                         |
| escalation minus baseline, sim-visible | +23.3  | +14.4 (CI still excludes 0) |
| v3 minus raw text                      | +14.6  | +14.1                       |

**Why this is a strength.**

- The correction came from our own audit, not from a reviewer.
- We changed the primary metric to the stricter one.
- We kept the as-run numbers beside it (in brackets in Table 5).

A claim that survives a harder oracle is worth more.

**If a reviewer asks:** "We prefer the lower, harder-oracle numbers in the headline. Both sets are in the paper and the
supplement, so nothing is hidden."

### Q74. How do I read Table 5?

**Short answer:** One row per condition, 198 runs each. Columns are grouped: sign-off (clean rate, its CI, signed off
defective), loop (pass, loop-clean) and cost (calls and tokens per run).

**In depth (Table 5, page 11):**

| Condition  | Sign-off clean | CI       | Signed off defective | Loop pass | Loop clean | Calls per run | Tokens per run |
| ---------- | -------------- | -------- | -------------------- | --------- | ---------- | ------------- | -------------- |
| baseline   | 22             | 17 to 28 | 63                   | 85        | 23         | 1.34          | 1,425          |
| alarm      | 52             |          | 15                   | 67        | 56         | 3.39          | 3,835          |
| raw text   | 53             |          | 12                   | 65        | 59         | 3.27          | 4,396          |
| v2         | 63             |          | 8                    | 71        | 68         | 2.83          | 3,831          |
| v3         | 67             |          | 8                    | 74        | 74         | 2.51          | 3,377          |
| escalation | **72**   | 65 to 78 | 13                   | 85        | 80         | 2.99          | 3,798          |

Rates are percentages. Bold marks the best value only where it helps the comparison.

**If a reviewer asks:** "Baseline's low call count is because it stops at the input on sim-silent tasks. It is not an
efficiency."

### Q75. Why does interpretation beat raw text, and what is "in-sample" (v2 against v3)? Why is v2's +10.1 the honest estimate?

**Short answer:**

- **Why:** a short directive that names the signal and the fix is easier for a small model to act on than raw tool
  text.
- **In-sample:** v3 was written from these designs' logs, so its gain could partly reflect tuning to them.
- **The honest estimate:** v2 was written before the case study, so its +10.1 over raw text is out of sample.

**In depth (Result 3, page 11):**

- **v3 against raw text:** 132/198 against 104/198, +14.1 points (CI +3.5 to +24.7, p=0.014; 40 discordant against 12).
- **v2 against raw text:** +10.1 (CI +2.0 to +18.7, p=0.030).
- **Cost:** v3 needs about 23% fewer calls and tokens per run, and 5,066 against 8,370 tokens per sign-off clean run.
- **"In-sample"** means the rules were developed on the same data they are tested on. It inflates expected gains.
  v2's rules predate Phase 3 and were never tuned on its designs.

**If a reviewer asks:** "We quote v2's +10.1 as what interpretation is worth out of sample, and list held-out defects
as direction (i)."

### Q76. Why does raw tool text hurt the 3B model on sim-visible tasks (1/15)?

**Short answer:** The raw text is long and technical. A 3B model given it on every round tends to break logic it had
right. With simulation feedback alone it does better (7/15), and with escalation best (8/15).

**In depth (Result 4, page 12; `PHASE3_RESULTS.md`, finding 4 and limitation 6):**

- **The counts.** On sim-visible tasks, llama3.2:3b is sign-off clean in 7/15 runs with simulation only, 1/15 with raw
  text every round, and 8/15 with escalation.
- **The as-run version** of the same harm is 9/15 against 1/15 (McNemar p=0.008, uncorrected).
- **Why it is long.** Phase 3 raw feedback is far longer than in Sets 1 and 3, because it carries every filtered tool
  line.
- **The regressions are real.** 92 runs lost a simulation pass they had at some iteration, all with tool feedback,
  including 36 under raw text.
- **Compile failures** concentrate in the smallest models: of 124 final candidates that failed to compile, 66 came
  from gemma3:4b and 42 from llama3.2:3b.
- **Escalation protects the small model.** It withholds tool text until the run is stuck.

**If a reviewer asks:** "It is one model on 15 runs, so it is an illustration of the conference's harmful regime under
raw text, not a general law. It is exactly the case escalation is designed for."

### Q77. How is "47.5% fewer tool rounds" computed (Result 4)?

**Short answer:** A tool round is a model call whose prompt carried tool feedback. Escalation averages 1.32 per run
against v3's 2.51, which is 47.5% fewer.

**In depth:**

- `tool_feedback_iters` in `phase3/runner/stitch_runner_p3.py` counts the calls whose feedback included tool text or
  directives.
- Means over 198 runs: escalation 1.32, v3 2.51, raw text 3.27; the alarm and baseline 0.00 (Table S23).
- Over 198 runs each, v3 used 497 tool rounds and escalation 261 (counted from the run metrics): (497 - 261) / 497 = 47.5%. Rounding the means first would give 47.4%.
- Escalation also keeps baseline's 85% loop pass rate and reaches the highest sign-off clean rate, 72%.

**If a reviewer asks:** "In Phase 3 every candidate is fully evaluated in every condition, so we count what reaches the
model, not tool invocations. Escalation simply withholds tool text until it is needed."

### Q78. Leaf repairs compose: why was leaf-clean enough here, and what kind of defect would break that?

**Short answer:** Here every defect lived inside one leaf, so a clean leaf meant a clean contribution to the design. A
defect that only exists in how modules are connected would not be caught by repairing leaves.

**In depth (Result 5, page 12; Directions iii, page 14):**

- **The data.** In the 990 runs, whenever all composed leaves were loop-clean, the design reached its bound: 32/32,
  32/32 and 27/27.
- **Composition-only defects exist in this design:**

  - a one-bit program-counter port driven with 32 bits;
  - a network-interface FIFO instantiated by position with a missing port, so two status signals land on the wrong
    pins.

  Each leaf is fine alone; the connection is wrong. Leaf-level repair cannot see them.
- **The fix** needs integration-level feedback, which is direction (iii).

**If a reviewer asks:** "Composition success is reported only for defects that live in leaves, and the paper names the
integration-level defects it cannot address."

### Q79. Up the ladder (Table 7): why does interpretation's edge vanish at 32B and for the API models, while the guard is still needed?

**Short answer:** Bigger models can act on raw tool text as well as on directives, so the translation stops mattering.
But a simulation-only loop still ships every sim-silent defect at every size, because the problem is what simulation
cannot see, not the model.

**In depth (Result 6, page 12; Table 7, page 13):**

- **At 32B and for all three API models,** every tool condition repairs all 18 sim-silent runs. The alarm alone
  manages 16 or 18.
- **The remaining misses** are on `Address_select`, plus two alarm-only runs on the ALU task.
- **Simulation-only repair** signs off all 18 sim-silent runs as defective for every model.
- **Raw text is the cheapest** at 32B: 1,492 tokens per run against 1,660 for v3.

**If a reviewer asks:** "The interpreter's pass-rate benefit is a small-model phenomenon. The structural check, the
guard, is needed at every size. The paper separates the two claims."

### Q80. Result 7: what does "the upgrade closes the vocabulary gaps" show?

**Short answer:** Where v2 was silent or wrong, v3 gives the right directive. On the async-reset register,
interpreter-credited wins rise from 3/18 to 15/18.

**In depth (page 12; Table S25):**

- **Where v2 was silent:** on `register_1bit` and `ni_flit_pack` v2 produced no directive. v3 fires the intended class
  in 18/18 runs.
- **Where v2 was wrong:** on the two latching registers, v3 replaces the clock-gating advice with the missing-clock
  directive. On `Address_select` it drops a misleading "gate the output on the instruction bus" directive.
- **The four tasks singled out before the runs:** sign-off clean rises from 42/72 to 50/72 (+11.1 points, CI -9.7 to
  +31.9). A favourable direction, in-sample.

**If a reviewer asks:** "Coverage improves by construction. Whether that improves pass rates beyond this design is not
established, and we say so."

### Q81. mem_wb_mux and Address_select: what is the "safe value" advice? Why is it a count, not a causal claim, and why is the violation invisible at processor level?

**Short answer:** The production latch directive suggests one default assignment such as `J_addr = <safe value>`. On
`Address_select`, repairs that followed it set `J_addr` to 0 where the specification requires `X + PC`. That removes
the latch and breaks the specification.

**In depth (Result 8, page 13; Table S28):**

- **`mem_wb_mux`:** a latch holds a stale store operand in exactly the cases the loop testbench never drives. 16
  loop-clean repairs drive an unspecified value there. This is the conference paper's motivating case, appearing in
  real RTL.
- **`Address_select`:** the specification defines `J_addr = X + PC` on every input, but the testbench checks it only on
  a non-flushed jump. 41 loop-clean repairs set it to 0 elsewhere: latch-free, synthesisable, and in violation of the
  specification.
- **The count.** Among the six models' `Address_select` runs that are loop-clean but fail sign-off:

| Condition       | Gap runs | Of which received the advice |
| --------------- | -------- | ---------------------------- |
| v2              | 8        | 8                            |
| v3              | 12       | 12                           |
| escalation      | 11       | 11                           |
| simulation only | 3        | 0                            |
| raw text        | 7        | 0                            |
| the alarm       | 2        | 0                            |

- **Why not causal.** Conditions without the advice also produce the violation, so the advice is neither necessary
  nor shown to be sufficient.
- **Why invisible at processor level.** The multiplexer that consumes `J_addr` reads it only on a jump, so the
  processor behaves the same. The pre-declared sensitivity that signs `Address_select` off with its loop testbench
  gives the same reading (Result 2).

**If a reviewer asks:** "A structural fix can be functionally wrong exactly where the loop testbench does not look, and
a specification-complete oracle catches it. The proposed fix, a directive that defaults to the specified value, is
direction (ii)."

### Q82. Does running the control arm on a different inference backend (Vulkan) threaten the result?

**Short answer:** No detectable effect. On identical prompts, the alarm arm's first responses match baseline's as often
as two baseline replicates match each other.

**In depth (S8.3; `PLANNER_BRIEF.md`, section 1):**

- In the control-arm job, Ollama's CUDA discovery timed out and it ran on its Vulkan backend: same H200 GPU, all layers
  on the GPU.
- On sim-visible tasks the first prompts of the alarm arm and baseline are byte-identical (90/90).
- **First responses are byte-identical:**
  - in 112 of 270 cross-arm pairs (41%);
  - in 37 of 90 pairs of two baseline replicates (41%).
- First-call simulation pass is 42/90 against 44/90.

**If a reviewer asks:** "It is disclosed in Threats (page 13) with the check that shows no detectable effect."

### Q83. What does "What the case study establishes" (page 13) claim, in one paragraph?

**Short answer:**

- On real multiprocessor RTL, a simulation-only loop cannot see sign-off defects at any model size tested.
- Telling the model *that* sign-off failed is worth about as much as raw tool text.
- Telling it *what* failed adds 14.6 points through interpretation and 19.7 through escalation.
- Leaf repairs compose into designs that synthesise.

**In depth:** each clause maps to a result:

- "blind at every model size": Result 1 and Table 7;
- "the alarm is worth about raw text": contrast 3;
- "detail adds 14.6 and 19.7": contrasts 2 and 1;
- "most on the smallest models": the per-model Holm results, +39.4 on llama3.2:3b and +33.3 on gemma3:4b;
- "sooner and more cheaply": Result 3;
- "leaf repairs compose": Result 5.

**If a reviewer asks:** "Of the two detail contrasts, only escalation's survives a Holm correction across the four
primary contrasts (Q68), and the summary's emphasis follows that."

---

## Part K. Section 10, threats to validity (page 13)

### Q84. Is a Threats to Validity section needed? Could it just be a sentence in the conclusion?

**Short answer:** Keep the section. Journals and reviewers in empirical software and EDA research expect one, and this
paper has several specific threats a reader must be able to find in one place.

**In depth:**

- A dedicated section lets a reviewer check, in one paragraph, that each known weakness is named with its mitigation.
  That is part of how an empirical paper earns trust.
- **Moving it into one sentence of the conclusion would:**
  - hide the specific mitigations (the drift gate, the matched toolchain, the post hoc label, the backend check);
  - read as minimising them.
- **Cost:** about half a column on page 13, well inside the 17-page limit.

**If a reviewer asks:** "We keep threats explicit and specific, because the paper's own history (replication retiring
claims, an oracle lowering numbers) shows they matter."

### Q85. What are the threats, and how is each handled?

**Short answer:** Nine named threats, each with its mitigation or its honest limit.

**In depth (Section 10, page 13):**

| Threat                                                                                 | Mitigation or limit                                                                                                                                                |
| -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Statistical:** correlated replicates; N=3                                      | cell-level bootstraps for every general claim; undecided per-model effects stated; the four primary contrasts uncorrected, and under Holm only contrast 1 survives |
| **Sampling:** one temperature, quantised local models; the control arm on Vulkan | the backend check shows no detectable effect (Q82)                                                                                                                 |
| **Toolchains:** message formats change between versions                          | a live drift gate; the API runs use a toolchain matched to the cluster build (140/140 and 51/51 parity)                                                            |
| **In-sample interpreter**                                                        | v3 written from these logs; v2's out-of-sample +10.1 is the conservative estimate                                                                                  |
| **Oracle:** the sign-off testbench is post hoc for the 990 runs                  | pre-registered for the rest; loop-clean reported beside it                                                                                                         |
| **Benchmark:** RTLLM is public, so contamination is possible                     | affects absolute rates, not within-model contrasts                                                                                                                 |
| **API coverage:** Haiku incomplete                                               | observed conclusions use completed runs; projections marked                                                                                                        |
| **API drift:** hosted models change behind stable names                          | snapshots pinned where possible; model versions, fingerprints and request identifiers logged                                                                       |
| **Composition:** checked by synthesis only                                       | composed systems were not simulated                                                                                                                                |

**If a reviewer asks:** "The list is specific on purpose: each threat names what we did about it, or that we could not."

---

## Part L. Section 11, conclusion and directions (page 14)

### Q86. What does "STITCH is best read as a deterministic sign-off guard and translator" mean?

**Short answer:** STITCH has two separable roles:

- **The guard:** running lint and synthesis at all catches what simulation misses, at every model size.
- **The translator:** turning their messages into directives helps small models repair, more than raw text or a bare
  alarm does.

**In depth:**

- **The guard's value** does not shrink with scale: simulation-only repair signs off every sim-silent defect even at
  32B and for API models (Table 7).
- **The translator's value** is largest on small models and on sim-silent defects, and vanishes at 32B (Q79).
- **Escalation** combines them cheaply: guard every run, and translate only when stuck.

**If a reviewer asks:** "The framing follows the data: the guard claim holds everywhere tested; the translator claim is
scoped to small models and structural defects."

### Q87. What are the Directions after the conclusion? Explain each one, and what it would take.

**Short answer:** Five next steps:

1. test the v3 rules on new defects;
2. make the latch advice specification-aware;
3. give feedback on how modules connect;
4. study reasoning models;
5. make repair robust to specification defects.

**In depth (page 14):**

1. **Held-out real defects.** Collect defective RTL from designs not used to write v3, such as another group's SoC or
   open cores, and run the same protocol. *Needs:* a second design with real structural defects, task extraction and
   about 1,000 runs.
2. **A specification-valued latch default.** Change the latch directive from "assign `<safe value>`" to "assign the
   value the specification defines on that path". This targets the `Address_select` violations. *Needs:* a link from
   the directive to the specification text (for example, a field in `spec.md`), then a rerun of the latch tasks.
3. **Integration-level feedback.** Detect defects that only exist between modules: a 1-bit port driven with 32 bits, a
   positional instantiation with a missing port. *Needs:* Verilator's `PINMISSING` and width checks at the top level
   (v3 already recognises `PINMISSING`; 748 in the MPSoC, S1), and tasks that ask for top-level repair.
4. **Reasoning models, and post-training rather than size.** Run reasoning models within a budgeted protocol (Set 4c
   showed thinking overflow), and study why gemma3:27b reverses the deficit while qwen2.5-coder:32b keeps it. *Needs:*
   larger token budgets, a stop rule for thinking, and model families of matched size.
5. **Specification-level robustness.** `freq_divbyfrac` shows a specification defect that fails every model.
   *Needs:* checks of specification against reference (the trace we used), or prompts that let the model flag an
   inconsistent specification.

**If a reviewer asks:** "Each direction comes from a concrete limitation observed in this study, not from a wish list."

### Q88. Practical question: should an engineer use STITCH today? When does it help most, and when does it not matter?

**Short answer:** Yes, as a guard in any repair loop that must produce synthesisable RTL. Use escalation. It matters
most for small local models and for structural defects simulation cannot see. For large models on functional bugs,
raw tool text is as good, and cheaper.

**In depth:**

- **Always run lint and synthesis** before accepting a repair. A simulation pass is not sign-off (Result 1).
- **Prefer escalation:**
  - the highest sign-off clean rate (72%);
  - the fewest tool rounds;
  - it keeps working logic.
- **For 3B to 8B models,** interpretation beats raw text clearly (+24.2 on llama3.2:3b, +27.3 on qwen2.5-coder:7b).
- **For 32B and API models,** any tool feedback suffices.
- **Keep a specification-complete check:** structural fixes can violate the specification where the loop testbench
  is weak (Result 8).
- **Where it does not matter:** pure functional bugs with no tool-visible signal, such as the RTLLM floor, where the
  interpreter fires but credits no pass.

**If a reviewer asks:** "The recommendation is scoped to what the case study measured: one design family and models up
to 32B, plus three non-reasoning API models."

---

## Part M. Availability, reproducibility and cost (page 14)

### Q89. Reproducibility: how do I rerun any table or figure? Where does the evidence live? What is gitignored, and why?

**Short answer:** `REPO_INDEX.md` lists the command and the evidence file for every table and figure. Raw result trees
and API ledgers are gitignored because of their size and, for ledgers, request identifiers. Snapshots of every analysis
output the paper cites are committed.

**In depth:**

- **The paper.** `paper/overleaf/` builds with `latexmk -pdf main.tex` (and `supplement.tex`).
  - Figures: `python -B paper/make_v10_figures.py`.
  - Set 4 numbers, tables and the heat map: `python -B phase2/frontier/make_numbers_set4.py`.
- **Evidence files:**
  - Phase 3: `phase3/evidence/phase3_final/PHASE3_FINAL.md` (every interval);
  - RTLLM: `phase2/SET1_ANALYSIS.md`, `phase2/SET3_ANALYSIS.md`, `phase2/TWIN_RUN_ANALYSIS.md`;
  - the API study: `phase2/frontier/evidence/`;
  - change logs: `paper/V10_CHANGES.md` and `paper/archive/`.
- **Gitignored:**
  - per-run result trees (`phase*/results/`), large and regenerable;
  - API ledgers, which hold request and response identifiers;
  - API keys, kept outside the repository;
  - LaTeX build output;
  - private notes.
- **Statistics** are seeded per label, so reruns reproduce byte for byte (S9).

**If a reviewer asks:** "Result trees are available on request (Availability, page 14). Every published number can be
regenerated from them with the listed commands."

### Q90. Is the code public?

**Short answer:** The paper points to `https://github.com/Karthik-Flash/STITCH`. The repository must be made public
before submission. That is the one open release step (`phase2/frontier/PENDING.md`).

**In depth:**

- Personal paths and cluster identifiers in documents and scripts were replaced with placeholders. Evidence,
  pre-registrations and hash-frozen scripts were left unchanged so their hashes still verify.
- Secret scans run before every commit, and an all-history audit found no key in any commit.

**If a reviewer asks:** "The repository, the evidence and the pre-registration hashes are given in Availability."

### Q91. What did the whole study cost (GPU runs and API spend)?

**Short answer:** 4,140 cluster runs on A100, H100 and H200 GPUs, plus laptop runs. About $13.70 (INR 1,552) of API
calls in total.

**In depth (`docs/reSTITCH.md`, Part 12):**

- **Cluster runs:**

  - Twin: 630 (H100);
  - Set 1: 1,512 (A100);
  - Set 3: 612 (A100);
  - Phase 3: 990 plus 396 (H200 NVL).

  Each run records its wall time, but no total GPU-hour figure was compiled.
- **Laptop runs:** the 255-run in-house benchmark, the Phase 0 hunt, and all API runs.
- **API:** $13.70 over Sets 4, 4b and 4c, the Phase 3 ladder rows and the completion runs, including smoke tests
  (`phase2/frontier/evidence/spend_summary.txt`).

**If a reviewer asks:** "The study is reproducible on a modest budget: open models on one GPU node, and API calls
costing a few dollars per model."

### Q92. How were the paper's numbers kept honest?

**Short answer:** Every number comes from a generated evidence file, never typed by hand. Every change between
versions is logged with its source line.

**In depth:**

- `paper/V10_CHANGES.md` lists every newly quoted number with its file and line. The v9 log
  (`paper/archive/V9_CHANGES.md`) has a 33-row number-source table, built by a script that checks each value against
  its file.
- The Set 4 numbers are macros written by `make_numbers_set4.py` from the analysis JSON. The paper text needs no edit
  when data change.
- Statistics code was verified against published values before use (S9).

**If a reviewer asks:** "Any number in the paper can be traced to a file in the repository. The traceability is part of
the deliverable."

### Q93. What would make this a 10/10?

**Short answer:** Held-out defects for the v3 rules, a second external design, more replicates for the per-model
questions, and reasoning models.

**In depth:**

1. **Out-of-sample interpreter rules:** v3 evaluated on defects it was not written from (direction i).
2. **A second real design** from another group, to show that the case-study results are not specific to one code base.
3. **More replicates** (N=5 to 10) on the small models, to settle the always-on deficit (currently CI -10.5 to +0.7)
   and the per-model effects.
4. **A pre-registered sign-off oracle for every arm,** rather than post hoc for the 990 runs.
5. **Reasoning models** within a budgeted protocol.
6. **Simulation of composed designs,** not only synthesis.

**If a reviewer asks:** "We list these as limitations and directions rather than claim them. The present paper's claims
are scoped to what was measured."

---

## What a reviewer is most likely to attack, and our answers

1. **"N=3 is too small."**
   - General claims use cell-level bootstraps, which are wider than run-level intervals.
   - Undecided effects are reported as undecided.
   - The headline Phase 3 contrast (+19.7, CI +11.1 to +29.3, p<0.001) survives Holm.
2. **"Baseline on sim-silent tasks is a strawman."**
   - It is what a simulation-only loop does.
   - The quality claims use the sim-visible stratum (+14.4 for escalation) and the pre-registered control arm.
3. **"The sign-off oracle was written after seeing results."**
   - It is post hoc for the 990 runs, labelled so, and validated against the golden fix and a mutant.
   - It was pre-registered for the final batch.
   - Every ordering is the same under the loop testbench.
4. **"v3 was tuned on the test set."**
   - Yes, and we say so.
   - v2, written before Phase 3, gives the out-of-sample estimate (+10.1 over raw text).
5. **"The escalation gain is just the alarm message."**
   - The pre-registered control arm tests exactly that. Escalation beats the alarm by 19.7 points, and the alarm
     equals raw text.
6. **"RTLLM shows no benefit."**
   - Correct for pass rate on a functional benchmark. The paper reports that as a null result.
   - RTLLM shows the cost result, and the paper explains why RTLLM cannot measure structural repair.
7. **"Contamination inflates the API numbers."**
   - Possibly for absolute rates. Within-model contrasts are unaffected.
   - The API models' role is to locate the floor, not to show STITCH's gain.
8. **"One MPSoC is one design."**
   - It is real, already-defective RTL, not written for the study.
   - The paper scopes the claims to it and lists a second design as future work.
9. **"Haiku is incomplete and projected."**
   - Projections appear in two marked places only, never in an observed conclusion.
   - One command removes them, and a compile switch prevents shipping them by accident.
10. **"Determinism means it cannot generalise."**
    - The rules generalise per defect class, not per design.
    - The input/output asymmetry predicts where a rule can act.
    - The drift gate guards format changes.

## If we had one more month

1. Run held-out defects for v3 on a second open-source SoC, under the same pre-registered protocol and the sign-off
   oracle from the start.
2. Implement the specification-valued latch directive and rerun the latch tasks, especially `Address_select` and
   `mem_wb_mux`.
3. Complete Claude Haiku 4.5's 85 floor runs, which removes every projection.
4. Raise N to 6 for the three smallest models on the recoverable band, to decide the always-on deficit.
5. Add integration-level feedback for the two known composition-only defects, and simulate the composed meshes with a
   network traffic testbench.
6. Run one reasoning model on the Phase 3 tasks with a thinking budget sized from a pilot.
