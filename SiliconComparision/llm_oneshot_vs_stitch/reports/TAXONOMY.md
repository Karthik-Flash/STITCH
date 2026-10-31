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
| syntax | 11 | 4 | 4 |
| ports | 9 | 6 | 7 |
| function | 3 | 4 | 4 |
| multi-driven | 0 | 1 | 0 |
| width | 1 | 2 | 2 |
| timing | 1 | 3 | 3 |
| ok | 9 | 14 | 14 |

## What retrying changed: primary label of iteration 0 (one-shot input) -> final iteration

| change | simloop | stitch |
|---|---|---|
| function -> ok | 1 | 1 |
| function -> ports | 0 | 1 |
| ports -> function | 1 | 1 |
| ports -> ok | 3 | 3 |
| ports -> width | 1 | 1 |
| same | 21 | 20 |
| syntax -> function | 1 | 2 |
| syntax -> multi-driven | 1 | 0 |
| syntax -> ok | 1 | 1 |
| syntax -> ports | 2 | 2 |
| syntax -> timing | 2 | 2 |

## (a, b) Final files

| module | arm | primary label | cited line | all labels (first line each) |
|---|---|---|---|---|
| allot_vc | oneshot | ports | runs/analysis/oneshot/allot_vc/sim.log:1 `dut.v:13: error: 'gnt_or' has already been declared in this scope.` | ports (runs/analysis/oneshot/allot_vc/sim.log:1) |
| asynch_comparator | oneshot | syntax | runs/analysis/oneshot/asynch_comparator/sim.log:1 `dut.v:14: error: 'rd_pos' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/oneshot/asynch_comparator/sim.log:1) |
| demux_16 | oneshot | ports | runs/analysis/oneshot/demux_16/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | ports (runs/analysis/oneshot/demux_16/sim.log:1) |
| dff_asynch_clr | oneshot | syntax | runs/analysis/oneshot/dff_asynch_clr/sim.log:1 `dut.v:2: error: ';' is an invalid port declaration separator.` | syntax (runs/analysis/oneshot/dff_asynch_clr/sim.log:1) |
| dff_synch_clr | oneshot | ok | - | - |
| dff_synch_reset | oneshot | ok | - | - |
| dff_synch_set | oneshot | ok | - | - |
| encoder | oneshot | function | runs/analysis/oneshot/encoder/sim.log:1 `FAIL t=14000 cycle 0: encoded_addr = b, expected a` | function (runs/analysis/oneshot/encoder/sim.log:1) |
| falling_edge_pulse_generator | oneshot | syntax | runs/analysis/oneshot/falling_edge_pulse_generator/sim.log:1 `dut.v:37: error: 'q0_int' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/oneshot/falling_edge_pulse_generator/sim.log:1) |
| final_op_data | oneshot | ports | runs/analysis/oneshot/final_op_data/sim.log:1 `dut.v:8: error: 'data_out' has already been declared in this scope.` | ports (runs/analysis/oneshot/final_op_data/sim.log:1) |
| gray_mod6 | oneshot | syntax | runs/analysis/oneshot/gray_mod6/sim.log:1 `dut.v:31: error: 'j' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/oneshot/gray_mod6/sim.log:1) |
| ip_chnl | oneshot | ports | runs/analysis/oneshot/ip_chnl/sim.log:1 `dut.v:25: error: expression not valid in assign l-value: 2'd0` | ports (runs/analysis/oneshot/ip_chnl/sim.log:1), syntax (runs/analysis/oneshot/ip_chnl/sim.log:13), width (runs/analysis/oneshot/ip_chnl/verilator.log:6), multi-driven (runs/analysis/oneshot/ip_chnl/verilator.log:123) |
| ip_link | oneshot | function | runs/analysis/oneshot/ip_link/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | function (runs/analysis/oneshot/ip_link/sim.log:10), width (runs/analysis/oneshot/ip_link/verilator.log:123) |
| irs | oneshot | syntax | runs/analysis/oneshot/irs/sim.log:1 `dut.v:64: error: 'en4_w' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/oneshot/irs/sim.log:1) |
| jk_ff | oneshot | ok | - | - |
| memory | oneshot | ok | - | - |
| mux | oneshot | ok | - | - |
| op_core | oneshot | syntax | runs/analysis/oneshot/op_core/sim.log:25 `dut.v:283: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | syntax (runs/analysis/oneshot/op_core/sim.log:25), ports (runs/analysis/oneshot/op_core/sim.log:27), width (runs/analysis/oneshot/op_core/verilator.log:7) |
| op_data_path | oneshot | ports | runs/analysis/oneshot/op_data_path/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | ports (runs/analysis/oneshot/op_data_path/sim.log:1) |
| op_link1 | oneshot | width | runs/analysis/oneshot/op_link1/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | width (runs/analysis/oneshot/op_link1/sim.log:1), syntax (runs/analysis/oneshot/op_link1/sim.log:48) |
| op_link2 | oneshot | syntax | runs/analysis/oneshot/op_link2/sim.log:33 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/oneshot/op_link2/sim.log:33) |
| op_link3 | oneshot | ports | runs/analysis/oneshot/op_link3/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | ports (runs/analysis/oneshot/op_link3/sim.log:1), syntax (runs/analysis/oneshot/op_link3/sim.log:54) |
| op_link4 | oneshot | syntax | runs/analysis/oneshot/op_link4/sim.log:25 `dut.v:285: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | syntax (runs/analysis/oneshot/op_link4/sim.log:25), ports (runs/analysis/oneshot/op_link4/sim.log:27), width (runs/analysis/oneshot/op_link4/verilator.log:237) |
| priority_encoder | oneshot | ok | - | - |
| register_1bit | oneshot | ports | runs/analysis/oneshot/register_1bit/sim.log:1 `dut.v:6: error: 'dout' has already been declared in this scope.` | ports (runs/analysis/oneshot/register_1bit/sim.log:1) |
| register_32bit | oneshot | ok | - | - |
| register_4bit | oneshot | ok | - | - |
| round_robin_req | oneshot | ports | runs/analysis/oneshot/round_robin_req/sim.log:1 `dut.v:13: error: 'req_10' has already been declared in this scope.` | ports (runs/analysis/oneshot/round_robin_req/sim.log:1) |
| router_fifo | oneshot | timing | runs/analysis/oneshot/router_fifo/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | timing (runs/analysis/oneshot/router_fifo/sim.log:1) |
| routing_algo_mesh | oneshot | ports | runs/analysis/oneshot/routing_algo_mesh/sim.log:1 `dut.v:8: error: 'req_link1' has already been declared in this scope.` | ports (runs/analysis/oneshot/routing_algo_mesh/sim.log:1) |
| rr_arbiter | oneshot | syntax | runs/analysis/oneshot/rr_arbiter/sim.log:1 `dut.v:7: syntax error` | syntax (runs/analysis/oneshot/rr_arbiter/sim.log:1) |
| rr_comb_new | oneshot | syntax | runs/analysis/oneshot/rr_comb_new/sim.log:1 `dut.v:36: error: Unable to bind wire/reg/memory `r2_w' in `tb.dut'` | syntax (runs/analysis/oneshot/rr_comb_new/sim.log:1) |
| top_2x2_router | oneshot | function | runs/analysis/oneshot/top_2x2_router/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | function (runs/analysis/oneshot/top_2x2_router/sim.log:362), ports (runs/analysis/oneshot/top_2x2_router/verilator.log:1), width (runs/analysis/oneshot/top_2x2_router/verilator.log:323) |
| top_module | oneshot | syntax | runs/analysis/oneshot/top_module/sim.log:11 `dut.v:1349: error: 'req_l1_link1' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/oneshot/top_module/sim.log:11), ports (runs/analysis/oneshot/top_module/verilator.log:1), width (runs/analysis/oneshot/top_module/verilator.log:136) |
| allot_vc | simloop | function | runs/analysis/simloop/allot_vc/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | function (runs/analysis/simloop/allot_vc/sim.log:4), width (runs/analysis/simloop/allot_vc/verilator.log:1) |
| asynch_comparator | simloop | function | runs/analysis/simloop/asynch_comparator/sim.log:1 `FAIL t=84000 cycle 7: full_ext = 1, expected 0` | function (runs/analysis/simloop/asynch_comparator/sim.log:1) |
| demux_16 | simloop | ports | runs/analysis/simloop/demux_16/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | ports (runs/analysis/simloop/demux_16/sim.log:1) |
| dff_asynch_clr | simloop | ok | - | - |
| dff_synch_clr | simloop | ok | - | - |
| dff_synch_reset | simloop | ok | - | - |
| dff_synch_set | simloop | ok | - | - |
| encoder | simloop | ok | - | - |
| falling_edge_pulse_generator | simloop | syntax | runs/analysis/simloop/falling_edge_pulse_generator/sim.log:1 `dut.v:57: error: 'q0' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/simloop/falling_edge_pulse_generator/sim.log:1) |
| final_op_data | simloop | ok | - | - |
| gray_mod6 | simloop | timing | runs/analysis/simloop/gray_mod6/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | timing (runs/analysis/simloop/gray_mod6/sim.log:1) |
| ip_chnl | simloop | ports | runs/analysis/simloop/ip_chnl/sim.log:1 `dut.v:27: error: expression not valid in assign l-value: 2'd0` | ports (runs/analysis/simloop/ip_chnl/sim.log:1), syntax (runs/analysis/simloop/ip_chnl/sim.log:13), width (runs/analysis/simloop/ip_chnl/verilator.log:6), multi-driven (runs/analysis/simloop/ip_chnl/verilator.log:99) |
| ip_link | simloop | function | runs/analysis/simloop/ip_link/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | function (runs/analysis/simloop/ip_link/sim.log:10), width (runs/analysis/simloop/ip_link/verilator.log:123) |
| irs | simloop | timing | runs/analysis/simloop/irs/sim.log:1 `FAIL t=69000 cycle 5: rd_en_out = 0, expected 1` | timing (runs/analysis/simloop/irs/sim.log:1) |
| jk_ff | simloop | ok | - | - |
| memory | simloop | ok | - | - |
| mux | simloop | ok | - | - |
| op_core | simloop | ports | runs/analysis/simloop/op_core/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 4'd1` | ports (runs/analysis/simloop/op_core/sim.log:1), syntax (runs/analysis/simloop/op_core/sim.log:13), width (runs/analysis/simloop/op_core/verilator.log:1), multi-driven (runs/analysis/simloop/op_core/verilator.log:605) |
| op_data_path | simloop | ports | runs/analysis/simloop/op_data_path/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | ports (runs/analysis/simloop/op_data_path/sim.log:1) |
| op_link1 | simloop | width | runs/analysis/simloop/op_link1/sim.log:1 `dut.v:67: error: Index req[16] is out of range.` | width (runs/analysis/simloop/op_link1/sim.log:1), ports (runs/analysis/simloop/op_link1/sim.log:16), syntax (runs/analysis/simloop/op_link1/sim.log:18) |
| op_link2 | simloop | syntax | runs/analysis/simloop/op_link2/sim.log:9 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/simloop/op_link2/sim.log:9), width (runs/analysis/simloop/op_link2/verilator.log:279) |
| op_link3 | simloop | ports | runs/analysis/simloop/op_link3/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | ports (runs/analysis/simloop/op_link3/sim.log:1), syntax (runs/analysis/simloop/op_link3/sim.log:42) |
| op_link4 | simloop | syntax | runs/analysis/simloop/op_link4/sim.log:9 `dut.v:416: error: 'all_vc_not_busy' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/simloop/op_link4/sim.log:9), width (runs/analysis/simloop/op_link4/verilator.log:237) |
| priority_encoder | simloop | ok | - | - |
| register_1bit | simloop | ok | - | - |
| register_32bit | simloop | ok | - | - |
| register_4bit | simloop | ok | - | - |
| round_robin_req | simloop | width | runs/analysis/simloop/round_robin_req/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | width (runs/analysis/simloop/round_robin_req/sim.log:1), multi-driven (runs/analysis/simloop/round_robin_req/verilator.log:203), latch (runs/analysis/simloop/round_robin_req/verilator.log:310) |
| router_fifo | simloop | timing | runs/analysis/simloop/router_fifo/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | timing (runs/analysis/simloop/router_fifo/sim.log:1) |
| routing_algo_mesh | simloop | ok | - | - |
| rr_arbiter | simloop | syntax | runs/analysis/simloop/rr_arbiter/sim.log:1 `dut.v:7: syntax error` | syntax (runs/analysis/simloop/rr_arbiter/sim.log:1) |
| rr_comb_new | simloop | multi-driven | runs/analysis/simloop/rr_comb_new/sim.log:1 `dut.v:71: error: Cannot perform procedural assignment to variable 'g1_reg' because it is also continuously assigned.` | multi-driven (runs/analysis/simloop/rr_comb_new/sim.log:1) |
| top_2x2_router | simloop | function | runs/analysis/simloop/top_2x2_router/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | function (runs/analysis/simloop/top_2x2_router/sim.log:362), ports (runs/analysis/simloop/top_2x2_router/verilator.log:1), width (runs/analysis/simloop/top_2x2_router/verilator.log:323) |
| top_module | simloop | ports | runs/analysis/simloop/top_module/sim.log:1 `dut.v:111: error: port ``full_vc1'' already bound.` | ports (runs/analysis/simloop/top_module/sim.log:1), syntax (runs/analysis/simloop/top_module/sim.log:255) |
| allot_vc | stitch | function | runs/analysis/stitch/allot_vc/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | function (runs/analysis/stitch/allot_vc/sim.log:4), width (runs/analysis/stitch/allot_vc/verilator.log:7) |
| asynch_comparator | stitch | function | runs/analysis/stitch/asynch_comparator/sim.log:1 `FAIL t=84000 cycle 7: full_ext = 1, expected 0` | function (runs/analysis/stitch/asynch_comparator/sim.log:1) |
| demux_16 | stitch | ports | runs/analysis/stitch/demux_16/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | ports (runs/analysis/stitch/demux_16/sim.log:1) |
| dff_asynch_clr | stitch | ok | - | - |
| dff_synch_clr | stitch | ok | - | - |
| dff_synch_reset | stitch | ok | - | - |
| dff_synch_set | stitch | ok | - | - |
| encoder | stitch | ok | - | - |
| falling_edge_pulse_generator | stitch | timing | runs/analysis/stitch/falling_edge_pulse_generator/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | timing (runs/analysis/stitch/falling_edge_pulse_generator/sim.log:1) |
| final_op_data | stitch | ok | - | - |
| gray_mod6 | stitch | timing | runs/analysis/stitch/gray_mod6/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | timing (runs/analysis/stitch/gray_mod6/sim.log:1) |
| ip_chnl | stitch | ports | runs/analysis/stitch/ip_chnl/sim.log:1 `dut.v:28: error: expression not valid in assign l-value: 3'd0` | ports (runs/analysis/stitch/ip_chnl/sim.log:1), multi-driven (runs/analysis/stitch/ip_chnl/verilator.log:28) |
| ip_link | stitch | ports | runs/analysis/stitch/ip_link/sim.log:1 `dut.v:47: error: expression not valid in assign l-value: 1'd0` | ports (runs/analysis/stitch/ip_link/sim.log:1), syntax (runs/analysis/stitch/ip_link/sim.log:101), width (runs/analysis/stitch/ip_link/verilator.log:1), multi-driven (runs/analysis/stitch/ip_link/verilator.log:498) |
| irs | stitch | syntax | runs/analysis/stitch/irs/sim.log:1 `dut.v:121: error: 'rd_en_out' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/stitch/irs/sim.log:1) |
| jk_ff | stitch | ok | - | - |
| memory | stitch | ok | - | - |
| mux | stitch | ok | - | - |
| op_core | stitch | ports | runs/analysis/stitch/op_core/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 2'd1` | ports (runs/analysis/stitch/op_core/sim.log:1), syntax (runs/analysis/stitch/op_core/sim.log:13), width (runs/analysis/stitch/op_core/verilator.log:7), multi-driven (runs/analysis/stitch/op_core/verilator.log:665) |
| op_data_path | stitch | ports | runs/analysis/stitch/op_data_path/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | ports (runs/analysis/stitch/op_data_path/sim.log:1) |
| op_link1 | stitch | width | runs/analysis/stitch/op_link1/sim.log:1 `dut.v:70: error: Index req[16] is out of range.` | width (runs/analysis/stitch/op_link1/sim.log:1), syntax (runs/analysis/stitch/op_link1/sim.log:20) |
| op_link2 | stitch | syntax | runs/analysis/stitch/op_link2/sim.log:9 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/stitch/op_link2/sim.log:9), width (runs/analysis/stitch/op_link2/verilator.log:279) |
| op_link3 | stitch | ports | runs/analysis/stitch/op_link3/sim.log:1 `dut.v:250: error: port ``g1'' already bound.` | ports (runs/analysis/stitch/op_link3/sim.log:1), syntax (runs/analysis/stitch/op_link3/sim.log:42) |
| op_link4 | stitch | syntax | runs/analysis/stitch/op_link4/sim.log:9 `dut.v:416: error: 'all_vc_not_busy' is not a valid l-value for a procedural assignment.` | syntax (runs/analysis/stitch/op_link4/sim.log:9), width (runs/analysis/stitch/op_link4/verilator.log:231) |
| priority_encoder | stitch | ok | - | - |
| register_1bit | stitch | ok | - | - |
| register_32bit | stitch | ok | - | - |
| register_4bit | stitch | ok | - | - |
| round_robin_req | stitch | width | runs/analysis/stitch/round_robin_req/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | width (runs/analysis/stitch/round_robin_req/sim.log:1), syntax (runs/analysis/stitch/round_robin_req/sim.log:6) |
| router_fifo | stitch | timing | runs/analysis/stitch/router_fifo/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | timing (runs/analysis/stitch/router_fifo/sim.log:1) |
| routing_algo_mesh | stitch | ok | - | - |
| rr_arbiter | stitch | syntax | runs/analysis/stitch/rr_arbiter/sim.log:1 `dut.v:7: syntax error` | syntax (runs/analysis/stitch/rr_arbiter/sim.log:1) |
| rr_comb_new | stitch | function | runs/analysis/stitch/rr_comb_new/sim.log:1 `FAIL t=59000 cycle 4: g2 = 0, expected 1` | function (runs/analysis/stitch/rr_comb_new/sim.log:1), multi-driven (runs/analysis/stitch/rr_comb_new/yosys.log:86), latch (runs/analysis/stitch/rr_comb_new/yosys.log:100) |
| top_2x2_router | stitch | function | runs/analysis/stitch/top_2x2_router/sim.log:1 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | function (runs/analysis/stitch/top_2x2_router/sim.log:1) |
| top_module | stitch | ports | runs/analysis/stitch/top_module/sim.log:1 `dut.v:652: error: port ``data_to_link1_ch1'' is not a port of op_data_path_inst.` | ports (runs/analysis/stitch/top_module/sim.log:1), syntax (runs/analysis/stitch/top_module/sim.log:41) |

## (c) Per-iteration sequence (iteration 0 = the one-shot file; [STITCH: ...] = categories of the directives fed back after that iteration)

| module | arm | sequence |
|---|---|---|
| allot_vc | simloop | ports -> function -> function -> function -> function -> function -> function |
| asynch_comparator | simloop | syntax -> syntax -> function -> function -> function -> function -> function |
| demux_16 | simloop | ports -> ports -> ports -> ports -> ports -> ports -> ports |
| dff_asynch_clr | simloop | syntax -> ok |
| dff_synch_clr | simloop | ok |
| dff_synch_reset | simloop | ok |
| dff_synch_set | simloop | ok |
| encoder | simloop | function -> ok |
| falling_edge_pulse_generator | simloop | syntax -> timing -> timing -> timing -> timing -> timing -> syntax |
| final_op_data | simloop | ports -> ok |
| gray_mod6 | simloop | syntax -> timing -> timing -> timing -> timing -> timing -> timing |
| ip_chnl | simloop | ports -> ports -> ports -> ports -> ports -> ports -> ports |
| ip_link | simloop | function -> function -> function -> function -> function -> function -> function |
| irs | simloop | syntax -> syntax -> syntax -> syntax -> syntax -> timing -> timing |
| jk_ff | simloop | ok |
| memory | simloop | ok |
| mux | simloop | ok |
| op_core | simloop | syntax -> ports -> syntax -> ports -> ports -> ports -> ports |
| op_data_path | simloop | ports -> ports -> ports -> ports -> ports -> ports -> ports |
| op_link1 | simloop | width -> width -> width -> width -> width -> width -> width |
| op_link2 | simloop | syntax -> ports -> syntax -> ports -> syntax -> ports -> syntax |
| op_link3 | simloop | ports -> ports -> ports -> ports -> ports -> ports -> ports |
| op_link4 | simloop | syntax -> ports -> syntax -> ports -> syntax -> ports -> syntax |
| priority_encoder | simloop | ok |
| register_1bit | simloop | ports -> ok |
| register_32bit | simloop | ok |
| register_4bit | simloop | ok |
| round_robin_req | simloop | ports -> width -> width -> width -> width -> width -> width |
| router_fifo | simloop | timing -> timing -> timing -> timing -> timing -> timing -> timing |
| routing_algo_mesh | simloop | ports -> syntax -> ok |
| rr_arbiter | simloop | syntax -> syntax -> syntax -> syntax -> syntax -> syntax -> syntax |
| rr_comb_new | simloop | syntax -> function -> function -> multi-driven -> multi-driven -> multi-driven -> multi-driven |
| top_2x2_router | simloop | function -> function -> function -> function -> function -> function -> function |
| top_module | simloop | syntax -> syntax -> ports -> ports -> ports -> ports -> ports |
| allot_vc | stitch | ports -> function -> function -> function [STITCH: width] -> function -> function [restart] -> function |
| asynch_comparator | stitch | syntax -> syntax -> syntax -> syntax [restart] -> syntax -> syntax -> function |
| demux_16 | stitch | ports -> ports -> ports -> ports [restart] -> ports -> ports -> ports |
| dff_asynch_clr | stitch | syntax -> ok |
| dff_synch_clr | stitch | ok |
| dff_synch_reset | stitch | ok |
| dff_synch_set | stitch | ok |
| encoder | stitch | function -> ok |
| falling_edge_pulse_generator | stitch | syntax -> timing -> timing [STITCH: ports] -> timing [STITCH: ports] -> timing [STITCH: ports] [restart] -> timing [STITCH: ports] -> timing |
| final_op_data | stitch | ports -> ok |
| gray_mod6 | stitch | syntax -> timing -> timing -> timing [STITCH: ports] -> timing -> timing [STITCH: ports] -> timing |
| ip_chnl | stitch | ports -> ports [STITCH: ports, width] -> ports [STITCH: ports] -> ports [STITCH: ports] -> ports [STITCH: multi-driven, ports] -> ports [STITCH: ports, width] -> ports |
| ip_link | stitch | function -> function -> function [STITCH: ports, width] -> ports [STITCH: ports] -> ports [STITCH: ports, width] [restart] -> ports [STITCH: ports] -> ports |
| irs | stitch | syntax -> ports -> syntax -> syntax [STITCH: ports] -> syntax [STITCH: ports] -> syntax -> syntax |
| jk_ff | stitch | ok |
| memory | stitch | ok |
| mux | stitch | ok |
| op_core | stitch | syntax -> ports -> syntax -> ports -> ports -> ports [STITCH: ports, width] -> ports |
| op_data_path | stitch | ports -> ports -> ports -> ports [restart] -> ports -> ports -> ports |
| op_link1 | stitch | width -> width -> width -> width [STITCH: ports, width] -> width [STITCH: ports] -> width [STITCH: ports, width] [restart] -> width |
| op_link2 | stitch | syntax -> ports [STITCH: ports] -> syntax [STITCH: ports, width] -> ports [STITCH: ports] -> syntax [STITCH: ports, width] -> ports [STITCH: ports] -> syntax |
| op_link3 | stitch | ports -> ports [STITCH: ports] -> ports [STITCH: ports] -> ports [STITCH: ports] [restart] -> ports [STITCH: ports] -> ports [STITCH: ports] -> ports |
| op_link4 | stitch | syntax -> ports -> syntax -> ports -> syntax -> ports -> syntax |
| priority_encoder | stitch | ok |
| register_1bit | stitch | ports -> ports -> ok |
| register_32bit | stitch | ok |
| register_4bit | stitch | ok |
| round_robin_req | stitch | ports -> width -> width [STITCH: latch, ports, width] -> width [STITCH: latch, ports, width] -> width [STITCH: ports, width] -> width [STITCH: width] -> width |
| router_fifo | stitch | timing -> timing -> timing -> timing [restart] -> timing -> timing -> timing |
| routing_algo_mesh | stitch | ports -> syntax -> ok |
| rr_arbiter | stitch | syntax -> syntax -> syntax -> syntax [restart] -> syntax -> syntax -> syntax |
| rr_comb_new | stitch | syntax -> function -> multi-driven -> multi-driven [STITCH: ports] -> multi-driven -> multi-driven [restart] -> function |
| top_2x2_router | stitch | function -> function [STITCH: ports, width] -> function [STITCH: ports] -> function [STITCH: ports, width] [restart] -> function [STITCH: ports] -> function [STITCH: ports] -> function |
| top_module | stitch | syntax -> syntax -> ports -> ports -> ports -> ports [STITCH: ports] -> ports |

### Per-iteration citations

| module | arm | iter | label | cited line | directive codes fed back |
|---|---|---|---|---|---|
| allot_vc | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/allot_vc/rep1/iter0/sim.log:1 `dut.v:13: error: 'gnt_or' has already been declared in this scope.` | - |
| allot_vc | simloop | 1 | function | runs/arms/results/qwen2.5-coder_32b/baseline/allot_vc/rep1/iter1/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| allot_vc | simloop | 2 | function | runs/arms/results/qwen2.5-coder_32b/baseline/allot_vc/rep1/iter2/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| allot_vc | simloop | 3 | function | runs/arms/results/qwen2.5-coder_32b/baseline/allot_vc/rep1/iter3/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| allot_vc | simloop | 4 | function | runs/arms/results/qwen2.5-coder_32b/baseline/allot_vc/rep1/iter4/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| allot_vc | simloop | 5 | function | runs/arms/results/qwen2.5-coder_32b/baseline/allot_vc/rep1/iter5/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| allot_vc | simloop | 6 | function | runs/arms/results/qwen2.5-coder_32b/baseline/allot_vc/rep1/iter6/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| asynch_comparator | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/asynch_comparator/rep1/iter0/sim.log:1 `dut.v:14: error: 'rd_pos' is not a valid l-value for a procedural assignment.` | - |
| asynch_comparator | simloop | 1 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/asynch_comparator/rep1/iter1/sim.log:1 `dut.v:42: error: 'diff' is not a valid l-value for a procedural assignment.` | - |
| asynch_comparator | simloop | 2 | function | runs/arms/results/qwen2.5-coder_32b/baseline/asynch_comparator/rep1/iter2/sim.log:1 `FAIL t=84000 cycle 7: full_ext = 1, expected 0` | - |
| asynch_comparator | simloop | 3 | function | runs/arms/results/qwen2.5-coder_32b/baseline/asynch_comparator/rep1/iter3/sim.log:1 `FAIL t=84000 cycle 7: full_ext = 1, expected 0` | - |
| asynch_comparator | simloop | 4 | function | runs/arms/results/qwen2.5-coder_32b/baseline/asynch_comparator/rep1/iter4/sim.log:1 `FAIL t=84000 cycle 7: full_ext = 1, expected 0` | - |
| asynch_comparator | simloop | 5 | function | runs/arms/results/qwen2.5-coder_32b/baseline/asynch_comparator/rep1/iter5/sim.log:1 `FAIL t=84000 cycle 7: full_ext = 1, expected 0` | - |
| asynch_comparator | simloop | 6 | function | runs/arms/results/qwen2.5-coder_32b/baseline/asynch_comparator/rep1/iter6/sim.log:1 `FAIL t=84000 cycle 7: full_ext = 1, expected 0` | - |
| demux_16 | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/demux_16/rep1/iter0/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | simloop | 1 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/demux_16/rep1/iter1/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | simloop | 2 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/demux_16/rep1/iter2/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | simloop | 3 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/demux_16/rep1/iter3/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | simloop | 4 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/demux_16/rep1/iter4/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | simloop | 5 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/demux_16/rep1/iter5/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | simloop | 6 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/demux_16/rep1/iter6/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| dff_asynch_clr | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/dff_asynch_clr/rep1/iter0/sim.log:1 `dut.v:2: error: ';' is an invalid port declaration separator.` | - |
| dff_asynch_clr | simloop | 1 | ok | - | - |
| dff_synch_clr | simloop | 0 | ok | - | - |
| dff_synch_reset | simloop | 0 | ok | - | - |
| dff_synch_set | simloop | 0 | ok | - | - |
| encoder | simloop | 0 | function | runs/arms/results/qwen2.5-coder_32b/baseline/encoder/rep1/iter0/sim.log:1 `FAIL t=14000 cycle 0: encoded_addr = b, expected a` | - |
| encoder | simloop | 1 | ok | - | - |
| falling_edge_pulse_generator | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/falling_edge_pulse_generator/rep1/iter0/sim.log:1 `dut.v:37: error: 'q0_int' is not a valid l-value for a procedural assignment.` | - |
| falling_edge_pulse_generator | simloop | 1 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/falling_edge_pulse_generator/rep1/iter1/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | - |
| falling_edge_pulse_generator | simloop | 2 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/falling_edge_pulse_generator/rep1/iter2/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | - |
| falling_edge_pulse_generator | simloop | 3 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/falling_edge_pulse_generator/rep1/iter3/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | - |
| falling_edge_pulse_generator | simloop | 4 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/falling_edge_pulse_generator/rep1/iter4/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | - |
| falling_edge_pulse_generator | simloop | 5 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/falling_edge_pulse_generator/rep1/iter5/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | - |
| falling_edge_pulse_generator | simloop | 6 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/falling_edge_pulse_generator/rep1/iter6/sim.log:1 `dut.v:57: error: 'q0' is not a valid l-value for a procedural assignment.` | - |
| final_op_data | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/final_op_data/rep1/iter0/sim.log:1 `dut.v:8: error: 'data_out' has already been declared in this scope.` | - |
| final_op_data | simloop | 1 | ok | - | - |
| gray_mod6 | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/gray_mod6/rep1/iter0/sim.log:1 `dut.v:31: error: 'j' is not a valid l-value for a procedural assignment.` | - |
| gray_mod6 | simloop | 1 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/gray_mod6/rep1/iter1/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 0, expected 1` | - |
| gray_mod6 | simloop | 2 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/gray_mod6/rep1/iter2/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | - |
| gray_mod6 | simloop | 3 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/gray_mod6/rep1/iter3/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | - |
| gray_mod6 | simloop | 4 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/gray_mod6/rep1/iter4/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | - |
| gray_mod6 | simloop | 5 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/gray_mod6/rep1/iter5/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | - |
| gray_mod6 | simloop | 6 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/gray_mod6/rep1/iter6/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | - |
| ip_chnl | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/ip_chnl/rep1/iter0/sim.log:1 `dut.v:25: error: expression not valid in assign l-value: 2'd0` | - |
| ip_chnl | simloop | 1 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/ip_chnl/rep1/iter1/sim.log:1 `dut.v:25: error: expression not valid in assign l-value: 2'd0` | - |
| ip_chnl | simloop | 2 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/ip_chnl/rep1/iter2/sim.log:1 `dut.v:27: error: expression not valid in assign l-value: 2'd0` | - |
| ip_chnl | simloop | 3 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/ip_chnl/rep1/iter3/sim.log:1 `dut.v:27: error: expression not valid in assign l-value: 2'd0` | - |
| ip_chnl | simloop | 4 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/ip_chnl/rep1/iter4/sim.log:1 `dut.v:27: error: expression not valid in assign l-value: 2'd0` | - |
| ip_chnl | simloop | 5 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/ip_chnl/rep1/iter5/sim.log:1 `dut.v:27: error: expression not valid in assign l-value: 2'd0` | - |
| ip_chnl | simloop | 6 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/ip_chnl/rep1/iter6/sim.log:1 `dut.v:27: error: expression not valid in assign l-value: 2'd0` | - |
| ip_link | simloop | 0 | function | runs/arms/results/qwen2.5-coder_32b/baseline/ip_link/rep1/iter0/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | - |
| ip_link | simloop | 1 | function | runs/arms/results/qwen2.5-coder_32b/baseline/ip_link/rep1/iter1/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | - |
| ip_link | simloop | 2 | function | runs/arms/results/qwen2.5-coder_32b/baseline/ip_link/rep1/iter2/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | - |
| ip_link | simloop | 3 | function | runs/arms/results/qwen2.5-coder_32b/baseline/ip_link/rep1/iter3/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | - |
| ip_link | simloop | 4 | function | runs/arms/results/qwen2.5-coder_32b/baseline/ip_link/rep1/iter4/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | - |
| ip_link | simloop | 5 | function | runs/arms/results/qwen2.5-coder_32b/baseline/ip_link/rep1/iter5/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | - |
| ip_link | simloop | 6 | function | runs/arms/results/qwen2.5-coder_32b/baseline/ip_link/rep1/iter6/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | - |
| irs | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/irs/rep1/iter0/sim.log:1 `dut.v:64: error: 'en4_w' is not a valid l-value for a procedural assignment.` | - |
| irs | simloop | 1 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/irs/rep1/iter1/sim.log:1 `dut.v:11: error: Unable to bind wire/reg/memory `en4_w' in `tb.dut'` | - |
| irs | simloop | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/irs/rep1/iter2/sim.log:1 `dut.v:11: error: Unable to bind wire/reg/memory `en4_w' in `tb.dut'` | - |
| irs | simloop | 3 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/irs/rep1/iter3/sim.log:1 `dut.v:11: error: Unable to bind wire/reg/memory `en4_next' in `tb.dut'` | - |
| irs | simloop | 4 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/irs/rep1/iter4/sim.log:1 `dut.v:11: error: Unable to bind wire/reg/memory `en4_next' in `tb.dut'` | - |
| irs | simloop | 5 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/irs/rep1/iter5/sim.log:1 `FAIL t=69000 cycle 5: rd_en_out = 0, expected 1` | - |
| irs | simloop | 6 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/irs/rep1/iter6/sim.log:1 `FAIL t=69000 cycle 5: rd_en_out = 0, expected 1` | - |
| jk_ff | simloop | 0 | ok | - | - |
| memory | simloop | 0 | ok | - | - |
| mux | simloop | 0 | ok | - | - |
| op_core | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/op_core/rep1/iter0/sim.log:25 `dut.v:283: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | - |
| op_core | simloop | 1 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_core/rep1/iter1/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 3'd0` | - |
| op_core | simloop | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/op_core/rep1/iter2/sim.log:9 `dut.v:283: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | - |
| op_core | simloop | 3 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_core/rep1/iter3/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 4'd1` | - |
| op_core | simloop | 4 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_core/rep1/iter4/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 4'd1` | - |
| op_core | simloop | 5 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_core/rep1/iter5/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 4'd1` | - |
| op_core | simloop | 6 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_core/rep1/iter6/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 4'd1` | - |
| op_data_path | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_data_path/rep1/iter0/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | simloop | 1 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_data_path/rep1/iter1/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | simloop | 2 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_data_path/rep1/iter2/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | simloop | 3 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_data_path/rep1/iter3/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | simloop | 4 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_data_path/rep1/iter4/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | simloop | 5 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_data_path/rep1/iter5/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | simloop | 6 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_data_path/rep1/iter6/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_link1 | simloop | 0 | width | runs/arms/results/qwen2.5-coder_32b/baseline/op_link1/rep1/iter0/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | - |
| op_link1 | simloop | 1 | width | runs/arms/results/qwen2.5-coder_32b/baseline/op_link1/rep1/iter1/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | - |
| op_link1 | simloop | 2 | width | runs/arms/results/qwen2.5-coder_32b/baseline/op_link1/rep1/iter2/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | - |
| op_link1 | simloop | 3 | width | runs/arms/results/qwen2.5-coder_32b/baseline/op_link1/rep1/iter3/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | - |
| op_link1 | simloop | 4 | width | runs/arms/results/qwen2.5-coder_32b/baseline/op_link1/rep1/iter4/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | - |
| op_link1 | simloop | 5 | width | runs/arms/results/qwen2.5-coder_32b/baseline/op_link1/rep1/iter5/sim.log:1 `dut.v:67: error: Index req[16] is out of range.` | - |
| op_link1 | simloop | 6 | width | runs/arms/results/qwen2.5-coder_32b/baseline/op_link1/rep1/iter6/sim.log:1 `dut.v:67: error: Index req[16] is out of range.` | - |
| op_link2 | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/op_link2/rep1/iter0/sim.log:33 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | - |
| op_link2 | simloop | 1 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link2/rep1/iter1/sim.log:1 `dut.v:266: error: expression not valid in assign l-value: 3'd0` | - |
| op_link2 | simloop | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/op_link2/rep1/iter2/sim.log:9 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | - |
| op_link2 | simloop | 3 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link2/rep1/iter3/sim.log:1 `dut.v:266: error: expression not valid in assign l-value: 3'd0` | - |
| op_link2 | simloop | 4 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/op_link2/rep1/iter4/sim.log:9 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | - |
| op_link2 | simloop | 5 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link2/rep1/iter5/sim.log:1 `dut.v:266: error: expression not valid in assign l-value: 3'd0` | - |
| op_link2 | simloop | 6 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/op_link2/rep1/iter6/sim.log:9 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | - |
| op_link3 | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link3/rep1/iter0/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | - |
| op_link3 | simloop | 1 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link3/rep1/iter1/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | - |
| op_link3 | simloop | 2 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link3/rep1/iter2/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | - |
| op_link3 | simloop | 3 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link3/rep1/iter3/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | - |
| op_link3 | simloop | 4 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link3/rep1/iter4/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | - |
| op_link3 | simloop | 5 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link3/rep1/iter5/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | - |
| op_link3 | simloop | 6 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link3/rep1/iter6/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | - |
| op_link4 | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/op_link4/rep1/iter0/sim.log:25 `dut.v:285: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | - |
| op_link4 | simloop | 1 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link4/rep1/iter1/sim.log:1 `dut.v:275: error: expression not valid in assign l-value: 3'd0` | - |
| op_link4 | simloop | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/op_link4/rep1/iter2/sim.log:9 `dut.v:285: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | - |
| op_link4 | simloop | 3 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link4/rep1/iter3/sim.log:1 `dut.v:275: error: expression not valid in assign l-value: (4'd1)&({e1, e1, e1, e1})` | - |
| op_link4 | simloop | 4 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/op_link4/rep1/iter4/sim.log:9 `dut.v:285: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | - |
| op_link4 | simloop | 5 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/op_link4/rep1/iter5/sim.log:1 `dut.v:275: error: expression not valid in assign l-value: (4'd1)&({e1, e1, e1, e1})` | - |
| op_link4 | simloop | 6 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/op_link4/rep1/iter6/sim.log:9 `dut.v:416: error: 'all_vc_not_busy' is not a valid l-value for a procedural assignment.` | - |
| priority_encoder | simloop | 0 | ok | - | - |
| register_1bit | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/register_1bit/rep1/iter0/sim.log:1 `dut.v:6: error: 'dout' has already been declared in this scope.` | - |
| register_1bit | simloop | 1 | ok | - | - |
| register_32bit | simloop | 0 | ok | - | - |
| register_4bit | simloop | 0 | ok | - | - |
| round_robin_req | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/round_robin_req/rep1/iter0/sim.log:1 `dut.v:13: error: 'req_10' has already been declared in this scope.` | - |
| round_robin_req | simloop | 1 | width | runs/arms/results/qwen2.5-coder_32b/baseline/round_robin_req/rep1/iter1/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | - |
| round_robin_req | simloop | 2 | width | runs/arms/results/qwen2.5-coder_32b/baseline/round_robin_req/rep1/iter2/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | - |
| round_robin_req | simloop | 3 | width | runs/arms/results/qwen2.5-coder_32b/baseline/round_robin_req/rep1/iter3/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | - |
| round_robin_req | simloop | 4 | width | runs/arms/results/qwen2.5-coder_32b/baseline/round_robin_req/rep1/iter4/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | - |
| round_robin_req | simloop | 5 | width | runs/arms/results/qwen2.5-coder_32b/baseline/round_robin_req/rep1/iter5/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | - |
| round_robin_req | simloop | 6 | width | runs/arms/results/qwen2.5-coder_32b/baseline/round_robin_req/rep1/iter6/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | - |
| router_fifo | simloop | 0 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/router_fifo/rep1/iter0/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | simloop | 1 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/router_fifo/rep1/iter1/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | simloop | 2 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/router_fifo/rep1/iter2/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | simloop | 3 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/router_fifo/rep1/iter3/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | simloop | 4 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/router_fifo/rep1/iter4/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | simloop | 5 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/router_fifo/rep1/iter5/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | simloop | 6 | timing | runs/arms/results/qwen2.5-coder_32b/baseline/router_fifo/rep1/iter6/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| routing_algo_mesh | simloop | 0 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/routing_algo_mesh/rep1/iter0/sim.log:1 `dut.v:8: error: 'req_link1' has already been declared in this scope.` | - |
| routing_algo_mesh | simloop | 1 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/routing_algo_mesh/rep1/iter1/sim.log:1 `dut.v:18: error: 'req_link1_w' is not a valid l-value for a procedural assignment.` | - |
| routing_algo_mesh | simloop | 2 | ok | - | - |
| rr_arbiter | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/rr_arbiter/rep1/iter0/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | simloop | 1 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/rr_arbiter/rep1/iter1/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | simloop | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/rr_arbiter/rep1/iter2/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | simloop | 3 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/rr_arbiter/rep1/iter3/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | simloop | 4 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/rr_arbiter/rep1/iter4/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | simloop | 5 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/rr_arbiter/rep1/iter5/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | simloop | 6 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/rr_arbiter/rep1/iter6/sim.log:1 `dut.v:7: syntax error` | - |
| rr_comb_new | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/rr_comb_new/rep1/iter0/sim.log:1 `dut.v:36: error: Unable to bind wire/reg/memory `r2_w' in `tb.dut'` | - |
| rr_comb_new | simloop | 1 | function | runs/arms/results/qwen2.5-coder_32b/baseline/rr_comb_new/rep1/iter1/sim.log:1 `FAIL t=59000 cycle 4: g2 = 0, expected 1` | - |
| rr_comb_new | simloop | 2 | function | runs/arms/results/qwen2.5-coder_32b/baseline/rr_comb_new/rep1/iter2/sim.log:1 `FAIL t=59000 cycle 4: g2 = 0, expected 1` | - |
| rr_comb_new | simloop | 3 | multi-driven | runs/arms/results/qwen2.5-coder_32b/baseline/rr_comb_new/rep1/iter3/sim.log:1 `dut.v:71: error: Cannot perform procedural assignment to variable 'g1_reg' because it is also continuously assigned.` | - |
| rr_comb_new | simloop | 4 | multi-driven | runs/arms/results/qwen2.5-coder_32b/baseline/rr_comb_new/rep1/iter4/sim.log:1 `dut.v:71: error: Cannot perform procedural assignment to variable 'g1_reg' because it is also continuously assigned.` | - |
| rr_comb_new | simloop | 5 | multi-driven | runs/arms/results/qwen2.5-coder_32b/baseline/rr_comb_new/rep1/iter5/sim.log:1 `dut.v:71: error: Cannot perform procedural assignment to variable 'g1_reg' because it is also continuously assigned.` | - |
| rr_comb_new | simloop | 6 | multi-driven | runs/arms/results/qwen2.5-coder_32b/baseline/rr_comb_new/rep1/iter6/sim.log:1 `dut.v:71: error: Cannot perform procedural assignment to variable 'g1_reg' because it is also continuously assigned.` | - |
| top_2x2_router | simloop | 0 | function | runs/arms/results/qwen2.5-coder_32b/baseline/top_2x2_router/rep1/iter0/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | - |
| top_2x2_router | simloop | 1 | function | runs/arms/results/qwen2.5-coder_32b/baseline/top_2x2_router/rep1/iter1/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | - |
| top_2x2_router | simloop | 2 | function | runs/arms/results/qwen2.5-coder_32b/baseline/top_2x2_router/rep1/iter2/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | - |
| top_2x2_router | simloop | 3 | function | runs/arms/results/qwen2.5-coder_32b/baseline/top_2x2_router/rep1/iter3/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | - |
| top_2x2_router | simloop | 4 | function | runs/arms/results/qwen2.5-coder_32b/baseline/top_2x2_router/rep1/iter4/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | - |
| top_2x2_router | simloop | 5 | function | runs/arms/results/qwen2.5-coder_32b/baseline/top_2x2_router/rep1/iter5/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | - |
| top_2x2_router | simloop | 6 | function | runs/arms/results/qwen2.5-coder_32b/baseline/top_2x2_router/rep1/iter6/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | - |
| top_module | simloop | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/baseline/top_module/rep1/iter0/sim.log:11 `dut.v:1349: error: 'req_l1_link1' is not a valid l-value for a procedural assignment.` | - |
| top_module | simloop | 1 | syntax | unmapped compile error | - |
| top_module | simloop | 2 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/top_module/rep1/iter2/sim.log:1 `dut.v:101: error: 'full_out_link1_vc1' has already been declared in this scope.` | - |
| top_module | simloop | 3 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/top_module/rep1/iter3/sim.log:1 `dut.v:101: error: 'full_out_link1_vc1' has already been declared in this scope.` | - |
| top_module | simloop | 4 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/top_module/rep1/iter4/sim.log:1 `dut.v:107: error: 'sel_vc_link1' has already been declared in this scope.` | - |
| top_module | simloop | 5 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/top_module/rep1/iter5/sim.log:1 `dut.v:111: error: port ``tailer_link1_vc1'' is not a port of ip_link1_inst.` | - |
| top_module | simloop | 6 | ports | runs/arms/results/qwen2.5-coder_32b/baseline/top_module/rep1/iter6/sim.log:1 `dut.v:111: error: port ``full_vc1'' already bound.` | - |
| allot_vc | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/allot_vc/rep1/iter0/sim.log:1 `dut.v:13: error: 'gnt_or' has already been declared in this scope.` | - |
| allot_vc | stitch | 1 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/allot_vc/rep1/iter1/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| allot_vc | stitch | 2 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/allot_vc/rep1/iter2/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| allot_vc | stitch | 3 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/allot_vc/rep1/iter3/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | WIDTHEXPAND, WIDTHTRUNC |
| allot_vc | stitch | 4 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/allot_vc/rep1/iter4/sim.log:1 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| allot_vc | stitch | 5 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/allot_vc/rep1/iter5/sim.log:1 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| allot_vc | stitch | 6 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/allot_vc/rep1/iter6/sim.log:4 `FAIL t=59000 cycle 4: link_1 = 0, expected 2` | - |
| asynch_comparator | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/asynch_comparator/rep1/iter0/sim.log:1 `dut.v:14: error: 'rd_pos' is not a valid l-value for a procedural assignment.` | - |
| asynch_comparator | stitch | 1 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/asynch_comparator/rep1/iter1/sim.log:1 `dut.v:42: error: 'diff' is not a valid l-value for a procedural assignment.` | - |
| asynch_comparator | stitch | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/asynch_comparator/rep1/iter2/sim.log:1 `dut.v:58: error: 'empty' is not a valid l-value for a procedural assignment.` | - |
| asynch_comparator | stitch | 3 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/asynch_comparator/rep1/iter3/sim.log:1 `dut.v:15: error: 'rd_pos' is not a valid l-value for a procedural assignment.` | - |
| asynch_comparator | stitch | 4 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/asynch_comparator/rep1/iter4/sim.log:1 `dut.v:58: error: 'empty' is not a valid l-value for a procedural assignment.` | - |
| asynch_comparator | stitch | 5 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/asynch_comparator/rep1/iter5/sim.log:1 `dut.v:15: error: 'rd_pos' is not a valid l-value for a procedural assignment.` | - |
| asynch_comparator | stitch | 6 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/asynch_comparator/rep1/iter6/sim.log:1 `FAIL t=84000 cycle 7: full_ext = 1, expected 0` | - |
| demux_16 | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/demux_16/rep1/iter0/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/demux_16/rep1/iter1/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | stitch | 2 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/demux_16/rep1/iter2/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | stitch | 3 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/demux_16/rep1/iter3/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | stitch | 4 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/demux_16/rep1/iter4/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/demux_16/rep1/iter5/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| demux_16 | stitch | 6 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/demux_16/rep1/iter6/sim.log:1 `dut.v:7: error: 'op1' has already been declared in this scope.` | - |
| dff_asynch_clr | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/dff_asynch_clr/rep1/iter0/sim.log:1 `dut.v:2: error: ';' is an invalid port declaration separator.` | - |
| dff_asynch_clr | stitch | 1 | ok | - | - |
| dff_synch_clr | stitch | 0 | ok | - | - |
| dff_synch_reset | stitch | 0 | ok | - | - |
| dff_synch_set | stitch | 0 | ok | - | - |
| encoder | stitch | 0 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/encoder/rep1/iter0/sim.log:1 `FAIL t=14000 cycle 0: encoded_addr = b, expected a` | - |
| encoder | stitch | 1 | ok | - | - |
| falling_edge_pulse_generator | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/falling_edge_pulse_generator/rep1/iter0/sim.log:1 `dut.v:37: error: 'q0_int' is not a valid l-value for a procedural assignment.` | - |
| falling_edge_pulse_generator | stitch | 1 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/falling_edge_pulse_generator/rep1/iter1/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | - |
| falling_edge_pulse_generator | stitch | 2 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/falling_edge_pulse_generator/rep1/iter2/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | UNUSEDSIGNAL |
| falling_edge_pulse_generator | stitch | 3 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/falling_edge_pulse_generator/rep1/iter3/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | UNUSEDSIGNAL |
| falling_edge_pulse_generator | stitch | 4 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/falling_edge_pulse_generator/rep1/iter4/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | UNUSEDSIGNAL |
| falling_edge_pulse_generator | stitch | 5 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/falling_edge_pulse_generator/rep1/iter5/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | UNUSEDSIGNAL |
| falling_edge_pulse_generator | stitch | 6 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/falling_edge_pulse_generator/rep1/iter6/sim.log:1 `FAIL t=84000 cycle 7: q0 = 0, expected 1` | - |
| final_op_data | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/final_op_data/rep1/iter0/sim.log:1 `dut.v:8: error: 'data_out' has already been declared in this scope.` | - |
| final_op_data | stitch | 1 | ok | - | - |
| gray_mod6 | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/gray_mod6/rep1/iter0/sim.log:1 `dut.v:31: error: 'j' is not a valid l-value for a procedural assignment.` | - |
| gray_mod6 | stitch | 1 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/gray_mod6/rep1/iter1/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 0, expected 1` | - |
| gray_mod6 | stitch | 2 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/gray_mod6/rep1/iter2/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | - |
| gray_mod6 | stitch | 3 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/gray_mod6/rep1/iter3/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | UNUSEDSIGNAL |
| gray_mod6 | stitch | 4 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/gray_mod6/rep1/iter4/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 0, expected 1` | - |
| gray_mod6 | stitch | 5 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/gray_mod6/rep1/iter5/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | UNUSEDSIGNAL |
| gray_mod6 | stitch | 6 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/gray_mod6/rep1/iter6/sim.log:1 `FAIL t=69000 cycle 5: gray_out = 6, expected 1` | - |
| ip_chnl | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_chnl/rep1/iter0/sim.log:1 `dut.v:25: error: expression not valid in assign l-value: 2'd0` | - |
| ip_chnl | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_chnl/rep1/iter1/sim.log:1 `dut.v:25: error: expression not valid in assign l-value: 2'd0` | PINMISSING, UNDRIVEN, WIDTHTRUNC |
| ip_chnl | stitch | 2 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_chnl/rep1/iter2/sim.log:1 `dut.v:27: error: expression not valid in assign l-value: 3'd0` | PINMISSING, UNUSEDSIGNAL |
| ip_chnl | stitch | 3 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_chnl/rep1/iter3/sim.log:1 `dut.v:27: error: expression not valid in assign l-value: 3'd0` | PINMISSING, UNUSEDSIGNAL |
| ip_chnl | stitch | 4 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_chnl/rep1/iter4/sim.log:1 `dut.v:27: error: expression not valid in assign l-value: 3'd0` | MULTIDRIVEN, PINMISSING, UNUSEDSIGNAL |
| ip_chnl | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_chnl/rep1/iter5/sim.log:1 `dut.v:28: error: expression not valid in assign l-value: 3'd0` | PINMISSING, WIDTHEXPAND, WIDTHTRUNC |
| ip_chnl | stitch | 6 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_chnl/rep1/iter6/sim.log:1 `dut.v:28: error: expression not valid in assign l-value: 3'd0` | - |
| ip_link | stitch | 0 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_link/rep1/iter0/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | - |
| ip_link | stitch | 1 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_link/rep1/iter1/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | - |
| ip_link | stitch | 2 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_link/rep1/iter2/sim.log:10 `FAIL t=69000 cycle 5: data_out_vc3 = 60000000, expected 54e2c721` | PINMISSING, WIDTHEXPAND, WIDTHTRUNC |
| ip_link | stitch | 3 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_link/rep1/iter3/sim.log:1 `dut.v:62: error: expression not valid in assign l-value: 1'd0` | PINMISSING, UNUSEDSIGNAL |
| ip_link | stitch | 4 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_link/rep1/iter4/sim.log:1 `dut.v:62: error: expression not valid in assign l-value: 1'd0` | PINMISSING, WIDTHEXPAND, WIDTHTRUNC |
| ip_link | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_link/rep1/iter5/sim.log:1 `dut.v:42: error: expression not valid in assign l-value: 1'd0` | PINMISSING, UNUSEDSIGNAL |
| ip_link | stitch | 6 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/ip_link/rep1/iter6/sim.log:1 `dut.v:47: error: expression not valid in assign l-value: 1'd0` | - |
| irs | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/irs/rep1/iter0/sim.log:1 `dut.v:64: error: 'en4_w' is not a valid l-value for a procedural assignment.` | - |
| irs | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/irs/rep1/iter1/sim.log:1 `dut.v:96: error: 'data_sel_w' has already been declared in this scope.` | - |
| irs | stitch | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/irs/rep1/iter2/sim.log:1 `dut.v:11: error: Unable to bind wire/reg/memory `en4_w' in `tb.dut'` | - |
| irs | stitch | 3 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/irs/rep1/iter3/sim.log:1 `dut.v:11: error: Unable to bind wire/reg/memory `en4_w' in `tb.dut'` | UNUSEDSIGNAL |
| irs | stitch | 4 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/irs/rep1/iter4/sim.log:1 `dut.v:11: error: Unable to bind wire/reg/memory `en4_next' in `tb.dut'` | UNUSEDSIGNAL |
| irs | stitch | 5 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/irs/rep1/iter5/sim.log:1 `dut.v:11: error: Unable to bind wire/reg/memory `en4_next' in `tb.dut'` | - |
| irs | stitch | 6 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/irs/rep1/iter6/sim.log:1 `dut.v:121: error: 'rd_en_out' is not a valid l-value for a procedural assignment.` | - |
| jk_ff | stitch | 0 | ok | - | - |
| memory | stitch | 0 | ok | - | - |
| mux | stitch | 0 | ok | - | - |
| op_core | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_core/rep1/iter0/sim.log:25 `dut.v:283: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | - |
| op_core | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_core/rep1/iter1/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 3'd0` | - |
| op_core | stitch | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_core/rep1/iter2/sim.log:9 `dut.v:283: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | - |
| op_core | stitch | 3 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_core/rep1/iter3/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 4'd1` | - |
| op_core | stitch | 4 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_core/rep1/iter4/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 4'd1` | - |
| op_core | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_core/rep1/iter5/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 4'd1` | UNUSEDSIGNAL, WIDTHTRUNC |
| op_core | stitch | 6 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_core/rep1/iter6/sim.log:1 `dut.v:273: error: expression not valid in assign l-value: 2'd1` | - |
| op_data_path | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_data_path/rep1/iter0/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_data_path/rep1/iter1/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | stitch | 2 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_data_path/rep1/iter2/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | stitch | 3 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_data_path/rep1/iter3/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | stitch | 4 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_data_path/rep1/iter4/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_data_path/rep1/iter5/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_data_path | stitch | 6 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_data_path/rep1/iter6/sim.log:1 `dut.v:17: error: 'data_out_l1' has already been declared in this scope.` | - |
| op_link1 | stitch | 0 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link1/rep1/iter0/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | - |
| op_link1 | stitch | 1 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link1/rep1/iter1/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | - |
| op_link1 | stitch | 2 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link1/rep1/iter2/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | - |
| op_link1 | stitch | 3 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link1/rep1/iter3/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | PINMISSING, WIDTHEXPAND, WIDTHTRUNC |
| op_link1 | stitch | 4 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link1/rep1/iter4/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | PINMISSING |
| op_link1 | stitch | 5 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link1/rep1/iter5/sim.log:1 `dut.v:68: error: Index req[16] is out of range.` | PINMISSING, WIDTHTRUNC |
| op_link1 | stitch | 6 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link1/rep1/iter6/sim.log:1 `dut.v:70: error: Index req[16] is out of range.` | - |
| op_link2 | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link2/rep1/iter0/sim.log:33 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | - |
| op_link2 | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link2/rep1/iter1/sim.log:1 `dut.v:266: error: expression not valid in assign l-value: 3'd0` | PINMISSING |
| op_link2 | stitch | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link2/rep1/iter2/sim.log:9 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | PINMISSING, WIDTHEXPAND |
| op_link2 | stitch | 3 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link2/rep1/iter3/sim.log:1 `dut.v:266: error: expression not valid in assign l-value: 3'd0` | PINMISSING |
| op_link2 | stitch | 4 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link2/rep1/iter4/sim.log:9 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | PINMISSING, WIDTHEXPAND |
| op_link2 | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link2/rep1/iter5/sim.log:1 `dut.v:266: error: expression not valid in assign l-value: 3'd0` | PINMISSING |
| op_link2 | stitch | 6 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link2/rep1/iter6/sim.log:9 `dut.v:388: error: 'ip1' is not a valid l-value for a procedural assignment.` | - |
| op_link3 | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link3/rep1/iter0/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | - |
| op_link3 | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link3/rep1/iter1/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | PINMISSING |
| op_link3 | stitch | 2 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link3/rep1/iter2/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | PINMISSING |
| op_link3 | stitch | 3 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link3/rep1/iter3/sim.log:1 `dut.v:273: error: port ``g1'' already bound.` | PINMISSING |
| op_link3 | stitch | 4 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link3/rep1/iter4/sim.log:1 `dut.v:250: error: port ``g1'' already bound.` | PINMISSING |
| op_link3 | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link3/rep1/iter5/sim.log:1 `dut.v:250: error: port ``g1'' already bound.` | PINMISSING |
| op_link3 | stitch | 6 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link3/rep1/iter6/sim.log:1 `dut.v:250: error: port ``g1'' already bound.` | - |
| op_link4 | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link4/rep1/iter0/sim.log:25 `dut.v:285: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | - |
| op_link4 | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link4/rep1/iter1/sim.log:1 `dut.v:275: error: expression not valid in assign l-value: 3'd0` | - |
| op_link4 | stitch | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link4/rep1/iter2/sim.log:9 `dut.v:285: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | - |
| op_link4 | stitch | 3 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link4/rep1/iter3/sim.log:1 `dut.v:275: error: expression not valid in assign l-value: (4'd1)&({e1, e1, e1, e1})` | - |
| op_link4 | stitch | 4 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link4/rep1/iter4/sim.log:9 `dut.v:285: error: Unable to bind wire/reg/memory `ready_vc1' in `tb.dut'` | - |
| op_link4 | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link4/rep1/iter5/sim.log:1 `dut.v:275: error: expression not valid in assign l-value: (4'd1)&({e1, e1, e1, e1})` | - |
| op_link4 | stitch | 6 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/op_link4/rep1/iter6/sim.log:9 `dut.v:416: error: 'all_vc_not_busy' is not a valid l-value for a procedural assignment.` | - |
| priority_encoder | stitch | 0 | ok | - | - |
| register_1bit | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/register_1bit/rep1/iter0/sim.log:1 `dut.v:6: error: 'dout' has already been declared in this scope.` | - |
| register_1bit | stitch | 1 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/register_1bit/rep1/iter1/sim.log:1 `dut.v:6: error: 'dout' has already been declared in this scope.` | - |
| register_1bit | stitch | 2 | ok | - | - |
| register_32bit | stitch | 0 | ok | - | - |
| register_4bit | stitch | 0 | ok | - | - |
| round_robin_req | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/round_robin_req/rep1/iter0/sim.log:1 `dut.v:13: error: 'req_10' has already been declared in this scope.` | - |
| round_robin_req | stitch | 1 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/round_robin_req/rep1/iter1/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | - |
| round_robin_req | stitch | 2 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/round_robin_req/rep1/iter2/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | COMB_LOOP, UNDRIVEN, WIDTHTRUNC |
| round_robin_req | stitch | 3 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/round_robin_req/rep1/iter3/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | COMB_LOOP, UNDRIVEN, WIDTHTRUNC |
| round_robin_req | stitch | 4 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/round_robin_req/rep1/iter4/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | UNDRIVEN, UNUSEDSIGNAL, WIDTHTRUNC |
| round_robin_req | stitch | 5 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/round_robin_req/rep1/iter5/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | WIDTHTRUNC |
| round_robin_req | stitch | 6 | width | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/round_robin_req/rep1/iter6/sim.log:1 `dut.v:32: error: Index gi[16] is out of range.` | - |
| router_fifo | stitch | 0 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/router_fifo/rep1/iter0/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | stitch | 1 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/router_fifo/rep1/iter1/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | stitch | 2 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/router_fifo/rep1/iter2/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | stitch | 3 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/router_fifo/rep1/iter3/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | stitch | 4 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/router_fifo/rep1/iter4/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | stitch | 5 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/router_fifo/rep1/iter5/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| router_fifo | stitch | 6 | timing | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/router_fifo/rep1/iter6/sim.log:1 `FAIL t=59000 cycle 4: rd_add = 1, expected 0` | - |
| routing_algo_mesh | stitch | 0 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/routing_algo_mesh/rep1/iter0/sim.log:1 `dut.v:8: error: 'req_link1' has already been declared in this scope.` | - |
| routing_algo_mesh | stitch | 1 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/routing_algo_mesh/rep1/iter1/sim.log:1 `dut.v:18: error: 'req_link1_w' is not a valid l-value for a procedural assignment.` | - |
| routing_algo_mesh | stitch | 2 | ok | - | - |
| rr_arbiter | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_arbiter/rep1/iter0/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | stitch | 1 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_arbiter/rep1/iter1/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | stitch | 2 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_arbiter/rep1/iter2/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | stitch | 3 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_arbiter/rep1/iter3/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | stitch | 4 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_arbiter/rep1/iter4/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | stitch | 5 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_arbiter/rep1/iter5/sim.log:1 `dut.v:7: syntax error` | - |
| rr_arbiter | stitch | 6 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_arbiter/rep1/iter6/sim.log:1 `dut.v:7: syntax error` | - |
| rr_comb_new | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_comb_new/rep1/iter0/sim.log:1 `dut.v:36: error: Unable to bind wire/reg/memory `r2_w' in `tb.dut'` | - |
| rr_comb_new | stitch | 1 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_comb_new/rep1/iter1/sim.log:1 `FAIL t=59000 cycle 4: g2 = 0, expected 1` | - |
| rr_comb_new | stitch | 2 | multi-driven | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_comb_new/rep1/iter2/sim.log:1 `dut.v:72: error: Cannot perform procedural assignment to variable 'g1_reg' because it is also continuously assigned.` | - |
| rr_comb_new | stitch | 3 | multi-driven | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_comb_new/rep1/iter3/sim.log:1 `dut.v:72: error: Cannot perform procedural assignment to variable 'g1_reg' because it is also continuously assigned.` | UNDRIVEN |
| rr_comb_new | stitch | 4 | multi-driven | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_comb_new/rep1/iter4/sim.log:1 `dut.v:72: error: Cannot perform procedural assignment to variable 'g1_reg' because it is also continuously assigned.` | - |
| rr_comb_new | stitch | 5 | multi-driven | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_comb_new/rep1/iter5/sim.log:1 `dut.v:72: error: Cannot perform procedural assignment to variable 'g1_reg' because it is also continuously assigned.` | - |
| rr_comb_new | stitch | 6 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/rr_comb_new/rep1/iter6/sim.log:1 `FAIL t=59000 cycle 4: g2 = 0, expected 1` | - |
| top_2x2_router | stitch | 0 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_2x2_router/rep1/iter0/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | - |
| top_2x2_router | stitch | 1 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_2x2_router/rep1/iter1/sim.log:362 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | PINMISSING, WIDTHEXPAND, WIDTHTRUNC |
| top_2x2_router | stitch | 2 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_2x2_router/rep1/iter2/sim.log:1 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | PINMISSING, UNUSEDSIGNAL |
| top_2x2_router | stitch | 3 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_2x2_router/rep1/iter3/sim.log:1 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | PINMISSING, WIDTHEXPAND, WIDTHTRUNC |
| top_2x2_router | stitch | 4 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_2x2_router/rep1/iter4/sim.log:1 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | PINMISSING, UNUSEDSIGNAL |
| top_2x2_router | stitch | 5 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_2x2_router/rep1/iter5/sim.log:1 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | PINMISSING, UNUSEDSIGNAL |
| top_2x2_router | stitch | 6 | function | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_2x2_router/rep1/iter6/sim.log:1 `FAIL t=149000 cycle 13: data_out_core_r1 = 60000000, expected 27160600` | - |
| top_module | stitch | 0 | syntax | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_module/rep1/iter0/sim.log:11 `dut.v:1349: error: 'req_l1_link1' is not a valid l-value for a procedural assignment.` | - |
| top_module | stitch | 1 | syntax | unmapped compile error | - |
| top_module | stitch | 2 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_module/rep1/iter2/sim.log:1 `dut.v:101: error: 'full_out_link1_vc1' has already been declared in this scope.` | - |
| top_module | stitch | 3 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_module/rep1/iter3/sim.log:1 `dut.v:101: error: 'full_out_link1_vc1' has already been declared in this scope.` | - |
| top_module | stitch | 4 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_module/rep1/iter4/sim.log:1 `dut.v:108: error: 'sel_vc_link1' has already been declared in this scope.` | - |
| top_module | stitch | 5 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_module/rep1/iter5/sim.log:1 `dut.v:652: error: port ``clk'' is not a port of op_data_path_inst.` | PINMISSING |
| top_module | stitch | 6 | ports | runs/arms/results/qwen2.5-coder_32b/sem_esc_restart_v3/top_module/rep1/iter6/sim.log:1 `dut.v:652: error: port ``data_to_link1_ch1'' is not a port of op_data_path_inst.` | - |
