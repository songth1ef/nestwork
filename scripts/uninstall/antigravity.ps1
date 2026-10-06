# ---------------------------------------------
# nestwork x Antigravity uninstaller (Windows)
#
# Usage:
#   .\nestwork\scripts\uninstall\antigravity.ps1 [-PurgeIdentity]
# ---------------------------------------------

param(
    [switch]$PurgeIdentity
)

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$GeminiDir     = if ($env:ANTIGRAVITY_HOME) { $env:ANTIGRAVITY_HOME } elseif ($env:GEMINI_HOME) { $env:GEMINI_HOME } else { "$env:USERPROFILE\.gemini" }
$GeminiMd      = "$GeminiDir\GEMINI.md"
$HooksJson     = "$GeminiDir\config\hooks.json"

$HostFile = "$env:USERPROFILE\.nestwork_host"
$IdFile   = "$env:USERPROFILE\.nestwork_id_antigravity"

$NestHost = if (Test-Path $HostFile) { (Get-Content $HostFile -Raw).Trim() } else { "<unknown>" }
$AgentId  = if (Test-Path $IdFile)   { (Get-Content $IdFile -Raw).Trim() }   else { "<unknown>" }

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork uninstaller"
}

# 1. Remove bootstrap block from GEMINI.md
& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") $GeminiMd
if ($LASTEXITCODE -ne 0) {
    throw "unbootstrap failed (exit $LASTEXITCODE)"
}

# 2. Remove hooks from hooks.json
& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_antigravity_unhooks.py") $HooksJson
if ($LASTEXITCODE -ne 0) {
    throw "unhooks failed (exit $LASTEXITCODE)"
}

# 3. Optionally purge identity
if ($PurgeIdentity) {
    if (Test-Path $IdFile) {
        Remove-Item -Force $IdFile
        Write-Host "v removed $IdFile (next install gets a new agent id)"
    }
}

Write-Host ""
Write-Host "OK nestwork unbound from Antigravity"
Write-Host "   memory kept : $NestworkPath\agents\$NestHost\$AgentId\"
Write-Host "   to rebind   : .\nestwork\scripts\install\antigravity.ps1"
