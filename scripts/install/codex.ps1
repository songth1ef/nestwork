# ---------------------------------------------
# hivequeen x Codex installer (Windows)
# ---------------------------------------------

$ErrorActionPreference = "Stop"

$HivequeenPath = (Resolve-Path "$PSScriptRoot\..\..").Path
$CodexDir = "$env:USERPROFILE\.codex"
$Settings = "$CodexDir\config.json"

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by hivequeen installer"
}

$IdentityLines = & $PythonCmd (Join-Path $HivequeenPath "scripts\install\_identity.py") codex
if ($LASTEXITCODE -ne 0) { throw "identity resolver failed (exit $LASTEXITCODE)" }
$HiveHost = $IdentityLines[0].Trim()
$AgentId  = $IdentityLines[1].Trim()
$AgentDir = "$HivequeenPath\agents\$HiveHost\$AgentId"

Write-Host "-> hivequeen path : $HivequeenPath"
Write-Host "-> host           : $HiveHost"
Write-Host "-> agent id       : $AgentId"

# 1. Create this agent's memory directory
New-Item -ItemType Directory -Force -Path $AgentDir | Out-Null
$MemoryFile = "$AgentDir\memory.md"
if (-not (Test-Path $MemoryFile)) {
    @"
# MEMORY -- $HiveHost/$AgentId

> Private memory for this agent instance.
> Only $HiveHost/$AgentId writes here.

---

_No memory yet._
"@ | Set-Content -Path $MemoryFile -Encoding UTF8
    Write-Host "v created $MemoryFile"
}

# 2. Inject hivequeen bootstrap (marker-preserved).
New-Item -ItemType Directory -Force -Path $CodexDir | Out-Null
& $PythonCmd (Join-Path $HivequeenPath "scripts\install\_bootstrap.py") `
    "$CodexDir\instructions.md" $HivequeenPath $HiveHost $AgentId
if ($LASTEXITCODE -ne 0) {
    throw "Codex instructions bootstrap injection failed (exit $LASTEXITCODE)"
}

# 3. Register session end hook in config.json
if (-not (Test-Path $Settings)) {
    '{}' | Set-Content -Path $Settings -Encoding UTF8
}

$AgentRel = "agents/$HiveHost/$AgentId"
$HookCmd = "Set-Location -LiteralPath `"$HivequeenPath`"; git pull --rebase --autostash -q; if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE }; git add $AgentRel/; if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE }; git diff --cached --quiet -- $AgentRel/; if (`$LASTEXITCODE -ne 0) { git commit -m 'memory: update $HiveHost/$AgentId' -- $AgentRel/; if (`$LASTEXITCODE -ne 0) { exit `$LASTEXITCODE } }; git push -q"

$SettingsObj = Get-Content $Settings -Raw | ConvertFrom-Json

if (-not $SettingsObj.session) {
    $SettingsObj | Add-Member -NotePropertyName session -NotePropertyValue @{}
}
$SettingsObj.session | Add-Member -NotePropertyName end_hook -NotePropertyValue $HookCmd -Force

$SettingsObj | ConvertTo-Json -Depth 10 | Set-Content -Path $Settings -Encoding UTF8
Write-Host "v registered session end hook in $Settings"

Write-Host ""
Write-Host "OK hivequeen installed for Codex"
Write-Host "   agent: $HiveHost/$AgentId"
Write-Host "   memory: $MemoryFile"
