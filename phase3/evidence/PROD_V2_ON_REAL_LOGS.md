# Evidence: production interpreter (v2) on real Yosys 0.33 / Verilator 5.020 output

**Scope.** Every row below was produced by running the UNMODIFIED production `src/interpreter/stitch_interpreter.py`
(SHA-256 of the LF-normalised file: `42f61a493e4544e027b880ba5ae16ef1677c52f9b328cce2e13c25028fb2abff`;
raw CRLF upload: `6f48bdfd…3c5805`) on real tool logs. Logs are frozen in `phase3/tests/fixtures/real/`, and each row is
pinned by a characterisation test (`phase3/tests/test_v3_layer.py`, section D) so a future change to production is detected.
Same evidence standard as `WARNING_TAXONOMY.md`: "Yes (real data)" = confirmed on an actual tool run.

**What is confirmed correct in production (unchanged, relied on by v3):** quoted-name extraction (`'en'`, `'oe'`),
literal-fragment guard, UNDRIVEN disambiguation, source-aware UNUSEDSIGNAL output widths, anchored Yosys latch
regex (rejects `No latch inferred` and the PROC_DLATCH banner), Yosys loop detection, structure-aware latch options.
v3 passes production text through byte-identically wherever no v3 rule applies (tests section B).

## Findings

| # | Production behaviour | Real case (fixture) | Consequence | v3 rule |
|---|---|---|---|---|
| F1 | `UNUSEDSIGNAL` on a clock port gets the gate template `if (clk) begin … end else dout = 4'b0;` inside `always @(*)` | `mpsoc_register_4bit`, `mpsoc_register_32bit` (80 instances each in the 2×2 mesh, 180 in 3×3) | Steers the model toward a clock-gated latch; the real defect is a missing `@(posedge clk)` | R1 → `MISSING_CLOCK` (Yosys latch in a level-sensitive block + unused clock) |
| F2 | `Bits of signal are not used: 'X'[a:b]` treated as a whole unused **port** | `mpsoc_Address_select` (`Instruction_code[11:7]` — legitimately unused rd field), `mpsoc_multiply` (internal wire `prod[31:0]`) | Directive `if (Instruction_code) … else J_addr = 32'b0;` / `if (prod) …` | R3 suppress (logged in `suppressed`) |
| F3 | Output-port scan reads every module of a multi-module file | `mpsoc_multiply` (9 "outputs" listed from sub-modules) | Else-branch assigns signals of other modules | R5 scope to the module under repair (line numbers preserved) |
| F4 | `WIDTHTRUNC`/`WIDTHEXPAND` whose operand is an expression (`… Assign RHS's REPLICATE generates 50 bits.`): no quoted identifier → extractor returns None → warning silently dropped | `task_ni_flit_pack` | `interpret_verilator(...) == ("", [])` for a real, sim-visible defect | N6 (names destination + offending line; generic template, no answer leakage — tested) |
| F5 | `BLKSEQ`/`COMBDLY`: Verilator 5 message quotes `'='`/`'<='`, not an identifier; fallback extracts the prose word **`process`**. With source: dropped (not in file). Without source: directive names `'process'`. `COMBDLY` template describes `#` delays, but Verilator 5 `COMBDLY` = non-blocking `<=` in a combinational block | `probe_more` | Directive either absent or wrong | R4 (names real LHS from the reported line; correct text; lowest priority) |
| F6 | Yosys hard error `Multiple edge sensitive events found for this signal!` (names no signal) has no handler | `mpsoc_register_1bit` | Silent; this single leaf makes BOTH meshes and the MPSoC fail top-level synthesis | N1 `ASYNC_RESET` (block recovered from source) |
| F7 | Loops are Yosys-only; Yosys `check` is silent on `PC = PC` in `always @(*)`, Verilator reports `UNOPTFLAT` | `mpsoc_IFU` | Loop never reported to the model | N2 (Verilator loop when Yosys is silent) |
| F8 | `interpret_yosys_latches()` must receive raw Yosys **lines**; passing `detect_yosys_latches()` output (bare names) yields `signal(s) an output signal … latch on 'out'` | `probe_latch` | Wrong signal named if any runner passes names | L1 (v3 always passes lines). **Check runners** (handoff step 2) |
| F9 | Only the first signal per Verilator code is reported | `probe_multi` (`w` reported, `q` dropped) | Second multi-driven net invisible | N4 (dedupes; Verilator repeats one net per driver pair) |
| F10 | `_assigns()` does not recognise a concatenation LHS (`{carry, result} = …`) | `task_riscv_alu_flags` ("assign 'result' in the 4 branch(es) that currently omit it" — it is assigned in all 10) | Branch count wrong; the suggested hoisted default is still correct | **Documented only** (not overridden; low harm) |

## Resolved open item from WARNING_TAXONOMY.md: MULTIDRIVEN real trigger

`phase3/tests/fixtures/real/probe_multi/src.v` triggers both Verilator 5.020 formats, and production extracts the signal from both:

```verilog
assign w = d;  assign w = ~d;                                  // format A: "Bits [0:0] of signal 'w' have multiple combinational drivers"
always @(posedge clk) q <= d;
always @(posedge clk or posedge rst) if (rst) q <= 1'b0;       // format B: "Signal has multiple driving blocks with different clocking: 'q'"
```
(The taxonomy's first attempt — identical clocking on both blocks — is exactly the case Verilator does not flag.)
Seeded task `noc_xbar4` (four `assign`s to one crossbar output) also produces format A in a realistic context.

## Reproduce
```bash
python phase3/tests/run_tests.py          # 44 passed (frozen Yosys 0.33 / Verilator 5.020 logs)
python phase3/runner/validate_tasks.py    # live drift check on the installed toolchain
```
