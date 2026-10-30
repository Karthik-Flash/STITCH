# LAPTOP (PowerShell), run from the repository root D:\Projects\STITCH :
#   powershell -ExecutionPolicy Bypass -File SiliconComparision\llm_oneshot_vs_stitch\pipeline\deploy_gen.ps1
# Ships ONLY what the generation job needs to /scratch/<user>/STITCH_GEN, with LF line endings:
#   phase3/runner (no __pycache__), the three src/interpreter modules, and this study folder without runs/, outputs/,
#   prompts/ and hpc_logs/ (the scripts create those folders on the cluster).
# Results on the cluster are never deleted or overwritten: the tar holds no file under runs/, outputs/ or prompts/
# (checked below), tar -xf only adds or replaces the files it holds, and the remote result counts are compared before
# and after the untar (the script stops if one drops).
# -DryRun builds and lists the tar and prints the hashes, without ssh/scp.
param([switch]$DryRun)
$ErrorActionPreference = "Stop"
$H = "soumyaj@hpc.bits-hyderabad.ac.in"
$B = "/scratch/soumyaj/STITCH_GEN"
$Stage = Join-Path $env:TEMP "stitch_gen_stage"
$T = Join-Path $env:TEMP "stitch_gen_deploy.tar"
$Study = "SiliconComparision\llm_oneshot_vs_stitch"

if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
New-Item -ItemType Directory -Force "$Stage\phase3", "$Stage\src\interpreter", "$Stage\SiliconComparision" | Out-Null
Copy-Item -Recurse "phase3\runner" "$Stage\phase3\runner"
foreach ($f in "stitch_interpreter.py", "stitch_interpreter_v3.py", "_v3_parsers.py") {
    Copy-Item "src\interpreter\$f" "$Stage\src\interpreter\$f"
}
Copy-Item -Recurse $Study "$Stage\$Study"
# The cluster copy has no .git: record the deployed commit for runs/RUN_MANIFEST.json (preflight.py).
$commit = (git rev-parse HEAD).Trim()
if (git status --porcelain -- $Study phase3/runner src/interpreter) { $commit += " (dirty)" }
Set-Content -NoNewline -Encoding ascii "$Stage\$Study\DEPLOYED_COMMIT.txt" $commit
Write-Host "== deployed commit: $commit"
Get-ChildItem $Stage -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
foreach ($d in "runs", "outputs", "prompts", "hpc_logs") {
    if (Test-Path "$Stage\$Study\$d") { Remove-Item -Recurse -Force "$Stage\$Study\$d" }
}

# CRLF -> LF in every text file (Windows checkouts may carry CRLF; bash and sbatch reject it).
$utf8 = New-Object System.Text.UTF8Encoding $false
Get-ChildItem $Stage -Recurse -File -Include *.py, *.sh, *.slurm, *.v, *.md, *.txt, *.json, *.csv, *.tmpl, *.ps1 | ForEach-Object {
    $text = [System.IO.File]::ReadAllText($_.FullName)
    if ($text.Contains("`r")) { [System.IO.File]::WriteAllText($_.FullName, $text.Replace("`r`n", "`n"), $utf8) }
}
$crlf = Get-ChildItem $Stage -Recurse -File -Include *.py, *.sh, *.slurm, *.v | Where-Object { [System.IO.File]::ReadAllText($_.FullName).Contains("`r") }
if ($crlf) { throw "CRLF left in: $($crlf.FullName -join ', ')" }

Write-Host "== local hashes (LF, staged)"
$key = "phase3\runner\stitch_runner_p3.py", "phase3\runner\p3_eval.py", "phase3\runner\system_prompt.txt",
       "src\interpreter\stitch_interpreter.py", "src\interpreter\stitch_interpreter_v3.py", "src\interpreter\_v3_parsers.py",
       "$Study\pipeline\p3_bridge.py", "$Study\pipeline\run_arms.py", "$Study\pipeline\oneshot_gen.py", "$Study\pipeline\preflight.py", "$Study\pipeline\gen_job.slurm",
       "$Study\modules.csv"
foreach ($k in $key) { "{0}  {1}" -f (Get-FileHash -Algorithm SHA256 "$Stage\$k").Hash.ToLower(), ($k -replace '\\', '/') }

if (Test-Path $T) { Remove-Item $T }
tar -cf $T -C $Stage phase3 src SiliconComparision
if ($LASTEXITCODE -ne 0) { throw "tar failed" }
$results = tar -tf $T | Select-String -Pattern "llm_oneshot_vs_stitch/(runs|outputs|prompts|hpc_logs)/."
if ($results) { throw "the tar holds result files, refusing to deploy: $($results -join ', ')" }
Write-Host "== tar holds no file under runs/, outputs/, prompts/, hpc_logs/"
if ($DryRun) {
    $n = (tar -tf $T | Measure-Object -Line).Lines
    Write-Host "DryRun: $T holds $n entries ($([math]::Round((Get-Item $T).Length / 1MB, 2)) MB); nothing sent."
    Remove-Item -Recurse -Force $Stage
    exit 0
}
$S = $Study -replace '\\', '/'
$count = "cd $B && echo `$(ls $S/runs/oneshot/*/record.json 2>/dev/null | wc -l) `$(find $S/runs/arms/results -name metrics.json 2>/dev/null | wc -l) `$(ls $S/outputs/oneshot/*.v 2>/dev/null | wc -l)"
ssh $H "mkdir -p $B/logs"
$before = (ssh $H $count).Trim()
Write-Host "== remote results before (one-shot records, arm metrics.json, one-shot outputs): $before"
scp $T "${H}:${B}/stitch_gen_deploy.tar"
ssh $H "cd $B && tar -xf stitch_gen_deploy.tar && rm stitch_gen_deploy.tar"
$after = (ssh $H $count).Trim()
Write-Host "== remote results after: $after"
# PowerShell names are case-insensitive: never reuse $B/$H/$S/$T for locals.
$nBefore = $before -split ' '; $nAfter = $after -split ' '
for ($i = 0; $i -lt 3; $i++) { if ([int]$nAfter[$i] -lt [int]$nBefore[$i]) { throw "remote result count dropped ($before -> $after)" } }
Remove-Item $T
Remove-Item -Recurse -Force $Stage
Write-Host "== remote hashes (must equal the local ones above)"
$remote = ($key | ForEach-Object { $_ -replace '\\', '/' }) -join " "
ssh $H "cd $B && sha256sum $remote && grep -lr `$'\r' phase3/runner src $($Study -replace '\\', '/')/pipeline | head -3 || true"
Write-Host "Deployed to ${H}:${B}. Next: HPC_RUN.md step 3."
