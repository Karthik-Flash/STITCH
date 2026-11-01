# Failure taxonomy (pipeline/taxonomy.py)

Categories: syntax, ports, function, latch, multi-driven, width, timing, duplicate child definition, truncation. For a timing-dependent module (rr_arbiter, irs, round_robin_req, falling_edge_pulse_generator, gray_mod6, memory, router_fifo) a failing tb line is labelled timing, otherwise function. Logic loops (Yosys `found logic loop`, Verilator UNOPTFLAT, directive COMB_LOOP) are labelled latch (combinational feedback storage). Not counted: Verilator UNUSEDSIGNAL, PINCONNECTEMPTY, UNDRIVEN, IMPLICIT (style warnings; the golden has them too).

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
| ports | 0 | 0 | 1 |
| function | 1 | 1 | 0 |

## What retrying changed: primary label of iteration 0 (one-shot input) -> final iteration

| change | simloop | stitch |
|---|---|---|
| function -> ports | 0 | 1 |
| same | 1 | 0 |

## (a, b) Final files

| module | arm | primary label | cited line | all labels (first line each) |
|---|---|---|---|---|
| top_3x3_router | oneshot | function | runs/analysis/oneshot/top_3x3_router/sim.log:110 `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000` | function (runs/analysis/oneshot/top_3x3_router/sim.log:110), multi-driven (runs/analysis/oneshot/top_3x3_router/yosys.log:124), width (runs/analysis/oneshot/top_3x3_router/verilator.log:1) |
| top_3x3_router | simloop | function | runs/analysis/simloop/top_3x3_router/sim.log:110 `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000` | function (runs/analysis/simloop/top_3x3_router/sim.log:110), multi-driven (runs/analysis/simloop/top_3x3_router/yosys.log:124), width (runs/analysis/simloop/top_3x3_router/verilator.log:1) |
| top_3x3_router | stitch | ports | runs/analysis/stitch/top_3x3_router/sim.log:1 `dut.v:97: error: 'full_out_link4_vc4_r8' has already been declared in this scope.` | ports (runs/analysis/stitch/top_3x3_router/sim.log:1) |

## (c) Per-iteration sequence (iteration 0 = the one-shot file; [STITCH: ...] = categories of the directives fed back after that iteration)

| module | arm | sequence |
|---|---|---|
| top_3x3_router | simloop | function -> ports -> ports -> function -> ports -> ports -> function |
| top_3x3_router | stitch | function -> ports -> ports -> function [STITCH: ports, width] -> ports -> function [STITCH: ports] -> ports |

### Per-iteration citations

| module | arm | iter | label | cited line | directive codes fed back |
|---|---|---|---|---|---|
| top_3x3_router | simloop | 0 | function | runs/arms/results/qwen2.5-coder_32b/baseline/top_3x3_router/rep1/iter0/sim.log:110 `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000` | - |
| top_3x3_router | simloop | 1 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/top_3x3_router/rep1/iter1/sim.log:1 `dut.v:91: error: 'full_out_link3_vc4_r9' has already been declared in this scope.` | - |
| top_3x3_router | simloop | 2 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/top_3x3_router/rep1/iter2/sim.log:1 `dut.v:79: error: 'full_out_link4_vc4_r6' has already been declared in this scope.` | - |
| top_3x3_router | simloop | 3 | function | runs/arms/results/qwen2.5-coder_32b/baseline/top_3x3_router/rep1/iter3/sim.log:110 `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000` | - |
| top_3x3_router | simloop | 4 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/top_3x3_router/rep1/iter4/sim.log:1 `dut.v:91: error: 'full_out_link3_vc4_r9' has already been declared in this scope.` | - |
| top_3x3_router | simloop | 5 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/top_3x3_router/rep1/iter5/sim.log:1 `dut.v:79: error: 'full_out_link4_vc4_r6' has already been declared in this scope.` | - |
| top_3x3_router | simloop | 6 | function | runs/arms/results/qwen2.5-coder_32b/baseline/top_3x3_router/rep1/iter6/sim.log:110 `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000` | - |
| top_3x3_router | stitch | 0 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_3x3_router/rep1/iter0/sim.log:110 `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000` | - |
| top_3x3_router | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_3x3_router/rep1/iter1/sim.log:1 `dut.v:91: error: 'full_out_link3_vc4_r9' has already been declared in this scope.` | - |
| top_3x3_router | stitch | 2 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_3x3_router/rep1/iter2/sim.log:1 `dut.v:79: error: 'full_out_link4_vc4_r6' has already been declared in this scope.` | - |
| top_3x3_router | stitch | 3 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_3x3_router/rep1/iter3/sim.log:110 `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000` | UNUSEDSIGNAL, WIDTHEXPAND |
| top_3x3_router | stitch | 4 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_3x3_router/rep1/iter4/sim.log:1 `dut.v:101: error: 'full_out_link3_vc4_r9' has already been declared in this scope.` | - |
| top_3x3_router | stitch | 5 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_3x3_router/rep1/iter5/sim.log:20 `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000` | UNUSEDSIGNAL |
| top_3x3_router | stitch | 6 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_3x3_router/rep1/iter6/sim.log:1 `dut.v:97: error: 'full_out_link4_vc4_r8' has already been declared in this scope.` | - |
