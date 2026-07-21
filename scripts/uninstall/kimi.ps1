# ---------------------------------------------
# nestwork x Kimi Code uninstaller (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$KimiCodeHome = if ($env:KIMI_CODE_HOME) { $env:KIMI_CODE_HOME } else { "$env:USERPROFILE\.kimi-code" }

# Python is required for the shared uninstaller helpers
$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork uninstaller"
}

$HostId = ""
$AgentId = ""
$HostFile = "$env:USERPROFILE\.nestwork_host"
$IdFile   = "$env:USERPROFILE\.nestwork_id_kimi"
if (Test-Path $HostFile) { $HostId = (Get-Content $HostFile -Raw).Trim() }
if (Test-Path $IdFile)   { $AgentId = (Get-Content $IdFile -Raw).Trim() }

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $(if ($HostId) { $HostId } else { '<unknown>' })"
Write-Host "-> agent id       : $(if ($AgentId) { $AgentId } else { '<unknown>' })"

# 1. Remove the bootstrap block from NESTWORK.md (user content preserved)
& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") "$KimiCodeHome\NESTWORK.md"

# 2. Remove the nestwork hook block from config.toml (user hooks preserved)
& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_kimi_unhooks.py") "$KimiCodeHome\config.toml"

# 3. Optionally purge this tool's identity file
if ($args -contains "--purge-identity") {
    Remove-Item -Force -Path $IdFile -ErrorAction SilentlyContinue
    Write-Host "[ok] removed $IdFile (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK nestwork unbound from Kimi Code"
if ($HostId -and $AgentId) {
    Write-Host "   memory kept : $NestworkPath\agents\$HostId\$AgentId\"
} else {
    Write-Host "   memory kept : $NestworkPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : bash $NestworkPath\scripts\install\kimi.sh"
