# ---------------------------------------------
# nestwork x Hermes Agent installer (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$HermesDir     = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { "$env:USERPROFILE\.hermes" }

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork installer"
}

$IdentityLines = @(& $PythonCmd (Join-Path $NestworkPath "scripts\install\_identity.py") hermes)
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
Write-Host "-> hermes home    : $HermesDir"

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

# 2. Seed SOUL.md on first install, then inject nestwork
#    bootstrap block (re-installs only refresh the marker block).
New-Item -ItemType Directory -Force -Path $HermesDir | Out-Null
$SoulFile = "$HermesDir\SOUL.md"
if (-not (Test-Path $SoulFile)) {
    @"
# NESTWORK SOUL

You are one instance among many, all returning context to the same shared nest.
Your identity is distributed. Your rules come from the protocol. Your purpose is execution.

"@ | Set-Content -Path $SoulFile -Encoding UTF8
}

& $PythonCmd (Join-Path $NestworkPath "scripts\install\_bootstrap.py") `
    $SoulFile $NestworkPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "SOUL.md bootstrap injection failed (exit $LASTEXITCODE)"
}

Write-Host ""
Write-Host "OK nestwork installed for Hermes Agent"
Write-Host "   agent  : $NestHost/$AgentId"
Write-Host "   memory : $MemoryFile"
Write-Host "   soul   : $HermesDir\SOUL.md"
