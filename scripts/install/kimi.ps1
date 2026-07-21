# ---------------------------------------------
# nestwork x Kimi Code installer (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$KimiCodeHome = if ($env:KIMI_CODE_HOME) { $env:KIMI_CODE_HOME } else { "$env:USERPROFILE\.kimi-code" }
$KimiConfig   = "$KimiCodeHome\config.toml"

# Python is required for the shared installer helpers
$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork installer"
}

# Resolve (host, agent-id) via shared identity helper. Kimi uses a random
# suffix so multiple installs on one machine stay distinct.
$IdentityLines = & $PythonCmd (Join-Path $NestworkPath "scripts\install\_identity.py") kimi --with-suffix
if ($LASTEXITCODE -ne 0) { throw "identity resolver failed (exit $LASTEXITCODE)" }
$NestHost = $IdentityLines[0].Trim()
$AgentId  = $IdentityLines[1].Trim()
if (-not $NestHost -or -not $AgentId) {
    throw "identity resolver returned host='$NestHost' agent='$AgentId' (expected two non-empty lines)"
}
$AgentDir = "$NestworkPath\agents\$NestHost\$AgentId"

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"
Write-Host "-> Kimi Code home : $KimiCodeHome"

# 1. Create this agent's memory directory
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

# 2. Inject nestwork bootstrap into Kimi Code's startup reference file.
#    Kimi Code does not (yet) support SessionStart additionalContext, so the
#    bootstrap instructs the agent to Read the priority-chain files itself.
New-Item -ItemType Directory -Force -Path $KimiCodeHome | Out-Null
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_bootstrap.py") `
    "$KimiCodeHome\NESTWORK.md" $NestworkPath $NestHost $AgentId --tool=kimi
if ($LASTEXITCODE -ne 0) {
    throw "NESTWORK.md bootstrap injection failed (exit $LASTEXITCODE)"
}

# 3. Register hooks in ~/.kimi-code/config.toml via shared Python helper.
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_kimi_hooks.py") `
    $KimiConfig $NestworkPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "hook installation failed (exit $LASTEXITCODE)"
}

Write-Host ""
Write-Host "OK nestwork installed for Kimi Code"
Write-Host "   agent : $NestHost/$AgentId"
Write-Host "   memory: $MemoryFile"
Write-Host "   config: $KimiConfig"
Write-Host ""
Write-Host "Run '/reload' in Kimi Code (or start a new session) for hooks to take effect."
