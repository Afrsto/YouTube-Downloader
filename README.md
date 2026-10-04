<div align="center">

# YouTube Downloader

### Windows + Android — YouTube → **M4A** & **MP4**

**yt-dlp** on Windows · **NewPipe Extractor** on Android · Mandatory updates

[![Release](https://img.shields.io/github/v/release/Afrsto/YouTube-Downloader?style=for-the-badge&color=c62828&label=Latest%20Release)](https://github.com/Afrsto/YouTube-Downloader/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/Afrsto/YouTube-Downloader/total?style=for-the-badge&color=2ba640)](https://github.com/Afrsto/YouTube-Downloader/releases)
[![Platform](https://img.shields.io/badge/Windows-10%20%7C%2011-0f0f0f?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Afrsto/YouTube-Downloader/releases/latest)
[![Android](https://img.shields.io/badge/Android-9%2B-3DDC84?style=for-the-badge&logo=android&logoColor=white)](https://github.com/Afrsto/YouTube-Downloader/releases/latest)

**[⬇ Download](https://github.com/Afrsto/YouTube-Downloader/releases/latest)** ·
**[Issues](https://github.com/Afrsto/YouTube-Downloader/issues)**

<br/>

<img src="YouTube%20Downloader.ico" alt="YouTube Downloader icon" width="96" />

</div>

---

## Features

| | |
|---|---|
| **M4A audio** | Cover art + **embedded lyrics** from YouTube captions |
| **MP4 video** | Muxed MP4 via ffmpeg — **144p** to **4K** |
| **Full quality ladder** | Video 144–2160p · Audio 64–320 kbps |
| **Size confirmation** | Estimated size with Yes / No before download |
| **Smart fallback** | If 2K is missing, offers the highest available |
| **Mandatory updates** | GitHub Releases — no “later” |
| **Android APK** | Setup-style home + share-from-YouTube download UI (NewPipe Extractor) |

---

## Install (Windows)

1. Open the **[latest release](https://github.com/Afrsto/YouTube-Downloader/releases/latest)**.
2. Download **`YouTube.Downloader.Setup.exe`** (or Setup asset).
3. Run Setup (per-user).
4. Put **[ffmpeg](https://ffmpeg.org/download.html)** on **PATH**.

> Defender may ML-flag unsigned freezers (`Wacatac.!ml`). See [AV_FALSE_POSITIVE.md](AV_FALSE_POSITIVE.md).

---

## Install (Android 9+)

1. Download the **`.apk`** from the latest release.
2. Allow install from unknown sources if prompted.
3. Open the app for the **Setup-style** home (paste a URL), **or** share a video from the YouTube app to **YouTube Downloader**.

Android module source: [`android/`](android/) — GPL-3.0 obligations apply because of NewPipe Extractor. See [`android/README.md`](android/README.md).

---

## Usage (Windows)

1. Paste a YouTube URL or **Search Video**.
2. Choose **M4A · audio** or **MP4 · video**.
3. Select quality → **Download**.
4. Confirm size. For M4A, captions are fetched and lyrics are embedded when available.

---

## Build from source

### Windows

```powershell
.\build.ps1
```

Requires Python 3.9+, Inno Setup 6. Output: `installer\output\YouTube Downloader Setup.exe`.

### Android

```powershell
cd android
.\gradlew.bat assembleDebug
```

Requires JDK 17+ and Android SDK. See [`android/README.md`](android/README.md).

---

## Updates (mandatory)

```text
https://api.github.com/repos/Afrsto/YouTube-Downloader/releases/latest
```

---

## Contacts

- Telegram: https://t.me/X2_616
- Discord user: https://discord.com/users/994817247061225633
- Discord server: https://discord.gg/btRCeujadA

---

## Disclaimer

Download only content you have the right to access. Respect YouTube’s Terms of Service and copyright law.

---

<div align="center">

[Download the latest release](https://github.com/Afrsto/YouTube-Downloader/releases/latest)

</div>
