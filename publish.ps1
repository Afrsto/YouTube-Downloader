#Requires -Version 5.1
<#
.SYNOPSIS
  Authenticate (if needed), push to Afrsto/YouTube-Downloader, create v1.1.2 Release with Setup + APK.

.USAGE
  cd github
  .\publish.ps1
#>
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Tag = "v1.1.2"
$Title = "YouTube Downloader v1.1.2"
$NotesFile = Join-Path $PSScriptRoot "release-assets\NOTES-1.1.2.md"

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

$Setup = Join-Path $PSScriptRoot "release-assets\YouTube-Downloader-Setup-1.1.2.exe"
if (-not (Test-Path $Setup)) {
    $Fallback = Join-Path $PSScriptRoot "..\installer\output\YouTube Downloader Setup.exe"
    if (Test-Path $Fallback) {
        Copy-Item -LiteralPath $Fallback -Destination $Setup -Force
    }
}
$Apk = Join-Path $PSScriptRoot "release-assets\YouTube-Downloader-1.1.2-android.apk"
if (-not (Test-Path $Apk)) {
    $FallbackApk = Join-Path $PSScriptRoot "..\android\app\build\outputs\apk\debug\app-debug.apk"
    if (Test-Path $FallbackApk) {
        Copy-Item -LiteralPath $FallbackApk -Destination $Apk -Force
    }
}

$assets = @()
if (Test-Path $Setup) { $assets += $Setup } else {
    Write-Host "Setup.exe not found. From project root run: ..\build.ps1" -ForegroundColor Yellow
}
if (Test-Path $Apk) { $assets += $Apk } else {
    Write-Host "APK not found. Build android debug first." -ForegroundColor Yellow
}
if ($assets.Count -eq 0) { exit 0 }
if (-not (Test-Path $NotesFile)) { throw "Missing notes: $NotesFile" }

Write-Host "==> Release $Tag" -ForegroundColor Cyan
gh release view $Tag 2>$null
if ($LASTEXITCODE -eq 0) {
    gh release upload $Tag @assets --clobber
} else {
    gh release create $Tag @assets `
        --title $Title `
        --notes-file $NotesFile
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
Write-Host "  Repo:    https://github.com/Afrsto/YouTube-Downloader"
Write-Host "  Release: https://github.com/Afrsto/YouTube-Downloader/releases/tag/$Tag"
