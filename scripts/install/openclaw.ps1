# ---------------------------------------------
# nestwork x OpenClaw installer (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$OpenclawDir   = "$env:USERPROFILE\.openclaw\workspace"

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork installer"
}

$IdentityLines = @(& $PythonCmd (Join-Path $NestworkPath "scripts\install\_identity.py") openclaw)
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
Write-Host "-> openclaw ws    : $OpenclawDir"

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

# 2. Create OpenClaw workspace directory
New-Item -ItemType Directory -Force -Path $OpenclawDir | Out-Null

# 3. Inject nestwork bootstrap into AGENTS.md (marker-preserved).
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_bootstrap.py") `
    "$OpenclawDir\AGENTS.md" $NestworkPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "OpenClaw AGENTS.md bootstrap injection failed (exit $LASTEXITCODE)"
}

# 4. Copy SOUL.md (Windows symlinks require elevation; copy instead)
$SoulSrc = "$NestworkPath\SOUL.md"
$SoulDst = "$OpenclawDir\SOUL.md"
if (-not (Test-Path $SoulDst)) {
    Copy-Item $SoulSrc $SoulDst
    Write-Host "v copied SOUL.md"
} else {
    Write-Host "v SOUL.md already exists"
}

Write-Host ""
Write-Host "OK nestwork installed for OpenClaw"
Write-Host "   agent  : $NestHost/$AgentId"
Write-Host "   memory : $MemoryFile"
Write-Host "   ws     : $OpenclawDir"
