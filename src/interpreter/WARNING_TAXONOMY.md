# STITCH interpreter — warning taxonomy

**Created 2026-08-17.** No prior version of this table existed anywhere in
the project (checked `STITCH_PROGRESS_AND_FINDINGS.md`, the handoff docs, and
the runner files) — this is the first one. Lists every warning class
`stitch_interpreter.py` currently knows how to convert into a directive, plus
the classes it's been checked against and found *not* to cover yet.

**Verified column meaning:** "Yes (real data)" means confirmed against an
actual Verilator/Yosys run and, where applicable, an actual LLM run on disk —
not just a synthetic unit-test string. "Yes (synthetic only)" means the
detection logic is unit-tested but has never been checked against real tool
output. "No — real trigger not found" means the class is in the dict/regex
set but nothing has produced a genuine positive from it yet.

## Verilator-sourced (via `_VERILATOR_INTERP` / `interpret_verilator()`)

| Code | What it means | Verified against real data? | Evidence |
|---|---|---|---|
| `UNUSEDSIGNAL` | Declared port never read in the logic | **Yes — two independent modules, two models** | `phase0/illustrations/proven/decoder_3to8/` (gemma3:4b, fired on `enable`, iter 1 FAIL → iter 2 PASS) and `phase0/illustrations/proven/mux4_oe/` (2026-08-18: gemma3:4b FAIL\|6 / FAIL\|6 / **PASS\|2**; llama3.1 PASS\|4 / PASS\|4 / **PASS\|2**) |
| `MULTIDRIVEN` | Signal driven from >1 procedural block with different clocking | **No — real trigger not found** | Two RTL designs tried (`arbiter_two_writers`, never given a dedicated file directory — analysis only) — neither one produced this warning from Verilator. First design: identical clocking on both blocks, Verilator didn't flag it at all. Second design (clocked + combinational mix): produced `%Error-BLKANDNBLK` (hard error) and `%Warning-LATCH` instead. Blocked pending a working RTL pattern — see `phase0/illustrations/retired/retired_candidates.md` section 5. |
| `UNDRIVEN` | Two conflated sub-cases: output never assigned vs. identifier never declared | Yes (synthetic + one real regression case) | `llama3.1`/`simple_cpu_alu` investigation, `STITCH_PROGRESS_AND_FINDINGS.md` §5.2 |
| `WIDTHTRUNC` | Wider value assigned into narrower signal | Yes (synthetic only) | Unit tests only — no confirmed real-run firing on disk yet |
| `WIDTHEXPAND` | Value zero-extended into a wider signal | Yes (synthetic only) | Same — unit tests only |
| `BLKSEQ` | Blocking `=` inside a clocked always block | **Yes** | `llama3.1`/`comb_sensitivity`, `runs/nightly_20260814_012758/v2/llama31_latest/sem_adv/comb_sensitivity/` — fired real (iters 1, 3), though didn't lead to a pass in that run |
| `COMBDLY` | `#` delay inside a combinational block | Yes (synthetic only) | Unit tests only |

## Yosys-sourced (direct functions, not part of `_VERILATOR_INTERP`)

| Class | Detection function | Interpreter function | Verified against real data? | Evidence |
|---|---|---|---|---|
| Latch inferred | `detect_yosys_latches()` / `has_latches()` | `interpret_yosys_latches()` | **Yes** | `mode_mux_latch` (never given a dedicated file directory) — real Yosys 0.33 output, `out` correctly extracted, directive generated; see `phase0/illustrations/retired/retired_candidates.md` section 3. Verilator's own code for the same bug (`CASEINCOMPLETE`) is *not* in `_VERILATOR_INTERP`, so this class is Yosys-only end to end. |
| Combinational loop | `detect_comb_loops()` | `interpret_comb_loop()` | **Yes** | `priority_chain_comb` (never given a dedicated file directory) — real Yosys 0.33 output (6 loop-chain reports), module name correctly extracted, directive generated; see `phase0/illustrations/retired/retired_candidates.md` section 3. New as of 2026-08-17 — no coverage existed before this. Verilator's code for the same bug (`UNOPTFLAT`) is also not in `_VERILATOR_INTERP`. |

## Known false-NEGATIVE history (fixed 2026-08-18)

`_LITERAL_FRAGMENT_RE` — the guard added to stop the interpreter fabricating
signal names out of numeric-literal fragments (`8'h00` → `"h0"`) — was
written as a pure shape test, `^[hHdDbBoO][0-9a-fA-F_xzXZ]+$`. That class
matches a large set of perfectly ordinary Verilog identifiers, because `o`
is an octal base specifier and `e`/`a`-`f` are hex digits. Confirmed
swallowed: **`oe`, `bcd`, `be`, `de`, `da`, `dead`**. Any `UNUSEDSIGNAL`,
`MULTIDRIVEN`, `WIDTHTRUNC`, `WIDTHEXPAND`, `BLKSEQ` or `COMBDLY` warning
naming one of those signals produced **no directive at all** — silently, with
`codes_fired == []`, indistinguishable from "no warning present."

Found when a real `gemma3:4b` run on `mux4_oe` emitted a textbook
`%Warning-UNUSEDSIGNAL: Signal is not used: 'oe'` and the interpreter
returned nothing. Fixed by making the guard context-based: a genuine literal
fragment sits directly after `<digits>'` in the same line, which an
identifier Verilator itself quoted never does. The shape test is retained
only for candidates that actually contain a digit. Fixing this converted
`mux4_oe` from FAIL/FAIL/FAIL into the enabling result now recorded above.

## Known false-positive history (fixed 2026-08-17)

The old runner-side `_LATCH_KEYWORDS` substring check (still present, unfixed,
in `AutoChipAdvFB/autochip_stitch_runner.py` and `HPC/stitch_runner_hpc.py` —
see `phase0/evidence/session_2026-08-18_findings.md` defect 1) matched:
1. Yosys's own `PROC_DLATCH` pass-name banner, printed on every module regardless of latches.
2. The literal substring `"latch inferred for signal"` inside Yosys 0.33's *negative* message, `"No latch inferred for signal ..."`.

`detect_yosys_latches()`'s anchored regex fixes both — see the comment block
directly above `_LATCH_WARNING_RE` in `stitch_interpreter.py` for the full
history, including a second, subtler bug (missing `Warning:` prefix
assumption; unbounded hierarchical-name group) found and fixed the same day
while re-verifying against real captured output instead of only synthetic
test strings.
