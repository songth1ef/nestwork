# ---------------------------------------------
# nestwork x Gemini CLI uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from GEMINI.md.
# Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\gemini.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$GeminiDir     = if ($env:GEMINI_HOME) { $env:GEMINI_HOME } else { "$env:USERPROFILE\.gemini" }

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
if (Test-Path "$env:USERPROFILE\.nestwork_id_gemini") {
    $AgentId = (Get-Content "$env:USERPROFILE\.nestwork_id_gemini" -Raw).Trim()
}

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") `
    "$GeminiDir\GEMINI.md"
if ($LASTEXITCODE -ne 0) { throw "GEMINI.md bootstrap removal failed (exit $LASTEXITCODE)" }

if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.nestwork_id_gemini"
    Write-Host "v removed .nestwork_id_gemini (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK nestwork unbound from Gemini CLI"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $NestworkPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $NestworkPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\gemini.ps1"
