# freq_divbyfrac: material for a manual oracle check

Written 2026-10-12 for a human reviewer. It covers the RTLLM v2.1 module `freq_divbyfrac`, which every API model
fails in Set 4b (0/36 runs). Files are in `D:\Projects\RTLLM\Miscellaneous\Frequency divider\freq_divbyfrac\`.
Line numbers refer to those files. The run evidence is in `SET4_REPORT.md` (the oracle audit of the Gemini
completion section, "Q7 answer") and in `phase2/results/set4_api/analysis_4c/`.

## 1. Specification (`design_description.txt`, lines 1–24, verbatim)

```text
 1  Please act as a professional Verilog designer.
 2
 3  A frequency divider that divides the input clock frequency by fractional values. It generates a clock signal with a fractional frequency division (3.5x), using the double-edge clocking technique to achieve half-integer division while adjusting for duty cycle imbalance. By dividing uneven clock cycles and phase-shifting them, a smooth fractional clock output is produced.
 4
 5  Module name:
 6      freq_divbyfrac
 7
 8  Input ports:
 9      clk: Input clock signal.
10      rst_n: Active low reset signal to initialize the module.
11
12  Output ports:
13      clk_div: Fractionally divided clock output.
14
15  Implementation:
16  The module performs fractional frequency division by counting clock cycles and generating intermediate divided clock signals. For 3.5x division:
17  The counter cycles through 7 half clock steps (MUL2_DIV_CLK = 7).
18  It generates one divided clock pulse on the positive edge of clk, and another adjusted pulse on the negative edge of clk.
19  The negative-edge pulse extends the output by half a source clock cycle, so the final output has the required 3.5x division period.
20  In each divided clock period, clk_div keeps high for the first 3 half clock steps and keeps low for the next 4 half clock steps.
21  Finally, the two intermediate clocks are logically OR-ed to produce the final fractional divided clock output.
22  The active low reset signal rst_n asynchronously initializes the counter and the intermediate clock signals to 0.
23
24  Give me the complete code.
```

## 2. Testbench check lines (`testbench.v`)

| Line | Code | What it fixes |
|---|---|---|
| 1 | `` `timescale 1ns / 1ps `` | time unit 1 ns |
| 15 | `always #5 clk = ~clk;` | clk period 10 ns; one half clock step = 5 ns |
| 22 | `clk = 1;` | clk starts high at t=0, so its posedges fall at t=10, 20, 30, … ns |
| 23–24 | `rst_n = 0; # 10 rst_n = 1;` | reset is released at t=10 ns, **in the same timestep as a clk posedge** |
| 18 | `integer expected_value = 1;` | the first check expects 1 |
| 31 | `#15;` | the first check is at t=15 ns |
| 32 | `for (i = 0; i < 20; i = i + 1) begin` | 20 checks |
| 33–35 | `if (clk_div !== expected_value) … $display("Failed at%d: clk=%d, clk_div=%d (expected %d)", …)` | each check compares with the value set on the PREVIOUS iteration |
| 38–44 | `if (i < 2) expected_value = 1; else if (i < 6) … = 0; else if (i < 9) … = 1; else if (i < 13) … = 0; else if (i < 16) … = 1; else if (i < 20) … = 0;` | the expected sequence below |
| 45 | `#5;` | one check per half clock step (every 5 ns) |
| 47–51 | `if (error == 0) $display("=========== Your Design Passed ===========") …` | pass verdict |

**Expected `clk_div` at checks 0–19** (t = 15, 20, …, 110 ns), as lines 18 and 38–44 produce it:

```text
check:     0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19
expected:  1 1 1 0 0 0 0 1 1 1  0  0  0  0  1  1  1  0  0  0
```

That is 3 half-steps high and 4 low, repeating, which matches spec line 20. The spec does not say at which
half-step after reset the first high phase starts. The testbench fixes it: high from t=15 ns, the first check
after the posedge at t=10 ns where reset is released, then low from t=30 ns.

## 3. Reference design (`verified_freq_divbyfrac.v`)

Lines 7–56: `MUL2_DIV_CLK = 7`; a 0–6 counter on posedge; `clk_ave_r` high at cnt 0 and cnt 4 (posedge, lines
22–37); `clk_adjust_r` high at cnt 1 and cnt 4 (negedge, lines 41–54); `clk_div = clk_adjust_r | clk_ave_r`
(line 56). The reference passes the testbench under the Set 4 harness and the 0.69 toolchain
(`oracle_audit.py`). The comment on line 26 says "first cycle: 4 source clk cycle"; the spec says 3 high / 4 low
half-steps.

## 4. What the runs show

Set 4b: 0 of 36 runs pass (GPT-4.1 mini, Gemini 2.5 Flash and Claude Haiku 4.5, 12 runs each). Set 4c (Gemini 2.5
Pro, reasoning) was closed before it reached this module: its stop rule fired on run 1, and no Set 4c results are
reported (`SET4_PREREG.md` Amendment 5). There is no reasoning-model evidence. The verdict below rests on the 36
Set 4b runs.

## 5. Evidence from the scripts (`set4c.py trace`; outputs in `phase2/results/set4_api/analysis_4c/`)

Method. The original `testbench.v` is run with one added line after line 32,
`$display("C %0d %0d", i, clk_div);`, so `clk_div` is printed at each of the 20 checks with the same event ordering
as the check. This is done for the final candidate of every Set 4b run and for the reference. Each trace is
compared with the expected sequence at shifts of −2 to +2 checks (half clock steps), over the checks that overlap.

| | Result |
|---|---|
| Reference | passes; 20/20 at shift 0, 14/19 at ±1, 8/18 at ±2 |
| Candidates simulated | 34 of 36 (2 compile errors) |
| Match at shift 0 | 0 |
| Pure shift of the expected sequence (±1 or ±2) | 0 |
| First mismatching check | check 3 (`clk_div=1, expected 0`) in 32; check 0 (`clk_div=0, expected 1`) in 2 |
| First high phase (candidates starting high, half-steps) | H4 5, H5 3, H6 6, H7 7, H9 3, H11 3, H13 4, H20 1 (never H3) |
| Typical traces | `H6 L7 H7`, `H7 L7 H6`, `H11 L3 H6`, `H13 L1 H6` |

**Verdict: genuine model failures on a hard fractional-divider spec; not supported as an oracle defect; needs
manual confirmation.**
- The reference fails when shifted by one step, so the expected sequence is not shift-tolerant.
- No candidate is a shifted copy of the expected waveform.
- The candidates have the wrong period and duty cycle: typically high 6–7 and low 7 half-steps, against the
  specified 3 and 4, so a period of about 13–14 half-steps instead of 7.

That points to models misreading "7 half clock steps" and double-edge clocking, not to a phase-strict testbench.
The expected sequence agrees with spec line 20, and the reference passes.

**Correction** to the earlier report wording ("every model keeps clk_div high one half-step longer"): the first high
phase lasts 4 to 20 half-steps, and the period is about 2× the specified one.

A human should still check question 1 below: whether the start phase after reset is fully determined by the spec.

### 5b. The reference counter, logged (`set4c.py refcheck`, 2026-10-13)

The original testbench was re-run with one added `always @(clk) $strobe(...)` that logs the counter `cnt`, the two
intermediate clocks and `clk_div` at every clock edge. Output: `phase2/frontier/evidence/freq_divbyfrac_refcheck_stdout.txt`.

| | Result |
|---|---|
| Counter | advances once per **rising** edge (0 to 6), never on a falling edge |
| Counter period | 14 half clock steps (7 rising edges) |
| `clk_div` period | 7 half steps, high 3 / low 4 (`H3 L4 H3 L4 ...`) |
| `clk_div` periods per counter wrap | 2 |
| Reference passes its testbench | yes |

Spec line 17 says "The counter cycles through 7 half clock steps (MUL2_DIV_CLK = 7)"; the reference counter cycles
through 7 rising edges, i.e. 14 half steps, and produces two output periods per wrap. **Our reading:** the spec's
description of the counter does not match its own reference design, which plausibly explains the models' roughly
doubled period (Section 5). This is a spec-wording defect, not a testbench defect. The same-timestep reset release
(testbench line 24) is a minor robustness weakness that did not cause the failures, since no candidate fails by a
phase offset. The verdict is unchanged: genuine model failures on a hard fractional-divider spec; not supported as an
oracle defect; needs manual confirmation.

## 6. Points for the human reviewer

1. Is the phase of the first high window (t=15–25 ns) derivable from the spec alone, given that reset is
   released in the same timestep as a clk posedge (testbench line 24)?
2. Spec line 19 (negedge pulse "extends the output by half a source clock cycle") and line 20 (3 high, 4 low)
   describe the shape. Does the reference's line-26 comment ("4 source clk cycle") conflict with them?
3. Section 5 answers whether the model outputs are a pure shift of the expected sequence (which would make the
   testbench phase-strict) or a different shape: none is a shift, all have a different period and duty cycle.
   The remaining question is whether "3.5x" plus "7 half clock steps" invites the about-2× period the models
   produce.

Every conclusion here is a candidate that needs manual confirmation.
