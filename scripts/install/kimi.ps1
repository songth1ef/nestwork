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

# 2. Inject nestwork bootstrap into Kimi Code's user-level instruction file.
#    Kimi Code reads exactly two instruction files: $KIMI_CODE_HOME\AGENTS.md
#    (user level, default ~\.kimi-code\AGENTS.md) and <project>\AGENTS.md.
#    No other filename is loaded, so the bootstrap has to live there.
#    Kimi Code also does not support SessionStart additionalContext -- a hook may
#    only return a permission decision -- so the bootstrap instructs the agent to
#    Read the priority-chain files itself.
New-Item -ItemType Directory -Force -Path $KimiCodeHome | Out-Null
& $PythonCmd (Join-Path $NestworkPath "scripts\install\_bootstrap.py") `
    "$KimiCodeHome\AGENTS.md" $NestworkPath $NestHost $AgentId --tool=kimi
if ($LASTEXITCODE -ne 0) {
    throw "AGENTS.md bootstrap injection failed (exit $LASTEXITCODE)"
}

# 2b. Migrate installs made before 2026-08-02: they wrote the bootstrap to
#     NESTWORK.md, a filename Kimi Code never reads (the install looked fine,
#     hooks ran, and the agent still started with zero nestwork context). Drop
#     the stale block so two copies cannot drift; content the user added outside
#     the markers is preserved, and the file is removed only if nothing is left.
$LegacyBootstrap = "$KimiCodeHome\NESTWORK.md"
if (Test-Path $LegacyBootstrap) {
    & $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") $LegacyBootstrap
    if ($LASTEXITCODE -ne 0) {
        throw "legacy NESTWORK.md cleanup failed (exit $LASTEXITCODE)"
    }
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
