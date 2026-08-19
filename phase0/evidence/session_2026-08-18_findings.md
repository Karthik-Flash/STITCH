# Pre-Phase-1 findings — 2026-08-18

Read this before designing any new illustration module. It is the compressed record of the pre-Phase-1 investigation:
five defects and eight candidate modules.

## Headline

`mux4_oe` reproduces STITCH's enabling regime on `gemma3:4b`
(**FAIL|6 / FAIL|6 / PASS|2**) and an efficiency gain on `llama3.1`
(**PASS|4 / PASS|4 / PASS|2**). It is the first module other than
`decoder_3to8` to do so. Details: `mux4_oe/README.md`.

## The recipe (what actually determines success)

Three conditions, all required. Four earlier candidates each failed exactly
one of them:

| # | Condition | Failed by |
|---|---|---|
| 1 | Spec describes **only** the gate-asserted behavior; never states what happens when the gate is off | `counter_with_enable`, `register_with_load` — both spelled out "if X is low, hold" |
| 2 | Target a **forgotten port** (`UNUSEDSIGNAL`), not a missing case `default` | `mode_mux_latch` — `SYSTEM_PROMPT` rule 3 already mandates a `default`, pre-empting the bug |
| 3 | Module must be **small** — no independent error surface beyond the target bug | `seg7_blank` — fires `UNUSEDSIGNAL` correctly but ten segment patterns introduce unrelated errors it never converges past |

Corollary worth internalizing: **the system prompt is part of the
experimental apparatus.** Any bug the system prompt explicitly warns against
cannot be used to demonstrate the interpreter, because the model fixes it
before any tool ever runs. Check `SYSTEM_PROMPT` before designing a target.

## Defects found and fixed (5)

Each was hiding the next; #3 concealed #1, #2, and #4 for the project's
entire history by making Yosys silently never run.

1. **`_LATCH_KEYWORDS` substring false-positives** (runner) — matched the
   `PROC_DLATCH` pass banner and the negative "No latch inferred" message.
   *Fixed* by deleting the runner's duplicate list entirely; classification
   now comes only from the interpreter.
2. **`_LATCH_WARNING_RE` required a `Warning:` prefix** Yosys 0.33 doesn't
   emit for latches (interpreter). *Fixed*, plus the unbounded
   hierarchical-name group that could overrun into file paths.
3. **Yosys path unquoted with spaces** (runner) — `read_verilog` only ever
   received `/mnt/d/BITS`. **Yosys had never successfully run in this
   project, ever.** *Fixed* by quoting the path inside the `-p` script.
4. **`interpret_comb_loop` never wired into the runner** — a working, tested
   handler with no call site. *Fixed*; `priority_chain_comb` now genuinely
   produces a converted loop directive.
5. **`_LITERAL_FRAGMENT_RE` swallowed real signal names** (interpreter) —
   `^[hHdDbBoO][0-9a-fA-F_xzXZ]+$` matches ordinary identifiers because `o`
   is an octal specifier and `e`/`a`-`f` are hex digits. **`oe`, `bcd`, `be`,
   `de`, `da`, `dead` were all silently dropped**, killing their directives
   before they reached the model. *Fixed* — the guard is now context-based
   (a literal fragment sits directly after `<digits>'`), with the shape test
   retained only for candidates containing a digit.

Bug #5 is why `mux4_oe` initially came back FAIL/FAIL/FAIL with
`semantic_fired=0` despite `UNUSEDSIGNAL` being right there in the raw text.
Fixing it converted that module into the day's positive result — the single
clearest demonstration that these were real defects suppressing real signal,
not cosmetic cleanups.

Interpreter test suite: **39 tests, all passing**, including regressions built
from the verbatim captured strings for #1, #2, #4 and #5. (31 at the time these
five defects were closed; the UNUSEDSIGNAL parameterisation below added 8 more.)

### Follow-on change — UNUSEDSIGNAL template parameterisation

The directive else-branch previously hard-coded `out = 8'b0;`, correct only for
a module whose single output is named `out` and is 8 bits wide — true by
coincidence for both proven illustrations, wrong for anything else. It now
extracts the real output port name(s) and width(s) from the module header, with
a logged fallback for parameterised widths and unparseable headers. **That
fallback is not currently observable**: the runner configures no logging
handler, so its `INFO` records are discarded. See
`../../../interpreter/README.md` §Monitoring.

## Why the interpreter works (mechanism)

The repair loop has three information layers. They are not redundant — each
answers a question the others structurally cannot.

| Layer | Source | Carries | Missing |
|---|---|---|---|
| 1. Behavioural | iverilog + testbench | **WHAT** is wrong (`at en=0 got 00000001, expected 00000000`) | WHERE, WHY |
| 2. Structural | Verilator static analysis | **WHERE** (`Signal is not used: 'oe'`) | HOW to repair, and salience |
| 3. Directive | the interpreter | **HOW**, priority, and the link from 2 back to 1 | — |

Layer 2 is not a second opinion on layer 1 — it is a different observability
domain. Verilator elaborates the module and flags a declared port with no read
fanout, using no vectors and no simulation. A testbench observes values at the
module boundary, and a port with zero fanout has no boundary behaviour to
observe. Neither can see what the other sees.

**The empirical control is the important part.** In every replicated cell,
`raw_adv` equals `baseline` exactly — same verdict, same iteration count.
`raw_adv` runs Verilator and Yosys and pastes the full warning text into every
prompt, and it changes nothing. The entire effect sits in interpretation, not in
tool presence. That is what the three-condition design exists to separate.

Three things the directive adds over the raw warning:

1. **Severity reclassification.** "Signal is not used" is a style nit in
   essentially every language a model has seen — an unused variable is benign.
   In RTL an unused *port* is missing functionality and a correctness bug. The
   `*** CRITICAL ***` framing overrides a prior that is correct nearly
   everywhere else.
2. **The repair shape.** Knowing `oe` is unused does not say what to write. The
   template supplies the exact structure, and the model adopts it rather than
   inventing an alternative.
3. **The causal join** — *"The FAIL lines ... are caused by 'oe' being
   ignored."* Layers 1 and 2 both sat in the `raw_adv` prompt in full, and the
   model did not connect them. Stating the link explicitly is the inference that
   was not happening on its own.

### Scope boundary

A defect is reachable only if it leaves a **static structural fingerprint**.
That single criterion predicts every result here, including the negatives:
`priority_chain_comb` failed because the actual defect gemma3:4b wrote was a
wrong priority order — clean syntax, sound structure, wrong value. No tool has
anything to say about it. Wrong constants, wrong operators and off-by-ones are
permanently out of reach by construction.

## Replication (N=3) — reproducibility, not a variance bound

Both proven illustrations were replicated three times per cell at
`temperature=0.1` — `results/n3_replication/`, with `sem_adv` re-verified
against the post-parameterisation interpreter in
`results/n3_replication_postTrackC/`.

| Model | Module | baseline | raw_adv | sem_adv |
|---|---|---|---|---|
| gemma3:4b | `decoder_3to8` | 0/3 | 0/3 | **3/3, 2 iters** |
| gemma3:4b | `mux4_oe` | 0/3 | 0/3 | **3/3, 2 iters** |
| llama3.1 | `decoder_3to8` | 3/3, 2 iters | 3/3, 2 iters | 3/3, 2 iters |
| llama3.1 | `mux4_oe` | 3/3, 4 iters | 3/3, 4 iters | **3/3, 2 iters** |

Zero variance in verdict or iteration count within any cell.

**This establishes reproducibility, not variance.** Iteration-1 output was
byte-identical across all three samples in 6 of 12 cells; where it varied (2-3
variants) verdict and iteration count were still identical. `temperature=0.1`
produces a near-degenerate distribution, so repetition at this setting
re-measures the same mode. See `../../research_plan_v4.md` §2 for the
resulting methodology decision.

**`decoder_3to8` shows no effect on llama3.1** (all three conditions PASS|2).
llama3.1 writes `if (enable)` and omits only the `else`, so `enable` *is* used,
no `UNUSEDSIGNAL` fires, and it self-corrects from testbench output alone. This
is why `mux4_oe` is the stronger cross-model illustration — it produces the
forgotten-port defect in both models.

## Module status

| Module | Verdict |
|---|---|
| `mux4_oe` | **Working** — enabling on gemma3:4b, efficiency on llama3.1 |
| `decoder_3to8` | **Working** — re-confirmed against the fixed pipeline, FAIL\|6 / FAIL\|6 / PASS\|2 |
| `seg7_blank` | Mechanism fires, module too complex to converge — shrink it (fewer digits) and retry |
| `cmp8_en` | Too easy — model uses `en` correctly on iteration 1 (gemma3:4b PASS\|1 all conditions) |
| `mode_mux_latch` | Dead for this purpose — system prompt pre-empts the bug (PASS\|1 across 3 separate sweeps) |
| `priority_chain_comb` | Dead for this purpose — gemma3:4b fails it with a *logic* bug the interpreter doesn't target; llama3.1 passes it outright on iteration 1 |
| `counter_with_enable`, `counter_with_enable_dir`, `register_with_load` | Dead — spec states the gate-off behavior outright |
| `arbiter_two_writers` | Dead — two designs tried, neither triggers `MULTIDRIVEN`. Identical clocking produces no warning; a clocked/combinational mix produces `%Error-BLKANDNBLK` (aborts lint) plus `LATCH`. Leaves the `MULTIDRIVEN` handler **unverified against real model output** |

## Next

1. ~~Re-run `mux4_oe` at N>=3 per cell.~~ **Done** — see Replication above. The
   outcome reframed the exercise: it establishes reproducibility, not a
   variance bound.
2. Build 1-2 more modules on the same recipe (small, gated port, spec silent on
   the gate-off case) to widen the illustration set.
3. Consider shrinking `seg7_blank` to 4 digits — the closest near-miss, and its
   mechanism already fires correctly.
4. Design a module that cleanly triggers `MULTIDRIVEN`; the handler is
   currently unverified against real model output.
5. Wire up logging so the UNUSEDSIGNAL fallback rate becomes observable
   (`../../../interpreter/README.md` §Monitoring).
