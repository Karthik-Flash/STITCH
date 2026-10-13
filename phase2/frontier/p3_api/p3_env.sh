#!/bin/bash
# Environment for Part A (matched 0.69 suite, no bytecode under phase3/): p3_env.sh <script.py> [args...]
export STITCH_SET4_OSSCAD=${STITCH_SET4_OSSCAD:-$HOME/set4_osscad/20260917/oss-cad-suite}
export PATH="$STITCH_SET4_OSSCAD/bin:$PATH" PYTHONDONTWRITEBYTECODE=1
exec python3 "$@"
