# LAPTOP (PowerShell), run from D:\Projects\STITCH :   powershell -ExecutionPolicy Bypass -File phase3\hpc\deploy_phase3.ps1
# Copies Phase 3 to /scratch/soumyaj/Phase3_HPC. Re-run after ANY local change (same discipline as Sets 1-3).
$H = "soumyaj@hpc.bits-hyderabad.ac.in"
$B = "/scratch/soumyaj/Phase3_HPC"
ssh $H "mkdir -p $B/logs $B/results $B/src/interpreter $B/ollama_models $B/bin"
# the whole phase3 folder (tasks, designs, runner, tests, hpc, evidence, docs); results/ is never shipped
scp -r phase3 "${H}:${B}/"
# interpreter: production v2 (unchanged) + the v3 layer
scp src\interpreter\stitch_interpreter.py src\interpreter\stitch_interpreter_v3.py src\interpreter\_v3_parsers.py "${H}:${B}/src/interpreter/"
# Windows checkouts may carry CRLF; sbatch rejects DOS line breaks and bash chokes on \r. Normalise on arrival.
ssh $H "find $B/phase3 $B/src -type f \( -name '*.slurm' -o -name '*.sh' -o -name '*.py' -o -name '*.v' -o -name '*.txt' -o -name '*.json' -o -name '*.md' -o -name '*.log' \) -exec sed -i 's/\r$//' {} +"
ssh $H "cd $B && grep -c \$'\r' phase3/hpc/*.slurm phase3/hpc/common_env.sh | grep -v ':0$' || echo 'LINE ENDINGS OK'"
Write-Host "Deployed. Next: HPC_PHASE3_COMMANDS.md Part C (gate)."
