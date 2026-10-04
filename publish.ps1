#Requires -Version 5.1
<#
.SYNOPSIS
  Push github/ package to Afrsto/YouTube-Downloader and (optionally) create v1.0.0 release with Setup.

.NOTES
  Run from the github folder after: gh auth login
#>
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "==> Checking GitHub auth..." -ForegroundColor Cyan
gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Not logged in. Starting gh auth login (browser)..." -ForegroundColor Yellow
    gh auth login --hostname github.com --git-protocol https --web
}

Write-Host "==> Pushing main..." -ForegroundColor Cyan
git push -u origin main

$SetupCandidates = @(
    (Join-Path $PSScriptRoot "..\installer\output\YouTube Downloader Setup.exe"),
    (Join-Path $PSScriptRoot "installer\output\YouTube Downloader Setup.exe")
)
$Setup = $SetupCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $Setup) {
    Write-Host "No Setup.exe found. Build with ..\build.ps1 (from project root) then re-run to attach release." -ForegroundColor Yellow
    exit 0
}

Write-Host "==> Creating / updating release v1.0.0 with Setup..." -ForegroundColor Cyan
$existing = gh release view v1.0.0 2>$null
if ($LASTEXITCODE -eq 0) {
    gh release upload v1.0.0 "$Setup" --clobber
} else {
    gh release create v1.0.0 "$Setup" `
        --title "YouTube Downloader v1.0.0" `
        --notes "Initial release.`n`n- M4A / MP4 downloads via yt-dlp`n- Full quality ladder + size confirmation`n- Mandatory update check via GitHub Releases"
}

Write-Host "Done. https://github.com/Afrsto/YouTube-Downloader/releases/latest" -ForegroundColor Green
