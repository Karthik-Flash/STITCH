# RTLLM v2.1 pilot — pre-registration

**Status: TRIAL / DEMO for researcher review. Not a publishable result.**
5 modules, chosen by a fixed rule (not hand-picked for a favorable
outcome), stand in for RTLLM v2.1's full 50-module suite so the harness
and the reviewer can see a real run before committing HPC time to the
full pass@5 study. **Nothing in this pilot should be cited as an RTLLM
result** — the deferred full study is the actual benchmark.

RTLLM v2.1 is cloned at `D:\Projects\RTLLM`, a sibling of this repo, not
inside it. Nothing under that path is committed to STITCH; the pilot
runner reads design specs and testbenches from it live at run time and
stages only renamed/temporary copies under the gitignored
`phase1/results/rtllm_pilot/` tree.

---

## Task A — batch compatibility screen (full results)

All 50 designs screened for real: reference (`verified_*.v`) file renamed
to the bare module name the testbench instantiates, compiled and
simulated under real iverilog/vvp (WSL), pass hook = the literal string
`"Your Design Passed"` appearing in simulation output. No LLM involved —
this screens RTLLM's own reference solutions, not model output. Script:
`phase1/rtllm_task_a_screen.py`. Raw per-design record:
`phase1/results/rtllm_pilot/task_a_screen.json` (gitignored).

**44 / 50 pass clean.**

| category      | design                  | status                  | note                                                                                                                                                                                                                                                                                        |
| ------------- | ----------------------- | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Arithmetic    | accu                    | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | adder_16bit             | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | adder_32bit             | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | adder_8bit              | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | adder_bcd               | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | adder_pipe_64bit        | pass                    | reference file`verified_adder_64bit.v` names a different module than the design dir; handled by renaming whatever `module verified_XXXX` is actually declared                                                                                                                           |
| Arithmetic    | comparator_3bit         | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | comparator_4bit         | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | div_16bit               | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | radix2_div              | **sim_fail**      | the reference design itself fails its own testbench, 3/8 vectors (`dividend=156, divisor=10, expected=00f6, got=faf1`, etc.) — an RTLLM golden-reference bug, not a screening artifact                                                                                                   |
| Arithmetic    | multi_16bit             | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | multi_8bit              | **compile_error** | `Incomprehensible for loop` at line 15 — non-Verilog-2001 for-loop syntax this iverilog build rejects                                                                                                                                                                                    |
| Arithmetic    | multi_booth_8bit        | pass                    | file-I/O design (`test_data.dat`) — confirmed works when the data file is copied alongside                                                                                                                                                                                               |
| Arithmetic    | multi_pipe_4bit         | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | multi_pipe_8bit         | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | fixed_point_adder       | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | fixed_point_substractor | pass                    | **module-name caveat**: testbench instantiates `fixed_point_subtractor` (correct spelling), not `fixed_point_substractor` (the directory's spelling) — an RTLLM naming inconsistency, not a screening bug. Confirmed passes when the module is named `fixed_point_subtractor`. |
| Arithmetic    | float_multi             | pass                    |                                                                                                                                                                                                                                                                                             |
| Arithmetic    | sub_64bit               | pass                    |                                                                                                                                                                                                                                                                                             |
| Control       | JC_counter              | pass                    |                                                                                                                                                                                                                                                                                             |
| Control       | counter_12              | pass                    |                                                                                                                                                                                                                                                                                             |
| Control       | ring_counter            | **compile_error** | `reg out; cannot be driven by primitives or continuous assignment` + an array-slice assignment requiring SystemVerilog                                                                                                                                                                    |
| Control       | up_down_counter         | pass                    |                                                                                                                                                                                                                                                                                             |
| Control       | fsm                     | pass                    |                                                                                                                                                                                                                                                                                             |
| Control       | sequence_detector       | pass                    |                                                                                                                                                                                                                                                                                             |
| Memory        | asyn_fifo               | **compile_error** | `Enable of unknown task \`\`break''`— testbench uses a`break` statement this iverilog build doesn't support (SystemVerilog-only construct). File-I/O design (`rempty.txt`/`tdata.txt`/`wfull.txt`) — the failure is the `break` statement, not the data files.                |
| Memory        | LIFObuffer              | pass                    |                                                                                                                                                                                                                                                                                             |
| Memory        | LFSR                    | pass                    |                                                                                                                                                                                                                                                                                             |
| Memory        | barrel_shifter          | pass                    |                                                                                                                                                                                                                                                                                             |
| Memory        | right_shifter           | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | freq_div                | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | freq_divbyeven          | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | freq_divbyfrac          | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | freq_divbyodd           | **compile_error** | `reg clk_div; cannot be driven by primitives or continuous assignment`                                                                                                                                                                                                                    |
| Miscellaneous | calendar                | pass                    | file-I/O design (`reference.txt`) — confirmed works when the data file is copied alongside                                                                                                                                                                                               |
| Miscellaneous | edge_detect             | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | parallel2serial         | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | pulse_detect            | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | serial2parallel         | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | synchronizer            | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | traffic_light           | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | width_8to16             | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | RAM                     | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | ROM                     | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | alu                     | pass                    | file-I/O design (`reference.dat`) — confirmed works when the data file is copied alongside                                                                                                                                                                                               |
| Miscellaneous | clkgenerator            | **compile_error** | `reg clk_tb; cannot be driven by primitives or continuous assignment` — the testbench's own clock-generation code, not the design                                                                                                                                                        |
| Miscellaneous | instr_reg               | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | pe                      | pass                    |                                                                                                                                                                                                                                                                                             |
| Miscellaneous | signal_generator        | pass                    | file-I/O design (`tri_gen.txt`) — confirmed works when the data file is copied alongside                                                                                                                                                                                                 |
| Miscellaneous | square_wave             | pass                    |                                                                                                                                                                                                                                                                                             |

**On the 5 file-I/O designs the user flagged in advance**
(`multi_booth_8bit`, `asyn_fifo`, `calendar`, `Miscellaneous/RISC-V/alu`,
`signal_generator`): 4 of 5 pass cleanly once their data file is copied
alongside the renamed reference — the earlier concern about needing data
files was correct, but copying them resolves it. Only `asyn_fifo` fails,
and the failure is unrelated to its data files — it's the testbench's use
of `break`, an Icarus-incompatible construct.

**6 designs do not pass**: `radix2_div` (reference bug, not a compile
issue), `multi_8bit`, `ring_counter`, `asyn_fifo`, `freq_divbyodd`,
`clkgenerator` (all genuine compile incompatibilities with this iverilog
build, mostly reg-driven-by-continuous-assignment or non-Verilog-2001
syntax in the testbench itself). None were excluded from this table —
every one of the 50 is listed with its real status.

---

## Task B — pilot selection rule

**Rule** (fixed before looking at which designs would make it look good):
take the alphabetically-first (case-insensitive) design that passed
Task A's screen in each of the 4 categories (Arithmetic, Control, Memory,
Miscellaneous), plus one additional design — the alphabetically-second
passing design (first is already taken) — from whichever category has
the most total designs in RTLLM overall (by directory count, not by
passing count).

Category sizes (total designs in RTLLM, not just passing):
Arithmetic 19, Control 6, Memory 5, **Miscellaneous 20** — Miscellaneous
is the largest, so it contributes the 5th pick.

| # | category      | design             | path                              | rule                                                                              |
| - | ------------- | ------------------ | --------------------------------- | --------------------------------------------------------------------------------- |
| 1 | Arithmetic    | `accu`           | `Arithmetic/Accumulator/accu`   | alphabetically-first passing                                                      |
| 2 | Control       | `counter_12`     | `Control/Counter/counter_12`    | alphabetically-first passing                                                      |
| 3 | Memory        | `barrel_shifter` | `Memory/Shifter/barrel_shifter` | alphabetically-first passing                                                      |
| 4 | Miscellaneous | `alu`            | `Miscellaneous/RISC-V/alu`      | alphabetically-first passing                                                      |
| 5 | Miscellaneous | `calendar`       | `Miscellaneous/Others/calendar` | alphabetically-second passing, Miscellaneous is the largest category (20 designs) |

`alu` and `calendar` are both file-I/O designs (`reference.dat`,
`reference.txt`) — the runner stages these alongside their renamed
testbench per design; see `phase1/rtllm_pilot_runner.py`.

**This is a demo sample chosen by a stated rule, not a representative or
hand-picked benchmark subset. It is replaced by the full 50-design
pass@5 study on HPC later. Do not cite pilot numbers as an RTLLM result.**
