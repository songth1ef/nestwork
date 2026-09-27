# ---------------------------------------------
# nestwork x Doubao Work uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from the Doubao rules file.
# Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\doubao.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$DoubaoDir     = if ($env:DOUBAO_HOME) { $env:DOUBAO_HOME } else { "$env:USERPROFILE\.doubao" }
$TargetMd      = if ($env:DOUBAO_NESTWORK_MD) { $env:DOUBAO_NESTWORK_MD } else { "$DoubaoDir\nestwork.md" }

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork uninstaller"
}

$NestHost = ""
$AgentId  = ""
if (Test-Path "$env:USERPROFILE\.nestwork_host") {
    $NestHost = (Get-Content "$env:USERPROFILE\.nestwork_host" -Raw).Trim()
}
if (Test-Path "$env:USERPROFILE\.nestwork_id_doubao") {
    $AgentId = (Get-Content "$env:USERPROFILE\.nestwork_id_doubao" -Raw).Trim()
}

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") `
    $TargetMd
if ($LASTEXITCODE -ne 0) { throw "Doubao rules bootstrap removal failed (exit $LASTEXITCODE)" }

if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.nestwork_id_doubao"
    Write-Host "v removed .nestwork_id_doubao (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK nestwork unbound from Doubao Work"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $NestworkPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $NestworkPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\doubao.ps1"
