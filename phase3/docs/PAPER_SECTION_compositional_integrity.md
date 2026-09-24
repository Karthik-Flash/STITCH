# Compositional Integrity: Scaling Semantic Feedback to MPSoC Topologies

*Draft for the journal extension. Every number not marked **[HPC]** was measured with Yosys 0.33 / Verilator 5.020 /
Icarus 12 and is reproducible from `phase3/evidence/`. **[HPC]** marks values that the Phase 3 runs produce.*

## X.1 Motivation

Sections 5–9 evaluate repair one module at a time. Hardware is not deployed that way: a leaf module is instantiated
tens to hundreds of times inside a topology, and a structural defect in its single definition becomes a defect in
every instance. We ask two questions. How does a leaf-level structural defect scale when composed? And does repair
at the leaf, where the interpreter operates, restore integrity at the top, where synthesis sign-off happens?

## X.2 Substrate: a real MPSoC, not a synthetic one

We use an independently developed multiprocessor system-on-chip that was not written for this study (the
`p20230031/RISC-V` codebase). It comprises a 5-stage RV32 core, a network interface (packetiser/depacketiser with
asynchronous FIFOs) and a virtual-channel wormhole mesh router. The same codebase has a 2×2 mesh (N=4 routers) and a
3×3 mesh (N=9) that share 28 of 33 router leaf files. The only changes we made were compile-level ones needed by
open-source tools (redeclarations, nested comments, and Vivado-style implicit trailing ports, reproduced with
identical binding semantics). No structural defect was touched.

This choice exposes a fact that single-module benchmarks hide. **The reference design already contains the defect
classes STITCH targets.** Synthesising the MPSoC top reports 63 latch inferences across 12 module definitions, and it
*fails outright*: one 1-bit register cell writes `if (clr | reset)` inside `always @(posedge clk, posedge reset)`, and
Yosys aborts with *Multiple edge sensitive events*. That register simulates correctly, and so does every latch-bearing
multiplexer we examined against its intended behaviour. The defects are invisible to the simulation oracle that
AutoChip-style loops use.

## X.3 Propagation is linear in N, while the feedback signal is constant

| Design | Routers | Yosys latch messages | Latch cells | Top-level synthesis |
|---|---|---|---|---|
| 2×2 mesh | 4 | 2 | 2,880 | fails (async-reset leaf) |
| 3×3 mesh | 9 | 2 | 6,480 | fails (async-reset leaf) |

Both meshes inherit two defective register definitions: `register_32bit` (32 latch bits) and `register_4bit`
(4 bits). Each is instantiated 20 times per router, so the latch-cell count equals 36 × 20 × N, and the observed ratio
6,480 / 2,880 = 9/4 is exact. Yet the text an EDA-feedback loop sees does **not** scale: Yosys prints one message
per module *definition*, so the interpreter receives the same two lines at N=4 and N=9. Two consequences follow.
First, propagation is linear, not exponential, and it is predictable before synthesis from instance multiplicity
alone. Second, the leverage of a leaf repair is proportional to N: one directive acting on one definition removes
36·20·N latch cells. This is the quantitative form of the "primitives compose" argument (Section 2.1).

## X.4 Leaf repair restores top-level integrity

Replacing the three defective register definitions with repaired versions lets **both meshes synthesise, with
0 latch cells**. The MPSoC top needs its processor-side latch-bearing leaves repaired too (eight task modules in
all). With those eight in place it goes from a synthesis failure to a synthesis pass. The latch cells in scope fall
from 269 to 122, and the remaining 122 sit in five modules outside the Phase 3 task set (the register-file decoder,
control unit, instruction ROM, fetch unit and M-extension unit). We therefore claim *restored synthesisability*
at the MPSoC top, not a latch-free MPSoC. These figures are upper bounds obtained with reference repairs. The
fraction of LLM repair runs that reach them, per condition, is **[HPC] Table X.3**.

## X.5 Interpreter coverage on real defects

Running the production interpreter (Section 5, unchanged) on the real leaves exposed gaps that synthetic tests had
not. The clearest is this: Verilator's `UNUSEDSIGNAL` on the unused **clock** of the latching registers triggers the
generic gating template, `if (clk) … else dout = 0` inside `always @(*)`. That repair builds a clock-gated latch,
while the actual defect is a missing edge trigger. Other gaps are listed in `phase3/evidence/PROD_V2_ON_REAL_LOGS.md`:
- the async-reset abort had no handler;
- a loop visible only to Verilator (`PC = PC`) was never reported;
- width truncation of concatenations was silently dropped;
- partial-bit "unused" warnings were escalated into port-gating directives.

We address these with an *additive* layer (v3). It imports the production interpreter byte-for-byte and adds 12
rules, each justified by a real failing case. It reproduces the production output exactly wherever no rule applies,
so all Phase 1–2 results stand on the recorded interpreter hash. The most consequential rule is **cross-tool
fusion**: a Yosys latch in a level-sensitive block, combined with a Verilator unused-clock warning, is diagnosed
as `MISSING_CLOCK` rather than as either tool's warning alone.

## X.6 Experiment

The repair set contains the eight real defective leaves plus three seeded RISC-V/NoC tasks, which cover defect
classes absent from the reference: multi-driven crossbar output, flit-packing truncation, and ALU flag latches. Six of
the eleven are **sim-silent**, meaning the defective input passes its testbench. Five conditions share one iteration
budget: baseline, raw tools, the production interpreter (v2), v3, and escalation with v3. The model ladder is
[HPC: 4B–14B, list], with N=3 and T=0.1. Wherever a condition shows raw tool text (raw tools, v2, v3, and escalation
once it escalates; baseline shows none), that text is filtered by the same function to Verilator warning and error
lines and Yosys latch, error and logic-loop lines, at most 40 lines per tool, so conditions differ only in whether tool
text is shown and whether directives accompany it.
- **Primary metric:** `clean_pass`, i.e. simulation pass AND a Yosys synthesis pass with 0 latches, 0 loops and no
  hard Verilator warnings.
- **Silent structural pass:** a baseline run that stops at simulation pass with the defect intact.

Per the discipline of Section 1.2, an interpreter-attributed success requires `semantic_fired = 1` in the same
replicate. After repair, every (model, condition, replicate) set of leaves is spliced back into all three designs
and re-synthesised.

## X.7 Results **[HPC]**

- Silent structural pass rate of baseline on sim-silent tasks: **[HPC]** (the upper bound is 100%, since baseline has
  no signal).
- `clean_pass` by condition: **[HPC] Table X.2**. v2 vs v3 is paired by (model, task, replicate). Report v3-only
  clean passes with `semantic_fired = 1`, and flag `register_1bit` and `ni_flit_pack`, where v2 cannot fire by
  construction.
- Top-level synthesis pass after re-integration, by condition: **[HPC] Table X.3**.
- Retro-audit (E0): fraction of Phase 1–2 recorded passes whose final RTL is structurally dirty: **[HPC]**.

## X.8 Boundaries (reported with equal weight)

- **Composition-only defects exist, and no leaf-level check sees them.**
  - The fetch-address module declares a 1-bit `PC` port that the core drives with 32 bits. At leaf level this
    surfaces only as a width-extension warning.
  - The network interface instantiates its FIFO positionally with one port missing. As a result, `full_int` binds to
    `full_ext` and `empty` to `full_int`. That is a functional miswire, which Verilator reports only as one of
    748 `PINMISSING` warnings across the design.
  - Detecting these needs feedback at the integration level, not the leaf level.
- **The top-level functional oracle is weak.** The MPSoC testbench executes two instructions before fetching
  undefined memory, and the NoC output is constant for 5,000 cycles. We therefore make only *structural* claims at the
  top, and every functional claim rests on per-leaf, specification-based testbenches.
- **At the MPSoC top the NoC is optimised away** (its outputs do not reach the top-level port). Router-side results
  therefore come from the mesh tops, where the router outputs are primary outputs.
