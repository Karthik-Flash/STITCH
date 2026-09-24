# WARNING_TAXONOMY — Phase 3 addendum

Append-only companion to `src/interpreter/WARNING_TAXONOMY.md` (that file is not edited). Evidence standard is unchanged.
Details and fixtures: `phase3/evidence/PROD_V2_ON_REAL_LOGS.md`, `phase3/tests/fixtures/real/`.

## Status updates to existing rows (production v2)

| Code | Previous status | Phase 3 status |
|---|---|---|
| `MULTIDRIVEN` | No — real trigger not found | **Yes (real data)** — both Verilator 5.020 formats triggered (`probe_multi`), production extracts the signal from both; realistic trigger in `noc_xbar4`. Only the first net is named (F9). |
| `WIDTHTRUNC` / `WIDTHEXPAND` | Synthetic only | **Yes (real data)** for named operands (`probe_width`, `Address_select` 1-bit PC). **Real false negative** when the operand is an expression (`… CONCAT/REPLICATE generates 50 bits.`) — dropped with `codes_fired == []` (F4). |
| `COMBDLY` | Synthetic only | **Real data contradicts the template**: Verilator 5 `COMBDLY` = `'<='` in a combinational block, not a `#` delay; signal extraction yields the prose word `process` (F5). |
| `BLKSEQ` | Yes | Extraction yields `process` on real Verilator 5 output (F5). Verify the comb_sensitivity run (phase3/HANDOFF_PHASE3_CLAUDE_CODE.md, task T4). |
| `UNUSEDSIGNAL` | Yes | Correct for gating inputs. **Real wrong-directive cases**: clock ports (F1) and partial-bit warnings, incl. internal wires (F2, F3). |
| Latch inferred | Yes | Correct. API caveat: `interpret_yosys_latches()` needs raw lines, not `detect_yosys_latches()` names (F8). Branch count ignores concatenation LHS (F10). |
| Combinational loop | Yes (Yosys) | Real loop missed: Yosys `check` silent, Verilator `UNOPTFLAT` fires (`IFU`, `PC = PC`) (F7). |

## New classes (v3 layer only — `src/interpreter/stitch_interpreter_v3.py`)

| Class | Source | Verified against real data? | Evidence |
|---|---|---|---|
| `MISSING_CLOCK` | fusion: Yosys latch in level-sensitive block + Verilator UNUSEDSIGNAL on clock | **Yes** | `register_4bit`, `register_32bit` (MPSoC router) |
| `ASYNC_RESET` | Yosys ERROR "Multiple edge sensitive events" | **Yes** | `register_1bit` (blocks synthesis of both meshes and the MPSoC) |
| `COMB_LOOP` (Verilator) | `UNOPTFLAT` when Yosys silent | **Yes** | `IFU` |
| `WIDTH_EXPR` | WIDTHTRUNC/EXPAND on expressions | **Yes** | `ni_flit_pack` |
| `PINMISSING` | Verilator `PINMISSING` | **Yes** (748 in MPSoC) | composition-level; not a Phase 3 repair task |
| `RESET_UNUSED` | UNUSEDSIGNAL on reset name | Synthetic only | `probe_more` (`rst`) |
