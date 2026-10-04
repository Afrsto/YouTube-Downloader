# Download official gradle-wrapper.jar into android/gradle/wrapper/
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $root "settings.gradle.kts"))) {
  $root = "C:\Users\X2\Downloads\YouTube Downloader\android"
}
$wrapperDir = Join-Path $root "gradle\wrapper"
New-Item -ItemType Directory -Force -Path $wrapperDir | Out-Null
$jar = Join-Path $wrapperDir "gradle-wrapper.jar"
# Use Gradle 8.11.1 distribution's wrapper jar via GitHub raw from gradle repo release
$url = "https://raw.githubusercontent.com/gradle/gradle/v8.11.1/gradle/wrapper/gradle-wrapper.jar"
Write-Host "Downloading $url"
Invoke-WebRequest -Uri $url -OutFile $jar -UseBasicParsing
Get-Item $jar | Select-Object FullName, Length
