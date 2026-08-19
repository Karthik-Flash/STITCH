# `mux4_oe` — WORKING illustration (second reproduction of the decoder mechanism)

**Status: 2026-08-18 — enabling regime confirmed on gemma3:4b, efficiency
gain confirmed on llama3.1. Both replicated 3/3 (see Replication below).** This is the first module other than
`decoder_3to8` to reproduce STITCH's enabling regime end-to-end with a real
LLM. Not yet promoted to `proven/` — see "Before promotion" below.

## Results

**gemma3:4b — enabling regime** (`results/probes/gated_port_sweep_v2_gemma3-4b/`):

| Condition | Result | Iterations | semantic_fired | Tokens |
|---|---|---|---|---|
| baseline | **FAIL** | 6 | 0 | 9,939 |
| raw_adv | **FAIL** | 6 | 0 | 13,154 |
| sem_adv | **PASS** | **2** | 1 (`UNUSEDSIGNAL`) | **2,270** |

**llama3.1:latest — efficiency regime** (`results/probes/crossmodel_llama31/`):

| Condition | Result | Iterations | semantic_fired | Tokens |
|---|---|---|---|---|
| baseline | PASS | 4 | 0 | 4,673 |
| raw_adv | PASS | 4 | 0 | 6,198 |
| sem_adv | PASS | **2** | 1 | **2,030** |

Same directive, two different regimes: on the weaker model it converts a
total failure into a pass; on the stronger one it halves the iterations and
the token cost. `raw_adv` matching `baseline` exactly in both cases is the
important control — the tools alone do nothing, the *interpretation* is what
moves the outcome.

## Files

The testbench is at `../mux4_oe_tb.v` (flat, runner-readable). A
byte-identical nested copy used to sit here as `tb.v`; it was removed
2026-08-19 so the flat file the runner actually reads is the single source
of truth and the two cannot drift apart. `correct.v` is the reference
implementation used for the pre-screen, not model output.

## The mechanism, verified end to end

Iteration 1 (both models) omits `oe` entirely:
```verilog
always @(*) begin
  case (sel)
    2'd0: out = a; ... 2'd3: out = d;
    default: out = 1'b0;   // 'oe' never referenced anywhere
  endcase
end
```
Verilator: `%Warning-UNUSEDSIGNAL: Signal is not used: 'oe'`
Interpreter directive (real, from `iter_2/feedback.txt`):
```
*** CRITICAL: Port 'oe' is declared but NEVER USED in your always block. ***
You MUST condition on 'oe':
  always @(*) begin
    if (oe) begin
      <your existing case or logic here>
    end else begin
      out = 8'b0;
    end
  end
```
Iteration 2 adopts the template verbatim and passes. Meanwhile `baseline`
iteration 6 still has no `oe` anywhere in the module — six iterations of
iverilog FAIL output never once pointed at the actual cause.

## Why this one worked when four earlier candidates didn't

The recipe, learned the hard way across `counter_with_enable`,
`counter_with_enable_dir`, `register_with_load`, and `mode_mux_latch`:

1. **The spec must describe only the gate-asserted behavior.** `decoder_3to8`
   says "When enable is asserted, ..." and never states the enable=0 case.
   `counter_with_enable` spelled out "if en is low, count holds its current
   value" — handing the model the answer. Those all passed on iteration 1.
2. **Target a forgotten PORT, not a missing case default.** `SYSTEM_PROMPT`
   rule 3 already commands "EVERY combinational always block MUST have a
   'default' branch", so `mode_mux_latch`'s intended bug is pre-empted by the
   prompt itself (confirmed: gemma3:4b emits `default: out = 0;` verbatim).
   No prompt rule says "use every port you declared" — so that bug survives.
3. **Keep the module small.** `seg7_blank` fires the same `UNUSEDSIGNAL`
   correctly but never converges, because reproducing ten 7-bit segment
   patterns introduces independent errors that swamp the fix. `mux4_oe` has
   four trivially-copied branches, so once `oe` is handled, nothing else is
   left to get wrong.

## Replication

Three samples per cell at `temperature=0.1` — `results/n3_replication/`, with
`sem_adv` re-verified against the post-parameterisation interpreter in
`results/n3_replication_postTrackC/`.

| Model | baseline | raw_adv | sem_adv |
|---|---|---|---|
| gemma3:4b | 0/3 pass (6 iters each) | 0/3 pass (6 iters each) | **3/3 pass, 2 iters each** |
| llama3.1 | 3/3 pass, 4 iters each | 3/3 pass, 4 iters each | **3/3 pass, 2 iters each** |

Zero variance in verdict or iteration count within any cell. `raw_adv` tracks
`baseline` exactly in both models — the control that isolates interpretation
from tool presence.

Read the caveat under "Before promotion" below before citing these as a
variance result.

## Before promotion to `proven/`

`decoder_3to8`'s bar is a real LLM run with on-disk before/after evidence —
which this now has. Two caveats to settle first:

- ~~**n=1 per cell.**~~ **Addressed, with a caveat that changes its meaning.**
  Replicated 3/3 per cell (see Replication below). But the three samples are
  *not* three independent draws: at `temperature=0.1` iteration-1 output was
  byte-identical across all three samples in 6 of 12 replication cells, and
  where it varied the verdict and iteration count did not. This establishes
  **reproducibility, not a variance bound**. See
  `../../research_plan_v4.md` §2 for the methodology decision that
  follows from it.
- **Illustration, not benchmark.** Written specifically to trigger a known
  mechanism. That is what illustrations are for (`decoder_3to8` in the
  published paper is exactly this), but it must never be counted in a
  pass-rate percentage or merged into `benchmark/`.
