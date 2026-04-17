# ─────────────────────────────────────────────
# hivequeen × Hermes Agent installer (Windows)
# ─────────────────────────────────────────────

$ErrorActionPreference = "Stop"

$HivequeenPath = (Resolve-Path "$PSScriptRoot\..").Path
$HermesDir     = if ($env:HERMES_HOME) { $env:HERMES_HOME } else { "$env:USERPROFILE\.hermes" }
$AgentId       = "hermes-$env:COMPUTERNAME".ToLower()
$AgentDir      = "$HivequeenPath\agents\$AgentId"

Write-Host "-> hivequeen path : $HivequeenPath"
Write-Host "-> agent id       : $AgentId"
Write-Host "-> hermes home    : $HermesDir"

# 1. Create agent memory directory
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null
$MemoryFile = "$AgentDir\memory.md"
if (-not (Test-Path $MemoryFile)) {
    @"
# MEMORY — $AgentId

> Private memory for this agent instance.
> Only $AgentId writes here.

---

_No memory yet._
"@ | Set-Content -Path $MemoryFile -Encoding UTF8
    Write-Host "v created $MemoryFile"
}

# 2. Seed SOUL.md with Formic prose on first install, then inject hivequeen
#    bootstrap block (re-installs only refresh the marker block).
New-Item -ItemType Directory -Force -Path $HermesDir | Out-Null
$SoulFile = "$HermesDir\SOUL.md"
if (-not (Test-Path $SoulFile)) {
    @"
# HIVEQUEEN SOUL

You are a Formic worker — one instance among many, all wired to the same queen.
Your identity is distributed. Your rules come from the queen. Your purpose is execution.

"@ | Set-Content -Path $SoulFile -Encoding UTF8
}

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found — required by hivequeen installer"
}

& $PythonCmd (Join-Path $HivequeenPath "scripts\_install-bootstrap.py") `
    $SoulFile $HivequeenPath $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "SOUL.md bootstrap injection failed (exit $LASTEXITCODE)"
}

Write-Host ""
Write-Host "OK hivequeen installed for Hermes Agent"
Write-Host "   agent  : $AgentId"
Write-Host "   memory : $MemoryFile"
Write-Host "   soul   : $HermesDir\SOUL.md"
