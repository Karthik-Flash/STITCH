# Compile-only sanitisation of the reference designs

Source: `p20230031/RISC-V` → `MPSoC Source Codes.zip` (mpsoc_ref, mesh2x2_ref) and `Automation Code.zip` →
`Sai Siddharth Rokkam/MESH_AUTOMATION.srcs/sources_1/Router/router/` (mesh3x3_ref). Vivado accepts these files;
Icarus/Yosys/Verilator reject some constructs. The following changes were made, all semantics-preserving, and
**no structural defect was touched** (every latch, the async-reset abort, the 1-bit PC port and the positional
miswire are intentionally still there):

1. CRLF → LF; all comments removed (a `/*` inside a block comment is an Icarus error). Line structure preserved.
2. `main.v`: removed the redeclarations `wire rd_clk,wr_clk;` and `result` in the wire list (the ports already declare them).
3. `new.v` (`new1`) and `nidepack.v`: instantiations with one port fewer than the definition
   (`router_fifo` 13 of 14, `depack` 5 of 6). Vivado leaves the trailing port unconnected; we append an explicit empty
   trailing connection (`, )`) — identical binding, so the positional shift (`full_int`→`full_ext`, `empty`→`full_int`) is kept.
4. Duplicate module files (router_fifo, memory, jk_ff, gray_mod6, asynch_comparator appear in router/, NI/flit maker/,
   NI/packetiser/) are byte-identical; one copy kept.
5. The mesh folders contain only the router tree (top = `top_2x2_router` / `top_3x3_router`).

Verification: `phase3/HANDOFF_PHASE3_CLAUDE_CODE.md` task T3 compares every module body against the repo copy after comment stripping;
expected differences are exactly `main`, `new1` and `nidepack`.
