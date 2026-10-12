#!/bin/bash
# Set 4 launcher: fixed environment (HPC-matched oss-cad-suite 20260917, openai lib, RTLLM),
# all arguments passed through to set4_runner.py.
export STITCH_SET4_OSSCAD=/home/flash/set4_osscad/20260917/oss-cad-suite
export PYTHONPATH=/mnt/c/Users/karth/stitch_set4_pylib
export RTLLM_ROOT=/mnt/d/Projects/RTLLM
exec python3 /mnt/d/Projects/STITCH/phase2/frontier/set4_runner.py "$@"
