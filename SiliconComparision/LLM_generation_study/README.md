# LLM generation study: can an AI write a working network-on-chip router from a written description?

**Status: done (2026-11-07).** Two AI models wrote all 7 modules of a 5-port router, in three ways (once, with a
simulation feedback loop, with STITCH), 5 times each. Every router fully written by an AI was tested and, where it
compiled, built in Vivado for the ZedBoard FPGA and compared with a hand-checked reference ("golden") router.

## In one minute

- **Gemma 4 31B** wrote no working router when asked once (0 of 5). With feedback it did: **3 of 5** with a plain
  simulation loop, **4 of 5** with STITCH. In Vivado these routers are as good as the reference: all meet timing at
  100 MHz, have no latches, and use slightly fewer lookup tables (664 to 699 against 716) at the same power.
- **qwen2.5-coder 32B** wrote **no working router in any arm**. Its queue (`fifo`) never worked, and every router
  needs five of them.
- **STITCH against the plain loop:** one more working router on Gemma, equal on qwen. That one router came from
  STITCH's "start again from scratch" step, not from its diagnosis; STITCH's other differences were lint warnings
  with no effect in hardware; and its diagnosis on the parent modules contained a false statement (a flaw in the
  test set-up, see Limitations). So this study does not show that STITCH's diagnosis helps an AI write new hardware.
  Feedback loops in general help a lot.

| | asked once | simulation loop | STITCH loop |
|---|---|---|---|
| Gemma 4 31B: working routers (of 5) | 0 | 3 | 4 |
| qwen2.5-coder 32B: working routers (of 5) | 0 | 0 | 0 |

---

# Part 1. The study in plain words

## 1. What is being built

A chip with many processors needs a way to move data between them. A **network-on-chip** does this with small
**routers**, like road junctions. Our router has **5 ports**: 4 to neighbouring routers (called link1 to link4) and
1 to the local processor (core). Data travels in **packets**; each packet is cut into 32-bit pieces called
**flits**: a **head** flit that carries the destination, **body** flits with the data, and a **tail** flit that
closes the packet.

The router is made of 7 **modules** (building blocks of Verilog code):

| module | what it does, in plain words |
|---|---|
| `fifo` | a small queue: holds up to 4 flits, first in, first out |
| `route_compute` | reads a head flit's destination and picks the way out (first move along rows, then columns) |
| `rr_arbiter` | when several inputs want the same output, lets them take turns fairly (round-robin) |
| `flit_mux` | a switch: lets one of 4 inputs through |
| `input_port` | one entrance: a `fifo` plus `route_compute`, and it remembers a packet's way until its tail has passed |
| `output_port` | one exit: an `rr_arbiter` plus a `flit_mux`, and it stays with one packet until its tail has left ("wormhole") |
| `router_5port` | the whole router: 5 entrances and 5 exits wired together |

## 2. The golden reference

To judge an AI's router we need a router we know is right: the **golden reference**. We started from a router that
a student had built and run on a ZedBoard board (`original_2x2_mesh_zedboard/`). It worked on the board, but its
code makes 1,744 **latches** (accidental memory cells), has 2,202 **combinational loops** (wires that feed back into
themselves) and has no clock constraint, so Vivado cannot even measure its speed. That is not a fair yardstick.

So we rebuilt it cleanly (`golden/`): the same pins, packet format and routing, but one clock and no latches or
loops. Then we checked it in every way we could: all tests pass in two simulators, its routing is mathematically
proved equal to the board-tested original, four rebuilt routers wired together deliver the very packets the
original was tested with on the board, and 19 deliberately planted bugs are all caught by the tests. In Vivado it
uses **716 LUTs** and **245 flip-flops**, meets timing at **100 MHz** with **0.209 ns** to spare, and uses
**0.010 W** of dynamic power. `golden/DESIGN.md` explains it step by step.

## 3. What the AI is given, and how its work is checked

- **A spec per module** (`specs/`): a plain description of what the module must do, its exact pins (names,
  directions, widths) and the pins of the smaller modules it must use. No golden code, and no hints about how to
  write it. The same spec and the same request go to every model and every arm.
- **Two tests per module** (`tasks/<module>/`). A **testbench** is a program that feeds the module inputs and
  checks every output.
  - The **visible testbench** (`tb.v`): in the loops, the AI is shown what failed.
  - The **hidden sign-off testbench** (`tb_signoff.v`): the same checks with different random inputs and twice the
    traffic; the AI never sees it, so it catches code that passes the visible test by luck. The router also gets a
    hidden test of four routers wired as a 2x2 mesh.
- **Clean code** ("struct_clean"): Yosys finds no latch and no combinational loop, and Verilator (a "lint" checker,
  like a spelling and grammar checker for code) reports none of the serious warnings.
- Each module is written **on its own**. When a bigger module (`input_port`, `output_port`, `router_5port`) is
  tested, its smaller modules are the golden ones, so one bad small module cannot hide a good big one.

## 4. The three ways of asking ("arms")

| arm | how it works |
|---|---|
| **oneshot** | ask once and take the answer |
| **simloop** (simulation loop) | ask; run the visible testbench; show the AI what failed; let it fix; up to 6 more requests. It **stops as soon as the testbench passes**. |
| **stitch** (STITCH loop) | the same, but it **stops only when the testbench passes and the code is clean**. After two identical failures it switches to STITCH's detailed diagnosis (plain instructions built from the Verilator and Yosys messages); if still stuck, it **starts again once from the original answer**. |

Both loops start from the oneshot answer of the same rep.

## 5. Reps, and what a "pure router" is

An AI does not always give the same answer, so every arm was run **5 times** ("**rep** 1" to "rep 5"). Rep 1 of
simloop and rep 1 of STITCH both start from oneshot's rep-1 answer, so they can be compared directly. The settings
were fixed (temperature 0.1), but the tool we used cannot fix the random seed, so some reps came out identical:
qwen wrote the very same `route_compute` 5 times out of 5.

A **pure router** is the 7 files of one arm and one rep put together, with **nothing golden**. That is the real
question: did the AI, by itself, produce a whole router that works? Each model gives 3 arms × 5 reps = 15 pure
routers. A pure router counts as **working** when the router test, the hidden router test and the hidden 2x2-mesh
test all pass.

## 6. The two AI models

| | qwen2.5-coder 32B | Gemma 4 31B (instruction-tuned) |
|---|---|---|
| kind | specialised for code; used in the earlier phases of this project | general model from Google that **thinks** (reasons privately) before it answers |
| size and format | 32 billion parameters, compressed to Q4_K_M | 31 billion parameters, the same Q4_K_M compression, for a fair match |
| speed on the cluster | about 65 to 68 tokens (word pieces) per second | about 122 to 131 tokens per second, plus long reasoning (464,230 characters of thinking for its 35 oneshot answers) |

## 7. Where and how it ran

The models ran on the university's GPU cluster (BITS Hyderabad HPC, NVIDIA H100 and H200 cards), through Ollama
0.34.1. Before the first job, every file that decides what the AI is asked and how it is judged (79 files) was
**frozen**: its fingerprint (sha256) is in `FREEZE.sha256`, and every job checked it before doing anything. Each
job also ran a full test of the pipeline with fake AIs, re-ran the golden through the cluster's own tools, and
checked that the model was exactly the recorded one. The cluster was busy, so the work ran in 2-hour pieces that
continue where the previous one stopped (`hpc/HPC_RUN.md`, section 7).

## 8. What happened

**Gemma.** Asked once, Gemma got the four small modules right in 19 of 20 answers but never got `input_port` or
`output_port` right, so none of its oneshot routers worked. The loops fixed most of that: 3 working routers with the
simulation loop, 4 with STITCH. The hidden tests never disagreed with the visible ones.

**qwen.** Asked once, qwen's code did not compile for four modules, in all 5 reps each. In `rr_arbiter`,
`input_port` and `router_5port` it set a signal declared as a `wire` inside an `always` block, which Verilog does
not allow; in `flit_mux` it declared the output `out` a second time. The instructions it was given state the right
rule. The loops fixed this for the small modules in one request. But:
- its **queue never worked**, in any arm or rep: it counted up to 4 with a 2-bit counter (`reg [1:0] count`, which
  can only reach 3) and handled "read and write at the same time" wrongly, and 6 rounds of feedback never fixed it.
  Every router needs five queues, so every qwen router was broken from the start;
- `input_port`, `output_port` and `router_5port` never passed their tests, even with golden smaller modules (wrong
  "full" signal, flits from the wrong input, packets sent the wrong way);
- the 4 qwen routers that the simulator could compile were rejected by Vivado (a `reg` connected to an output of a
  smaller module, which Vivado does not accept).

**STITCH against the plain loop, fairly.**
- Gemma rep 5: Gemma wrote `case ... end` instead of `case ... endcase` and repeated the same mistake in all 6
  requests of the plain loop. STITCH fixed it only after its "start again" step, with the same compiler message the
  plain loop got (STITCH's diagnosis adds nothing for a typing error). So the restart did it, not the diagnosis.
- Gemma reps 1 and 4: both loops produced working routers, but the plain loop's `output_port` kept a lint warning
  (`WIDTHTRUNC`: a 3-bit number used to pick one of 4 positions). The code checks the value first, so it is safe;
  Vivado shows nothing, and that plain-loop router is in fact the fastest of all. STITCH went on until the warning
  was gone.
- Gemma rep 2: the plain loop fixed `input_port`; STITCH did not.
- qwen: both loops ended equal (15 of 35 module runs right in each, no working router).
- STITCH's diagnosis switched on in no Gemma small-module run, and on the bigger modules every one of its messages
  contained a false statement (Limitations, first point).

## 9. Is the AI's hardware any good? (Vivado)

Vivado turns the code into a real circuit for the ZedBoard's chip and reports its size, speed and power:
- **LUT** (lookup table): the chip's basic logic cell. Fewer means smaller.
- **FF** (flip-flop): a 1-bit memory cell.
- **WNS** (worst negative slack): time to spare on the slowest path at 100 MHz. Positive means the speed is met.
- **Dynamic power**: power used because the circuit switches. **Static power** is the chip's leakage; it is the
  same for any design on that chip.

| router | LUT | FF | WNS | dynamic power | total power |
|---|---|---|---|---|---|
| golden | 716 | 245 | +0.209 ns | 0.010 W | 0.113 W |
| Gemma, simulation loop (3 working routers) | 667 to 699 | 240 | +0.087 to +0.629 ns | 0.008 to 0.010 W | 0.112 W in rep 1 |
| Gemma, STITCH loop (4 working routers) | 664 to 680 | 240 to 245 | +0.216 to +0.321 ns | 0.008 to 0.010 W | 0.112 W in rep 1 |

Every working AI router meets timing, has no latch, no loop and no warning beyond the golden's, and is slightly
smaller. **The power difference is not real:** the total is mostly the chip's static 0.103 W, and the dynamic part
differs only in the third decimal (0.010 against 0.009 W) of an estimate that guesses how often signals switch.
Building the golden and the two rep-1 routers by hand in the Vivado GUI (`vivado/projects/`) gave the same power
summary: 0.113 W total and 0.010 W dynamic for the golden, 0.112 W and 0.009 W for both rep-1 routers.

## 10. What went wrong along the way, and what we changed

| what happened | what we did |
|---|---|
| The hidden test of `rr_arbiter`, with new random inputs, said the **golden** was wrong | the test itself had a bug: after a reset in the middle of the run it did not restart its fairness count. One line fixed in `golden/tb/tb_rr_arbiter.v`; every golden check rerun. The extra hidden test found a defect in our own test. |
| The frozen tool that cuts the AI's code out of its answer starts at the first word "module"; the golden router's comment says "top_module" | the tasks' copy of the golden starts at its `module` line. Checked afterwards: no AI answer was cut this way (0 cases). |
| A 24-hour cluster job would have waited two days; the cluster refuses jobs that name two queues | the work was split into 2-hour pieces that run one after another and continue where the last stopped |
| STITCH's diagnosis on the bigger modules said "clk is never used" (found in the results) | a flaw of the test set-up, kept and reported (Limitations); fixing it would mean redoing both models |
| The laptop has older versions of the free tools than the cluster | the golden passes on both; the report says which tool gave which number |

## 11. What to keep in mind

- STITCH's diagnosis was fed a false statement on the bigger modules (Limitations, first point).
- 5 reps is a small number, and some reps were identical copies.
- Two models, both compressed, and one design.
- All arms used the same system instructions as the earlier phases, which include a rule about latches.

---

# Part 2. Technical record

Every number below comes from `scripts/analyze_gen.py` (`reports/GEN_<model>.md`) or
`scripts/vivado/vivado_routers.py` (`reports/VIVADO_LLM.md`). Counts are out of 5 reps, or out of 35 module runs
per arm (7 modules × 5 reps).

Settings: 7 modules × 5 reps × 3 arms per model; budget 6 LLM calls per loop run; T = 0.1; num_ctx 32768; Ollama
0.34.1; system prompt `phase3/runner/system_prompt.txt`; arms through the unmodified Phase 3 runner
(simloop = `baseline`, stitch = `sem_esc_restart_v3`). Deployed commit `2017dca`; `FREEZE.sha256` (79 files)
unchanged in every job. Models: `qwen2.5-coder:32b` (digest `b92d6a0bd47e…`, the Phase 3 digest) and
`gemma4:31b-it-q4_K_M` (digest `17ba34c06c80…`). Jobs: Gemma 434462 (H200, stopped at its 2-hour limit) and 434463
(H200, finished); qwen 434444 (H100, stopped at its 2-hour limit), 436070 (H200, finished) and 436071 (H100, found
nothing left). Logs in `hpc_logs/`.

## Modules (each generated alone; parents tested with the golden children)

| model | arm | loop testbench | hidden sign-off | struct_clean | all three | LLM calls | output tokens | thinking characters |
|---|---|---|---|---|---|---|---|---|
| Gemma 4 31B | oneshot | 23 | 23 | 32 | 23 | 35 | 206,392 | 464,230 |
| Gemma 4 31B | simloop | 33 | 33 | 32 | 31 | 35 | 378,747 | 940,647 |
| Gemma 4 31B | stitch | 33 | 33 | 35 | 33 | 31 | 316,342 | 729,793 |
| qwen2.5-coder 32B | oneshot | 5 | 5 | 10 | 5 | 35 | 20,552 | 0 |
| qwen2.5-coder 32B | simloop | 15 | 15 | 27 | 15 | 130 | 126,358 | 0 |
| qwen2.5-coder 32B | stitch | 15 | 15 | 27 | 15 | 130 | 121,480 | 0 |

The hidden sign-off testbenches never disagreed with the loop testbench (the same count in every row). Per-module
tables: `reports/GEN_<model>.md`.

## Pure routers (one arm's 7 files of one rep, nothing golden)

| model | arm | compile (Icarus) | working (router tb, router sign-off and 2x2 mesh pass) | working and struct_clean |
|---|---|---|---|---|
| Gemma 4 31B | oneshot | 4 | 0 | 0 |
| Gemma 4 31B | simloop | 4 | 3 | 1 |
| Gemma 4 31B | stitch | 5 | 4 | 4 |
| qwen2.5-coder 32B | oneshot | 0 | 0 | 0 |
| qwen2.5-coder 32B | simloop | 2 | 0 | 0 |
| qwen2.5-coder 32B | stitch | 2 | 0 | 0 |

## Vivado (golden flow: xc7z020clg484-1, out of context, 100 MHz)

The golden, run again through the same script, gives the same numbers as `reports/VIVADO_GOLDEN.md`.

| routers | count | LUT (golden 716) | FF (golden 245) | WNS ns (golden +0.209) | dynamic W (golden 0.010) | latches, non-OOC DRC, methodology, new warning ids |
|---|---|---|---|---|---|---|
| Gemma simloop, working | 3 | 667 to 699 | 240 | +0.087 to +0.629 | 0.008 to 0.010 | none |
| Gemma stitch, working | 4 | 664 to 680 | 240 to 245 | +0.216 to +0.321 | 0.008 to 0.010 | none |
| Gemma, failing (oneshot 4, simloop 1, stitch 1) | 6 | 5 of them 10, one 680 | 15, one 240 | | | none; the broken modules make most logic constant |
| qwen, compiling (simloop 2, stitch 2) | 4 | Vivado synthesis stops: `[Synth 8-685]`, a `reg` connected to an instance output | | | | |

## Where simloop and STITCH differ (same module and rep, different result)

- **Gemma: STITCH ahead in 3 module runs, simloop ahead in 1.**
  - `output_port` reps 1 and 4: simloop stopped at a testbench pass that still had a Verilator `WIDTHTRUNC`
    (`selected[owner]`, a 3-bit `owner` indexing a 4-bit vector); STITCH went on to a clean file.
  - `rr_arbiter` rep 5: a `case ... end` syntax error that Gemma repeated in all 6 simloop calls. STITCH fixed it
    after its blank-slate restart. Its feedback was the same compiler output as simloop's: the interpreter adds
    nothing for a compile error.
  - `input_port` rep 2: simloop fixed it, STITCH did not within 6 calls.
- The `WIDTHTRUNC` has no effect in hardware: the code tests `owner == 4` before indexing, so the index is 0 to 3.
  Vivado gives no extra warning, and simloop rep 1 has the best WNS of all routers (+0.629 ns).
- **qwen: STITCH ahead in 3 module runs, simloop ahead in 2**, all on `input_port` and `output_port` (compile or
  struct_clean); none of those files passes its testbench in either arm.
- STITCH's semantic feedback fired on 0 of 20 Gemma leaf-module runs and 2 of 20 qwen leaf runs. On parent modules
  it fired in 5 of 15 Gemma runs and 15 of 15 qwen runs, and every one of those prompts (10 Gemma, 63 qwen) contained
  a false statement (Limitations, first point).

## Outcomes written down before the run

| outcome | Gemma 4 31B | qwen2.5-coder 32B |
|---|---|---|
| A: loops beat one-shot | yes: working routers 0 one-shot, 3 simloop, 4 stitch | modules yes (5 to 15 of 35); routers no (0 in every arm) |
| B: STITCH beats the loop only where loop finals pass tests but carry latches, loops or lint | yes in 2 reps (`output_port` `WIDTHTRUNC`), with no difference in Vivado; the third STITCH-only working router (rep 5) came from the restart on a syntax error, not from lint | no |
| C: STITCH = loop | no (4 against 3 working routers) | yes (15 against 15 modules, 0 against 0 routers) |
| D: no full router works | no | yes |
| E: routers work but cost more PPA | no: fewer LUTs, timing met, the same dynamic power | not measurable |

**Conclusion.** Feedback loops turn Gemma's one-shot output (0 of 5 working routers) into working routers (3 and 4
of 5) whose Vivado results match or beat the golden. qwen2.5-coder 32B produces no working router in any arm.
STITCH ended with one more working router than the simulation loop on Gemma and the same as the loop on qwen. That
router came from STITCH's blank-slate restart; its two other differences were lint warnings with no effect in
Vivado; and its semantic diagnosis did not contribute (it fired on no Gemma leaf module, and its feedback on parent
modules was wrong). With 5 reps, one router is a small difference, and it is not evidence that STITCH's diagnosis
helps spec-to-RTL generation. The conclusion rule set before the run (if STITCH beats the loop on neither model, say
that STITCH is not built for spec-to-RTL generation and that its value is repair and sign-off) is not triggered by
the counts, since STITCH ended one working router ahead on Gemma; but the mechanism behind that router was the
restart, not the diagnosis.

## Limitations

- **Stub noise in STITCH's feedback on parents.** The pipeline (`pipeline/p3_bridge.py`, copied from the closed
  study and frozen before the run) lints a parent together with port-only stubs of its children. The stubs' unused
  inputs and undriven outputs reach the STITCH interpreter as if they were the parent's own, so all 73 semantic
  prompts on parent modules (10 Gemma, 63 qwen) said that `clk` is never used, and some that a child port is never
  declared. It affects only the STITCH arm on `input_port`, `output_port` and `router_5port`. struct_clean and the
  verdicts are not affected (those warnings are not hard ones). Removing it means changing the frozen pipeline and
  rerunning both models; it is left as a possible follow-up.
- **System prompt.** Every arm uses the Phase 3 production system prompt (`phase3/runner/system_prompt.txt`, for
  comparability), which contains coding rules, one of them about latches. The specs themselves are neutral.
- **5 reps, no seed.** Ollama has no seed option, and at T = 0.1 some reps coincide (Gemma: `route_compute` 2
  distinct files of 5, `flit_mux` 3; qwen: `route_compute` 1, `flit_mux` 2), so the effective sample is smaller.
- **Toolchains.** Loop testbench and struct_clean come from the HPC (Icarus 14, Verilator 5.053, Yosys 0.69); the
  sign-off and pure-router checks ran on the laptop (Icarus 12, Verilator 5.020, Yosys 0.33). The golden passes on
  both. Vivado 2022.2 on the laptop.
- **Two models, both quantised (Q4_K_M), one design.** Gemma thinks by default (its thinking text is kept in every
  call's `llm_meta.json`); qwen has no thinking mode.
- **Power is a vectorless estimate;** the dynamic-power differences between routers are in the third decimal.
- **Golden testbench fix before the run.** Reseeding for sign-off found stale fairness counters at the mid-run reset
  of `tb_rr_arbiter.v`; fixed, and every golden check rerun (`reports/TASKS_CHECK.md`).

## The original

`original_2x2_mesh_zedboard/` is the MPSoC's 2x2 mesh as its author built it for the ZedBoard: four 5-port routers
(`top_module`: link1 to link4 and core, 4 virtual channels each), a VIO core driving the core inputs and an ILA
core watching them, the bitstream, and screenshots of flits arriving on the board (`Outputs_2x2/`). Its router is
the one in `phase3/designs/mesh2x2_ref`, apart from 4 modules (`reports/ORIGINAL.md`).

It works on the board but cannot be a golden reference for a PPA comparison. Its own reports show 1,744 latches,
2,202 combinational loops (allowed by its XDC), no clock constraint, and 3,150 clock roots, so Vivado cannot time
it (`reports/ORIGINAL.md`). The folder is kept unchanged: the project, the IP folders and the run folders stay
local; git tracks the sources, constraints, project file, IP configurations, screenshots and the 4 reports that
`ORIGINAL.md` reads (`.gitignore`). Do not open the project in a newer Vivado in place: the upgrade rewrites it.
Copy it first.

## The golden router

Same router function and pins as the original's `top_module`, rebuilt clean.

Kept from the original:
- 5 ports (link1 to link4, core) and their names.
- The 32-bit flit format: bits 30:29 are the type (`01` head, `00` body, `10` tail, `11` no flit); bits 7:4 and
  3:0 are the destination row and column of a head flit.
- Row-first routing, the same as `routing_algo_mesh`: destination row higher goes to link1, lower to link2;
  same row: column higher goes to link3, lower to link4, equal to core. The router address is the input
  `current_address` (row in 7:4, column in 3:0).
- Wormhole switching: a head flit wins an output; the output stays with that packet until its tail flit leaves.
- Full-flag flow control (no valid/ready) and the idle flit `32'h6000_0000`.
- Each output serves the 4 other inputs; a packet never leaves by the port it came in on.

Changed:
- 1 virtual channel instead of 4. Bits 28:27 (the original's VC number), bit 31 and the payload pass through.
- One clock, synchronous active-high reset, flip-flops only. No latches, no loops, no derived clocks.
- Input buffer: 4 flits. `full_out` goes high at 3, which leaves room for the 2 flits a neighbour may still send.
- Outputs leave from registers. A flit is loaded into `data_out` at a clock edge only if `full_in` was low before
  that edge.

| module | kind | contents |
|---|---|---|
| `fifo` | sequential | 4 x 32-bit buffer, first-word fall-through, `empty`, `almost_full` |
| `route_compute` | combinational | row-first routing of a head flit, one-hot request |
| `rr_arbiter` | sequential + combinational | 4-requester round-robin, priority moves past each taken grant |
| `flit_mux` | combinational | 4-to-1, one-hot select, idle flit otherwise |
| `input_port` | hierarchical | `fifo` + `route_compute` + the route held from head to tail |
| `output_port` | hierarchical | `rr_arbiter` + `flit_mux` + the hold (owner) + the output register |
| `router_5port` | top | 5 `input_port`, 5 `output_port`, read-enable wiring |

## Why it can serve as the golden reference

| check | result | report |
|---|---|---|
| module and router testbenches (Icarus) | all pass | `GOLDEN_CHECKS.md` |
| the same testbenches in the Vivado simulator (xsim) | all pass, identical summaries | `VIVADO_GOLDEN.md` |
| STITCH's own struct_clean check (Yosys 0 latches, 0 loops; no hard Verilator warning) | all 7 modules | `GOLDEN_CHECKS.md` |
| the same checks on the cluster toolchain (smoke job 434111) | all pass | `hpc_logs/golden_checks_hpc_434111.md` |
| routing equals the board-verified original (Yosys miter + SAT, all inputs) | proved | `GOLDEN_CHECKS.md` |
| 2x2 mesh of golden routers wired as the original, replaying the ZedBoard test packets | delivered unchanged | `GOLDEN_CHECKS.md` |
| mutation test: 19 planted bugs | 19 caught, by the loop and by the sign-off testbenches | `MUTANTS.md`, `TASKS_CHECK.md` |
| Vivado, ZedBoard, 100 MHz, out-of-context | timing met, 0 latches, 0 loops, 0 unconstrained endpoints | `VIVADO_GOLDEN.md` |

The router testbench drives all 5 inputs with random packets and all 5 outputs with random backpressure. Senders
use the worst-case timing of a neighbouring router. It checks that every flit arrives at the right output, in
order, exactly once, without interleaving packets, never while `full_in` was high, and that the router is idle at
the end. The timing margin is small (worst path: buffer read, routing, arbitration and read enable in one cycle;
see `VIVADO_GOLDEN.md`), so the comparisons report WNS and fmax as numbers, not only met or failed.

The sha256 of every golden file is in `GOLDEN_CHECKS.md`; any change to the golden means rerunning every check.

## Folder map

| folder or file | content |
|---|---|
| `original_2x2_mesh_zedboard/` | the original 2x2 mesh project, as downloaded (Vivado 2014.4, ZedBoard, tested on the board) |
| `golden/` | the golden router: `rtl/` (7 modules), `tb/` (testbenches), `constraints/` (100 MHz XDC), `figures/` (Vivado GUI screenshots), `DESIGN.md` (plain-language walk-through) |
| `specs/` | the 7 hand-written specs; their port blocks are filled from the golden by `scripts/spec_ports.py` |
| `tasks/<module>/` | generated by `scripts/make_tasks.py`: `spec.md` (what the AI sees), `golden.v`, `input.v`, `tb.v`, hidden `tb_signoff*.v`, `meta.json`, and for parents `lib/` (golden children) and `stubs/` |
| `pipeline/` | the code the cluster job runs: `generate.py` (oneshot, simloop, stitch; 5 paired reps), `p3_bridge.py` (the frozen Phase 3 runner with the golden children), `preflight.py`, `mock_e2e.py`, `freeze.py` |
| `FREEZE.sha256` | sha256 of the 79 files that decide the prompts and the judging; checked by every job |
| `hpc/` | everything for the cluster: `deploy_to_hpc.ps1`, `hpc_env.sh`, the step scripts, `gen_job.slurm`, `HPC_RUN.md` (every command) |
| `hpc_logs/` | job logs copied back from the cluster, `MODELS.txt` (model digests), `JOBIDS.txt` |
| `results/<model>/` | everything each model produced: `prompts/`, `oneshot/rep<r>/` (answers and records), `arms/rep<r>/` (every loop iteration: prompt, response, metrics), `outputs/<arm>/rep<r>/<module>.v` (final files), `RUN_MANIFEST.json` |
| `scripts/` | every laptop-side check; each writes one report |
| `reports/` | `ORIGINAL.md`, `GOLDEN_CHECKS.md`, `MUTANTS.md`, `VIVADO_GOLDEN.md`, `TASKS_CHECK.md`, `GEN_<model>.md` (+ `.json`), `VIVADO_LLM.md` (+ `.json`) |
| `vivado/` | Vivado runs and GUI projects (gitignored, regenerated by the scripts) |

`results/` keeps the generated RTL, prompts, responses, records and metrics; the compiled simulations and tool logs
are not committed (`.gitignore`), since `scripts/analyze_gen.py` reruns the checks from the RTL.

## Reproduce

| step | command (from this folder) | where |
|---|---|---|
| golden: testbenches, lint, Yosys, routing proof | `python3 scripts/check_golden.py` | WSL (Icarus, Verilator, Yosys) |
| golden: mutation test | `python3 scripts/mutants.py` | WSL |
| golden: xsim + Vivado implementation | `python scripts/vivado/run_vivado.py` | Windows, Vivado 2022.2 (`VIVADO_BIN` to change the path) |
| the original's numbers | `python scripts/describe_original.py` | any |
| spec ports equal the golden | `python scripts/spec_ports.py --check` | any |
| build the task folders | `python scripts/make_tasks.py` | any |
| task check: golden passes every testbench, every mutant fails | `python3 scripts/check_tasks.py` | WSL |
| pipeline self-test with fake models | `python3 pipeline/mock_e2e.py` | WSL |
| freeze check | `python pipeline/freeze.py --check` | any |
| generation | `hpc/HPC_RUN.md` (one job per model, `hpc/gen_job.slurm`) | HPC |
| analysis of one model | `python3 scripts/analyze_gen.py <model folder in results/>` | WSL |
| Vivado on every compiling AI router | `python scripts/vivado/vivado_routers.py` | Windows, Vivado 2022.2 |
| Vivado GUI projects of the golden and every compiling AI router | `python scripts/vivado/vivado_routers.py --projects` (list in `vivado/projects/PROJECTS.md`) | Windows, Vivado 2022.2 |

`check_golden.py`, `check_tasks.py` and the pipeline import the STITCH runner's evaluation functions
(`phase3/runner/p3_eval.py`) without changing them, so the golden passes exactly the checks the AI outputs face.

## Open a router in the Vivado GUI

1. Golden: from this folder, `vivado -mode batch -source scripts/vivado/create_project.tcl`, then open
   `vivado/project/golden_router.xpr`. AI routers: `python scripts/vivado/vivado_routers.py --projects`, then open a
   `vivado/projects/<model>_<arm>_rep<r>/router.xpr`.
2. RTL block diagram: Open Elaborated Design, then Schematic.
3. Simulation: Run Simulation. `sim_1` runs the router testbench and `sim_mesh` the mesh testbench; a working
   router prints `ALL TESTS PASSED`.
4. Run Synthesis and Run Implementation: the same out-of-context flow as `scripts/vivado/flow.tcl`. The golden and
   the rep-1 routers of both Gemma loops were built this way in the GUI; their power summaries equal the batch
   runs' (0.113 W and 0.112 W total).

The golden's schematic and implementation summary from the GUI are in `golden/figures/`. Project-mode simulation
could not be started from the command line on this machine (Vivado could not spawn `compile.bat` without a
console: `Spawn failed: Broken pipe`); the same testbenches pass in xsim through `run_vivado.py`.
