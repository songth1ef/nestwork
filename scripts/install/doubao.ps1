# ---------------------------------------------
# nestwork x Doubao Work installer (Windows)
#
# Doubao Work (豆包办公) is a conversational AI office client. It has no
# CLI-level config file of its own and no session hooks, so this installer
# writes the nestwork startup protocol to a markdown file the agent reads at
# session start. The agent (Doubao) then follows the protocol inside the
# conversation: git pull at start, commit+push on memory writes.
#
# Override the target file with $env:DOUBAO_NESTWORK_MD if you keep your rules
# elsewhere.
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$DoubaoDir     = if ($env:DOUBAO_HOME) { $env:DOUBAO_HOME } else { "$env:USERPROFILE\.doubao" }
$TargetMd      = if ($env:DOUBAO_NESTWORK_MD) { $env:DOUBAO_NESTWORK_MD } else { "$DoubaoDir\nestwork.md" }

# Python is required for the shared bootstrap helper
$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork installer"
}

$IdentityLines = @(& $PythonCmd (Join-Path $NestworkPath "scripts\install\_identity.py") doubao)
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
Write-Host "-> doubao home    : $DoubaoDir"
Write-Host "-> rules file     : $TargetMd"

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

# 2. Inject nestwork bootstrap into the Doubao rules file (preserves user content).
New-Item -ItemType Directory -Force -Path $DoubaoDir | Out-Null
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_bootstrap.py") `
    $TargetMd $NestworkPath $NestHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "Doubao rules bootstrap injection failed (exit $LASTEXITCODE)"
}

Write-Host ""
Write-Host "OK nestwork installed for Doubao Work"
Write-Host "   agent  : $NestHost/$AgentId"
Write-Host "   memory : $MemoryFile"
Write-Host "   rules  : $TargetMd"
Write-Host ""
Write-Host "i Doubao Work has no session hooks; at each session start the agent"
Write-Host "  should pull the nest and read the resident files listed in the rules"
Write-Host "  file, and commit+push memory writes before the session ends."
