# STITCH pending illustration modules — verification report

> **STATUS NOTE (2026-08-18).** This document records *tool-level* verification
> only: whether the target warning fires and whether the interpreter converts
> it. It predates the LLM runs, and its "viable — needs LLM run" verdicts for
> `mode_mux_latch` and `priority_chain_comb` were **not borne out**: both were
> subsequently retired after real model runs. `mux4_oe` — not covered here —
> became the second proven illustration instead.
>
> For current module status read `session_2026-08-18_findings.md` first; it
> supersedes the verdicts below. This file is retained because its
> tool-level captures and the `arbiter_two_writers` / MULTIDRIVEN analysis
> remain accurate and are not recorded elsewhere.

**Round 1 (2026-08-17, morning):** initial verification against real Verilator
5.020 / Yosys 0.33, found `mode_mux_latch` viable, `arbiter_two_writers` and
`priority_chain_comb` not.

**Round 2 (2026-08-17, afternoon):** applied `stitch_patches.md` —
fixed the `_LATCH_KEYWORDS` false-positive bug (replaced with anchored regex),
added combinational-loop detection (didn't exist before at all), redesigned
`arbiter_two_writers`'s RTL. Two more bugs were found and fixed *while
verifying the patch itself* against real captured output rather than only
synthetic test strings — see `interpreter/stitch_interpreter.py`'s comment
block above `_LATCH_WARNING_RE` for the full history. Current state below
reflects Round 2, fully re-verified.

**Verification methodology unchanged from Round 1:** real Verilator 5.020 /
Yosys 0.33 via WSL, using both a direct lint/synth invocation and the real
pipeline's exact invocation (from `AutoChipAdvFB/autochip_stitch_runner.py`),
saved per module as `raw_verilator.txt`/`raw_yosys.txt` (direct) and
`raw_verilator_pipeline.txt`/`raw_yosys_pipeline.txt` (real pipeline).
`interpreted_directive.txt` is the actual output of running the patched
`interpreter/stitch_interpreter.py` against the captured real text — not a
hand-written guess.

## Summary

| Module | Target warning | Fires? | Interpreter converts it? | Status |
|---|---|---|---|---|
| `mode_mux_latch` | Latch inferred | Yes (Yosys) | **Yes** | **Viable — needs LLM run for promotion to `proven/`** |
| `priority_chain_comb` | Combinational loop | Yes (both tools) | **Yes (new — `interpret_comb_loop`)** | **Viable — needs LLM run for promotion to `proven/`** |
| `arbiter_two_writers` | MULTIDRIVEN | **No** (fires LATCH + a hard error instead) | Yes, but for LATCH, not MULTIDRIVEN | **Blocked on MULTIDRIVEN specifically — see below** |

Two of three are now genuinely end-to-end viable —
positive results, not placeholders.

---

## `mode_mux_latch` — VIABLE, confirmed

Unchanged from Round 1's finding, re-verified against the corrected detector.
Verilator's real code is `CASEINCOMPLETE` (not in `_VERILATOR_INTERP`,
contributes nothing). Yosys genuinely fires:

```
Latch inferred for signal `\mode_mux_latch.\out' from process `\mode_mux_latch.$proc$broken.v:9$1': $auto$proc_dlatch.cc:427:proc_dlatch$29
```

Note: **no `Warning:` prefix** in Yosys 0.33's real output — this is exactly
the case Round 2's regex fix was for. `detect_yosys_latches()` correctly
extracts `['out']`, `interpret_yosys_latches()` produces the real directive
(see `interpreted_directive.txt`). Full text in Round 1's report below is
still accurate.

---

## `priority_chain_comb` — VIABLE (upgraded from Round 1)

Verilator's real code is `UNOPTFLAT` (not in `_VERILATOR_INTERP`,
contributes nothing). Yosys genuinely fires 6 loop-chain reports:

```
Warning: found logic loop in module priority_chain_comb:
    cell $and$broken.v:15$4 ($and)
    ...
```

Round 1 found there was **no interpreter code for this at all** — that's
fixed now. `detect_comb_loops()` correctly extracts `['priority_chain_comb']`
(×6, one per reported chain), and the new `interpret_comb_loop()` produces:

```
CRITICAL: Combinational loop detected in module 'priority_chain_comb'. A wire cannot
depend on itself through a cycle of pure combinational logic — the value has no
defined resolution and synthesis will reject the design. Fix by either:
  (a) building priority masks from EARLIER signals in the chain only, never later ones, or
  (b) inserting a register on the feedback path to make it sequential.
Do NOT try to fix this by adding an initial value or by disabling the warning —
combinational logic has no state to initialize.
```

This closes the "combinational loop — zero interpreter coverage" gap
identified in Round 1 and flagged as a real taxonomy gap in
`research_plan_v3.md` §D.

---

## `arbiter_two_writers` — MULTIDRIVEN still doesn't fire; blocked there

Redesigned per `stitch_patches.md` Patch 4 (clocked block + a combinational
override block, mixed sensitivity — the canonical MULTIDRIVEN pattern per the
patch's own reasoning). Verified with the exact command specified:

```
verilator --lint-only broken.v 2>&1 | grep MULTIDRIVEN
```

**No match.** Real output instead:

```
%Warning-LATCH: broken.v:26:5: Latch inferred for signal 'grant0' (not all control paths of combinational always assign a value)
%Error-BLKANDNBLK: broken.v:10:17: Unsupported: Blocked and non-blocking assignments to same variable: 'grant0'
    broken.v:27:29: ... Location of blocking assignment
    broken.v:19:20: ... Location of nonblocking assignment
%Error: Exiting due to 1 error(s), 1 warning(s)
```

Verilator treats mixing a blocking `=` (combinational block) and
non-blocking `<=` (clocked block) driving the same reg as an **unsupported
hard error** (`BLKANDNBLK`) and exits before producing `MULTIDRIVEN` — this
particular RTL shape trips a different, earlier check first. `BLKANDNBLK` is
not in `_VERILATOR_INTERP`, so even the error text itself doesn't convert
into anything.

**A genuine, unrelated finding worth keeping:** the combinational override
block (`always @(*) if (preempt) grant0 = 1'b0;`) is *itself* a second, real
bug — it doesn't assign `grant0` on the non-`preempt` path, so it's a real
incomplete-combinational-assignment, and Yosys correctly reports it as a
latch:

```
Latch inferred for signal `\arbiter_two_writers.\grant0' from process `\arbiter_two_writers.$proc$broken.v:26$7': $auto$proc_dlatch.cc:427:proc_dlatch$21
```

`detect_yosys_latches()` catches this correctly (`['grant0']`,
`has_latches()=True`) and `interpret_yosys_latches()` produces a real,
mechanistically-correct directive — this is a **true positive**, not the
banner/negative-message bug from Round 1. But it's converting the wrong
warning class for what this module was built to illustrate: MULTIDRIVEN,
not LATCH (and `mode_mux_latch` already covers LATCH). Using this module
as-is would just be a second latch example wearing an arbiter's name.

**Stopped here rather than guessing at a third RTL design.** Two directions
remain open:
1. Try a clock-edge-mismatch pattern (`always @(posedge clk)`
   + `always @(negedge clk)` both driving the same reg) — genuinely different
   clocking, which is what Verilator's `MULTIDRIVEN` check appears to require.
2. Accept this module as a second latch illustration under a different name/
   framing, and let `arbiter`/MULTIDRIVEN go — `stitch_interpreter.py`'s
   `MULTIDRIVEN` entry in `_VERILATOR_INTERP` would then remain unverified
   against any real trigger (noted honestly in `interpreter/WARNING_TAXONOMY.md`).

---

## Files per module

- `broken.v` / `correct.v` / `tb.v` — the RTL and shared testbench
- `raw_verilator.txt` / `raw_yosys.txt` — direct lint/synth invocation
- `raw_verilator_pipeline.txt` / `raw_yosys_pipeline.txt` — real pipeline's exact invocation (authoritative)
- `interpreted_directive.txt` — actual output of the patched interpreter against the real captured text above

## Boundary rule (unchanged)

Do not copy any of these into `benchmark/v20_baseline/` or
`benchmark/v2_extension/`. `mode_mux_latch` and `priority_chain_comb` are now
tool-fires-and-interpreter-converts viable — but per the original plan, that
still isn't "proven." Proven means an actual LLM run producing a real
before/after pass-rate flip, the same standard `proven/decoder_3to8/` meets.
Neither has that yet.
