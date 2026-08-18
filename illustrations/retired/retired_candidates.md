# Backup decoder-mode candidates

Priority order to try if `counter_with_enable` lands on outcome (c) — see
its `README.md`'s decision framework. Each targets the same recipe: a prompt
describes a gating condition a weak model is likely to *omit entirely* (not
subtly mis-implement), and the omission leaves a tool-visible fingerprint the
interpreter already has a handler for.

None of these have been written to disk as `pending/<name>/` folders yet, and
none have been probed. Promote the next one in line the same way
`counter_with_enable` was built: write `correct.v` + `tb.v` (no `broken.v`),
verify `correct.v` passes under Icarus, probe with a single baseline
iteration, apply the same three-outcome decision framework.

---

## 1 — `register_with_load`

**Target mechanism:** `UNUSEDSIGNAL` on `load` (same handler as
`counter_with_enable`/`decoder_3to8` — already verified working, no new
interpreter code needed).

**Prompt:**
```
Write a Verilog-2001 module named register_with_load with:
- input clk, input rst, input load
- input [7:0] data_in
- output reg [7:0] data_out

Behavior: on posedge clk, if rst is high, data_out resets to 0.
Otherwise if load is high, data_out captures data_in. If load is low,
data_out holds its current value.

Sequential logic only, no latches. Return only Verilog code.
```

**Expected naive failure:**
```verilog
always @(posedge clk) begin
    if (rst) data_out <= 8'b0;
    else     data_out <= data_in;   // forgot load entirely — always captures
end
```

**Testbench must exercise:** a period where `load=0` while `data_in` changes
to a different value than what's currently latched — the naive version fails
by capturing anyway.

---

## 2 — `shift_reg_with_enable`

**Target mechanism:** `UNUSEDSIGNAL` on `en` (same handler again).

**Prompt:**
```
Write a Verilog-2001 module named shift_reg_with_enable with:
- input clk, input rst, input en, input serial_in
- output reg [7:0] shift_out

Behavior: on posedge clk, if rst is high, shift_out resets to 0.
Otherwise if en is high, shift left by one bit and load serial_in into
bit 0. If en is low, shift_out holds its current value.

Sequential logic only, no latches. Return only Verilog code.
```

**Expected naive failure:**
```verilog
always @(posedge clk) begin
    if (rst) shift_out <= 8'b0;
    else     shift_out <= {shift_out[6:0], serial_in};   // forgot en
end
```

**Testbench must exercise:** toggle `en` low mid-sequence with `serial_in`
still changing — naive version keeps shifting.

**Note:** structurally near-identical to `counter_with_enable` (same
gating-signal-omission shape, same warning code). If `counter_with_enable`
lands on outcome (c) — meaning `gemma3:4b` didn't make the omission mistake
on a *counter* — there's a real chance it won't make it on a *shift
register* either, since it's the same underlying "forgot the enable" failure
mode. Consider skipping straight to `register_with_load` or
`traffic_light_fsm` (structurally different mechanisms) rather than burning
a probe on this one, unless there's a specific reason to think shift
registers are harder for this model.

---

## 3 — `traffic_light_fsm`

**Target mechanism:** `LATCH` inferred on `next_state` — the
`mode_mux_latch` mechanism (already verified working end-to-end via
`interpret_yosys_latches()`/`detect_yosys_latches()`), not the
`UNUSEDSIGNAL` mechanism the other two candidates and `counter_with_enable`
share. Worth trying third specifically *because* it's a different failure
class — if the first two both land on outcome (c), that's weak evidence this
model doesn't tend to omit single-bit enable/load signals, and a
structurally different trap (missing `default` in a `case`, not a missing
port condition) is a better next bet than a fourth variation on the same theme.

**Prompt:**
```
Write a Verilog-2001 module named traffic_light_fsm with:
- input clk, input rst
- output reg [1:0] state

Implement a 3-state traffic light controller with states RED (2'b00),
GREEN (2'b01), YELLOW (2'b10). On posedge clk, if rst is high, state
resets to RED. Otherwise the state advances each clock: RED -> GREEN,
GREEN -> YELLOW, YELLOW -> RED. Use a case statement on the current
state to compute the next state.

Sequential logic only. Return only Verilog code.
```

**Expected naive failure:**
```verilog
always @(posedge clk) begin
    if (rst) state <= 2'b00;
    else begin
        case (state)
            2'b00: state <= 2'b01;
            2'b01: state <= 2'b10;
            2'b10: state <= 2'b00;
            // no default — 2'b11 unreachable in practice, but Yosys/Verilator
            // don't know that from the case alone
        endcase
    end
end
```

**Mechanism check: FAILED — confirmed empirically, do not probe this version
as written.** Tested the exact naive-failure code above against real
Verilator 5.020 + Yosys 0.33 before finalizing this doc (same discipline as
`counter_with_enable`'s verified `UNUSEDSIGNAL` claim). Result:

- Verilator: `%Warning-CASEINCOMPLETE`, not `LATCH` — Verilator has no
  warning literally named `LATCH` (same finding as `mode_mux_latch`).
  `CASEINCOMPLETE` isn't in `_VERILATOR_INTERP`, contributes nothing.
- Yosys: **no genuine "Latch inferred for signal" line at all** — only the
  `PROC_DLATCH` pass-name banner, which is known-not-a-real-positive (see
  the false-positive bug documented in `interpreter/WARNING_TAXONOMY.md`).

The reasoning behind this result: `state <= ...` is inside a *clocked*
always block (`always @(posedge clk)`), not a combinational one. The outer
`if (rst) ... else case(...)` structure means `state` is assigned on every
clock edge regardless of which case branch executes or whether one executes
at all — that's exactly what a flip-flop is, so Yosys correctly does **not**
treat this as a latch. Missing `default` in a *registered* case statement is
functionally harmless here (the FSM just can't reach `2'b11` and doesn't
need to), unlike `mode_mux_latch`'s combinational case where a missing
`default` genuinely leaves the output undriven on some path.

**To make this candidate viable, redesign is needed**, not just probing:
split `state` (registered) from a separately-computed `next_state`
(combinational, via an *unclocked* `always @(*) case(state)` with no
`default`) — that reproduces `mode_mux_latch`'s exact mechanism on FSM-shaped
logic instead of copying its surface pattern into a context where it doesn't
apply. Do this redesign and re-run this same mechanism check before writing
`correct.v`/`tb.v` for it — don't promote this candidate to a `pending/`
folder in its current form.
