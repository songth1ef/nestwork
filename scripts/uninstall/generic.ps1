# -----------------------------------------------------------------------------
# nestwork x generic markdown-config uninstaller (Windows)
#
# Inverse of install/generic.ps1: removes the nestwork bootstrap block from the
# given config file. Memory and identity files are never deleted.
#
# Usage:
#   .\uninstall\generic.ps1 <tool-prefix> <config-path> [-PurgeIdentity]
#
# Example:
#   .\uninstall\generic.ps1 qwen "$env:USERPROFILE\.qwen\QWEN.md"
# -----------------------------------------------------------------------------

param(
    [Parameter(Mandatory = $true)][string]$Prefix,
    [Parameter(Mandatory = $true)][string]$ConfigPath,
    [switch]$PurgeIdentity
)

$ErrorActionPreference = "Stop"

$NestworkPath = (Resolve-Path "$PSScriptRoot\..\..").Path

$PythonCmd = $null
foreach ($Cand in @("python3", "python", "py")) {
    if (Get-Command $Cand -ErrorAction SilentlyContinue) { $PythonCmd = $Cand; break }
}
if (-not $PythonCmd) {
    throw "python3 (or python / py) not found -- required by nestwork uninstaller"
}

$NestHost = ""
$AgentId  = ""
if (Test-Path "$env:USERPROFILE\.nestwork_host") {
    $NestHost = (Get-Content "$env:USERPROFILE\.nestwork_host" -Raw).Trim()
}
if (Test-Path "$env:USERPROFILE\.nestwork_id_$Prefix") {
    $AgentId = (Get-Content "$env:USERPROFILE\.nestwork_id_$Prefix" -Raw).Trim()
}

Write-Host "-> nestwork path : $NestworkPath"
Write-Host "-> host           : $NestHost"
Write-Host "-> agent id       : $AgentId"

& $PythonCmd (Join-Path $NestworkPath "scripts\uninstall\_unbootstrap.py") $ConfigPath
if ($LASTEXITCODE -ne 0) { throw "bootstrap removal failed (exit $LASTEXITCODE)" }

if ($PurgeIdentity) {
    Remove-Item -Force -ErrorAction SilentlyContinue "$env:USERPROFILE\.nestwork_id_$Prefix"
    Write-Host "v removed .nestwork_id_$Prefix (next install gets a new agent id)"
}

Write-Host ""
Write-Host "OK nestwork unbound from $Prefix"
if ($NestHost -and $AgentId) {
    Write-Host "   memory kept : $NestworkPath\agents\$NestHost\$AgentId\"
} else {
    Write-Host "   memory kept : $NestworkPath\agents\<host>\<agent-id>\"
}
Write-Host "   to rebind   : .\scripts\install\generic.ps1 $Prefix $ConfigPath"
