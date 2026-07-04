# ---------------------------------------------
# nestwork x Codex uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from AGENTS.md / instructions.md
# and the nestwork Stop hook from hooks.json. `hooksPath` in config.toml is
# left alone. Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\codex.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$CodexDir      = "$env:USERPROFILE\.codex"

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
if (Test-Path "$env:USERPROFILE\.nestwork_id_codex") {
    $AgentId = (Get-Content "$env:USERPROFILE\.nestwork_id_codex" -Raw).Trim()
}

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

# 1. Remove the bootstrap block from Codex startup files (user content preserved)
& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") `
    "$CodexDir\AGENTS.md"
if ($LASTEXITCODE -ne 0) { throw "AGENTS.md bootstrap removal failed (exit $LASTEXITCODE)" }
& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") `
    "$CodexDir\instructions.md"
if ($LASTEXITCODE -ne 0) { throw "instructions.md bootstrap removal failed (exit $LASTEXITCODE)" }

# 2. Remove the nestwork Stop hook from hooks.json (user hooks preserved)
& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_codex_unhooks.py") `
    "$CodexDir\hooks.json"
if ($LASTEXITCODE -ne 0) { throw "Codex hook removal failed (exit $LASTEXITCODE)" }

# 3. Optionally purge this tool's identity file
if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.nestwork_id_codex"
    Write-Host "v removed .nestwork_id_codex (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK nestwork unbound from Codex"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $NestworkPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $NestworkPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\codex.ps1"
