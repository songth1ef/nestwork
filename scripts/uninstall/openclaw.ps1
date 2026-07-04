# ---------------------------------------------
# nestwork x OpenClaw uninstaller (Windows)
#
# Unbinds only: removes the bootstrap block from the workspace AGENTS.md and
# the SOUL.md symlink (only if it still points into this nestwork checkout).
# Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\openclaw.ps1 [-PurgeIdentity]
# ---------------------------------------------

param([switch]$PurgeIdentity)

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$OpenClawDir   = "$env:USERPROFILE\.openclaw\workspace"

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
if (Test-Path "$env:USERPROFILE\.nestwork_id_openclaw") {
    $AgentId = (Get-Content "$env:USERPROFILE\.nestwork_id_openclaw" -Raw).Trim()
}

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

# 1. Remove the bootstrap block from workspace AGENTS.md
& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") `
    "$OpenClawDir\AGENTS.md"
if ($LASTEXITCODE -ne 0) { throw "AGENTS.md bootstrap removal failed (exit $LASTEXITCODE)" }

# 2. Remove the SOUL.md link if it was ours (symlink pointing into this checkout)
$SoulPath = "$OpenClawDir\SOUL.md"
if (Test-Path $SoulPath) {
    $Item = Get-Item $SoulPath -Force
    if ($Item.LinkType -and $Item.Target -eq (Join-Path $NestworkPath "SOUL.md")) {
        Remove-Item -Force $SoulPath
        Write-Host "v removed SOUL.md symlink"
    }
}

# 3. Optionally purge this tool's identity file
if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.nestwork_id_openclaw"
    Write-Host "v removed .nestwork_id_openclaw (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK nestwork unbound from OpenClaw"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $NestworkPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $NestworkPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\openclaw.ps1"
