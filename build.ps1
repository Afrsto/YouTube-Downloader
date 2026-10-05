#Requires -Version 5.1
<#
.SYNOPSIS
  Build AV-safer "YouTube Downloader Setup.exe"
  (PyInstaller onedir --noupx + Inno Setup zip/no-solid).

.NOTES
  Requires: Python 3.9+, Inno Setup 6 (ISCC.exe on PATH or default install path).
  Do NOT upload every experimental build to VirusTotal — see AV_FALSE_POSITIVE.md.
#>
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$AppName = "YouTube Downloader"
$VenvDir = Join-Path $Root ".venv"
$Python = Join-Path $VenvDir "Scripts\python.exe"
$Pip = Join-Path $VenvDir "Scripts\pip.exe"
$Spec = Join-Path $Root "YouTube Downloader.spec"
$Iss = Join-Path $Root "installer\YouTubeDownloader.iss"
$Ico = Join-Path $Root "YouTube Downloader.ico"

function Write-Step([string]$Msg) {
    Write-Host ""
    Write-Host "==> $Msg" -ForegroundColor Cyan
}

function Find-ISCC {
    $cmd = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
        "${env:LOCALAPPDATA}\Programs\Inno Setup 6\ISCC.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

# --- Preconditions ---
if (-not (Test-Path $Ico)) {
    throw "Missing icon: $Ico"
}
if (-not (Test-Path (Join-Path $Root "youtube_downloadr.py"))) {
    throw "Missing youtube_downloadr.py"
}
if (-not (Test-Path $Spec)) {
    throw "Missing PyInstaller spec: $Spec"
}
if (-not (Test-Path $Iss)) {
    throw "Missing Inno script: $Iss"
}

$Iscc = Find-ISCC
if (-not $Iscc) {
    throw @"
Inno Setup 6 (ISCC.exe) not found.
Install from https://jrsoftware.org/isdl.php
or add ISCC.exe to PATH, then re-run this script.
"@
}

# --- Venv ---
Write-Step "Creating / refreshing venv"
if (-not (Test-Path $Python)) {
    python -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "Failed to create venv" }
}

Write-Step "Installing build dependencies"
& $Pip install --upgrade pip
& $Pip install --upgrade `
    "pyinstaller" `
    "yt-dlp" `
    "customtkinter" `
    "pillow" `
    "mutagen"
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

# --- Clean previous dist ---
Write-Step "Cleaning previous build outputs"
$DistDir = Join-Path $Root "dist"
$BuildDir = Join-Path $Root "build"
$OutDir = Join-Path $Root "installer\output"
foreach ($d in @($DistDir, $BuildDir)) {
    if (Test-Path $d) { Remove-Item $d -Recurse -Force }
}
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# --- PyInstaller onedir ---
Write-Step "PyInstaller onedir (upx=False, noconsole)"
& $Python -m PyInstaller --noconfirm --clean $Spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$AppDir = Join-Path $DistDir $AppName
$AppExe = Join-Path $AppDir "$AppName.exe"
if (-not (Test-Path $AppExe)) {
    throw "Expected app exe missing: $AppExe"
}

# --- Inno Setup ---
Write-Step "Compiling Inno Setup installer"
& $Iscc $Iss
if ($LASTEXITCODE -ne 0) { throw "ISCC failed" }

$Setup = Join-Path $OutDir "YouTube Downloader Setup.exe"
if (-not (Test-Path $Setup)) {
    throw "Setup not found: $Setup"
}

$hash = (Get-FileHash -Algorithm SHA256 $Setup).Hash
$sizeMb = [math]::Round((Get-Item $Setup).Length / 1MB, 2)

Write-Host ""
Write-Host "Build OK" -ForegroundColor Green
Write-Host "  Setup : $Setup"
Write-Host "  Size  : $sizeMb MB"
Write-Host "  SHA256: $hash"
Write-Host ""
Write-Host "Next: submit this exact file to Microsoft if Defender flags it." -ForegroundColor Yellow
Write-Host "  See AV_FALSE_POSITIVE.md"
Write-Host "  https://www.microsoft.com/en-us/wdsi/filesubmission"
