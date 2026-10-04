# Antivirus false positives (Microsoft Wacatac.!ml)

## What this is

`Trojan:Win32/Wacatac.B!ml` and `Trojan:Win32/Wacatac.C!ml` are **Microsoft Defender machine-learning heuristics**, not proof that this app contains malware. Unsigned PyInstaller + Inno Setup binaries are commonly mislabeled.

This project is packaged to **reduce** those heuristics:

- PyInstaller **onedir** (not onefile / TEMP self-extract)
- **UPX disabled**
- No runtime `pip install` in the frozen exe
- Inno Setup with **Compression=zip** and **SolidCompression=no**
- Per-user install (`PrivilegesRequired=lowest`) — no unnecessary UAC admin
- PE / Setup version metadata + product icon

**There is no free guarantee of zero Microsoft detections without Authenticode.** Every rebuild creates a new hash that may need a new submission.

## Do not spam VirusTotal

- Do **not** upload every experimental build to VirusTotal.
- VT reports feed reputation noise and can worsen cloud ML scores for similar hashes.
- While iterating: scan locally with Windows Defender only.
- Upload to VirusTotal **once** for the final release Setup if you want a public report.

## Clear Microsoft Defender (required for each release hash)

1. Build the final Setup: `.\build.ps1`
2. Note the SHA256 printed at the end (or: `Get-FileHash -Algorithm SHA256 "installer\output\YouTube Downloader Setup.exe"`).
3. Open [Microsoft Security Intelligence — Submit a file](https://www.microsoft.com/en-us/wdsi/filesubmission).
4. Choose **Software developer** → **Incorrectly detected as malware/malicious**.
5. Upload the **exact** `YouTube Downloader Setup.exe` that you will distribute (same hash).
6. In the description, state something like:
   - Product: YouTube Downloader (GUI front-end for yt-dlp)
   - Built with: Python + PyInstaller onedir (no UPX) + Inno Setup (zip, no solid)
   - Detection name: `Trojan:Win32/Wacatac.B!ml` or `.C!ml` (if shown)
   - Source is local / this project folder; legitimate media downloader for personal use
7. Wait for Microsoft’s determination (often hours to ~1 day). Have users update Defender definitions afterward.
8. **Repeat for every new Setup hash** after any rebuild.

## Local Defender check (optional, while developing)

```powershell
Start-MpScan -ScanType CustomScan -ScanPath "$PWD\installer\output\YouTube Downloader Setup.exe"
```

Or right-click → Scan with Microsoft Defender in Explorer.

## If still flagged after a clean determination

1. Confirm definitions are updated and you are testing the **same** submitted hash.
2. Rebuild once (new hash) and submit again if the old determination does not cover a new build.
3. Fallback (if Inno stub keeps getting hit): wrap the same `dist\YouTube Downloader\` folder in a **WiX MSI** instead of Inno — do **not** switch to NSIS, onefile, or UPX.

## What not to do

- Do not use `--onefile`, UPX, crypters, or “AV evade” tools.
- Do not use a self-signed certificate (no trust benefit; can look worse).
- Do not tell users to disable Defender as the distribution strategy.
- Do not embed a custom self-extracting ffmpeg installer inside Setup.
