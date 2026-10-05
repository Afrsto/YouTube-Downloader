# YouTube Downloader v1.0.0

Fresh v1.0.0 release — Windows desktop app + local web UI.

## What's included

- **Windows Setup** — CustomTkinter desktop app (M4A / MP4 via yt-dlp)
- **Web UI** — Run locally with `python website/server.py` (same backend)

## Highlights

- Fixed pre-download size estimate for MP4 (progressive streams, tbr fallback)
- Producer tags like `prod.L5vav` stripped from filenames
- Android APK removed; replaced by local website in `website/`

## Install (Windows)

1. Download **YouTube-Downloader-Setup-1.0.0.exe**
2. Run Setup (per-user)
3. Ensure **ffmpeg** is on PATH

## Web UI

```powershell
pip install -r website/requirements.txt
python website/server.py
```

Open http://127.0.0.1:8765
