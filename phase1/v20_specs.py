"""
v20_specs.py — module specs (LLM prompts) for the 10 v20-diagnostic modules
needed by TASK 2.5 (and, later, TASK 3's harmful/enabling run set).

PROVENANCE: these are NOT reconstructed or newly written. Each spec string
below is copied verbatim from a real recorded iteration-1 feedback.txt file
under the v2_fixes_20260816_030703 sweep (the same real historical dataset
already used for the STUCK_THRESHOLD fire-rate analysis) — iteration 1's
feedback.txt is exactly `messages[-1]["content"]` at that point in
stitch_runner.py's run_one_condition(), which for iteration 1 is the raw
spec text with no SYSTEM_PROMPT and no tool feedback mixed in. Source path
per module is cited below. No spec here was invented, paraphrased, or
tuned — copying the original spec text is exactly what "reused unmodified"
requires for these to be comparable to that historical run.

None of this lives in src/runner/stitch_runner.py's BENCHMARK dict (that
dict covers only the v2-suite modules, e.g. decoder_3to8, mux4_oe — a
different, smaller set). benchmarks/v20_diagnostic/ in this repo has the
testbenches for these 20 modules but not their spec/prompt text, which is
why this file exists.

DEPENDENCY: ripple_carry_adder's spec requires a separately-compiled
full_adder.v (it explicitly forbids redefining full_adder inline). The
recorded v2_fixes run was actually missing this dependency file — its
ripple_carry_adder runs all failed to compile with "Unknown module type:
full_adder" for that reason, a wiring gap in that historical sweep, not a
model defect. phase1/fixtures/full_adder_dependency.v is a real golden
full_adder implementation pulled from the original AutoChip project
(AgenticAI/Autochip/full_adder.v — the baseline system STITCH's own paper
compares against), port-compatible with the spec
(a, b, cin, sum, cout) and functionally equivalent to the spec's own
sum/cout formula. Pass it via the `dependencies=` argument when running
ripple_carry_adder.

Not a runnable script — a pure data module (spec strings + dependency
map). No WSL/Ollama involved; imported by stuck_threshold_diagnostic.py
and task3_runner.py.
"""

V20_SPECS = {
    # source: v2_fixes_20260816_030703/v20/deepseek-coder_67b/baseline/alu_8bit/iter_1/feedback.txt
    "alu_8bit": (
        "Create a Verilog-2001 module named 'alu_8bit'.\n"
        "Ports: input [7:0] A, B; input [2:0] op;\n"
        "       output reg [7:0] result; output wire zero\n"
        "Combinational always @(*) with case on op:\n"
        "  3'b000 ADD:   result = A + B;\n"
        "  3'b001 SUB:   result = A - B;\n"
        "  3'b010 AND:   result = A & B;\n"
        "  3'b011 OR:    result = A | B;\n"
        "  3'b100 XOR:   result = A ^ B;\n"
        "  3'b101 NOT_A: result = ~A;\n"
        "  3'b110 SHL:   result = A << 1;\n"
        "  3'b111 SHR:   result = A >> 1;\n"
        "  default:      result = 8'h00;\n"
        "assign zero = (result == 8'h00);\n"
        "Declare result as reg, zero as wire.\n"
    ),

    # source: v2_fixes_20260816_030703/v20/deepseek-coder_67b/baseline/counter_4bit/iter_1/feedback.txt
    "counter_4bit": (
        "Create a Verilog-2001 module named 'counter_4bit'.\n"
        "Ports: input clk, rst; output reg [3:0] count\n"
        "4-bit unsigned up-counter, synchronous active-high reset:\n"
        "  always @(posedge clk) begin\n"
        "    if (rst) count <= 4'b0;\n"
        "    else     count <= count + 1'b1;\n"
        "  end\n"
        "Declare count as reg. Wraps naturally 15->0.\n"
    ),

    # source: v2_fixes_20260816_030703/v20/deepseek-coder_67b/baseline/full_adder/iter_1/feedback.txt
    "full_adder": (
        "Create a Verilog-2001 module named 'full_adder'.\n"
        "Ports: input a, b, cin; output sum, cout\n"
        "Use only continuous assign statements:\n"
        "  assign sum  = a ^ b ^ cin;\n"
        "  assign cout = (a & b) | (b & cin) | (a & cin);\n"
        "Declare sum and cout as wire. Do NOT use always blocks.\n"
    ),

    # source: v2_fixes_20260816_030703/v20/deepseek-coder_67b/baseline/gray_counter_4bit/iter_1/feedback.txt
    "gray_counter_4bit": (
        "Create a Verilog-2001 module named 'gray_counter_4bit'.\n"
        "Ports: input clk, rst; output wire [3:0] gray_out\n"
        "Internal 4-bit binary up-counter, synchronous active-high reset:\n"
        "  always @(posedge clk) begin\n"
        "    if (rst) bin <= 4'b0;\n"
        "    else     bin <= bin + 1'b1;\n"
        "  end\n"
        "Gray encode: assign gray_out = bin ^ (bin >> 1);\n"
        "Declare bin as reg [3:0]. Declare gray_out as wire.\n"
    ),

    # source: v2_fixes_20260816_030703/v20/deepseek-coder_67b/baseline/pipeline_mult_4x4/iter_1/feedback.txt
    "pipeline_mult_4x4": (
        "Create a Verilog-2001 module named 'pipeline_mult_4x4'.\n"
        "Ports: input clk; input [3:0] a, b; output reg [7:0] product\n"
        "2-stage pipelined 4x4 unsigned multiplier.\n"
        "Internal registers: reg [3:0] a_r, b_r;\n"
        "Both stages update in ONE always block on the SAME posedge clk:\n"
        "  always @(posedge clk) begin\n"
        "    a_r     <= a;           // Stage 1: latch inputs\n"
        "    b_r     <= b;\n"
        "    product <= a_r * b_r;   // Stage 2: multiply the latched values\n"
        "  end\n"
        "TIMING: inputs at cycle N appear at product at cycle N+2 (not N+1).\n"
        "The testbench checks product exactly 2 cycles after inputs are applied.\n"
        "Do NOT compute the product combinationally.\n"
        "Do NOT use separate always blocks for the two stages.\n"
    ),

    # source: v2_fixes_20260816_030703/v20/deepseek-coder_67b/baseline/pwm_generator/iter_1/feedback.txt
    "pwm_generator": (
        "Create a Verilog-2001 module named 'pwm_generator'.\n"
        "Ports: input clk, rst; input [7:0] duty_cycle;\n"
        "       output wire pwm_out\n"
        "Internal 8-bit free-running counter (0..255 wraps), sync reset:\n"
        "  always @(posedge clk) begin\n"
        "    if (rst) counter <= 8'd0;\n"
        "    else     counter <= counter + 1'b1;\n"
        "  end\n"
        "Output (STRICTLY less-than -- NOT less-than-or-equal):\n"
        "  assign pwm_out = (counter < duty_cycle);\n"
        "  pwm_out=1 when counter is 0,1,...,duty_cycle-1\n"
        "  pwm_out=0 when counter is duty_cycle,...,255\n"
        "  Example: duty_cycle=4 => HIGH for counter=0,1,2,3 only.\n"
        "Declare counter as reg [7:0]. Declare pwm_out as wire.\n"
    ),

    # source: v2_fixes_20260816_030703/v20/deepseek-coder_67b/baseline/ripple_carry_adder/iter_1/feedback.txt
    "ripple_carry_adder": (
        "Create a Verilog-2001 module named 'ripple_carry_adder'.\n"
        "Ports: input [3:0] A, B; input cin; output [3:0] Sum; output cout\n"
        "CRITICAL: Do NOT define or redeclare the 'full_adder' module anywhere in this file. "
        "It is provided as a separately compiled dependency. Only write the 'ripple_carry_adder' module -- nothing else.\n"
        "Rules:\n"
        "1. Declare Sum [3:0] and cout as wire.\n"
        "2. Instantiate 'full_adder' four times: fa0, fa1, fa2, fa3.\n"
        "3. full_adder port names exactly: .a  .b  .cin  .sum  .cout\n"
        "4. Chain carries: fa0.cout->fa1.cin, fa1.cout->fa2.cin, fa2.cout->fa3.cin\n"
        "5. fa0.cin = cin (module input); fa3.cout = cout (module output)\n"
        "6. Sum[0]=fa0.sum, Sum[1]=fa1.sum, Sum[2]=fa2.sum, Sum[3]=fa3.sum\n"
    ),

    # source: v2_fixes_20260816_030703/v20/llama31_latest/baseline/simple_cpu_alu/iter_1/feedback.txt
    "simple_cpu_alu": (
        "Create a Verilog-2001 module named 'simple_cpu_alu'.\n"
        "Ports: input [3:0] A, B; input [1:0] op;\n"
        "       output reg [3:0] result; output wire zero\n"
        "Combinational always @(*) with case on op:\n"
        "  2'b00 ADD: result = A + B;\n"
        "  2'b01 SUB: result = A - B;\n"
        "  2'b10 AND: result = A & B;\n"
        "  2'b11 OR:  result = A | B;\n"
        "  default:   result = 4'b0;\n"
        "assign zero = (result == 4'b0000);\n"
        "Declare result as reg, zero as wire.\n"
    ),

    # source: v2_fixes_20260816_030703/v20/deepseek-coder_67b/baseline/spi_master_8bit/iter_1/feedback.txt
    "spi_master_8bit": (
        "Create a Verilog-2001 module named 'spi_master_8bit'.\n"
        "Parameter: CLK_DIV = 4\n"
        "Ports: input clk, rst, start; input [7:0] mosi_data; input miso;\n"
        "       output reg sclk, cs_n, mosi, done;\n"
        "       output reg [7:0] miso_capture\n"
        "SPI master mode 0 (CPOL=0, CPHA=0), 8-bit MSB-first.\n"
        "FSM states (reg [1:0]): IDLE=2'd0, ACTIVE=2'd1, DONE_ST=2'd2\n"
        "Internal: reg [7:0] shift_out, shift_in; reg [3:0] clk_cnt, bit_cnt;\n"
        "IDLE:  cs_n=1, sclk=0, done=0.\n"
        "  On start: cs_n<=0; shift_out<=mosi_data; bit_cnt<=0; clk_cnt<=0; goto ACTIVE.\n"
        "ACTIVE: each bit takes 2*CLK_DIV clocks.\n"
        "  clk_cnt increments each cycle.\n"
        "  First half  (clk_cnt < CLK_DIV):    sclk<=0; mosi<=shift_out[7].\n"
        "  At clk_cnt==CLK_DIV-1:               sclk<=1.\n"
        "  Second half (clk_cnt >= CLK_DIV):    sclk<=1.\n"
        "  At clk_cnt==2*CLK_DIV-2:             shift_in<={shift_in[6:0],miso}.\n"
        "  At clk_cnt==2*CLK_DIV-1: sclk<=0; shift_out<={shift_out[6:0],1'b0};\n"
        "    clk_cnt<=0; bit_cnt<=bit_cnt+1.\n"
        "  When bit_cnt==8: cs_n<=1; miso_capture<=shift_in; goto DONE_ST.\n"
        "DONE_ST: done<=1 for 1 cycle; goto IDLE.\n"
    ),

    # source: v2_fixes_20260816_030703/v20/deepseek-coder_67b/baseline/sync_fifo_8/iter_1/feedback.txt
    "sync_fifo_8": (
        "Create a Verilog-2001 module named 'sync_fifo_8'.\n"
        "Ports: input clk, rst, wr_en, rd_en; input [7:0] din;\n"
        "       output reg [7:0] dout; output wire full, empty\n"
        "Synchronous FIFO: 8 entries x 8-bit wide.\n"
        "Internal: reg [7:0] mem [0:7]; reg [3:0] wr_ptr, rd_ptr;\n"
        "  assign empty = (wr_ptr == rd_ptr);\n"
        "  assign full  = (wr_ptr[2:0] == rd_ptr[2:0]) && (wr_ptr[3] != rd_ptr[3]);\n"
        "Synchronous (posedge clk):\n"
        "  if rst: wr_ptr<=0; rd_ptr<=0; dout<=0;\n"
        "  else:\n"
        "    if (wr_en && !full):  mem[wr_ptr[2:0]]<=din; wr_ptr<=wr_ptr+1;\n"
        "    if (rd_en && !empty): dout<=mem[rd_ptr[2:0]]; rd_ptr<=rd_ptr+1;\n"
        "Declare dout as reg; full and empty as wire.\n"
    ),
}

# module -> list of dependency file paths (relative to this file's directory)
# needed alongside the module under repair, copied into each iter_dir exactly
# as stitch_runner.run_one_condition()'s `dependencies` argument already does.
V20_DEPENDENCIES = {
    "ripple_carry_adder": ["fixtures/full_adder_dependency.v"],
}
