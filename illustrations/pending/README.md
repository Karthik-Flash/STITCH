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
| `priority_encoder_valid` | Yosys latch on a partially-assigned output | **Yosys** | **LIVE** — gates 1, 3, 4 pass. Gate 2 was blocked on the latch directive prescribing a no-op; the interpreter fix landed 2026-08-19, so re-check gate 2 and run |
| `adder_with_overflow` | `UNDRIVEN` on a forgotten output | Verilator | **RETIRED 2026-08-19** |
| `fsm_next_state_error` | `UNDRIVEN` on a forgotten output | Verilator | **RETIRED 2026-08-19** |

Both retirements are for one shared reason — the forgotten-output defect class
does not occur — recorded in `../retired/retired_candidates.md` §1 and analysed
in `../../evidence/input_vs_output_asymmetry.md`. **Do not build a third
forgotten-output variant.**

Their directories are kept only as pre-screen scaffolding: the hand-written
`broken.v`/`correct.v` and the testbench that verified each gate. The real
evidence is the model output under `results/new_illustrations/`. Safe to delete
if the tree needs to get smaller.

## Gotcha — do not start a comment with the word `verilator`

Verilator parses any comment whose first token is `verilator` as a
**metacomment**. A documentation line reading `// Verilator: ...` aborts lint
with `Unknown verilator comment`, so the warning you are trying to observe
never fires. Found the hard way on `fsm_next_state_error`; write
`// Expected from Verilator: ...` instead. Details and the interpreter false
positive it exposed are in that candidate's README.
