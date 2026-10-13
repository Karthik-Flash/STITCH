# LAPTOP (PowerShell), run from D:\Projects\STITCH :   powershell -ExecutionPolicy Bypass -File phase3\hpc\deploy_phase3.ps1
# Copies Phase 3 to /scratch/soumyaj/Phase3_HPC. Re-run after ANY local change (same discipline as Sets 1-3).
# One tar, so phase3\results (the local run trees, gigabytes) is never shipped; results on the HPC live in $B/results.
$H = "soumyaj@hpc.bits-hyderabad.ac.in"
$B = "/scratch/soumyaj/Phase3_HPC"
$T = Join-Path $env:TEMP "phase3_deploy.tar"
tar -cf $T --exclude=phase3/results --exclude=__pycache__ phase3 src/interpreter/stitch_interpreter.py src/interpreter/stitch_interpreter_v3.py src/interpreter/_v3_parsers.py
if ($LASTEXITCODE -ne 0) { throw "tar failed" }
ssh $H "mkdir -p $B/logs $B/results $B/src/interpreter $B/ollama_models $B/bin"
scp $T "${H}:${B}/phase3_deploy.tar"
ssh $H "cd $B && tar -xf phase3_deploy.tar && rm phase3_deploy.tar"
Remove-Item $T
# Windows checkouts may carry CRLF; sbatch rejects DOS line breaks and bash chokes on \r. Normalise on arrival.
ssh $H "find $B/phase3 $B/src -type f \( -name '*.slurm' -o -name '*.sh' -o -name '*.py' -o -name '*.v' -o -name '*.txt' -o -name '*.json' -o -name '*.md' -o -name '*.log' \) -exec sed -i 's/\r$//' {} +"
ssh $H "cd $B && grep -c \$'\r' phase3/hpc/*.slurm phase3/hpc/common_env.sh | grep -v ':0$' || echo 'LINE ENDINGS OK'"
# After the CRLF strip, plain sha256sum equals the LF-normalised hashes in phase3/evidence/FREEZE_FINAL.md.
ssh $H "cd $B && sha256sum src/interpreter/*.py phase3/runner/stitch_runner_p3.py phase3/runner/p3_eval.py phase3/runner/system_prompt.txt"
Write-Host "Deployed. Compare the hashes above with phase3/evidence/FREEZE_FINAL.md, then run the gate."
