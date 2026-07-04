# ---------------------------------------------
# nestwork x Hermes Agent uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from SOUL.md; the SOUL prose and
# anything outside the markers is preserved. Memory and identity files are
# never deleted.
#
# Usage:
#   .\uninstall\hermes.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$HermesDir     = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { "$env:USERPROFILE\.hermes" }

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
if (Test-Path "$env:USERPROFILE\.nestwork_id_hermes") {
    $AgentId = (Get-Content "$env:USERPROFILE\.nestwork_id_hermes" -Raw).Trim()
}

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") `
    "$HermesDir\SOUL.md"
if ($LASTEXITCODE -ne 0) { throw "SOUL.md bootstrap removal failed (exit $LASTEXITCODE)" }

if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.nestwork_id_hermes"
    Write-Host "v removed .nestwork_id_hermes (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK nestwork unbound from Hermes Agent"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $NestworkPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $NestworkPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\hermes.ps1"
