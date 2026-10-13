#!/bin/bash
# Set 4c is CLOSED (SET4_PREREG Amendment 5, 2026-10-12): stop rule on run 1, 0/18 runs, no further paid calls.
# Kept for traceability; refuses to run unless --reopen is given (which needs a new pre-registration amendment).
if [ "$1" != "--reopen" ]; then
    echo "set4c_launch.sh: Set 4c is CLOSED (SET4_PREREG.md Amendment 5). Refusing to run without --reopen." >&2
    exit 2
fi
# Set 4c (SET4_PREREG Amendment 4), run in WSL: bash set4c_launch.sh --reopen
# Order: (i) baseline rep1 x 3 modules; projection; (ii) baseline reps 2-3; (iii) sem_escalate_restart reps 1-3,
# freq_divbyfrac first. Any non-zero exit (cap, stop rule) ends the chain; rerunning resumes, never re-runs a done run.
F="$(cd "$(dirname "$0")" && pwd)"
R="$F/../results/set4_api"
COMMON="--backend gemini --model gemini-2.5-pro --tag set4c --max-tokens 10240 --thinking-budget 2048
        --ledger-dir $R/ledgers_4c --provider-cap-usd 7.5 --budget-usd 7.5 --run-worst-usd 0.7204 --planned 18"
step() { echo "$(date -u +%FT%TZ) STEP $1 start"; bash $F/run_set4.sh $COMMON "${@:2}"; rc=$?
         echo "$(date -u +%FT%TZ) STEP $1 exit $rc"; [ $rc -eq 0 ] || { echo "CHAIN STOPPED at step $1"; exit $rc; }; }
step i   --modules adder_pipe_64bit,alu,freq_divbyfrac --conditions baseline --n 1
python3 $F/set4c.py after1
step ii  --modules adder_pipe_64bit,alu,freq_divbyfrac --conditions baseline --n 3
step iii --modules freq_divbyfrac,adder_pipe_64bit,alu --conditions sem_escalate_restart --n 3
echo "CHAIN DONE"
