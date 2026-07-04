# ---------------------------------------------
# nestwork x Claude Code uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from CLAUDE.md and the nestwork
# hooks from settings.json. Memory (agents/<host>/<id>/) and identity files
# are never deleted; re-running the installer restores the same identity.
#
# Usage:
#   .\uninstall\claude.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$ClaudeDir     = "$env:USERPROFILE\.claude"
$Settings      = "$ClaudeDir\settings.json"

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
if (Test-Path "$env:USERPROFILE\.nestwork_id_claude") {
    $AgentId = (Get-Content "$env:USERPROFILE\.nestwork_id_claude" -Raw).Trim()
}

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

# 1. Remove the bootstrap block from global CLAUDE.md (user content preserved)
& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") `
    "$ClaudeDir\CLAUDE.md"
if ($LASTEXITCODE -ne 0) { throw "CLAUDE.md bootstrap removal failed (exit $LASTEXITCODE)" }

# 2. Remove nestwork hooks from settings.json (user hooks preserved)
& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unhooks.py") `
    $Settings $NestHost $AgentId
if ($LASTEXITCODE -ne 0) { throw "hook removal failed (exit $LASTEXITCODE)" }

# 3. Optionally purge this tool's identity file
if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.nestwork_id_claude"
    Write-Host "v removed .nestwork_id_claude (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK nestwork unbound from Claude Code"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $NestworkPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $NestworkPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\claude.ps1"
