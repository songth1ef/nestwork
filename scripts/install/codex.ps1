# ---------------------------------------------
# nestwork x Codex installer (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$CodexDir = "$env:USERPROFILE\.codex"
$CodexAgents = "$CodexDir\AGENTS.md"
$CodexInstructions = "$CodexDir\instructions.md"
$CodexConfig = "$CodexDir\config.toml"
$CodexHooks = "$CodexDir\hooks.json"

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork installer"
}

$IdentityLines = @(& $PythonCmd (Join-Path $NestworkPath "scripts\install\_identity.py") codex)
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

# 2. Inject nestwork bootstrap (marker-preserved).
New-Item -ItemType Directory -Force -Path $CodexDir | Out-Null
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_bootstrap.py") `
    "$CodexAgents" $NestworkPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "Codex AGENTS.md bootstrap injection failed (exit $LASTEXITCODE)"
}
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_bootstrap.py") `
    "$CodexInstructions" $NestworkPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "Codex instructions.md compatibility bootstrap injection failed (exit $LASTEXITCODE)"
}

# 3. Register the Codex Stop hook used for optional local-history snapshots.
#    Current Codex reads config.toml + hooks.json; the old config.json
#    session.end_hook entry is ignored by recent releases.
$env:NESTWORK_CODEX_PLATFORM = "windows"
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_codex_hooks.py") `
    "$CodexConfig" "$CodexHooks" $NestworkPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "Codex hook registration failed (exit $LASTEXITCODE)"
}
Remove-Item Env:\NESTWORK_CODEX_PLATFORM

Write-Host ""
Write-Host "OK nestwork installed for Codex"
Write-Host "   agent: $NestHost/$AgentId"
Write-Host "   memory: $MemoryFile"
