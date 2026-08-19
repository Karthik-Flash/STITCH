# Forgotten inputs are reachable; forgotten outputs are not

**2026-08-19.** Four illustration candidates, gemma3:4b, all three conditions.
Two targeted a forgotten *input*, two a forgotten *output*. The split is clean
and it changes the scope claim the paper can make.

**This supersedes the scope boundary stated in
`session_2026-08-18_findings.md`.** That version is necessary but not
sufficient; the refined version is in §4 below.

## 1. Observation

| Target class | Module | Target port | What the model did on iteration 1 | Outcome |
|---|---|---|---|---|
| Forgotten **input** | `decoder_3to8` | `enable` | `enable` appears **once, in the port list, and never in the body** | mechanism fires |
| Forgotten **input** | `mux4_oe` | `oe` | `oe` never referenced anywhere | mechanism fires |
| Forgotten **output** | `adder_with_overflow` | `overflow` | `overflow = carry;` — assigned | target defect never occurred |
| Forgotten **output** | `fsm_next_state_error` | `error` | `error <= 0;` in **all three branches** | target defect never occurred |

Both input candidates produced the target defect and demonstrated the
interpreter end to end. Both output candidates produced code in which the
target output was assigned unprompted on iteration 1, with no tool feedback and
without the spec asking for it. The defect the interpreter was waiting for
never happened, so neither run says anything about the interpreter in either
direction.

Both output candidates passed their full four-gate pre-screen first. The
mechanism works; the defect does not occur.

## 2. Data

gemma3:4b, one sample per cell. `semfired` is `semantic_fired` from
`metrics.json`; `codes` is `verilator_codes_seen`.

| Module | Condition | Pass | Iters | semfired | Tokens | Codes |
|---|---|---|---|---|---|---|
| `decoder_3to8` | baseline | FAIL | 6 | 0 | 15,595 | `[]` |
| | raw_adv | FAIL | 6 | 0 | 17,353 | `[]` |
| | **sem_adv** | **PASS** | **2** | **1** | **2,861** | `['UNUSEDSIGNAL']` |
| `mux4_oe` | baseline | FAIL | 6 | 0 | 9,939 | `[]` |
| | raw_adv | FAIL | 6 | 0 | 13,154 | `[]` |
| | **sem_adv** | **PASS** | **2** | **1** | **2,270** | `['UNUSEDSIGNAL']` |
| `adder_with_overflow` | baseline | FAIL | 6 | 0 | 6,265 | `[]` |
| | raw_adv | PASS | 2 | 0 | 1,237 | `[]` |
| | sem_adv | PASS | 2 | **0** | 1,298 | `[]` |
| `fsm_next_state_error` | baseline | PASS | 1 | 0 | 521 | `[]` |
| | raw_adv | PASS | 1 | 0 | 521 | `[]` |
| | sem_adv | PASS | 1 | **0** | 521 | `[]` |

Read the two blocks against each other. On the input candidates the
interpreter fires once and cuts tokens by 5-7x against both controls. On the
output candidates `semantic_fired` is **0 in every cell** and
`verilator_codes_seen` is empty — the interpreter was never invoked at all.

**`fsm_next_state_error` iteration-1 output is byte-identical across all three
conditions** (`md5 92b1fc5d1491722bb4075b547484fda0`), 521 tokens total across
the entire three-condition run. The model wrote:

```verilog
always @(posedge clk) begin
  if (rst) begin
    state <= 0;  error <= 0;
  end else begin
    if (go) begin  state <= 1;  error <= 0;  end
    else    begin  state <= 0;  error <= 0;  end
  end
end
```

Three assignments to `error`, on every path, unprompted.

`adder_with_overflow` iteration 1 is likewise byte-identical across conditions
(`md5 70ead1609604a8b859e210b69262c0ce`).

### The system prompt is not the explanation

`fsm_next_state_error` was built specifically so that `SYSTEM_PROMPT` rule 3
could not pre-empt the bug: rule 3 mandates a `default` branch and an `else`
branch in **combinational** always blocks, and this module's logic is
`always @(posedge clk)`. Rule 3 does not apply, and no other rule requires
assigning a declared output. The model assigned `error` anyway.

That distinguishes this finding from `mode_mux_latch`, which died because the
prompt pre-empted its defect. Here the prior is the **model's own**, not
something the apparatus put there. Removing a prompt rule would not recover
this defect class.

## 3. Hypothesized mechanism

Assigning a declared output is a **local completeness obligation**. The output
sits in the always block the model is currently writing; a block that omits it
looks visibly unfinished in the text being generated.

Consulting a declared input is a **non-local obligation**. Nothing in the body
reminds the model the port exists, and the module reads as complete without it
— `decoder_3to8`'s iteration-1 output is a perfectly coherent decoder that
simply has one more port than it uses.

Autoregressive generation is good at local completeness and bad at non-local
obligations. That is the asymmetry, and it predicts the 2-for-2 split in both
directions.

**Status: hypothesis.** It is consistent with four modules on one model, across
both combinational and sequential logic. It is not established. §5 gives the
experiment that would test it directly.

## 4. Refined scope claim

Replaces the earlier version in `session_2026-08-18_findings.md`.

> A defect is reachable if it leaves a static structural fingerprint **and
> models actually produce it**. The set of reachable defect classes is smaller
> than the set of tool-visible ones and must be established empirically per
> class.

The earlier claim — reachable iff it leaves a static structural fingerprint —
is necessary but not sufficient. `UNDRIVEN` on a declared output leaves a
textbook static fingerprint: Verilator names the signal, the interpreter takes
the right branch, the directive prescribes the applicable repair. All of that
was verified before either run. It is unreachable anyway, because the defect
does not occur.

Two consequences worth stating in the paper:

1. Reachability cannot be derived from the interpreter's warning vocabulary. It
   is a joint property of the tool and the generator's failure distribution,
   and it has to be measured.
2. `UNUSEDSIGNAL` on a gating input is therefore not an arbitrary choice among
   seven handled codes. It is the class where tool visibility and real model
   failure behaviour are known to overlap. Two clean negatives make that a
   positive argument rather than a convenient one.

## 5. What this does NOT rule out

**Path-completeness defects, as distinct from output-existence defects.**

The two negatives establish that this model reliably assigns a declared output
*somewhere*. They say nothing about whether it assigns it on **every path**.
Those are different obligations:

| | Question | Evidence |
|---|---|---|
| Output existence | Is the output assigned at all? | Settled — yes, reliably |
| Path completeness | Is it assigned on every branch? | **Open** |

`SYSTEM_PROMPT` rule 3 pushes toward a `default` branch but says nothing about
assigning every output *inside* each branch, so the prompt does not close this
gap either.

`illustrations/pending/priority_encoder_valid/` is the remaining candidate for
this class: a `casez` with a compliant `default` where `valid` is assigned only
in the default and left unassigned on eight of nine paths. Pre-screen gates 1,
3 and 4 pass; Yosys fires cleanly on `valid` and Verilator is silent, so it is
also the only Yosys-sole-source candidate. Gate 2 was blocked on
`interpret_yosys_latches` prescribing a no-op fix for this shape — tracked as
`plans/research_plan_v4.md` §7 #7 and addressed 2026-08-19.

**The direct test of §3's hypothesis** would be a matched pair: one module
whose spec omits a gating input and one otherwise-identical module whose spec
omits a secondary output, same size, same logic style, run together. That
converts an observation across four heterogeneous modules into a designed
experiment. Not run.

## Sources

- `illustrations/proven/decoder_3to8/`, `illustrations/proven/mux4_oe/`
- `results/new_illustrations/adder_with_overflow/` (spec v1),
  `results/new_illustrations/fsm_next_state_error/`
- Retirement records: `illustrations/retired/retired_candidates.md`
