# YouTube Downloadr — Web UI

Local web interface with the same yt-dlp backend as the Windows desktop app.

## Requirements

- Python 3.9+
- [ffmpeg](https://ffmpeg.org/download.html) on PATH (for MP4 mux / M4A cover embed)

## Run

From the project root:

```powershell
python -m pip install -r website/requirements.txt
python website/server.py
```

Your browser opens at `http://127.0.0.1:8765`.

## Features

- Paste or search YouTube URLs
- M4A audio (64–320 kbps) or MP4 video (144p–4K)
- Estimated size confirmation before download
- Quality fallback when requested resolution is unavailable
- Downloads save to the folder you specify (default: `%USERPROFILE%\Downloads\YouTube`)
