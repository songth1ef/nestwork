# ---------------------------------------------
# nestwork x WorkBuddy AI uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from the WorkBuddy rules file.
# Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\workbuddy.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$WorkBuddyDir  = if ($env:WORKBUDDY_HOME) { $env:WORKBUDDY_HOME } else { "$env:USERPROFILE\.workbuddy-ai" }
$TargetMd      = if ($env:WORKBUDDY_NESTWORK_MD) { $env:WORKBUDDY_NESTWORK_MD } else { "$WorkBuddyDir\nestwork.md" }

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
if (Test-Path "$env:USERPROFILE\.nestwork_id_workbuddy") {
    $AgentId = (Get-Content "$env:USERPROFILE\.nestwork_id_workbuddy" -Raw).Trim()
}

Write-Host "-> nestwork path  : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") `
    $TargetMd
if ($LASTEXITCODE -ne 0) { throw "WorkBuddy rules bootstrap removal failed (exit $LASTEXITCODE)" }

if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.nestwork_id_workbuddy"
    Write-Host "v removed .nestwork_id_workbuddy (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK nestwork unbound from WorkBuddy AI"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $NestworkPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $NestworkPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\workbuddy.ps1"
