#!/bin/bash
# Run the engine's exact Verilator lint command on one saved candidate: lint_one.sh <file.v>
verilator --lint-only -Wall --bbox-unsup -Wno-DECLFILENAME -Wno-TIMESCALEMOD -Wno-EOFNEWLINE "$1" 2>&1 | grep -E '^%(Warning|Error)' | head -20
echo "exit=${PIPESTATUS[0]}"
