# Failure audit (pipeline/audit.py)

Every final file that is not so_clean, from the local re-evaluation (`pipeline/reeval.py`; flags identical to the cluster's `reports/summary.json` for all 3 files). Classes: LLM_BUG, SPEC_AMBIGUITY, TB_ARTIFACT.

## Class counts per arm

| arm | not so_clean | LLM_BUG | SPEC_AMBIGUITY | TB_ARTIFACT |
|---|---|---|---|---|
| oneshot | 1 | 1 | 0 | 0 |
| simloop | 1 | 1 | 0 | 0 |
| stitch | 1 | 1 | 0 | 0 |

## Audit findings


## Cases

| module | arm | flags | class | reason | spec line | evidence |
|---|---|---|---|---|---|---|
| top_3x3_router | oneshot | C..K | LLM_BUG | each router's core output data_out_core_rN is driven by two router outputs (data_out_core and data_out_c), and the four VC data outputs of each link share one net with data_out_l<k> (multiple drivers): every core output is X from cycle 0 | "`data_in_core_rN` and `data_out_core_rN` are router N's core input and output." | tb.v runs/analysis/oneshot/top_3x3_router/sim.log:110: `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000`<br>tb_signoff.v runs/analysis/oneshot/top_3x3_router/signoff.log:110: `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000` |
| top_3x3_router | simloop | C..K | LLM_BUG | each router's core output data_out_core_rN is driven by two router outputs (data_out_core and data_out_c), and the four VC data outputs of each link share one net with data_out_l<k> (multiple drivers): every core output is X from cycle 0 | "`data_in_core_rN` and `data_out_core_rN` are router N's core input and output." | tb.v runs/analysis/simloop/top_3x3_router/sim.log:110: `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000`<br>tb_signoff.v runs/analysis/simloop/top_3x3_router/signoff.log:110: `FAIL t=14000 cycle 0: data_out_core_r1 = xxxxxxxx, expected 60000000` |
| top_3x3_router | stitch | .... | LLM_BUG | port redeclared in the body; also fails with iverilog -g2001 | "Write the complete Verilog-2001 module `top_3x3_router` that meets this specification, with exactly the port list above." | compile (iverilog -g2012) runs/analysis/stitch/top_3x3_router/sim.log:1: `dut.v:97: error: 'full_out_link4_vc4_r8' has already been declared in this scope.` |
