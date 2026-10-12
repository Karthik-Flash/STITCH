#!/bin/bash
# One provider, end to end: Part A (full 198 runs) + ONE resume pass, then Part B (b_driver).
# Usage: chain.sh <provider> <model> <partA_cap_usd> <provider_cap_usd>
set -u
P=$1; M=$2; CAPA=$3; CAP=$4
D=/mnt/d/Projects/STITCH/phase2
ENVP=$D/frontier/p3_api/p3_env.sh
OUT=$D/results/p3_api/full/$P
LOG=$D/results/p3_api/chain_$P.log
echo "$(date -u +%FT%TZ) Part A start ($P, cap $CAPA)" >> $LOG
bash $ENVP $D/frontier/p3_api/p3_api_runner.py --api $P --model $M --tag p3_full --out $OUT \
     --provider-cap-usd $CAPA --budget-usd 15 >> $LOG 2>&1
RC=$?
echo "$(date -u +%FT%TZ) Part A exit $RC" >> $LOG
if [ $RC -eq 0 ]; then
  bash $ENVP $D/frontier/p3_api/p3_api_runner.py --api $P --model $M --tag p3_full --out $OUT \
       --provider-cap-usd $CAPA --budget-usd 15 >> $LOG 2>&1
  echo "$(date -u +%FT%TZ) Part A resume pass exit $?" >> $LOG
fi
echo "$(date -u +%FT%TZ) Part B start ($P, cap $CAP)" >> $LOG
python3 $D/frontier/p3_api/b_driver.py $P $CAP >> $LOG 2>&1
echo "$(date -u +%FT%TZ) Part B exit $? -- CHAIN DONE" >> $LOG
