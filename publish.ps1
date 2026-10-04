#Requires -Version 5.1
<#
.SYNOPSIS
  Authenticate (if needed), push to Afrsto/YouTube-Downloader, create v1.0.0 Release with Setup.

.USAGE
  cd github
  .\publish.ps1
#>
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
            [System.Environment]::GetEnvironmentVariable("Path", "User")

Write-Host "==> GitHub auth" -ForegroundColor Cyan
gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Log in via browser when prompted..." -ForegroundColor Yellow
    gh auth login --hostname github.com --git-protocol https --web
}
gh auth setup-git

Write-Host "==> Push main -> https://github.com/Afrsto/YouTube-Downloader" -ForegroundColor Cyan
git push -u origin main
if ($LASTEXITCODE -ne 0) { throw "git push failed" }

$Setup = Join-Path $PSScriptRoot "..\installer\output\YouTube Downloader Setup.exe"
if (-not (Test-Path $Setup)) {
    $Setup = Join-Path $PSScriptRoot "installer\output\YouTube Downloader Setup.exe"
}
if (-not (Test-Path $Setup)) {
    Write-Host "Setup.exe not found. From project root run: ..\build.ps1 then re-run publish.ps1" -ForegroundColor Yellow
    exit 0
}

Write-Host "==> Release v1.0.0 + Setup asset" -ForegroundColor Cyan
gh release view v1.0.0 2>$null
if ($LASTEXITCODE -eq 0) {
    gh release upload v1.0.0 "$Setup" --clobber
} else {
    gh release create v1.0.0 "$Setup" `
        --title "YouTube Downloader v1.0.0" `
        --notes @"
Initial release.

- M4A / MP4 via yt-dlp
- Full quality ladder (144p–4K, 64–320 kbps)
- Size confirmation before download
- Mandatory updates from GitHub Releases
"@
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "  Repo:    https://github.com/Afrsto/YouTube-Downloader"
Write-Host "  Release: https://github.com/Afrsto/YouTube-Downloader/releases/latest"
