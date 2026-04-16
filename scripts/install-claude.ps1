# ─────────────────────────────────────────────
# hivequeen x Claude Code installer (Windows)
# ─────────────────────────────────────────────

$ErrorActionPreference = "Stop"

$HivequeenPath = (Resolve-Path "$PSScriptRoot\..").Path
$ClaudeDir = "$env:USERPROFILE\.claude"
$Settings = "$ClaudeDir\settings.json"
$AgentId = "claude-$env:COMPUTERNAME".ToLower()
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

# 2. Write global CLAUDE.md
New-Item -ItemType Directory -Force -Path $ClaudeDir | Out-Null
@"
# Global Startup Protocol

Before starting analysis, planning, or implementation, run:

``````powershell
git -C "$HivequeenPath" pull --rebase
``````

Then load context from hivequeen in this order:

1. ``$HivequeenPath\queen\agent-rules.md``
2. ``$HivequeenPath\queen\strategy.md``
3. ``$HivequeenPath\shared\memory.md``
4. ``$HivequeenPath\agents\$AgentId\memory.md``
5. Relevant ``$HivequeenPath\projects\*.md`` for current task

Write protocol: only write to ``$HivequeenPath\agents\$AgentId\``

See full protocol: ``$HivequeenPath\AGENTS.md``
"@ | Set-Content -Path "$ClaudeDir\CLAUDE.md" -Encoding UTF8
Write-Host "v wrote $ClaudeDir\CLAUDE.md"

# 3. Register Stop hook in settings.json
if (-not (Test-Path $Settings)) {
    '{}' | Set-Content -Path $Settings -Encoding UTF8
}

$HookCmd = "cd `"$HivequeenPath`" && git pull --rebase --autostash -q && git add agents/$AgentId/ && git diff --cached --quiet || git commit -m 'memory: update $AgentId' && git push -q"

$SettingsObj = Get-Content $Settings -Raw | ConvertFrom-Json

if (-not $SettingsObj.hooks) {
    $SettingsObj | Add-Member -NotePropertyName hooks -NotePropertyValue @{}
}
if (-not $SettingsObj.hooks.Stop) {
    $SettingsObj.hooks | Add-Member -NotePropertyName Stop -NotePropertyValue @()
}

$NewHook = @{
    matcher = ""
    hooks   = @(@{ type = "command"; command = $HookCmd })
}

$Exists = $SettingsObj.hooks.Stop | Where-Object { $_.hooks[0].command -eq $HookCmd }
if (-not $Exists) {
    $SettingsObj.hooks.Stop += $NewHook
    $SettingsObj | ConvertTo-Json -Depth 10 | Set-Content -Path $Settings -Encoding UTF8
    Write-Host "v registered Stop hook in $Settings"
} else {
    Write-Host "v Stop hook already registered"
}

Write-Host ""
Write-Host "OK hivequeen installed for Claude Code"
Write-Host "   agent: $AgentId"
Write-Host "   memory: $MemoryFile"
