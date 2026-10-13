# Deliverable 2 — ALU flag latch elimination (real tool output)

Files: `riscv_alu_flags_buggy.v` (incomplete `case`, carry/overflow assigned only in ADD/SUB), `riscv_alu_flags_fixed.v`,
`tb_riscv_alu_flags.v`, raw logs `yosys_raw.log` / `verilator_raw.log` / `yosys_fixed.log`, directives `directive_v2.txt` / `directive_v3.txt`.

| | buggy | fixed |
|---|---|---|
| Icarus testbench | **PASS** (sim-silent: flags checked on ADD/SUB only) | PASS |
| Yosys latch events / latch cells | 3 / 34 | 0 / 0 |
| Verilator | {'CASEINCOMPLETE': 1} | clean |
| clean_pass | False | True |

The buggy ALU **passes simulation** — an AutoChip loop stops here with 34 latch cells (32 for `result`, 1 each for
`carry`, `overflow`). Real Yosys 0.33 lines (trailing `$auto…` cell ids trimmed):

```
Latch inferred for signal `\riscv_alu_flags.\result' from process `\riscv_alu_flags.$proc$dut.v:5$1':
Latch inferred for signal `\riscv_alu_flags.\carry' from process `\riscv_alu_flags.$proc$dut.v:5$1':
Latch inferred for signal `\riscv_alu_flags.\overflow' from process `\riscv_alu_flags.$proc$dut.v:5$1':
```

The interpreter directive (identical in v2 and v3 — no v3 rule applies, production text passes through) is in
`directive_v3.txt`. Its "4 branch(es) that currently omit it" count is off (evidence F10: `{carry, result} = …` is not
recognised as assigning `result`); the prescribed hoisted default is correct and is exactly the fix applied:

```verilog
result = 32'd0; carry = 1'b0; overflow = 1'b0;   // first statements of always @(*)
... unchanged case items ...
default: result = 32'd0;
```

Reproduce: `python phase3/runner/validate_tasks.py` (task `riscv_alu_flags`).
