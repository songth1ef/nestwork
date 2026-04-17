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

# 2. Inject hivequeen bootstrap (marker-preserved). Requires python.
New-Item -ItemType Directory -Force -Path $CodexDir | Out-Null

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found — required by hivequeen installer"
}

& $PythonCmd (Join-Path $HivequeenPath "scripts\_install-bootstrap.py") `
    "$CodexDir\instructions.md" $HivequeenPath $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "Codex instructions bootstrap injection failed (exit $LASTEXITCODE)"
}

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
