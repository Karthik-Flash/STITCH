#!/bin/bash
# Install one dated oss-cad-suite release into ~/set4_osscad/<date>/ (no sudo; system tools untouched).
# Usage: install_osscad.sh 20260917
set -e
D="$1"; Y="${D:0:4}-${D:4:2}-${D:6:2}"
DEST="$HOME/set4_osscad/$D"
mkdir -p "$DEST"
TGZ="$HOME/set4_osscad/oss-cad-suite-linux-x64-$D.tgz"
[ -f "$TGZ" ] || curl -sSL --retry 5 --retry-all-errors -C - -o "$TGZ" "https://github.com/YosysHQ/oss-cad-suite-build/releases/download/$Y/oss-cad-suite-linux-x64-$D.tgz"
[ -x "$DEST/oss-cad-suite/bin/yosys" ] || tar xzf "$TGZ" -C "$DEST"
B="$DEST/oss-cad-suite/bin"
echo "yosys: $($B/yosys -V)"
echo "verilator: $($B/verilator --version)"
echo "iverilog: $($B/iverilog -V 2>&1 | head -1)"
echo "STITCH_SET4_OSSCAD=$DEST/oss-cad-suite"
