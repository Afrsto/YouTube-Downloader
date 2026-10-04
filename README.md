<div align="center">

# YouTube Downloader

### A refined Windows app for YouTube → **M4A** & **MP4**

Built on **yt-dlp** · Guided quality · Size confirmation · Mandatory auto-updates

[![Release](https://img.shields.io/github/v/release/Afrsto/YouTube-Downloader?style=for-the-badge&color=c62828&label=Latest%20Release)](https://github.com/Afrsto/YouTube-Downloader/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/Afrsto/YouTube-Downloader/total?style=for-the-badge&color=2ba640)](https://github.com/Afrsto/YouTube-Downloader/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-3ea6ff?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Windows-10%20%7C%2011-0f0f0f?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Afrsto/YouTube-Downloader/releases/latest)

**[⬇ Download Setup](https://github.com/Afrsto/YouTube-Downloader/releases/latest)** ·
**[Issues](https://github.com/Afrsto/YouTube-Downloader/issues)** ·
**[Source](https://github.com/Afrsto/YouTube-Downloader)**

<br/>

<img src="YouTube%20Downloader.ico" alt="YouTube Downloader icon" width="96" />

</div>

---

## Why this exists

Most downloaders dump a pile of cryptic formats on you. **YouTube Downloader** keeps the experience calm and intentional:

- Pick **audio (M4A)** or **video (MP4)**
- Choose from a full quality ladder
- See the **estimated size** and confirm before anything is fetched
- Stay current with **mandatory updates** from GitHub Releases

---

## Features

| | |
|---|---|
| **M4A audio** | High-quality audio with cover art (Explorer-friendly) |
| **MP4 video** | Muxed MP4 via ffmpeg — from **144p** to **4K** |
| **Full quality ladder** | Video: 144 · 240 · 360 · 480 · 720 · 1080 · 1440 (2K) · 2160 (4K). Audio: 64–320 kbps |
| **Smart fallback** | If you ask for 2K and the upload tops out at 1080p, you are told — then Yes downloads at the best available |
| **Size confirmation** | Estimated download size with **Yes / No** before starting |
| **Search** | Find a video by name without leaving the app |
| **Mandatory updates** | Checks [`releases/latest`](https://api.github.com/repos/Afrsto/YouTube-Downloader/releases/latest) on launch — no “remind me later” |
| **AV-safer packaging** | PyInstaller **onedir** (no UPX) + Inno Setup **zip / no solid** |

---

## Install (Windows)

1. Open the **[latest release](https://github.com/Afrsto/YouTube-Downloader/releases/latest)**.
2. Download **`YouTube Downloader Setup.exe`**.
3. Run the Setup (per-user install — no admin required).
4. Install **[ffmpeg](https://ffmpeg.org/download.html)** and ensure `ffmpeg` is on your **PATH**  
   (required for audio convert, cover embed, and MP4 merge).

> **SmartScreen / Defender note**  
> New unsigned builds can be flagged by Microsoft ML heuristics (`Wacatac.!ml`). That is a known false-positive class for Python + Inno installers. See [AV_FALSE_POSITIVE.md](AV_FALSE_POSITIVE.md). Prefer the release asset from **this** repository only.

---

## Usage

1. Paste a YouTube URL (right-click → Paste) or use **Search Video**.
2. Choose **M4A · audio** or **MP4 · video**.
3. Select quality.
4. Pick a save folder.
5. Click **Download**.
6. Confirm size (**Yes** / **No**). If your quality isn’t available, confirm the highest available (**Yes** / **No**).

---

## Updates (mandatory)

On every launch the app calls:

```text
https://api.github.com/repos/Afrsto/YouTube-Downloader/releases/latest
```

| Result | Behavior |
|--------|----------|
| Newer release with a Setup `.exe` | Blocking dialog — **Download update** or **Exit** (no skip) |
| Already current | App continues normally |
| Network / API error | **Retry**, **Continue offline**, or **Exit** |

Publish new versions as GitHub Releases with tag `vX.Y.Z` and attach **`YouTube Downloader Setup.exe`**.

Bump `APP_VERSION` in `youtube_downloadr.py` (and `version_info.txt` / Inno `AppVersion`) to match.

---

## Build from source

**Requirements:** Python 3.9+, [Inno Setup 6](https://jrsoftware.org/isdl.php), Windows x64.

```powershell
git clone https://github.com/Afrsto/YouTube-Downloader.git
cd YouTube-Downloader
.\build.ps1
```

Output:

```text
installer\output\YouTube Downloader Setup.exe
```

Manual run (dev):

```powershell
python -m pip install yt-dlp customtkinter pillow
python youtube_downloadr.py
```

---

## Project layout

```text
YouTube-Downloader/
├── youtube_downloadr.py      # App (GUI + yt-dlp + updater)
├── YouTube Downloader.ico    # Brand icon
├── YouTube Downloader.spec   # PyInstaller onedir (no UPX)
├── version_info.txt          # PE version resource
├── build.ps1                 # One-shot Windows build
├── installer/
│   └── YouTubeDownloader.iss # Inno Setup (zip, no solid)
├── AV_FALSE_POSITIVE.md      # Defender / VirusTotal guidance
├── LICENSE
└── README.md
```

---

## Tech stack

- **Python** + **CustomTkinter** UI
- **yt-dlp** extraction / download
- **ffmpeg** post-process & mux
- **PyInstaller** + **Inno Setup** for distribution
- **GitHub Releases API** for mandatory updates

---

## Disclaimer

This project is for downloading content you have the right to access. Respect YouTube’s Terms of Service and applicable copyright law. The authors are not responsible for misuse.

---

<div align="center">

**Made for a cleaner download workflow**

[Download the latest Setup](https://github.com/Afrsto/YouTube-Downloader/releases/latest)

</div>
