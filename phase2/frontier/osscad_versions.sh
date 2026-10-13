#!/bin/bash
# Extract (if needed) and print versions of a Set 4 oss-cad-suite: osscad_versions.sh 20260917
WIN_HOME="${WIN_HOME:-$(wslpath "$(cmd.exe /C 'echo %USERPROFILE%' 2>/dev/null | tr -d '\r')")}"
D="$1"; DEST="$HOME/set4_osscad/$D"; TGZ="$WIN_HOME/set4_osscad/oss-cad-suite-linux-x64-$D.tgz"
mkdir -p "$DEST"
[ -x "$DEST/oss-cad-suite/bin/yosys" ] || tar xzf "$TGZ" -C "$DEST"
B="$DEST/oss-cad-suite/bin"
echo "yosys: $($B/yosys -V)"
echo "verilator: $($B/verilator --version)"
echo "iverilog: $($B/iverilog -V 2>&1 | head -1)"
