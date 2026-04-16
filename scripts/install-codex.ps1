# ─────────────────────────────────────────────
# hivequeen x Codex installer (Windows)
# ─────────────────────────────────────────────

$ErrorActionPreference = "Stop"

$HivequeenPath = (Resolve-Path "$PSScriptRoot\..").Path
$CodexDir = "$env:USERPROFILE\.codex"
$Settings = "$CodexDir\config.json"
$AgentId = "codex-$env:COMPUTERNAME".ToLower()
$AgentDir = "$HivequeenPath\agents\$AgentId"

Write-Host "-> hivequeen path : $HivequeenPath"
Write-Host "-> agent id       : $AgentId"

# 1. Create this agent's memory directory
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

# 2. Write Codex instructions
New-Item -ItemType Directory -Force -Path $CodexDir | Out-Null
@"
# Hivequeen Bootstrap

Before starting, run:

``````powershell
git -C "$HivequeenPath" pull --rebase
``````

Load context in order:

1. ``$HivequeenPath\queen\agent-rules.md``
2. ``$HivequeenPath\queen\strategy.md``
3. ``$HivequeenPath\shared\memory.md``
4. ``$HivequeenPath\agents\$AgentId\memory.md``
5. Relevant ``$HivequeenPath\projects\*.md``

Write protocol: only write to ``$HivequeenPath\agents\$AgentId\``

Full protocol: ``$HivequeenPath\AGENTS.md``
"@ | Set-Content -Path "$CodexDir\instructions.md" -Encoding UTF8
Write-Host "v wrote $CodexDir\instructions.md"

# 3. Register session end hook in config.json
if (-not (Test-Path $Settings)) {
    '{}' | Set-Content -Path $Settings -Encoding UTF8
}

$HookCmd = "cd `"$HivequeenPath`" && git pull --rebase --autostash -q && git add agents/$AgentId/ && git diff --cached --quiet || git commit -m 'memory: update $AgentId' && git push -q"

$SettingsObj = Get-Content $Settings -Raw | ConvertFrom-Json

if (-not $SettingsObj.session) {
    $SettingsObj | Add-Member -NotePropertyName session -NotePropertyValue @{}
}
$SettingsObj.session | Add-Member -NotePropertyName end_hook -NotePropertyValue $HookCmd -Force

$SettingsObj | ConvertTo-Json -Depth 10 | Set-Content -Path $Settings -Encoding UTF8
Write-Host "v registered session end hook in $Settings"

Write-Host ""
Write-Host "OK hivequeen installed for Codex"
Write-Host "   agent: $AgentId"
Write-Host "   memory: $MemoryFile"
