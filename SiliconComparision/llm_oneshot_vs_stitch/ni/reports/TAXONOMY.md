# Failure taxonomy (pipeline/taxonomy.py)

Categories: syntax, ports, function, latch, multi-driven, width, timing, duplicate child definition, truncation. For a timing-dependent module (rr_arbiter, irs, round_robin_req, falling_edge_pulse_generator, gray_mod6, memory, router_fifo, new1, nidepack) a failing tb line is labelled timing, otherwise function. Logic loops (Yosys `found logic loop`, Verilator UNOPTFLAT, directive COMB_LOOP) are labelled latch (combinational feedback storage). Not counted: Verilator UNUSEDSIGNAL, PINCONNECTEMPTY, UNDRIVEN, IMPLICIT (style warnings; the golden has them too).

## Mapping table

| source | message / code (regex) | category |
|---|---|---|
| iverilog | `Module \S+ was already declared or module \S+ already declared` | duplicate child definition |
| iverilog | `syntax error or Invalid module item or invalid port declaration separator or Invalid port connection` | syntax |
| iverilog | `not a valid l-value for a procedural assignment` | syntax |
| iverilog | `Unable to bind wire/reg/memory` | syntax |
| iverilog | `has already been declared or is not a port of or already bound or Output port expression must support or not valid in assign l-value or Failed to elaborate input port` | ports |
| iverilog | `out of range` | width |
| iverilog | `also continuously assigned or cannot be driven by a continuous assignment` | multi-driven |
| tb | `FAIL property` | function | timing (timing-dependent module) |
| tb | `^FAIL t=` | function | timing (timing-dependent module) |
| yosys | `Re-definition of module or Duplicate module` | duplicate child definition |
| yosys | `Multiple edge sensitive events` | timing |
| yosys | `does not have a port named or not found in module` | ports |
| yosys | `Latch inferred for signal` | latch |
| yosys | `found logic loop` | latch |
| yosys | `multiple conflicting drivers` | multi-driven |
| verilator | `%Warning-(WIDTHTRUNC or WIDTHEXPAND or SELRANGE)` | width |
| verilator | `%Warning-(MULTIDRIVEN or MULTIDRIVENPROC) or %Error-PORTSHORT` | multi-driven |
| verilator | `%Warning-(LATCH or UNOPTFLAT)` | latch |
| verilator | `%Error-PROCASSWIRE or %Error-ASSIGNIN` | syntax |
| verilator | `%Error-PINNOTFOUND or %Warning-PINMISSING` | ports |
| directive | `PINMISSING or UNUSEDSIGNAL or UNDRIVEN` | ports |
| directive | `WIDTHTRUNC or WIDTHEXPAND` | width |
| directive | `COMB_LOOP or LATCH` | latch |
| directive | `MULTIDRIVEN` | multi-driven |
| directive | `MISSING_CLOCK or ASYNC_RESET` | timing |

## Primary label counts (final files)

| label | oneshot | simloop | stitch |
|---|---|---|---|
| ports | 2 | 1 | 2 |
| function | 2 | 2 | 2 |
| timing | 0 | 1 | 0 |

## What retrying changed: primary label of iteration 0 (one-shot input) -> final iteration

| change | simloop | stitch |
|---|---|---|
| ports -> timing | 1 | 0 |
| same | 3 | 4 |

## (a, b) Final files

| module | arm | primary label | cited line | all labels (first line each) |
|---|---|---|---|---|
| depack | oneshot | function | runs/analysis/oneshot/depack/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | function (runs/analysis/oneshot/depack/sim.log:1), multi-driven (runs/analysis/oneshot/depack/yosys.log:101) |
| new1 | oneshot | ports | runs/analysis/oneshot/new1/sim.log:1 `dut.v:22: error: expression not valid in assign l-value: 2'd0` | ports (runs/analysis/oneshot/new1/sim.log:1), width (runs/analysis/oneshot/new1/verilator.log:1), multi-driven (runs/analysis/oneshot/new1/verilator.log:17) |
| nidepack | oneshot | ports | runs/analysis/oneshot/nidepack/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | ports (runs/analysis/oneshot/nidepack/sim.log:1), multi-driven (runs/analysis/oneshot/nidepack/verilator.log:12) |
| rp1 | oneshot | function | runs/analysis/oneshot/rp1/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | function (runs/analysis/oneshot/rp1/sim.log:1), width (runs/analysis/oneshot/rp1/verilator.log:1) |
| depack | simloop | function | runs/analysis/simloop/depack/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | function (runs/analysis/simloop/depack/sim.log:1), multi-driven (runs/analysis/simloop/depack/yosys.log:101) |
| new1 | simloop | timing | runs/analysis/simloop/new1/sim.log:1 `FAIL t=14000 cycle 0: empty = 1, expected 0` | timing (runs/analysis/simloop/new1/sim.log:1), multi-driven (runs/analysis/simloop/new1/yosys.log:92) |
| nidepack | simloop | ports | runs/analysis/simloop/nidepack/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | ports (runs/analysis/simloop/nidepack/sim.log:1), multi-driven (runs/analysis/simloop/nidepack/verilator.log:12) |
| rp1 | simloop | function | runs/analysis/simloop/rp1/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | function (runs/analysis/simloop/rp1/sim.log:1), width (runs/analysis/simloop/rp1/verilator.log:1) |
| depack | stitch | function | runs/analysis/stitch/depack/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | function (runs/analysis/stitch/depack/sim.log:1), multi-driven (runs/analysis/stitch/depack/yosys.log:101) |
| new1 | stitch | ports | runs/analysis/stitch/new1/sim.log:1 `dut.v:22: error: expression not valid in assign l-value: 3'd0` | ports (runs/analysis/stitch/new1/sim.log:1), multi-driven (runs/analysis/stitch/new1/verilator.log:1) |
| nidepack | stitch | ports | runs/analysis/stitch/nidepack/sim.log:1 `dut.v:24: error: expression not valid in assign l-value: 1'd0` | ports (runs/analysis/stitch/nidepack/sim.log:1), multi-driven (runs/analysis/stitch/nidepack/verilator.log:30) |
| rp1 | stitch | function | runs/analysis/stitch/rp1/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | function (runs/analysis/stitch/rp1/sim.log:1), width (runs/analysis/stitch/rp1/verilator.log:1) |

## (c) Per-iteration sequence (iteration 0 = the one-shot file; [STITCH: ...] = categories of the directives fed back after that iteration)

| module | arm | sequence |
|---|---|---|
| depack | simloop | function -> function -> function -> function -> function -> function -> function |
| new1 | simloop | ports -> multi-driven -> timing -> timing -> timing -> timing -> timing |
| nidepack | simloop | ports -> ports -> ports -> ports -> ports -> ports -> ports |
| rp1 | simloop | function -> function -> function -> function -> function -> function -> function |
| depack | stitch | function -> function -> function [STITCH: multi-driven] -> function [STITCH: multi-driven] -> function [STITCH: multi-driven] [restart] -> function [STITCH: multi-driven] -> function |
| new1 | stitch | ports -> multi-driven -> multi-driven -> timing -> timing [STITCH: ports] -> ports -> ports |
| nidepack | stitch | ports -> ports [STITCH: ports] -> ports [STITCH: ports] -> ports [STITCH: ports] [restart] -> ports [STITCH: ports] -> ports [STITCH: ports] -> ports |
| rp1 | stitch | function -> function [STITCH: width] -> function [STITCH: width] -> function -> function -> function [STITCH: width] [restart] -> function |

### Per-iteration citations

| module | arm | iter | label | cited line | directive codes fed back |
|---|---|---|---|---|---|
| depack | simloop | 0 | function | runs/arms/results/qwen2.5-coder_32b/baseline/depack/rep1/iter0/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | - |
| depack | simloop | 1 | function | runs/arms/results/qwen2.5-coder_32b/baseline/depack/rep1/iter1/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | - |
| depack | simloop | 2 | function | runs/arms/results/qwen2.5-coder_32b/baseline/depack/rep1/iter2/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | - |
| depack | simloop | 3 | function | runs/arms/results/qwen2.5-coder_32b/baseline/depack/rep1/iter3/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | - |
| depack | simloop | 4 | function | runs/arms/results/qwen2.5-coder_32b/baseline/depack/rep1/iter4/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | - |
| depack | simloop | 5 | function | runs/arms/results/qwen2.5-coder_32b/baseline/depack/rep1/iter5/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | - |
| depack | simloop | 6 | function | runs/arms/results/qwen2.5-coder_32b/baseline/depack/rep1/iter6/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | - |
| new1 | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/new1/rep1/iter0/sim.log:1 `dut.v:22: error: expression not valid in assign l-value: 2'd0` | - |
| new1 | simloop | 1 | multi-driven | runs/arms/results/qwen2.5-coder_32b/baseline/new1/rep1/iter1/sim.log:5 `dut.v:60: error: Cannot perform procedural assignment to variable 'rd_add_reg' because it is also continuously assigned.` | - |
| new1 | simloop | 2 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/new1/rep1/iter2/sim.log:1 `FAIL t=14000 cycle 0: empty = 1, expected 0` | - |
| new1 | simloop | 3 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/new1/rep1/iter3/sim.log:1 `FAIL t=14000 cycle 0: empty = 1, expected 0` | - |
| new1 | simloop | 4 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/new1/rep1/iter4/sim.log:1 `FAIL t=14000 cycle 0: empty = 1, expected 0` | - |
| new1 | simloop | 5 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/new1/rep1/iter5/sim.log:1 `FAIL t=14000 cycle 0: empty = 1, expected 0` | - |
| new1 | simloop | 6 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/new1/rep1/iter6/sim.log:1 `FAIL t=14000 cycle 0: empty = 1, expected 0` | - |
| nidepack | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/nidepack/rep1/iter0/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | - |
| nidepack | simloop | 1 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/nidepack/rep1/iter1/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | - |
| nidepack | simloop | 2 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/nidepack/rep1/iter2/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | - |
| nidepack | simloop | 3 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/nidepack/rep1/iter3/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | - |
| nidepack | simloop | 4 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/nidepack/rep1/iter4/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | - |
| nidepack | simloop | 5 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/nidepack/rep1/iter5/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | - |
| nidepack | simloop | 6 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/nidepack/rep1/iter6/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | - |
| rp1 | simloop | 0 | function | runs/arms/results/qwen2.5-coder_32b/baseline/rp1/rep1/iter0/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | - |
| rp1 | simloop | 1 | function | runs/arms/results/qwen2.5-coder_32b/baseline/rp1/rep1/iter1/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | - |
| rp1 | simloop | 2 | function | runs/arms/results/qwen2.5-coder_32b/baseline/rp1/rep1/iter2/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | - |
| rp1 | simloop | 3 | function | runs/arms/results/qwen2.5-coder_32b/baseline/rp1/rep1/iter3/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | - |
| rp1 | simloop | 4 | function | runs/arms/results/qwen2.5-coder_32b/baseline/rp1/rep1/iter4/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | - |
| rp1 | simloop | 5 | function | runs/arms/results/qwen2.5-coder_32b/baseline/rp1/rep1/iter5/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | - |
| rp1 | simloop | 6 | function | runs/arms/results/qwen2.5-coder_32b/baseline/rp1/rep1/iter6/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | - |
| depack | stitch | 0 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/depack/rep1/iter0/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | - |
| depack | stitch | 1 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/depack/rep1/iter1/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | - |
| depack | stitch | 2 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/depack/rep1/iter2/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | MULTIDRIVEN |
| depack | stitch | 3 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/depack/rep1/iter3/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | MULTIDRIVEN |
| depack | stitch | 4 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/depack/rep1/iter4/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | MULTIDRIVEN |
| depack | stitch | 5 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/depack/rep1/iter5/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | MULTIDRIVEN |
| depack | stitch | 6 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/depack/rep1/iter6/sim.log:1 `FAIL t=119000 cycle 10: wr_en = 1, expected 0` | - |
| new1 | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/new1/rep1/iter0/sim.log:1 `dut.v:22: error: expression not valid in assign l-value: 2'd0` | - |
| new1 | stitch | 1 | multi-driven | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/new1/rep1/iter1/sim.log:5 `dut.v:62: error: Cannot perform procedural assignment to variable 'rd_add_reg' because it is also continuously assigned.` | - |
| new1 | stitch | 2 | multi-driven | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/new1/rep1/iter2/sim.log:1 `dut.v:62: error: Cannot perform procedural assignment to variable 'rd_add_reg' because it is also continuously assigned.` | - |
| new1 | stitch | 3 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/new1/rep1/iter3/sim.log:1 `FAIL t=14000 cycle 0: empty = 1, expected 0` | - |
| new1 | stitch | 4 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/new1/rep1/iter4/sim.log:1 `FAIL t=14000 cycle 0: empty = 1, expected 0` | UNUSEDSIGNAL |
| new1 | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/new1/rep1/iter5/sim.log:1 `dut.v:22: error: expression not valid in assign l-value: 3'd0` | - |
| new1 | stitch | 6 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/new1/rep1/iter6/sim.log:1 `dut.v:22: error: expression not valid in assign l-value: 3'd0` | - |
| nidepack | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/nidepack/rep1/iter0/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | - |
| nidepack | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/nidepack/rep1/iter1/sim.log:1 `dut.v:16: error: expression not valid in assign l-value: 1'd0` | PINMISSING |
| nidepack | stitch | 2 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/nidepack/rep1/iter2/sim.log:1 `dut.v:24: error: expression not valid in assign l-value: 1'd0` | UNUSEDSIGNAL |
| nidepack | stitch | 3 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/nidepack/rep1/iter3/sim.log:1 `dut.v:25: error: expression not valid in assign l-value: 1'd0` | PINMISSING |
| nidepack | stitch | 4 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/nidepack/rep1/iter4/sim.log:1 `dut.v:24: error: expression not valid in assign l-value: 1'd0` | UNUSEDSIGNAL |
| nidepack | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/nidepack/rep1/iter5/sim.log:1 `dut.v:22: error: expression not valid in assign l-value: 1'd0` | PINMISSING, UNUSEDSIGNAL |
| nidepack | stitch | 6 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/nidepack/rep1/iter6/sim.log:1 `dut.v:24: error: expression not valid in assign l-value: 1'd0` | - |
| rp1 | stitch | 0 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rp1/rep1/iter0/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | - |
| rp1 | stitch | 1 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rp1/rep1/iter1/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | CLOCK_UNUSED, WIDTHEXPAND, WIDTHTRUNC |
| rp1 | stitch | 2 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rp1/rep1/iter2/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | CLOCK_UNUSED, WIDTHEXPAND, WIDTHTRUNC |
| rp1 | stitch | 3 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rp1/rep1/iter3/sim.log:8 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | - |
| rp1 | stitch | 4 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rp1/rep1/iter4/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | CLOCK_UNUSED |
| rp1 | stitch | 5 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rp1/rep1/iter5/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | CLOCK_UNUSED, WIDTHEXPAND, WIDTHTRUNC |
| rp1 | stitch | 6 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rp1/rep1/iter6/sim.log:1 `FAIL t=69000 cycle 5: niout = 20006046, expected 60000000` | - |
