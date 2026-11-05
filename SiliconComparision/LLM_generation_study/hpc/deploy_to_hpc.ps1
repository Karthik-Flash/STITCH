# LAPTOP (PowerShell), from the repository root D:\Projects\STITCH :
#   powershell -ExecutionPolicy Bypass -File SiliconComparision\LLM_generation_study\hpc\deploy_to_hpc.ps1 -DryRun
#   powershell -ExecutionPolicy Bypass -File SiliconComparision\LLM_generation_study\hpc\deploy_to_hpc.ps1
# Ships the COMMITTED state (git archive of HEAD, LF line endings) to /scratch/soumyaj/STITCH_GEN:
#   phase3/runner, the three src/interpreter modules, and this study folder without original_2x2_mesh_zedboard/
#   (except routing_algo_mesh.v, which scripts/check_golden.py proves equal to golden route_compute), golden/figures/,
#   vivado/ and the result folders (hpc_logs/, runs/, outputs/, results/).
# Results on the cluster are never shipped, overwritten or deleted: the tar holds no result path (checked below), tar -xf
# only adds or replaces the files it holds, and the remote result-file count must not drop.
# Asks for the cluster password twice (scp, then ssh). The ssh step checks the tar's sha256 before unpacking it.
# -DryRun builds and checks the tar and sends nothing.
param([switch]$DryRun)
$ErrorActionPreference = "Stop"
$H = "soumyaj@hpc.bits-hyderabad.ac.in"
$B = "/scratch/soumyaj/STITCH_GEN"
$S = "SiliconComparision/LLM_generation_study"
$T = Join-Path $env:TEMP "llmgen_deploy.tar"
$Orig = "$S/original_2x2_mesh_zedboard/project_4on2014edition/project_4on2014edition.srcs/sources_1/imports/untitled folder"
$Interp = "src/interpreter/stitch_interpreter.py", "src/interpreter/stitch_interpreter_v3.py", "src/interpreter/_v3_parsers.py"
$Results = "hpc_logs", "runs", "outputs", "results"

$dirty = git status --porcelain -- phase3/runner $Interp $S
if ($dirty) { throw "uncommitted changes, commit first (the deploy ships HEAD):`n$($dirty -join "`n")" }
$commit = (git rev-parse HEAD).Trim()
Write-Host "== deploying commit $(git log -1 --oneline)"

$exclude = @("original_2x2_mesh_zedboard", "golden/figures", "vivado") + $Results | ForEach-Object { ":(exclude)$S/$_" }
if (Test-Path $T) { Remove-Item $T }
git -c core.autocrlf=false archive --format=tar -o $T "--add-virtual-file=$S/DEPLOYED_COMMIT.txt:$commit" `
    "--prefix=$Orig/" "--add-file=$Orig/routing_algo_mesh.v" "--prefix=" HEAD -- phase3/runner $Interp $S $exclude
if ($LASTEXITCODE -ne 0) { throw "git archive failed" }

$entries = tar -tf $T
$bad = $entries | Select-String -Pattern ("^$S/(" + ($Results -join "|") + ")/.")
if ($bad) { throw "the tar holds result files, refusing to deploy: $($bad -join ', ')" }
$hash = (Get-FileHash -Algorithm SHA256 $T).Hash.ToLower()
Write-Host "== $($entries.Count) entries, $([math]::Round((Get-Item $T).Length / 1MB, 2)) MB, no result files, sha256 $hash"
if ($DryRun) {
    $entries | Where-Object { $_ -match "^$S/[^/]+/?$" } | ForEach-Object { "   $_" }
    Write-Host "DryRun: $T built and checked; nothing sent."
    exit 0
}

$R = "$B/$S"
$count = "find $R/hpc_logs $R/runs $R/outputs $R/results -type f 2>/dev/null | wc -l"
scp $T "${H}:${B}/llmgen_deploy.tar"
if ($LASTEXITCODE -ne 0) { throw "scp failed" }
$remote = "set -e; cd $B; echo '$hash  llmgen_deploy.tar' | sha256sum -c -; n0=`$($count); " +
          "tar -xf llmgen_deploy.tar; rm llmgen_deploy.tar; mkdir -p $R/hpc_logs; n1=`$($count); " +
          "echo result files on the cluster: before `$n0, after `$n1; [ `$n1 -ge `$n0 ]; " +
          "echo deployed commit: `$(cat $R/DEPLOYED_COMMIT.txt)"
ssh $H $remote
if ($LASTEXITCODE -ne 0) { throw "remote step failed: hash mismatch, unpack error or result count dropped (output above)" }
Remove-Item $T
Write-Host "Deployed $commit to ${H}:${R}. Next: HPC_RUN.md, step 2."
