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

Discipline inherited from `../retired/tool_level_verification_report.md`, which
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
| `adder_with_overflow` | `UNDRIVEN` on a forgotten output | Verilator | **READY** — 4/4 pre-screen steps pass |
| `priority_encoder_valid` | Yosys latch on a partially-assigned output | **Yosys** | **BLOCKED** — step 2 fails; the directive's prescribed fix is a no-op for this shape. Interpreter change needed, not a module redesign. |
