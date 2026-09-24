# Phase 3, explained from zero

This document assumes no hardware background. It explains:
- what you asked for;
- what an MPSoC is;
- what the tools do, and exactly how Yosys finds each defect;
- what was built and measured;
- whether STITCH is likely to help.

Every code snippet and tool message below is real output from this project, not an illustration.

---

## 1. What you asked for, in plain words

Across these sessions you asked for four things:

1. **Make STITCH's "translator" smarter without breaking what already works.** The translator is the interpreter
   that turns tool warnings into advice for an AI model. Your production interpreter had to stay exactly as it is,
   so every earlier result stays valid.
2. **Test STITCH on real, bigger hardware.** The group's MPSoC is a multi-processor chip design, and the question is
   whether fixing small parts fixes the whole.
3. **Package everything so Claude Code can put it into your repo**, while you run the experiments on the H100 GPU
   node yourself.
4. **Explain all of it** (this document).

What was delivered:
- **An upgraded interpreter layer (v3)** that sits on top of your untouched production interpreter (v2).
- **11 repair tasks** built from the real MPSoC code.
- **A runner** that asks AI models to repair them under 5 conditions.
- **A composition tool** that plugs repaired parts back into the full chip.
- **Measurements** of the real chip that already answer part of the question.
- **Scripts and a checklist** for Claude Code (today) and for you on the HPC (tomorrow).

---

## 2. Hardware basics you need

### 2.1 Chips are described in code

A chip designer does not draw transistors by hand. They write a text description of the behaviour in a
**hardware description language**; here that language is **Verilog**. The description is called **RTL** (register-
transfer level). A tool then turns the text into real logic gates.

The unit of Verilog is a **module**, like a function in software. It has **ports** (inputs and outputs) and a body.
Modules can contain other modules, which is how big chips are built from small pieces.

The crucial difference from software is that hardware is not a list of steps run one after another. Every part of the
chip exists physically and works *at the same time*. Verilog code *describes wiring*; it is not a program that runs.

### 2.2 Two kinds of logic: "calculator" and "memory"

**Combinational logic** is like a calculator. Its outputs depend only on its inputs right now: change the inputs and
the outputs follow almost instantly. In Verilog you write it as `always @(*)` ("whenever anything changes, recompute")
or as `assign`.

**Sequential logic** is memory. It remembers a value and updates it only at a precise moment, the tick of the
**clock**. The clock is a signal that flips between 0 and 1 millions or billions of times per second, and the
**rising edge** (0→1) is the tick. The memory element that updates on the tick is a **flip-flop**. In Verilog it is
written `always @(posedge clk)`.

A good mental picture of a flip-flop is a camera. It takes one snapshot of its input at each tick and shows that
photo until the next tick. Everything in a modern chip runs to the beat of these snapshots, which is what makes timing
predictable.

### 2.3 The latch: the accidental memory

A **latch** is a different memory element. Instead of a camera it behaves like a window with a shutter:
- while its "enable" is open, the output follows the input continuously;
- when the enable closes, it freezes whatever was there.

Designers sometimes want latches, but in almost all modern design flows they are treated as a bug:
- **Timing analysis gets harder.** The tools that check the chip is fast enough reason about the clock ticks, and a
  latch is transparent for a whole window of time.
- **Glitches get through.** Brief wrong values (glitches) pass straight through an open latch.
- **They are usually unintended.** The designer wanted a calculator and accidentally got memory.

**How do you accidentally create one?** Take this real code from the MPSoC (`mux3`, the operand-forwarding selector
of the processor):

```verilog
always @(*) begin
  if (sel == 2'b00)      alu_in = id_ex_output_data1;
  else if (sel == 2'b01) alu_in = ex_forwarding;
  else if (sel == 2'b10) alu_in = mem_forwarding;
end
```

The code says what `alu_in` is for `sel` = 00, 01 and 10, but **not for 11**. In hardware, a wire cannot "not have
a value". The only way to honour "don't change `alu_in` when `sel` is 11" is to *remember* the previous value, and
remembering means memory. So the synthesis tool quietly builds a latch: 32 of them, one per bit of `alu_in`. Since
`mux3` is used twice in the processor, that is 64 accidental latches from four lines of code.

The fix is one line: give `alu_in` a value on every path, for example a final `else` or a default at the top.

### 2.4 Other defect types in this project

- **Combinational loop.** A signal that depends on itself with no clock in between. It is like two people each
  saying "I'll decide after you do": the value can oscillate or settle unpredictably. The real example is the
  processor's fetch unit writing `PC = PC;` inside `always @(*)`.
- **Multiple drivers.** Two pieces of logic both try to set the same wire. It is like two people talking on one
  phone line at the same time: if one says 1 and the other says 0, the real wire is in a fight, and the result is
  undefined (shown as `x` in simulation).
- **Width mismatch / truncation.** Pouring 50 bits into a 32-bit container: the top 18 bits silently spill away.
  Verilog allows it without an error, which is why it is dangerous.
- **Asynchronous-reset style error.** A reset that acts *immediately*, not waiting for the clock tick, must be
  written in one specific pattern. The MPSoC's 1-bit register mixes a normal "clear" signal into the reset
  condition, `if (clr | reset)`. Synthesis cannot build that as a standard flip-flop and gives up with an error.
- **Missing clock.** A register meant to update on the clock tick is written without the clock
  (`always @(clr, ce)`). The clock input is declared but never used, so the "register" becomes a latch. The MPSoC's
  `register_4bit` and `register_32bit` are like this. The original file even contains commented-out code showing the
  designer meant to use the clock.

---

## 3. RISC-V, NoC and MPSoC

### 3.1 RISC-V

A processor follows an **instruction set**: the list of commands it understands (add, load from memory, jump, and so
on). **RISC-V** is an open, free instruction set, so anyone can design a processor for it. The processor in this
project is a 32-bit RISC-V core with a **5-stage pipeline**.

A pipeline works like an assembly line: while one instruction is being executed, the next one is being decoded and
the one after that is being fetched. The stages are fetch, decode, execute, memory and write-back. Because
instructions overlap, a result an instruction needs may still be "in the pipe". **Forwarding multiplexers** such as
`mux3` pick the freshest copy of a value from wherever it currently is. That is why a defect in `mux3` matters.

The **ALU** (arithmetic logic unit) is the calculator of the core. It computes add, subtract, AND, OR, shifts and
so on, and raises status **flags**:
- *zero*: the result is 0;
- *negative*: the top bit is 1;
- *carry*: an unsigned add overflowed out of the top bit;
- *overflow*: a signed add gave the wrong sign.

### 3.2 MPSoC and the network-on-chip

An **MPSoC** (Multi-Processor System-on-Chip) puts several processors, memories and other blocks on one chip. They
need to talk, and a shared bus (one wire everyone takes turns on) becomes a traffic jam when many processors share it.
So MPSoCs use a **Network-on-Chip (NoC)**, a tiny road network etched into the chip:

- A **router** is a crossroads. It receives packets on its input ports (north, south, east, west, and "local", its
  own processor), decides where each packet goes (the **routing algorithm**; here XY routing: first travel along X,
  then along Y), and lets one packet at a time through each output (the **arbiter**, which works round-robin so
  everyone gets a turn).
- The **crossbar** is the switch inside the router that physically connects an input to an output.
- **Virtual channels** are like extra lanes, so one stuck packet does not block everyone behind it.
- A **mesh** is the road grid: a **2×2 mesh** has 4 routers in a square, a **3×3 mesh** has 9.
- The **network interface (NI)** is the post office between a processor and the network. It chops a message into
  **flits** (flow-control units, like train carriages with a head carriage that carries the address) and puts them
  back together on the other side.
- **FIFOs** (first-in-first-out queues) are the waiting rooms where flits sit until the road is free.

### 3.3 The MPSoC in your repo

`MPSoC/MPSoC Source Codes` has a RISC-V core (`processor/`), the router (`router/`, a 2×2 mesh), the network
interface (`NI/`) and a top module `main.v` that connects one core, one NI, the 2×2 router mesh and a depacketiser.
`Automation Code` in the RISC-V repo also contains a 3×3 mesh built from the same router pieces (28 of its 33 leaf
files are identical). That gave us two sizes of the same network to compare.

Four things were found when this design was put through open-source tools:

1. **It did not compile as-is.** Vivado, the tool it was written in, is forgiving. The open-source tools rejected
   nested comments, wires declared twice, and module instances with one port missing. These were fixed without
   touching any logic defect; every change is listed in `designs/SANITISATION.md`.
2. **The human-written reference contains the exact defect types STITCH targets.**
   - 63 latch inferences across 12 modules.
   - A synthesis **crash** caused by one 1-bit register (the async-reset style error).
   - A 1-bit program-counter port on a module the core drives with 32 bits.
   - A network-interface FIFO wired by position with one port missing, so two status signals land on the wrong
     pins.
3. **The top-level testbench is weak.** The processor executes 2 real instructions and then fetches garbage, and
   the network output never changes in 5,000 cycles. "The whole chip passes simulation" would therefore mean almost
   nothing, so the experiment only makes *structural* claims at the top and checks behaviour on each small module
   separately.
4. **At the `main` top, the network is optimised away.** Its outputs do not reach the chip's output pin, so
   synthesis deletes it as unused. That is why the network is measured using the mesh tops directly.

---

## 4. The three tools, and exactly how Yosys finds problems

### 4.1 Icarus Verilog: the simulator

Icarus runs the design like a video game against a **testbench**, a script that drives inputs and checks outputs. If
the checks pass, the testbench prints `ALL TESTS PASSED`.

Simulation can only catch what the testbench tests. The `mux3` task's specification declares `sel` = 11 unused, so its
testbench only drives 00, 01 and 10. So **`mux3` passes simulation with its 32
latches intact**. Six of the 11 Phase 3 tasks are like this ("sim-silent"). A loop that only uses simulation,
AutoChip-style, will declare victory on all six.

### 4.2 Verilator: the lint (grammar and style checker)

Verilator reads the code without running it and warns about suspicious patterns. Each warning has a code. The real
warnings in this project include:
- `LATCH`: "Latch inferred for signal 'alu_in'";
- `UNUSEDSIGNAL`: "Signal is not used: 'clk'";
- `MULTIDRIVEN`, `WIDTHTRUNC`, and `UNOPTFLAT` (a combinational loop).

### 4.3 Yosys: synthesis (turning code into gates)

Synthesis is the translation from "what should happen" to "which gates, wired how". Think of it as turning a recipe
into a shopping list plus a kitchen floor plan. Yosys does it in passes, and several of those passes are where
defects get caught.

**Step 1, `read_verilog`.** The text is parsed into an internal form.

**Step 2, `proc` (processes → decision trees).** Every `always` block is converted into a tree of decisions: "if sel
is 00 then this value, else if…". Inside `proc`, several sub-passes matter:

- **`proc_dlatch`: the latch detector.** For every signal assigned in a combinational block, Yosys works out the
  condition under which it is assigned. If some path through the decision tree assigns nothing, the signal must hold
  its value on that path. Yosys then inserts a latch cell whose enable is "one of the assigning paths was taken", and
  prints the message. The real output for `mux3` is:

  ```
  Latch inferred for signal `\mux3.\alu_in' from process `\mux3.$proc$dut.v:10$1'
  ```

  Reading it piece by piece: the module is `mux3`, the signal is `alu_in`, and the always block starts at **line 10**
  of the file. For a complete block Yosys instead prints `No latch inferred for signal …`. Your production
  interpreter deliberately ignores that negative message; it once caused a false alarm.
- **`proc_dff`: the flip-flop builder.** For `always @(posedge clk …)` blocks, it builds flip-flops. With an
  asynchronous reset it expects the pattern "if the reset signal → reset value, else normal behaviour". In
  `register_1bit` the first test is `clr | reset`, a mix of the reset and an ordinary signal. Yosys cannot express
  that as a standard reset flip-flop and stops with `ERROR: Multiple edge sensitive events found for this signal!`.
  Note that this message names **no signal at all**, so the v3 interpreter reads the source file to find the
  offending block.

**Step 3, `synth` (optimise and map to generic gates).** The design is optimised: unused logic is removed (which is
why the network disappears at `main`), and everything is mapped to simple gate types. Latches become cells named
`$_DLATCH_P_` / `$_DLATCH_N_`, one per bit.

**Step 4, `check`.** Yosys builds a graph of which signal feeds which. A cycle made only of combinational gates is a
combinational loop, reported as `Warning: found logic loop in module X:` followed by the gates and wires involved.
Yosys can also miss one: in the fetch unit it stayed silent while Verilator's `UNOPTFLAT` caught the `PC = PC` loop.
This is why the v3 layer listens to both tools.

**Step 5, `stat`.** Yosys counts cells. Combined with the design hierarchy (how many copies of each module exist),
this gives the number of latch **cells** in the whole chip, as opposed to the number of latch **messages**.

### 4.4 The key composition fact, measured

Both meshes contain the defective `register_32bit` (32 latch bits) and `register_4bit` (4 bits). Each router uses 20
of each.

| | 2×2 mesh (4 routers) | 3×3 mesh (9 routers) |
|---|---|---|
| Yosys latch messages | **2** | **2** |
| Latch cells in the chip | 2,880 = 36 × 20 × 4 | 6,480 = 36 × 20 × 9 |
| Synthesis | crash (1-bit register) | crash (1-bit register) |

The number of messages does not change with chip size, because Yosys reports once per module *definition*. The
physical damage grows exactly with the number of routers (6,480 / 2,880 = 9/4). Two consequences follow:

- **For STITCH:** an AI model repairing the leaf module sees the same two short messages whether the chip has 4
  routers or 400.
- **The good news:** fixing one small definition fixes every copy. When the three defective register modules were
  replaced with correct versions, **both meshes synthesised with 0 latches**. For the full MPSoC, fixing the 8 task
  modules turned the crash into a successful synthesis. The 122 latch cells that remain belong to 5 modules that are
  not in the task set, so the paper can claim "restored synthesis", not "latch-free chip".

The growth is linear (it grows with N), not exponential. The earlier plan's "exponential" wording and its "post-layout
timing failure" claim were dropped, because Yosys does no layout or timing analysis.

---

## 5. STITCH, AI models and the interpreter

### 5.1 The loop

A language model (LLM) is asked to write or fix Verilog. The code is run through the tools, the result is fed back,
and the model tries again, up to 6 times. This is the AutoChip-style loop. STITCH's idea is that small models
cannot read raw tool jargon well, so a deterministic **interpreter** (plain rules, no AI) translates each warning into
a short, specific instruction: a **directive**.

### 5.2 What the production interpreter (v2) does well

It is already careful:
- it handles Verilator's quoted names;
- it avoids fake signal names made from numbers;
- it ignores Yosys's "No latch inferred" message;
- it tailors the latch advice to the code structure.

For `mux3`, v2's directive says exactly the right thing: give `alu_in` a value at the top of the block. v3 passes
this text through unchanged.

### 5.3 Where v2 gave wrong or no advice on real code

On `register_4bit`, the real warnings are Yosys "latch on `dout`" plus Verilator "Signal is not used: 'clk'". v2
handles each warning separately. For the unused `clk` it uses its generic template for an unused input:

```
*** CRITICAL: Port 'clk' is declared but NEVER USED in your always block. ***
You MUST condition on 'clk':
  always @(*) begin
    if (clk) begin <your existing logic> end else begin dout = 4'b0; end
  end
```

That template is right for an *enable* input, but for a clock it is wrong. It tells the model to treat the clock as
an ordinary data signal inside a calculator block, which builds a clock-gated latch: the opposite of the fix. v3
combines both warnings, sees "latch in a block with no clock, plus an unused clock", and says instead:

```
*** CRITICAL: MISSING CLOCK -- 'dout' is a REGISTER but is written in a level-sensitive always block (line 11),
so synthesis built a LATCH, and the clock port 'clk' is never used. ***
EXACT FIX: change that block's header to  always @(posedge clk)  ... Do NOT add 'if (clk)' anywhere.
```

The ten findings (F1–F10) are in `evidence/PROD_V2_ON_REAL_LOGS.md`. In short:
- **Wrong advice:**
  - clocks treated as enables;
  - partly-unused buses (a 32-bit instruction of which 5 bits are legitimately unused) turned into "gate the output on
    this bus";
  - advice for the wrong module when one file holds several modules.
- **No advice:**
  - the async-reset crash;
  - a loop only Verilator sees;
  - width truncation of a whole expression (`{a, b, c}` too wide);
  - style warnings (`BLKSEQ`/`COMBDLY`), which named the English word "process" instead of a signal.
- **One API trap:** passing signal *names* instead of Yosys *lines* into the latch function produces "latch on
  'out'". Claude Code checks today whether your runners ever did that.

### 5.4 v3, the additive layer

- **Your production file is not modified.** v3 imports it, and in `version="v2"` mode it reproduces its output
  exactly. That way Phase 1 and 2 stay valid, and "v2 vs v3" becomes a clean experiment.
- **v3 only intervenes** where a real log showed v2 wrong or silent. Everywhere else, its output is v2's text,
  byte for byte, and tests enforce this.
- **Advice is capped** at 3 directives per attempt, most important first. Earlier phases showed long or complicated
  advice can hurt small models.
- **Measured on the 11 tasks** with the real tools: v2 produces advice on 9 of them. It is silent on `register_1bit`
  and `ni_flit_pack`, gives wrong advice on the two registers, and adds a misleading "gate the output on
  `Instruction_code`" directive on `Address_select`. v3 produces the intended advice on all 11.

---

## 6. The experiment in plain words

- **11 tasks.** 8 real defective modules from the MPSoC plus 3 seeded ones: an ALU with flag latches, a crossbar
  with multiple drivers, and a flit packer with truncation. Each task has four parts:
  - `input.v`: the defective code the model is given;
  - `spec.md`: what the module must do;
  - `tb.v`: a testbench that checks behaviour;
  - `golden.v`: a correct reference fix, used only to prove the task is solvable and never shown to the model.
- **5 conditions**, meaning 5 ways of giving feedback. All use the same limit of 6 attempts.
  1. `baseline`: simulation results only; stops as soon as simulation passes (what AutoChip ships).
  2. `raw_adv`: simulation plus the raw Verilator and Yosys text.
  3. `sem_adv_v2`: simulation plus your production interpreter's directives.
  4. `sem_adv_v3`: simulation plus v3's directives.
  5. `sem_esc_restart_v3`: starts like baseline, but only switches on v3 advice after the model gets stuck twice on
     the same problem, and restarts from scratch if still stuck.
- **6 models**, small to medium: llama3.2 3B, gemma3 4B, deepseek-coder 6.7B, qwen2.5-coder 7B, llama3.1 8B and
  qwen2.5-coder 14B.
- **3 repeats each.** Total: 11 × 5 × 6 × 3 = **990 runs**.
- **Metrics:**
  - `func_pass`: the testbench passes.
  - `clean_pass`: the testbench passes **and** Yosys synthesises with 0 latches and 0 loops **and** Verilator reports
    none of the serious warnings. This is the main score.
  - `silent_structural_pass`: `func_pass` without `clean_pass`, i.e. the model "passed" but the defect is still
    there. This is what a simulation-only loop cannot see.
  - `semantic_fired`: the interpreter actually produced advice in that run. A success is only credited to the
    interpreter if this is 1, the same rule your earlier phases used.
  - `latch_count_before` / `latch_count_after`, `verilator_warnings_count`, and `top_level_synthesis_pass` (filled in
    after the repaired modules are plugged back into the real chip).

---

## 7. Will STITCH actually help? An honest answer

**Two things are already established, without any AI:**
- **A simulation-only loop cannot see 6 of the 11 defects.** Any condition that runs Yosys and Verilator can.
- **v3 at least produces the right instruction every time.** v2 was silent on 2 of the 11 tasks, wrong on 2, and
  added a misleading extra directive on a fifth.

**What is not known until the HPC runs finish:** whether the *models* follow the advice. Your earlier phases found
that the interpreter's benefit depended on model size. It helped in a narrow band of small models, could hurt with
complicated advice, and produced no interpreter-credited wins among the large models in Set 3.

The comparisons that decide it:

| Comparison | What it isolates | Most informative tasks |
|---|---|---|
| `raw_adv` vs `sem_adv_v3` | Is the translation better than raw tool text? | all |
| `sem_adv_v2` vs `sem_adv_v3` | Did the upgrade matter? | `register_1bit`, `ni_flit_pack` (v2 silent), `register_4bit`, `register_32bit` (v2 misleading) |
| `baseline` silent structural pass rate | How often a simulation-only loop ships a broken chip | the 6 sim-silent tasks |

**Possible outcomes, all publishable:**
- **v3 beats raw and v2 on the tasks where v2 was silent or wrong.** This is direct evidence that the interpreter's
  vocabulary matters.
- **v3 ≈ raw.** The tools matter, not the translation, at least for these model sizes. That is an honest boundary.
- **Some models get worse with v3.** Consistent with the earlier "harmful regime" finding; report it with the same
  weight.

**What STITCH can never do at the leaf level:** catch defects that only exist when modules are connected. The 1-bit
PC port and the shifted FIFO wiring are examples. They need integration-level feedback, and the paper lists this as a
limitation.

---

## 8. Who does what, and when

| When | Who | What |
|---|---|---|
| Today | Claude Code, on the laptop | `HANDOFF_PHASE3_CLAUDE_CODE.md` tasks T0–T10, listed below |
| Tomorrow | You, in PowerShell + ssh | `HPC_PHASE3_COMMANDS.md` Parts A–I, listed below |

Claude Code's tasks today:
- place the files and delete yesterday's duplicates;
- fix line endings;
- check the MPSoC matches the analysed one;
- check the runner details (T4);
- save the production system prompt;
- run the retro-audit on old results;
- run all checks locally;
- add pointers to your existing docs;
- commit on a branch.

Your steps tomorrow:
- **A:** check what survived on scratch;
- **B:** deploy;
- **C:** run the gate job; nothing else runs unless it prints `ALL GATES PASSED`;
- **D:** pull models;
- **E:** a 20-run pilot, reviewed before continuing;
- **F:** the 990-run job on the H100;
- **G:** monitor and resubmit;
- **H:** composition + summary;
- **I:** download.

---

## Glossary

| Term | Meaning |
|---|---|
| RTL / Verilog | text description of hardware behaviour |
| module / port | a hardware block / its inputs and outputs |
| combinational | output depends only on current inputs (`always @(*)`, `assign`) |
| sequential / flip-flop | memory that updates on the clock edge (`always @(posedge clk)`) |
| latch | memory that follows its input while enabled; usually an accident in combinational code |
| synthesis | converting RTL into gates (Yosys) |
| lint | static checking for suspicious code (Verilator) |
| simulation / testbench | running the design against checks (Icarus) |
| MPSoC | a chip with several processors plus the network connecting them |
| NoC / router / mesh | on-chip network / its crossroads / its grid layout |
| NI / flit / FIFO | network interface / packet piece / queue |
| directive | the interpreter's plain-language repair instruction |
| sim-silent defect | a defect the testbench cannot see |
| clean_pass | testbench passes **and** synthesis is structurally clean |
