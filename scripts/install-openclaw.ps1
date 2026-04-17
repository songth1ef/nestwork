# ─────────────────────────────────────────────
# hivequeen × OpenClaw installer (Windows)
# ─────────────────────────────────────────────

$ErrorActionPreference = "Stop"

$HivequeenPath = (Resolve-Path "$PSScriptRoot\..").Path
$OpenclawDir   = "$env:USERPROFILE\.openclaw\workspace"
$AgentId       = "openclaw-$env:COMPUTERNAME".ToLower()
$AgentDir      = "$HivequeenPath\agents\$AgentId"

Write-Host "-> hivequeen path : $HivequeenPath"
Write-Host "-> agent id       : $AgentId"
Write-Host "-> openclaw ws    : $OpenclawDir"

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

# 2. Create OpenClaw workspace directory
New-Item -ItemType Directory -Force -Path $OpenclawDir | Out-Null

# 3. Inject hivequeen bootstrap into AGENTS.md (marker-preserved).
$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found — required by hivequeen installer"
}

& $PythonCmd (Join-Path $HivequeenPath "scripts\_install-bootstrap.py") `
    "$OpenclawDir\AGENTS.md" $HivequeenPath $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "OpenClaw AGENTS.md bootstrap injection failed (exit $LASTEXITCODE)"
}

# 4. Copy SOUL.md (Windows symlinks require elevation; copy instead)
$SoulSrc = "$HivequeenPath\SOUL.md"
$SoulDst = "$OpenclawDir\SOUL.md"
if (-not (Test-Path $SoulDst)) {
    Copy-Item $SoulSrc $SoulDst
    Write-Host "v copied SOUL.md"
} else {
    Write-Host "v SOUL.md already exists"
}

Write-Host ""
Write-Host "OK hivequeen installed for OpenClaw"
Write-Host "   agent  : $AgentId"
Write-Host "   memory : $MemoryFile"
Write-Host "   ws     : $OpenclawDir"
