#!/bin/bash
# Print the local (WSL) toolchain versions for the Step 2 parity comparison.
for t in python3 iverilog vvp verilator yosys; do printf '%-10s %s\n' "$t" "$(command -v $t || echo MISSING)"; done
python3 --version
python3 -c 'import openai; print("openai", openai.__version__)' 2>&1 | tail -1
echo "iverilog: $(iverilog -V 2>&1 | head -1)"
echo "verilator: $(verilator --version 2>&1 | head -1)"
echo "yosys: $(yosys -V 2>&1 | head -1)"
