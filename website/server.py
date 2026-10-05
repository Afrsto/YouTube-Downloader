#!/usr/bin/env python3
"""Local web UI for YouTube Downloader — same yt-dlp backend as the Windows app."""

from __future__ import annotations

import sys
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, render_template, request

from youtube_downloadr import (
    APP_VERSION,
    AUDIO_BITRATES,
    CONTACT_DISCORD_SERVER,
    CONTACT_DISCORD_USER,
    CONTACT_TELEGRAM,
    GITHUB_URL,
    VIDEO_HEIGHTS,
    Downloader,
    _FFMPEG_OK,
    _YTDLP_OK,
    _YTDLP_VER,
    _format_bytes,
    _height_label,
)

app = Flask(__name__)
api = Downloader()
_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()


def _default_out() -> str:
    return str(Path.home() / "Downloads" / "YouTube")


def _get_job(job_id: str) -> dict | None:
    with _jobs_lock:
        return _jobs.get(job_id)


@app.route("/")
def index():
    return render_template(
        "index.html",
        version=APP_VERSION,
        video_heights=VIDEO_HEIGHTS,
        audio_bitrates=AUDIO_BITRATES,
        default_out=_default_out(),
        contact_telegram=CONTACT_TELEGRAM,
        contact_discord_user=CONTACT_DISCORD_USER,
        contact_discord_server=CONTACT_DISCORD_SERVER,
        github_url=GITHUB_URL,
    )


@app.get("/api/status")
def system_status():
    import platform

    return jsonify(
        {
            "version": APP_VERSION,
            "ytdlp_ok": _YTDLP_OK,
            "ytdlp_ver": _YTDLP_VER,
            "ffmpeg_ok": _FFMPEG_OK,
            "python": platform.python_version(),
        }
    )


@app.post("/api/search")
def search():
    data = request.get_json(force=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "empty search query"}), 400
    try:
        results = api.search(query, limit=12)
        for r in results:
            r["duration_label"] = Downloader.format_duration(r.get("duration"))
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/probe")
def probe():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    fmt = data.get("fmt") or "mp3"
    quality = str(data.get("quality") or ("320" if fmt == "mp3" else "1080"))
    if not url:
        return jsonify({"error": "missing url"}), 400
    try:
        eff_q, downgrade_msg = api.resolve_quality(url, fmt, quality)
        return jsonify(
            {
                "quality": eff_q,
                "downgrade_msg": downgrade_msg,
                "title": api.sanitize(
                    api.probe_capabilities(url).get("title") or ""
                ),
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/estimate")
def estimate():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    fmt = data.get("fmt") or "mp3"
    quality = str(data.get("quality") or ("320" if fmt == "mp3" else "1080"))
    if not url:
        return jsonify({"error": "missing url"}), 400
    try:
        size = api.estimate_download_size(url, fmt, quality)
        if fmt == "mp3":
            q_txt = f"{quality} kbps (M4A)"
        else:
            q_txt = _height_label(int(quality)) + " (MP4)"
        return jsonify(
            {
                "size": size,
                "size_label": _format_bytes(size),
                "quality_label": q_txt,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _run_download(job_id: str, url: str, fmt: str, quality: str, out: str):
    job = _get_job(job_id)
    if not job:
        return
    stop: threading.Event = job["stop"]

    def log(msg: str):
        job["logs"].append(msg)

    def prog(v: float):
        job["progress"] = float(v)

    try:
        title = api.get_title(url, log=log)
        name = title or Downloader.vid_id(url)
        dest = api.download(url, fmt, quality, out, name, prog=prog, log=log, stop=stop)
        job["status"] = "done"
        job["dest"] = dest
        log(f"✓ Done → {dest}")
    except InterruptedError:
        job["status"] = "cancelled"
        log("⚠ cancelled by user")
    except Exception as e:
        job["status"] = "error"
        log(f"✗ {e}")
    finally:
        job["progress"] = 0 if job["status"] != "done" else 100


@app.post("/api/download")
def start_download():
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    fmt = data.get("fmt") or "mp3"
    quality = str(data.get("quality") or ("320" if fmt == "mp3" else "1080"))
    out = (data.get("out_dir") or _default_out()).strip()
    if not url:
        return jsonify({"error": "missing url"}), 400
    if not out:
        return jsonify({"error": "missing output directory"}), 400
    Path(out).mkdir(parents=True, exist_ok=True)

    job_id = uuid.uuid4().hex
    job = {
        "id": job_id,
        "status": "running",
        "progress": 0,
        "logs": [],
        "dest": None,
        "stop": threading.Event(),
    }
    with _jobs_lock:
        _jobs[job_id] = job

    threading.Thread(
        target=_run_download,
        args=(job_id, url, fmt, quality, out),
        daemon=True,
    ).start()
    return jsonify({"job_id": job_id})


@app.get("/api/download/<job_id>")
def download_status(job_id: str):
    job = _get_job(job_id)
    if not job:
        return jsonify({"error": "unknown job"}), 404
    return jsonify(
        {
            "status": job["status"],
            "progress": job["progress"],
            "logs": job["logs"],
            "dest": job["dest"],
        }
    )


@app.post("/api/download/<job_id>/stop")
def stop_download(job_id: str):
    job = _get_job(job_id)
    if not job:
        return jsonify({"error": "unknown job"}), 404
    job["stop"].set()
    return jsonify({"ok": True})


if __name__ == "__main__":
    import webbrowser

    port = 8765
    url = f"http://127.0.0.1:{port}"
    print(f"YouTube Downloadr web UI v{APP_VERSION}")
    print(f"Open {url} in your browser")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
