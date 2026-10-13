#!/bin/bash
# Set 4 launcher: fixed environment (HPC-matched oss-cad-suite 20260917, openai lib, RTLLM),
# all arguments passed through to set4_runner.py.
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WIN_HOME="${WIN_HOME:-$(wslpath "$(cmd.exe /C 'echo %USERPROFILE%' 2>/dev/null | tr -d '\r')")}"
export STITCH_SET4_OSSCAD=${STITCH_SET4_OSSCAD:-$HOME/set4_osscad/20260917/oss-cad-suite}
export PYTHONPATH=${PYTHONPATH:-$WIN_HOME/stitch_set4_pylib}
export RTLLM_ROOT=${RTLLM_ROOT:-$(cd "$REPO_ROOT/.." && pwd)/RTLLM}
exec python3 "$REPO_ROOT/phase2/frontier/set4_runner.py" "$@"
