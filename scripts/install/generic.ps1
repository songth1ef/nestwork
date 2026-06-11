# -----------------------------------------------------------------------------
# nestwork x generic markdown-config installer (Windows)
#
# See install-generic.sh for full docs.
#
# Usage:
#   .\install-generic.ps1 <tool-prefix> <config-path>
#
# Examples:
#   .\install-generic.ps1 qwen  "$env:USERPROFILE\.qwen\QWEN.md"
#   .\install-generic.ps1 trae  "$env:USERPROFILE\.trae\system.md"
# -----------------------------------------------------------------------------

param(
    [Parameter(Mandatory=$true, Position=0)] [string] $Prefix,
    [Parameter(Mandatory=$true, Position=1)] [string] $ConfigPath
)

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$ConfigPath    = [Environment]::ExpandEnvironmentVariables($ConfigPath)

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork installer"
}

$IdentityLines = @(& $PythonCmd (Join-Path $NestworkPath "scripts\install\_identity.py") $Prefix)
if ($LASTEXITCODE -ne 0) { throw "identity resolver failed (exit $LASTEXITCODE)" }
if ($IdentityLines.Count -lt 2) {
    throw "identity resolver returned $($IdentityLines.Count) line(s); expected host + agent-id"
}
$NestHost = $IdentityLines[0].Trim()
$AgentId  = $IdentityLines[1].Trim()
if (-not $NestHost -or -not $AgentId) {
    throw "identity resolver returned an empty host or agent-id"
}
$AgentDir = "$NestworkPath\agents\$NestHost\$AgentId"

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"
Write-Host "-> config target  : $ConfigPath"

# 1. Create agent memory directory
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null
$MemoryFile = "$AgentDir\memory.md"
if (-not (Test-Path $MemoryFile)) {
    @"
# MEMORY -- $NestHost/$AgentId

> Private memory for this agent instance.
> Only $NestHost/$AgentId writes here.

---

_No memory yet._
"@ | Set-Content -Path $MemoryFile -Encoding UTF8
    Write-Host "v created $MemoryFile"
}

# 2. Inject bootstrap into config file
$ConfigDir = Split-Path -Parent $ConfigPath
if ($ConfigDir) {
    New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
}
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_bootstrap.py") `
    $ConfigPath $NestworkPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "bootstrap injection failed (exit $LASTEXITCODE)"
}

Write-Host ""
Write-Host "OK nestwork installed for $Prefix"
Write-Host "   agent  : $NestHost/$AgentId"
Write-Host "   memory : $MemoryFile"
Write-Host "   config : $ConfigPath"
