# Changelog

Changes between the MLCAD paper submission and the journal-extension starting
point. This covers the pre-Phase-1 work only; Phase 1 has not begun.

Current plan of record: `docs/research_plan_v4.md`.

---

## Pre-Phase-1 — 2026-08-17 / 2026-08-18

### Repository structure

The journal-extension work was moved out of `AutoChipAdvFB/STITCHAdv/` into a
dedicated `STITCH_v3/` tree: interpreter, runner, benchmark, results, analysis
and documentation. Legacy and conference-era result trees were deliberately not
carried forward. The full old-path-to-new-path mapping, and the list of what
was left behind and why, is in `docs/RESTRUCTURE_NOTES.md`.

### Interpreter — five defects fixed

`interpreter/stitch_interpreter.py` is now the single source of truth for
warning classification and directive generation. Detail on each defect,
including how it was found and the dependency chain between them, is in
`illustrations/retired/session_2026-08-18_findings.md`.

1. **Latch-keyword substring matching produced false positives.** The keyword
   list matched the Yosys `PROC_DLATCH` pass banner, which prints for every
   module regardless of latch inference, and matched the negated message
   `No latch inferred for signal ...` as a substring. Both produced confident
   latch directives for modules containing no latch.

2. **The latch regex required a `Warning:` prefix that Yosys 0.33 does not
   emit** for latch inference, so genuine positives were discarded. The same
   pattern also allowed its optional hierarchical-name group to overrun into
   file paths, yielding an incorrect signal name.

3. **Yosys was invoked with an unquoted path.** The `-p` script string embedded
   the file path without quoting; Yosys tokenizes that argument on whitespace,
   and every path in this project contains spaces. Yosys received only the
   first path segment and aborted with `Can't open input file`. Yosys had
   therefore never executed successfully in this project, and every historical
   `yosys_latch` field reads `false` as a direct consequence.

4. **The combinational-loop handler was never invoked.** A working, tested
   `interpret_comb_loop` existed in the interpreter with no call site in the
   runner, so loop-class defects received no converted directive.

5. **The literal-fragment guard discarded real signal names.** The guard
   protecting against fabricated names derived from numeric literals was a
   shape test, `^[hHdDbBoO][0-9a-fA-F_xzXZ]+$`, which also matches ordinary
   Verilog identifiers — `o` is an octal base specifier and `a`–`f` are hex
   digits. Confirmed discarded: `oe`, `bcd`, `be`, `de`, `da`, `dead`. Warnings
   naming any of these produced no directive at all, reported as zero codes
   fired and indistinguishable from no warning being present. The guard is now
   context-based: a genuine literal fragment follows a sized-literal
   apostrophe, which a quoted identifier does not.

### Interpreter — UNUSEDSIGNAL template parameterised

The directive's else-branch previously hard-coded `out = 8'b0;`. That is
correct only for a module whose single output is named `out` and is 8 bits
wide. The template now extracts the module's real output port names and widths
from the module header and substitutes them.

A fallback path covers parameterised widths, unparseable headers, and the case
where no source is available; it emits the original generic template and logs
that the fallback was taken. **The fallback log is not currently observable** —
the runner attaches no logging handler, so `INFO` records are discarded. See
`interpreter/README.md` §Monitoring for the required prerequisite and the
inspection procedure.

### Runner

- **`runners/illustration_runner.py` created** as the canonical runner, derived
  from `autochip_stitch_runner.py`. The loop logic, prompt construction,
  extraction regex and feedback builders are unchanged from the original, to
  preserve comparability with the published Table 7 results.
- **Yosys path quoting fixed** (defect 3 above).
- **Latch detection consolidated into the interpreter.** The runner's local
  duplicate keyword list was deleted; classification now comes exclusively from
  `detect_yosys_latches` / `detect_comb_loops`. The duplication was itself the
  direct cause of defect 1 persisting after the interpreter had been corrected.
- **Combinational-loop directives wired into both feedback builders**
  (defect 4 above).
- Added `--testbench-dir` and `--modules` command-line options; the default
  testbench directory preserves the original behaviour.
- Console output made ASCII-safe. Non-ASCII characters in `print` statements
  raised `UnicodeEncodeError` under the Windows default console encoding once
  Yosys began returning non-zero cell counts.

### Illustrations

**Two proven end-to-end** against real model runs, replicated three times per
cell at `temperature=0.1`:

| Module | Mechanism | gemma3:4b | llama3.1 |
|---|---|---|---|
| `decoder_3to8` | `UNUSEDSIGNAL` on `enable` | Enabling: FAIL\|6 / FAIL\|6 / PASS\|2 | No effect: PASS\|2 in all conditions |
| `mux4_oe` | `UNUSEDSIGNAL` on `oe` | Enabling: FAIL\|6 / FAIL\|6 / PASS\|2 | Efficiency: PASS\|4 / PASS\|4 / PASS\|2 |

In both models and both modules the `raw_adv` condition matched `baseline`
exactly, isolating the effect to interpretation rather than tool presence.

**Five illustrations retired** after failing a design or empirical gate:
`priority_chain_comb`, `mode_mux_latch`, `counter_with_enable`,
`register_with_load`, `seg7_blank`. Reasons are recorded in
`illustrations/retired/backup_candidates.md` and in the findings
document's module-status table, because they define the design recipe for
future illustrations.

A sixth candidate, `arbiter_two_writers`, was abandoned after two designs
failed to trigger `MULTIDRIVEN`. That handler remains unverified against real
model output and is tracked as an open gap.

### Test suite

Expanded from **16 tests to 39**, all passing. New coverage includes
regression tests built from verbatim captured tool output for defects 1, 2, 4
and 5, and eight tests for the UNUSEDSIGNAL parameterisation including its
fallback path.

Run with:

```
python -m unittest discover -s interpreter/tests -p "test_interpreter.py"
```

### Retired files

- **`AutoChipAdvFB/autochip_stitch_runner.py`** — the runner that produced the
  MLCAD paper's Table 7 results.
- **`HPC/stitch_runner_hpc.py`** — its HPC port.

Both carry retirement headers naming all five defects, and both have had their
entrypoints removed so they cannot be executed. They are retained on disk for
provenance, so published results remain traceable to the code that generated
them. Neither was patched: their `stitch_interpreter` imports were already
broken by the restructure, and defect 3 voids their historical Yosys output
regardless. Rationale in `docs/RESTRUCTURE_NOTES.md`.

### Methodology

- **Variance approach revised.** Repeated runs at `temperature=0.1` were shown
  empirically to produce a near-degenerate distribution — iteration-1 output
  was byte-identical across all three samples in 6 of 12 replication cells, and
  where it varied the verdict and iteration count did not. Repetition at this
  setting establishes reproducibility, not a variance bound. The resulting
  decision is recorded in `docs/research_plan_v4.md` §2.
- **The system prompt is experimental apparatus.** Any defect the system prompt
  explicitly warns against is repaired before any tool fires and cannot
  demonstrate the interpreter. Confirmed on `mode_mux_latch`, whose target
  defect is pre-empted by the prompt's own rule mandating a `default` branch.
  Benchmark and illustration selection must account for this; see Plan v4 §5.

### Documentation

Added: `docs/research_plan_v4.md` (current plan of record),
`interpreter/README.md`, `interpreter/WARNING_TAXONOMY.md`,
`docs/RESTRUCTURE_NOTES.md`, `docs/illustrations/` (index, findings, per-module
records), and this changelog.

Plans v2 and v3 are superseded by v4 and retained for history.
