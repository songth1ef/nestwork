# ---------------------------------------------
# nestwork x Antigravity installer (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$GeminiDir     = if ($env:ANTIGRAVITY_HOME) { $env:ANTIGRAVITY_HOME } elseif ($env:GEMINI_HOME) { $env:GEMINI_HOME } else { "$env:USERPROFILE\.gemini" }
$GeminiMd      = "$GeminiDir\GEMINI.md"
$HooksJson     = "$GeminiDir\config\hooks.json"

# Python is required for the shared bootstrap helper
$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork installer"
}

$IdentityLines = @(& $PythonCmd (Join-Path $NestworkPath "scripts\install\_identity.py") antigravity)
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
Write-Host "-> gemini home    : $GeminiDir"

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

# 2. Inject nestwork bootstrap into ~/.gemini/GEMINI.md (preserves user content).
New-Item -ItemType Directory -Force -Path $GeminiDir | Out-Null
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_bootstrap.py") `
    $GeminiMd $NestworkPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "GEMINI.md bootstrap injection failed (exit $LASTEXITCODE)"
}

# 3. Register Antigravity hooks in ~/.gemini/config/hooks.json
New-Item -ItemType Directory -Force -Path "$GeminiDir\config" | Out-Null
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_antigravity_hooks.py") `
    $HooksJson $NestworkPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "Antigravity hook registration failed (exit $LASTEXITCODE)"
}

Write-Host ""
Write-Host "OK nestwork installed for Antigravity"
Write-Host "   agent  : $NestHost/$AgentId"
Write-Host "   memory : $MemoryFile"
Write-Host "   config : $GeminiMd"
Write-Host "   hooks  : $HooksJson"
