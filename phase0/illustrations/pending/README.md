# `illustrations/pending/` — candidates under pre-screen

Modules that have been designed and tool-verified but have **not** had a real
LLM run. Nothing here may be cited. Promotion to `proven/` requires a real run
with on-disk before/after evidence, the bar `decoder_3to8` set.

## Layout convention

Each candidate is a directory holding `correct.v`, `broken.v` and `README.md`.
Its testbench sits **flat** alongside as `<module>_tb.v`, because
`--testbench-dir` reads flat `<module>_tb.v` files, and because a single copy
cannot drift from a nested duplicate (the problem resolved in `proven/` on
2026-08-19).

So: `--testbench-dir illustrations/pending` serves every candidate here.

## Pre-screen gate — all four steps, before any LLM run

Discipline inherited from `../retired/retired_candidates.md` §4, which
is what caught `traffic_light_fsm` before it cost a run:

1. The target warning actually fires, from real Verilator/Yosys, on a
   hand-written `broken.v` — and the *intended* code, not a neighbour like
   `CASEINCOMPLETE` or `UNOPTFLAT` that the interpreter has no handler for.
2. The interpreter converts it into a directive that names the right signal
   **and prescribes a repair that applies to this defect shape**.
3. `SYSTEM_PROMPT` (`src/runner/stitch_runner.py:92-113`) does not pre-empt the
   bug. The system prompt is experimental apparatus — see plan v4 §5.
4. The testbench oracle fails on `broken.v` and passes on `correct.v`, with the
   failure set isolated to the target defect.

A candidate that fails any step is not run.

## Status

| Candidate | Mechanism | Sole tool source | Verdict |
|---|---|---|---|
| `priority_encoder_valid` | Yosys latch on a partially-assigned output | **Yosys** | **READY** — 4/4 gates. Gate 2 unblocked by the 2026-08-19 latch-directive fix. Never run — live candidate for phase 1 or later. |
| `adder_with_overflow` | `UNDRIVEN` on a forgotten output | Verilator | **RETIRED 2026-08-19** |
| `fsm_next_state_error` | `UNDRIVEN` on a forgotten output | Verilator | **RETIRED 2026-08-19** |

`alu_with_enable` and `instr_decode_unit` — both ran, both retired after N=3
replication (or its single-sample equivalent for an outcome-(c) verdict) —
have moved to `../retired/`; see that directory's `README.md` for the full
retired-candidate index. This directory only holds candidates that have not
yet had a real LLM run, or that are still live for one.

Three retirement causes across everything tried in phase 0, consolidated in
`../../evidence/phase0_illustration_hunt_findings.md`:

- **Forgotten-output class does not occur** — `adder_with_overflow`,
  `fsm_next_state_error`. Recorded in `../retired/retired_candidates.md` §1,
  analysed in `../../evidence/input_vs_output_asymmetry.md`. **Do not build a
  third forgotten-output variant.**
- **Too large for gemma3:4b's convergence horizon, and not attributable on
  llama3.1 either** — `datapath_mux_alu` (§1a) and its redesign
  `alu_with_enable`, which over-corrected into "too easy" (§1c). **This is
  the closed larger-module direction — see the consolidated findings doc
  before attempting a third variant.**
- **Mechanism fires correctly but the module doesn't converge reliably** —
  `instr_decode_unit` (§1b). A genuinely different failure mode from the one
  above: small module (11 cells), degenerate generation instability rather
  than scale.

Retired directories are kept only as pre-screen scaffolding. The real evidence
is the model output under `results/new_illustrations/`. Safe to delete if the
tree needs to get smaller.

## Gotcha — one directive per warning code, first match wins

`interpret_verilator` emits at most one directive per code and takes the first
matching line, so on a module with several `UNUSEDSIGNAL` warnings the winner
is decided by Verilator's source order, not relevance. It also does not
distinguish `Signal is not used: 'x'` (whole port, a real bug) from
`Bits of signal are not used: 'x'[3:0]` (a few bits of a wide bus, usually
benign).

That is what made the original `instr_decode_unit` design unrunnable — its
8-bit `instr` had 4 unused bits, so a competing warning captured the directive
ahead of the intended `valid`. Fixed by narrowing the bus so no bits are
unused; not fixed in the interpreter, so the underlying gap remains and will
matter at benchmark scale — wide input buses with partly-unused bits are
ordinary RTL. See that candidate's README for the full before/after.

**When designing a gated-port candidate, make sure every bit of every input
carries meaning**, or the gate's warning will lose the race.

## Gotcha — do not start a comment with the word `verilator`

Verilator parses any comment whose first token is `verilator` as a
**metacomment**. A documentation line reading `// Verilator: ...` aborts lint
with `Unknown verilator comment`, so the warning you are trying to observe
never fires. Found the hard way on `fsm_next_state_error`; write
`// Expected from Verilator: ...` instead. Details and the interpreter false
positive it exposed are in that candidate's README.
