#!/usr/bin/env python3
"""
YouTube Downloadr — YouTube → M4A / MP4 via yt-dlp

deps (auto-installed on first launch):
  yt-dlp, customtkinter, pillow
also required:
  ffmpeg on PATH (audio convert / cover embed / MP4 mux)
"""

from __future__ import annotations

import html
import importlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

# ── App identity / updates ────────────────────────────────────────────────────
APP_VERSION = "1.0.0"
GITHUB_REPO = "Afrsto/YouTube-Downloader"
GITHUB_LATEST_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_UA = f"YouTube-Downloader/{APP_VERSION} (+https://github.com/{GITHUB_REPO})"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"

CONTACT_TELEGRAM = "https://t.me/X2_616"
CONTACT_DISCORD_USER = "https://discord.com/users/994817247061225633"
CONTACT_DISCORD_SERVER = "https://discord.gg/btRCeujadA"

VIDEO_HEIGHTS = (144, 240, 360, 480, 720, 1080, 1440, 2160)
AUDIO_BITRATES = (64, 96, 128, 160, 192, 256, 320)

# ── Python version gate (before heavy imports) ────────────────────────────────
_MIN_PY = (3, 9)


def _show_fatal(title: str, message: str) -> None:
    print(message, file=sys.stderr)
    try:
        import tkinter as _tk
        from tkinter import messagebox as _mb

        root = _tk.Tk()
        root.withdraw()
        try:
            root.attributes("-topmost", True)
        except Exception:
            pass
        _mb.showerror(title, message)
        root.destroy()
    except Exception:
        pass


def _check_python() -> None:
    if sys.version_info >= _MIN_PY:
        return
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    need = f"{_MIN_PY[0]}.{_MIN_PY[1]}"
    _show_fatal(
        "YouTube Downloadr — Python version",
        f"This script requires Python {need} or newer.\n\n"
        f"You are running Python {ver}.\n\n"
        f"Please install Python {need}+ from https://www.python.org/downloads/\n"
        f"and run this script with that interpreter.",
    )
    sys.exit(1)


def _pkg_missing(mod_name: str) -> bool:
    try:
        importlib.import_module(mod_name)
        return False
    except ImportError:
        return True


def _is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _ensure_dependencies() -> None:
    """Install required pip packages on first launch if missing.

    Skipped when frozen (PyInstaller): deps are bundled, and runtime pip
    install is unreliable and looks suspicious to antivirus heuristics.
    """
    if _is_frozen():
        return

    # import name → pip name
    required = [
        ("yt_dlp", "yt-dlp"),
        ("customtkinter", "customtkinter"),
        ("PIL", "pillow"),
        ("mutagen", "mutagen"),
    ]
    missing_pip = [pip for mod, pip in required if _pkg_missing(mod)]
    if not missing_pip:
        return

    print(
        "YouTube Downloadr: installing missing packages:",
        ", ".join(missing_pip),
        flush=True,
    )
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", *missing_pip],
        )
    except Exception as e:
        _show_fatal(
            "YouTube Downloadr — dependencies",
            "Could not install required packages:\n"
            f"  {', '.join(missing_pip)}\n\n"
            f"Error: {e}\n\n"
            f"Try manually:\n"
            f"  {sys.executable} -m pip install yt-dlp customtkinter pillow mutagen",
        )
        sys.exit(1)

    still = [pip for mod, pip in required if _pkg_missing(mod)]
    if still:
        _show_fatal(
            "YouTube Downloadr — dependencies",
            "Packages are still missing after install:\n"
            f"  {', '.join(still)}\n\n"
            f"Try manually:\n"
            f"  {sys.executable} -m pip install yt-dlp customtkinter pillow mutagen",
        )
        sys.exit(1)


_check_python()
_ensure_dependencies()

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog

import yt_dlp
from yt_dlp.utils import DownloadError

try:
    from PIL import Image

    _PIL_OK = True
except ImportError:
    Image = None  # type: ignore
    _PIL_OK = False

try:
    from mutagen.mp4 import MP4, MP4Cover

    _MUTAGEN_OK = True
except ImportError:
    MP4 = None  # type: ignore
    MP4Cover = None  # type: ignore
    _MUTAGEN_OK = False

_YTDLP_OK = True
_YTDLP_VER = getattr(yt_dlp.version, "__version__", "?")

_FFMPEG = shutil.which("ffmpeg") or (
    r"C:\ffmpeg\bin\ffmpeg.exe" if os.path.isfile(r"C:\ffmpeg\bin\ffmpeg.exe") else None
)
_FFMPEG_OK = bool(_FFMPEG and os.path.isfile(_FFMPEG))

# ── YouTube logo palette ──────────────────────────────────────────────────────
C = {
    "bg":    "#0f0f0f",
    "b1":    "#212121",
    "b2":    "#272727",
    "b3":    "#3f3f3f",
    "bdr":   "#3f3f3f",
    "acc":   "#c62828",
    "acc_h": "#8e0000",
    "acc2":  "#8b1a1a",
    "acc2_h": "#5c1010",
    "txt":   "#ffffff",
    "dim":   "#aaaaaa",
    "grn":   "#2ba640",
    "grn_h": "#228b36",
    "red":   "#e57373",
    "ylw":   "#f5c518",
    "blu":   "#3ea6ff",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


def center_window(win, width: int, height: int, master=None) -> None:
    """Place a window at the center of its parent (or the screen)."""
    try:
        win.update_idletasks()
    except Exception:
        pass
    width = int(width)
    height = int(height)
    x = y = None
    if master is not None:
        try:
            master.update_idletasks()
            mx = int(master.winfo_rootx())
            my = int(master.winfo_rooty())
            mw = int(master.winfo_width())
            mh = int(master.winfo_height())
            if mw > 1 and mh > 1:
                x = mx + (mw - width) // 2
                y = my + (mh - height) // 2
        except Exception:
            x = y = None
    if x is None or y is None:
        try:
            sw = int(win.winfo_screenwidth())
            sh = int(win.winfo_screenheight())
            x = (sw - width) // 2
            y = (sh - height) // 2
        except Exception:
            x, y = 100, 100
    win.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")


def _parse_version(text: str) -> tuple[int, ...]:
    t = (text or "").strip().lstrip("vV")
    parts = re.findall(r"\d+", t)
    if not parts:
        return (0,)
    return tuple(int(p) for p in parts)


def _version_lt(a: str, b: str) -> bool:
    """True if version a is strictly less than version b."""
    ta, tb = list(_parse_version(a)), list(_parse_version(b))
    n = max(len(ta), len(tb))
    ta += [0] * (n - len(ta))
    tb += [0] * (n - len(tb))
    return tuple(ta) < tuple(tb)


def _http_json(url: str, timeout: float = 20.0) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": GITHUB_UA,
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def _format_bytes(n: int | float | None) -> str:
    if n is None or n <= 0:
        return "unknown"
    n = float(n)
    for unit, div in (("GB", 1024**3), ("MB", 1024**2), ("KB", 1024)):
        if n >= div:
            return f"{n / div:.1f} {unit}"
    return f"{int(n)} B"


def _height_label(h: int) -> str:
    if h >= 2160:
        return f"{h}p (4K)"
    if h >= 1440:
        return f"{h}p (2K)"
    return f"{h}p"


def check_github_update() -> dict:
    """
    Return dict:
      status: 'ok' | 'update' | 'error'
      latest, notes, asset_url, asset_name, error
    """
    try:
        data = _http_json(GITHUB_LATEST_API)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"status": "ok", "latest": APP_VERSION}
        return {"status": "error", "error": f"GitHub HTTP {e.code}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

    tag = str(data.get("tag_name") or "").strip()
    if not tag:
        return {"status": "ok", "latest": APP_VERSION}
    if not _version_lt(APP_VERSION, tag):
        return {"status": "ok", "latest": tag.lstrip("vV")}

    assets = data.get("assets") or []
    asset_url = ""
    asset_name = ""
    for a in assets:
        name = str(a.get("name") or "")
        url = a.get("browser_download_url") or ""
        if not url or not name.lower().endswith(".exe"):
            continue
        if "setup" in name.lower():
            asset_url, asset_name = url, name
            break
        if not asset_url:
            asset_url, asset_name = url, name
    if not asset_url:
        return {
            "status": "error",
            "error": f"Update {tag} has no .exe Setup asset yet.",
        }
    notes = str(data.get("body") or "").strip() or "(No release notes.)"
    return {
        "status": "update",
        "latest": tag.lstrip("vV"),
        "tag": tag,
        "notes": notes,
        "asset_url": asset_url,
        "asset_name": asset_name,
    }


def download_update_file(url: str, dest: Path, progress=None) -> Path:
    req = urllib.request.Request(url, headers={"User-Agent": GITHUB_UA})
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(256 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress and total:
                    progress(done / total * 100.0)
    if progress:
        progress(100.0)
    return dest


# ══════════════════════════════════════════════════════════════════════════════
#  Download backend (yt-dlp)
# ══════════════════════════════════════════════════════════════════════════════
class Downloader:
    """YouTube downloader powered by yt-dlp + ffmpeg."""

    class _Abort(Exception):
        pass

    @staticmethod
    def vid_id(url: str) -> str:
        m = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", url)
        return m.group(1) if m else "video"

    @staticmethod
    def sanitize(name: str) -> str:
        name = re.sub(r"\s*prod\.[A-Za-z0-9_-]+", "", name, flags=re.IGNORECASE)
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
        return (name or "video")[:120]

    def get_title(self, yt_url: str, log) -> str:
        if not _YTDLP_OK:
            return ""
        try:
            opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
            }
            if _FFMPEG:
                opts["ffmpeg_location"] = os.path.dirname(_FFMPEG)
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(yt_url, download=False)
            title = (info or {}).get("title") or ""
            return self.sanitize(title)
        except Exception as e:
            log(f"⚠ title lookup failed: {e}")
            return ""

    def search(self, query: str, limit: int = 12) -> list[dict]:
        """Flat YouTube search via yt-dlp. Returns list of result dicts."""
        if not _YTDLP_OK:
            raise RuntimeError("yt-dlp is not installed.\nRun:  pip install yt-dlp")
        q = (query or "").strip()
        if not q:
            raise ValueError("empty search query")
        opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{q}", download=False)
        out: list[dict] = []
        for e in (info or {}).get("entries") or []:
            if not e:
                continue
            vid = e.get("id") or ""
            if not vid or len(vid) != 11:
                url = e.get("url") or e.get("webpage_url") or ""
                m = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", url)
                vid = m.group(1) if m else ""
            if not vid:
                continue
            thumb = None
            thumbs = e.get("thumbnails") or []
            if thumbs:
                thumb = thumbs[-1].get("url")
            if not thumb:
                thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
            dur = e.get("duration")
            out.append(
                {
                    "id": vid,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "title": e.get("title") or "Untitled",
                    "uploader": e.get("uploader") or e.get("channel") or "",
                    "duration": dur,
                    "thumbnail": thumb,
                }
            )
        return out

    @staticmethod
    def format_duration(seconds) -> str:
        try:
            s = int(seconds)
        except (TypeError, ValueError):
            return ""
        if s < 0:
            return ""
        h, rem = divmod(s, 3600)
        m, sec = divmod(rem, 60)
        if h:
            return f"{h}:{m:02d}:{sec:02d}"
        return f"{m}:{sec:02d}"

    def _base_opts(self) -> dict:
        opts: dict = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
        }
        if _FFMPEG:
            opts["ffmpeg_location"] = os.path.dirname(_FFMPEG)
        return opts

    @staticmethod
    def _format_selector(fmt: str, quality: str) -> tuple[str, list[str] | None]:
        if fmt == "mp3":
            return "bestaudio[ext=m4a]/bestaudio/best", [f"abr~{quality}", "abr"]
        h = int(quality)
        # Prefer progressive HTTPS (known filesize) over HLS/m3u8.
        sel = (
            f"bestvideo[height<={h}][ext=mp4][protocol^=http]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={h}][protocol^=http]+bestaudio/"
            f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/"
            f"bestvideo[height<={h}]+bestaudio/"
            f"best[height<={h}]/best"
        )
        return sel, None

    def probe_capabilities(self, yt_url: str) -> dict:
        """Return available max height, audio abrs, and raw formats list."""
        if not _YTDLP_OK:
            raise RuntimeError("yt-dlp is not installed.")
        opts = self._base_opts()
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)
        formats = (info or {}).get("formats") or []
        heights: set[int] = set()
        abrs: list[float] = []
        for f in formats:
            h = f.get("height")
            if isinstance(h, int) and h > 0:
                heights.add(h)
            # audio-ish
            acodec = f.get("acodec") or "none"
            vcodec = f.get("vcodec") or "none"
            abr = f.get("abr") or f.get("tbr")
            if acodec != "none" and (vcodec == "none" or not f.get("height")):
                try:
                    abrs.append(float(abr))
                except (TypeError, ValueError):
                    pass
        max_h = max(heights) if heights else 0
        max_abr = max(abrs) if abrs else 0.0
        return {
            "title": (info or {}).get("title") or "",
            "heights": sorted(heights),
            "max_height": max_h,
            "max_abr": max_abr,
            "info": info,
        }

    def estimate_download_size(self, yt_url: str, fmt: str, quality: str) -> int | None:
        """Best-effort total bytes for the selected format (None if unknown)."""
        if not _YTDLP_OK:
            raise RuntimeError("yt-dlp is not installed.")
        selector, sort = self._format_selector(fmt, quality)
        opts = self._base_opts()
        opts["format"] = selector
        if sort:
            opts["format_sort"] = sort
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(yt_url, download=False)

        duration = None
        try:
            duration = float((info or {}).get("duration") or 0) or None
        except (TypeError, ValueError):
            duration = None

        def _one(entry: dict | None) -> int:
            if not entry:
                return 0
            n = entry.get("filesize") or entry.get("filesize_approx") or 0
            try:
                n = int(n)
            except (TypeError, ValueError):
                n = 0
            if n > 0:
                return n
            # Fallback: tbr (kbps) * duration → bytes
            try:
                tbr = float(entry.get("tbr") or 0)
            except (TypeError, ValueError):
                tbr = 0.0
            try:
                dur = float(entry.get("duration") or 0) or duration or 0.0
            except (TypeError, ValueError):
                dur = duration or 0.0
            if tbr > 0 and dur > 0:
                return int(tbr * 1000.0 / 8.0 * dur)
            return 0

        # Prefer summing merged streams; top-level filesize_approx is often audio-only.
        req = (info or {}).get("requested_formats") or []
        if req:
            total = sum(_one(x) for x in req)
        else:
            total = _one(info)
        return total if total > 0 else None

    def resolve_quality(self, yt_url: str, fmt: str, quality: str) -> tuple[str, str | None]:
        """
        Return (effective_quality, message_if_downgraded).
        message is None when requested quality is available / acceptable.
        """
        caps = self.probe_capabilities(yt_url)
        if fmt == "mp3":
            want = int(quality)
            max_abr = caps["max_abr"]
            if max_abr <= 0:
                return quality, None
            # If user asks higher than anything listed, clamp to nearest offered rung <= max
            available = [b for b in AUDIO_BITRATES if b <= max_abr + 32]
            if not available:
                available = list(AUDIO_BITRATES)
            best = max(available)
            if want > best:
                return str(best), (
                    f"{want} kbps is not available for this video.\n"
                    f"Highest available audio quality: {best} kbps."
                )
            return quality, None

        want_h = int(quality)
        max_h = int(caps["max_height"] or 0)
        if max_h <= 0:
            return quality, None
        # Clamp to highest ladder step that does not exceed stream max
        ladder = [h for h in VIDEO_HEIGHTS if h <= max_h]
        if not ladder:
            ladder = [max_h]
        best = max(ladder)
        # Also allow exact max_h if between ladder steps (e.g. 1440 when max is 1440)
        if max_h > best:
            best = max_h
        if want_h > max_h:
            label_want = _height_label(want_h)
            label_best = _height_label(best)
            return str(best), (
                f"{label_want} is not available for this video.\n"
                f"Highest available quality: {label_best}."
            )
        return quality, None

    @staticmethod
    def _vtt_to_lyrics(text: str) -> str:
        """Strip WebVTT / SRT timing into plain lyrics lines."""
        lines_out: list[str] = []
        seen: set[str] = set()
        for raw in (text or "").splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.upper().startswith("WEBVTT"):
                continue
            if line.startswith("NOTE") or line.startswith("STYLE") or line.startswith("REGION"):
                continue
            if re.match(r"^\d+$", line):
                continue
            if re.search(r"\d{2}:\d{2}:\d{2}[\.,]\d{3}\s*-->", line):
                continue
            if re.search(r"\d{2}:\d{2}[\.,]\d{3}\s*-->", line):
                continue
            # Drop simple VTT tags
            clean = re.sub(r"<[^>]+>", "", line).strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            lines_out.append(clean)
        return "\n".join(lines_out).strip()

    def _subtitle_paths_from_info(self, info: dict | None) -> list[Path]:
        """Collect on-disk caption paths recorded by yt-dlp in the info dict."""
        paths: list[Path] = []
        if not info:
            return paths
        requested = info.get("requested_subtitles") or {}
        if isinstance(requested, dict):
            for _lang, meta in requested.items():
                if not isinstance(meta, dict):
                    continue
                fp = meta.get("filepath") or meta.get("file")
                if fp and os.path.isfile(fp):
                    paths.append(Path(fp))
        for key in ("requested_downloads",):
            entries = info.get(key) or []
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                for subkey in ("requested_subtitles",):
                    subs = entry.get(subkey) or {}
                    if not isinstance(subs, dict):
                        continue
                    for _lang, meta in subs.items():
                        if isinstance(meta, dict):
                            fp = meta.get("filepath") or meta.get("file")
                            if fp and os.path.isfile(fp):
                                paths.append(Path(fp))
        return paths

    def _find_subtitle_file(
        self,
        out_dir: str,
        dest_base: str,
        info: dict | None = None,
    ) -> Path | None:
        from_info = self._subtitle_paths_from_info(info)
        if from_info:
            from_info.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            return from_info[0]

        base = Path(out_dir)
        exts = (".vtt", ".srt", ".ttml", ".srv3")
        found: list[Path] = []
        for pat in (
            f"{dest_base}*.vtt",
            f"{dest_base}*.srt",
            f"{dest_base}*.ttml",
            f"{dest_base}*.srv3",
        ):
            found.extend(base.glob(pat))
        if not found:
            try:
                cutoff = time.time() - 600
                for p in base.iterdir():
                    if (
                        p.is_file()
                        and p.suffix.lower() in exts
                        and p.stat().st_mtime >= cutoff
                    ):
                        found.append(p)
            except OSError:
                pass
        if not found:
            return None

        def _rank(p: Path) -> tuple[int, float]:
            name = p.name.lower()
            auto = 1 if (".auto." in name or name.endswith(".auto.vtt")) else 0
            return (auto, -p.stat().st_mtime)

        found.sort(key=_rank)
        return found[0]

    def _embed_lyrics_m4a(self, m4a_path: str, lyrics: str, log) -> bool:
        if not lyrics.strip():
            return False
        if not _MUTAGEN_OK or MP4 is None:
            log("⚠ mutagen missing — cannot embed lyrics (pip install mutagen)")
            return False
        try:
            audio = MP4(m4a_path)
            audio["\xa9lyr"] = [lyrics]
            audio.save()
            return True
        except Exception as e:
            log(f"⚠ lyrics embed failed: {e}")
            return False

    def _embed_lyrics_after_download(
        self,
        out_dir: str,
        dest_base: str,
        final: str,
        log,
        info: dict | None = None,
    ) -> None:
        sub = self._find_subtitle_file(out_dir, dest_base, info=info)
        if not sub:
            log("⚠ no lyrics/captions found")
            return
        try:
            raw = sub.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            log(f"⚠ could not read captions: {e}")
            return
        lyrics = self._vtt_to_lyrics(raw)
        if not lyrics:
            log("⚠ captions empty after cleanup")
            return
        if self._embed_lyrics_m4a(final, lyrics, log):
            log(f"── lyrics embedded ({sub.name})")
        try:
            for p in Path(out_dir).glob(f"{dest_base}.*"):
                if p.suffix.lower() in (".vtt", ".srt", ".ttml", ".srv3"):
                    p.unlink(missing_ok=True)
            if sub.exists() and sub.suffix.lower() in (".vtt", ".srt", ".ttml", ".srv3"):
                sub.unlink(missing_ok=True)
        except Exception:
            pass

    def download(
        self,
        yt_url: str,
        fmt: str,
        quality: str,
        out_dir: str,
        dest_base: str,
        prog,
        log,
        stop: threading.Event,
    ) -> str:
        """Download and convert. Returns final file path."""
        if not _YTDLP_OK:
            raise RuntimeError(
                "yt-dlp is not installed.\n"
                "Run:  pip install yt-dlp"
            )
        if fmt == "mp3" and not _FFMPEG_OK:
            raise RuntimeError(
                "ffmpeg not found — required for audio convert / cover embed.\n"
                "Install ffmpeg and ensure it is on PATH."
            )
        if stop.is_set():
            raise InterruptedError

        outtmpl = os.path.join(out_dir, dest_base + ".%(ext)s")
        opts: dict = {
            "outtmpl": outtmpl,
            "noprogress": True,
            "quiet": True,
            "no_warnings": True,
            "retries": 3,
            "fragment_retries": 3,
            "overwrites": True,
            "writethumbnail": True,
            "progress_hooks": [self._make_progress_hook(prog, log, stop)],
            "postprocessor_hooks": [self._make_pp_hook(prog, log, stop)],
        }
        if _FFMPEG:
            opts["ffmpeg_location"] = os.path.dirname(_FFMPEG)

        # YouTube thumbs are often .webp — convert then embed as cover art.
        # EmbedThumbnail must run AFTER FFmpegMetadata: Metadata remux strips m4a covers.
        thumb_pps = [
            {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
        ]
        meta_then_cover = [
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ]

        if fmt == "mp3":
            # M4A (MP4 container) so Windows Explorer shows cover like video files.
            selector, sort = self._format_selector(fmt, quality)
            opts["format"] = selector
            opts["format_sort"] = sort
            opts["postprocessors"] = thumb_pps + meta_then_cover
            # Captions → lyrics embed. Prefer a few langs (not "all") to avoid
            # rate-limit 429s on obscure auto-translate codes like ab-ar.
            # ignoreerrors=True is required so a failed caption fetch does not
            # abort the audio download (only_download still raises on subs).
            opts["writesubtitles"] = True
            opts["writeautomaticsub"] = True
            opts["subtitleslangs"] = ["en", "en-US", "en-GB", "ar", "ar-SA"]
            opts["subtitlesformat"] = "vtt/best"
            opts["sleep_interval_subtitles"] = 1
            opts["ignoreerrors"] = True
            log("── audio container: m4a (Explorer cover + lyrics)")
        else:
            selector, _ = self._format_selector(fmt, quality)
            opts["format"] = selector
            opts["merge_output_format"] = "mp4"
            opts["postprocessors"] = thumb_pps + meta_then_cover
            if not _FFMPEG_OK:
                log("⚠ ffmpeg missing — may fall back to single-file formats")

        fmt_label = "M4A" if fmt == "mp3" else fmt.upper()
        log(f"── yt-dlp starting ({fmt_label} @ {quality})")
        prog(2)

        info: dict | None = None
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(yt_url, download=True)
                if stop.is_set():
                    raise InterruptedError
                final = ydl.prepare_filename(info)
                if fmt == "mp3":
                    root = os.path.splitext(final)[0]
                    for ext in (".m4a", ".mp4", ".aac"):
                        candidate = root + ext
                        if os.path.isfile(candidate):
                            final = candidate
                            break
                    else:
                        final = root + ".m4a"
                elif fmt == "mp4":
                    root, _ = os.path.splitext(final)
                    candidate = root + ".mp4"
                    if os.path.isfile(candidate):
                        final = candidate
        except self._Abort:
            raise InterruptedError
        except DownloadError as e:
            msg = str(e)
            if stop.is_set() or "abort" in msg.lower():
                raise InterruptedError
            raise RuntimeError(msg) from e

        if not os.path.isfile(final):
            stem = dest_base
            matches = sorted(
                Path(out_dir).glob(stem + ".*"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            matches = [
                p for p in matches
                if p.suffix.lower() in (".m4a", ".mp4", ".mp3", ".webm", ".aac")
            ]
            if matches:
                final = str(matches[0])
            else:
                raise RuntimeError(f"Download finished but file not found:\n{final}")

        if fmt == "mp3":
            prog(97)
            self._embed_lyrics_after_download(
                out_dir, dest_base, final, log, info=info
            )

        prog(100)
        return final

    def _make_progress_hook(self, prog, log, stop: threading.Event):
        last_pct = [-1]

        def hook(d: dict):
            if stop.is_set():
                raise Downloader._Abort("cancelled")
            status = d.get("status")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                done = d.get("downloaded_bytes") or 0
                if total:
                    pct = int(done / total * 70) + 5
                    if pct != last_pct[0]:
                        last_pct[0] = pct
                        prog(pct)
                speed = d.get("_speed_str") or d.get("speed")
                eta = d.get("_eta_str") or ""
                if isinstance(speed, (int, float)) and speed:
                    speed = f"{speed / 1024 / 1024:.1f} MB/s"
                frag = d.get("_percent_str") or ""
                if frag and last_pct[0] % 8 == 0:
                    log(f"   ↓ {frag.strip()}  {speed or ''}  {eta}".rstrip())
            elif status == "finished":
                prog(76)
                name = os.path.basename(d.get("filename") or "")
                log(f"── downloaded: {name}")
            elif status == "error":
                log(f"✗ download error: {d}")

        return hook

    def _make_pp_hook(self, prog, log, stop: threading.Event):
        def hook(d: dict):
            if stop.is_set():
                raise Downloader._Abort("cancelled")
            status = d.get("status")
            pp = d.get("postprocessor") or "post"
            if status == "started":
                prog(82)
                log(f"── post-process: {pp}...")
            elif status == "finished":
                prog(95)
                log(f"── post-process done: {pp}")

        return hook


# ══════════════════════════════════════════════════════════════════════════════
#  Shared dialogs
# ══════════════════════════════════════════════════════════════════════════════
class ConfirmDialog(ctk.CTkToplevel):
    """Modal Yes / No dialog. result is True / False / None (closed)."""

    def __init__(self, master, title: str, message: str, yes="Yes", no="No"):
        super().__init__(master)
        self.title(title)
        self.minsize(400, 180)
        self.configure(fg_color=C["bg"])
        self.transient(master)
        self.grab_set()
        self.result: bool | None = None
        self.protocol("WM_DELETE_WINDOW", self._no)
        center_window(self, 460, 220, master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(
            self, text=message, justify="left", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C["txt"], wraplength=400,
        ).grid(row=0, column=0, sticky="nsew", padx=22, pady=(22, 10))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=1, column=0, sticky="e", padx=22, pady=(0, 18))
        ctk.CTkButton(
            row, text=no, width=100, height=36, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Semibold", size=13),
            fg_color=C["b3"], hover_color=C["bdr"], text_color=C["txt"],
            command=self._no,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            row, text=yes, width=100, height=36, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Semibold", size=13),
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=self._yes,
        ).pack(side="left")

        self.after(40, self.focus_force)

    def _yes(self):
        self.result = True
        self.destroy()

    def _no(self):
        self.result = False
        self.destroy()

    def ask(self) -> bool:
        self.wait_window()
        return bool(self.result)


class UpdateRequiredDialog(ctk.CTkToplevel):
    """Mandatory update — no Skip / later. Download update or Exit."""

    def __init__(self, master, info: dict):
        super().__init__(master)
        self.master_app = master
        self.info = info
        self.title("Update required")
        self.minsize(480, 360)
        self.configure(fg_color=C["bg"])
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._exit_app)
        center_window(self, 560, 420, master)
        self._busy = False

        latest = info.get("latest") or "?"
        notes = info.get("notes") or ""
        # Strip crude markdown-ish noise for display
        notes_plain = re.sub(r"[#*_`]+", "", notes)
        notes_plain = html.unescape(notes_plain)[:1200]

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self, text="A mandatory update is available",
            font=ctk.CTkFont(family="Segoe UI Semibold", size=18),
            text_color=C["acc"],
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 4))

        ctk.CTkLabel(
            self,
            text=f"Installed: v{APP_VERSION}    →    Latest: v{latest}\n"
                 "You must install this update before using the app.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C["dim"], justify="left",
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 8))

        box = ctk.CTkTextbox(
            self, font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=C["b1"], text_color=C["txt"], corner_radius=10,
        )
        box.grid(row=2, column=0, sticky="nsew", padx=20, pady=6)
        box.insert("1.0", notes_plain or "(No release notes.)")
        box.configure(state="disabled")

        self._status = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=C["blu"], anchor="w",
        )
        self._status.grid(row=3, column=0, sticky="ew", padx=20, pady=(4, 0))

        self._pbar = ctk.CTkProgressBar(
            self, height=10, corner_radius=6,
            progress_color=C["acc"], fg_color=C["b1"],
        )
        self._pbar.grid(row=4, column=0, sticky="ew", padx=20, pady=(6, 4))
        self._pbar.set(0)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=5, column=0, sticky="e", padx=20, pady=(8, 18))
        ctk.CTkButton(
            row, text="Exit", width=100, height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Semibold", size=13),
            fg_color=C["b3"], hover_color=C["bdr"], text_color=C["txt"],
            command=self._exit_app,
        ).pack(side="left", padx=(0, 8))
        self._btn_dl = ctk.CTkButton(
            row, text="Download update", width=160, height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Semibold", size=13),
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=self._start_download,
        )
        self._btn_dl.pack(side="left")

        self.after(40, self.focus_force)

    def _exit_app(self):
        try:
            self.master_app.destroy()
        except Exception:
            pass
        sys.exit(0)

    def _start_download(self):
        if self._busy:
            return
        self._busy = True
        self._btn_dl.configure(state="disabled")
        self._status.configure(text="Downloading update…", text_color=C["blu"])
        threading.Thread(target=self._download_thread, daemon=True).start()

    def _download_thread(self):
        try:
            name = self.info.get("asset_name") or "YouTube Downloader Setup.exe"
            dest = Path(tempfile.gettempdir()) / name
            url = self.info["asset_url"]

            def prog(v):
                self.after(0, lambda: self._pbar.set(max(0.0, min(1.0, v / 100.0))))

            download_update_file(url, dest, progress=prog)
            self.after(0, self._launch_and_exit, dest)
        except Exception as e:
            self.after(0, self._fail, str(e))

    def _fail(self, err: str):
        self._busy = False
        self._btn_dl.configure(state="normal")
        self._status.configure(text=f"Download failed: {err}", text_color=C["red"])

    def _launch_and_exit(self, path: Path):
        self._status.configure(text="Starting installer…", text_color=C["grn"])
        try:
            os.startfile(str(path))  # type: ignore[attr-defined]
        except Exception:
            subprocess.Popen([str(path)], shell=True)
        self._exit_app()


class UpdateCheckFailedDialog(ctk.CTkToplevel):
    """Network/API failure — Retry or Exit (no silent bypass of known policy)."""

    def __init__(self, master, error: str):
        super().__init__(master)
        self.master_app = master
        self.result = "exit"  # retry | exit | continue
        self.title("Update check failed")
        self.configure(fg_color=C["bg"])
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._exit)
        center_window(self, 480, 240, master)

        ctk.CTkLabel(
            self, text="Could not check for mandatory updates",
            font=ctk.CTkFont(family="Segoe UI Semibold", size=16),
            text_color=C["ylw"],
        ).pack(anchor="w", padx=20, pady=(18, 6))
        ctk.CTkLabel(
            self,
            text=f"{error}\n\nRetry when you are online, or Exit.",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C["dim"], justify="left", wraplength=420,
        ).pack(anchor="w", padx=20, pady=(0, 12))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="e", padx=20, pady=(0, 18))
        ctk.CTkButton(
            row, text="Exit", width=100, height=36, corner_radius=10,
            fg_color=C["b3"], hover_color=C["bdr"], text_color=C["txt"],
            command=self._exit,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            row, text="Continue offline", width=140, height=36, corner_radius=10,
            fg_color=C["b3"], hover_color=C["bdr"], text_color=C["txt"],
            command=self._continue,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            row, text="Retry", width=100, height=36, corner_radius=10,
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=self._retry,
        ).pack(side="left")

    def _exit(self):
        self.result = "exit"
        self.destroy()

    def _retry(self):
        self.result = "retry"
        self.destroy()

    def _continue(self):
        # Allowed only when check itself failed (no known pending update).
        self.result = "continue"
        self.destroy()

    def ask(self) -> str:
        self.wait_window()
        return self.result


class AboutDialog(ctk.CTkToplevel):
    """Professional About panel with contacts."""

    def __init__(self, master):
        super().__init__(master)
        self.title("About")
        self.minsize(480, 420)
        self.configure(fg_color=C["bg"])
        self.transient(master)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        center_window(self, 520, 480, master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self, text="About",
            font=ctk.CTkFont(family="Segoe UI Semibold", size=18),
            text_color=C["acc"],
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(18, 4))

        ctk.CTkLabel(
            self,
            text=f"YouTube Downloadr  v{APP_VERSION}",
            font=ctk.CTkFont(family="Segoe UI Semibold", size=16),
            text_color=C["txt"],
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 2))

        ctk.CTkLabel(
            self,
            text=(
                "A focused Windows app for downloading YouTube media as M4A audio "
                "or MP4 video. Powered by yt-dlp with ffmpeg for conversion, cover "
                "art, and muxing.\n\n"
                "Features:\n"
                "• Full quality ladder (144p–4K / 64–320 kbps)\n"
                "• Estimated size confirmation before download\n"
                "• Smart fallback when a quality is unavailable\n"
                "• Mandatory updates via GitHub Releases\n"
                "• Built-in YouTube search"
            ),
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=C["dim"], justify="left", wraplength=460, anchor="w",
        ).grid(row=2, column=0, sticky="ew", padx=22, pady=(8, 6))

        runtime = (
            f"Runtime: yt-dlp {_YTDLP_VER}  ·  "
            f"ffmpeg {'OK' if _FFMPEG_OK else 'missing'}  ·  "
            f"Python {sys.version_info.major}.{sys.version_info.minor}"
        )
        ctk.CTkLabel(
            self, text=runtime,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=C["blu"], anchor="w",
        ).grid(row=3, column=0, sticky="nw", padx=22, pady=(4, 4))

        links = ctk.CTkFrame(self, fg_color="transparent")
        links.grid(row=4, column=0, sticky="ew", padx=22, pady=(8, 4))
        ctk.CTkButton(
            links, text="Open GitHub", width=120, height=32, corner_radius=8,
            fg_color=C["b3"], hover_color=C["bdr"], text_color=C["txt"],
            command=lambda: webbrowser.open(GITHUB_URL),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            links, text="Telegram", width=100, height=32, corner_radius=8,
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=lambda: webbrowser.open(CONTACT_TELEGRAM),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            links, text="Discord User", width=110, height=32, corner_radius=8,
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=lambda: webbrowser.open(CONTACT_DISCORD_USER),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            links, text="Discord Server", width=120, height=32, corner_radius=8,
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=lambda: webbrowser.open(CONTACT_DISCORD_SERVER),
        ).pack(side="left")

        ctk.CTkButton(
            self, text="Close", width=100, height=36, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Semibold", size=13),
            fg_color=C["b3"], hover_color=C["bdr"], text_color=C["txt"],
            command=self.destroy,
        ).grid(row=5, column=0, sticky="e", padx=22, pady=(12, 18))

        self.after(40, self.focus_force)


# ══════════════════════════════════════════════════════════════════════════════
#  Search dialog
# ══════════════════════════════════════════════════════════════════════════════
class SearchDialog(ctk.CTkToplevel):
    def __init__(self, master: "App"):
        super().__init__(master)
        self.master_app = master
        self.title("Search YouTube")
        self.minsize(560, 420)
        self.configure(fg_color=C["bg"])
        self.transient(master)
        self.grab_set()
        self.focus_force()
        center_window(self, 720, 560, master)

        self._images: list = []
        self._busy = False
        self._thumb_gen = 0

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self, text="Search YouTube",
            font=ctk.CTkFont(family="Segoe UI Semibold", size=18),
            text_color=C["acc"],
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 8))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 8))
        row.grid_columnconfigure(0, weight=1)

        self._q = ctk.CTkEntry(
            row, height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=C["b1"], border_color=C["bdr"],
            text_color=C["txt"], placeholder_text="Video name…",
        )
        self._q.grid(row=0, column=0, sticky="ew")
        self._q.bind("<Return>", lambda _e: self._run_search())
        self.master_app._attach_entry_menu(self._q)

        ctk.CTkButton(
            row, text="Search", width=100, height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Semibold", size=13),
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=self._run_search,
        ).grid(row=0, column=1, padx=(8, 0))

        self._status = ctk.CTkLabel(
            self, text="Type a name and hit Search",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=C["dim"], anchor="w",
        )
        self._status.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 4))

        self._results = ctk.CTkScrollableFrame(
            self, fg_color=C["b1"], corner_radius=12,
            border_width=1, border_color=C["bdr"],
        )
        self._results.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 16))

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(60, self._q.focus_set)

    def _on_close(self):
        self._thumb_gen += 1
        self.destroy()

    def _alive(self) -> bool:
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def _clear_results(self):
        self._thumb_gen += 1
        for w in self._results.winfo_children():
            w.destroy()
        self._images.clear()

    def _run_search(self):
        if self._busy:
            return
        q = self._q.get().strip()
        if not q:
            self._status.configure(text="Enter a video name", text_color=C["ylw"])
            return
        if not _YTDLP_OK:
            self._status.configure(text="yt-dlp missing — pip install yt-dlp", text_color=C["red"])
            return

        self._busy = True
        self._status.configure(text="Searching…", text_color=C["blu"])
        self._clear_results()
        threading.Thread(target=self._search_thread, args=(q,), daemon=True).start()

    def _search_thread(self, query: str):
        try:
            results = self.master_app.api.search(query, limit=12)
            self.after(0, self._show_results, results)
        except Exception as e:
            self.after(0, self._search_failed, str(e))

    def _search_failed(self, err: str):
        if not self._alive():
            return
        self._busy = False
        try:
            self._status.configure(text=f"Search failed: {err}", text_color=C["red"])
        except tk.TclError:
            pass

    def _show_results(self, results: list[dict]):
        if not self._alive():
            return
        self._busy = False
        try:
            if not results:
                self._status.configure(text="No results", text_color=C["ylw"])
                return
            self._status.configure(
                text=f"{len(results)} result(s) — click one to select",
                text_color=C["grn"],
            )
        except tk.TclError:
            return

        if not _PIL_OK:
            self.master_app._log("⚠ pillow missing — search thumbs disabled (pip install pillow)")

        for item in results:
            self._add_row(item)

        if _PIL_OK:
            gen = self._thumb_gen
            threading.Thread(
                target=self._load_thumbs, args=(list(results), gen), daemon=True
            ).start()

    def _add_row(self, item: dict):
        row = ctk.CTkFrame(
            self._results, fg_color=C["b2"], corner_radius=10,
            border_width=1, border_color=C["bdr"],
        )
        row.pack(fill="x", padx=6, pady=5)
        row.grid_columnconfigure(1, weight=1)

        thumb_lbl = ctk.CTkLabel(
            row, text="", width=120, height=68,
            fg_color=C["bg"], corner_radius=6,
        )
        thumb_lbl.grid(row=0, column=0, rowspan=2, padx=8, pady=8, sticky="nw")
        row._thumb_lbl = thumb_lbl  # type: ignore
        row._vid_id = item["id"]  # type: ignore

        meta = []
        if item.get("uploader"):
            meta.append(item["uploader"])
        d = Downloader.format_duration(item.get("duration"))
        if d:
            meta.append(d)
        sub = "  ·  ".join(meta) if meta else item["url"]

        title_lbl = ctk.CTkLabel(
            row, text=item["title"],
            font=ctk.CTkFont(family="Segoe UI Semibold", size=13),
            text_color=C["txt"], anchor="w", justify="left",
            wraplength=480,
        )
        title_lbl.grid(row=0, column=1, sticky="ew", padx=(4, 8), pady=(10, 0))

        sub_lbl = ctk.CTkLabel(
            row, text=sub,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=C["dim"], anchor="w",
        )
        sub_lbl.grid(row=1, column=1, sticky="ew", padx=(4, 8), pady=(2, 10))

        def select(_e=None, it=item):
            self._select(it)

        for w in (row, thumb_lbl, title_lbl, sub_lbl):
            w.bind("<Button-1>", select)
            w.configure(cursor="hand2")

        ctk.CTkButton(
            row, text="Select", width=72, height=30, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=lambda it=item: self._select(it),
        ).grid(row=0, column=2, rowspan=2, padx=(0, 10))

    def _apply_thumb(self, lbl, img, gen: int):
        if gen != self._thumb_gen:
            return
        try:
            if lbl.winfo_exists():
                lbl.configure(image=img, text="")
        except tk.TclError:
            pass

    def _load_thumbs(self, results: list[dict], gen: int):
        by_id = {r["id"]: r for r in results}
        try:
            children = list(self._results.winfo_children())
        except tk.TclError:
            return

        for child in children:
            if gen != self._thumb_gen or not self._alive():
                return
            vid = getattr(child, "_vid_id", None)
            if not vid or vid not in by_id:
                continue
            url = by_id[vid].get("thumbnail")
            if not url:
                continue
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = resp.read()
                if gen != self._thumb_gen:
                    return
                img = Image.open(io.BytesIO(data)).convert("RGB")
                img.thumbnail((120, 68))
                cimg = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self._images.append(cimg)
                lbl = getattr(child, "_thumb_lbl", None)
                if lbl is not None:
                    self.after(0, self._apply_thumb, lbl, cimg, gen)
            except Exception:
                continue

    def _select(self, item: dict):
        self._thumb_gen += 1
        self.master_app.v_url.set(item["url"])
        self.master_app._log(f"── selected: {item['title']}")
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"YouTube Downloadr v{APP_VERSION}  ·  yt-dlp")
        self.geometry("880x740")
        self.minsize(720, 620)
        self.configure(fg_color=C["bg"])
        self._set_window_icon()

        self.api = Downloader()
        self._stop = threading.Event()
        self._running = False

        self.v_url = ctk.StringVar()
        self.v_fmt = ctk.StringVar(value="mp3")
        self.v_qmp3 = ctk.StringVar(value="320")
        self.v_qmp4 = ctk.StringVar(value="1080")
        self.v_out = ctk.StringVar(value=str(Path.home() / "Downloads"))
        self.v_prog = ctk.DoubleVar(value=0)
        self._update_ready = False
        self._ready_logged = False

        self._build()
        self._on_fmt()
        self.after(40, lambda: center_window(self, 880, 740))
        self.after(80, self._startup_check)
        self.after(120, self._run_mandatory_update_check)

    def _set_window_icon(self) -> None:
        """Use the app ICO for the window/taskbar when available."""
        candidates: list[Path] = []
        if _is_frozen():
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                candidates.append(Path(meipass) / "YouTube Downloader.ico")
            candidates.append(Path(sys.executable).with_name("YouTube Downloader.ico"))
        else:
            candidates.append(Path(__file__).resolve().parent / "YouTube Downloader.ico")
        for ico in candidates:
            if ico.is_file():
                try:
                    self.iconbitmap(str(ico))
                except Exception:
                    pass
                break

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        hdr = ctk.CTkFrame(self, fg_color=C["b1"], corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_propagate(False)

        brand = ctk.CTkFrame(hdr, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="w", padx=20, pady=12)
        ctk.CTkLabel(
            brand, text=f"YouTube Downloadr v{APP_VERSION}",
            font=ctk.CTkFont(family="Segoe UI Semibold", size=20),
            text_color=C["acc"],
        ).pack(side="left")
        ctk.CTkLabel(
            brand, text="  ·  yt-dlp",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=C["dim"],
        ).pack(side="left", pady=(4, 0))

        self._status_lbl = ctk.CTkLabel(
            hdr, text="checking…",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=C["dim"],
        )
        self._status_lbl.grid(row=0, column=2, sticky="e", padx=20)

        card = ctk.CTkFrame(
            self, fg_color=C["b2"], corner_radius=14,
            border_width=1, border_color=C["bdr"],
        )
        card.grid(row=1, column=0, sticky="ew", padx=16, pady=(14, 6))
        card.grid_columnconfigure(1, weight=1)

        def row_lbl(text, r):
            ctk.CTkLabel(
                card, text=text,
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=C["dim"], width=70, anchor="e",
            ).grid(row=r, column=0, sticky="e", padx=(18, 12), pady=10)

        # URL (+ Search Video only — paste via right-click)
        row_lbl("URL", 0)
        url_row = ctk.CTkFrame(card, fg_color="transparent")
        url_row.grid(row=0, column=1, sticky="ew", padx=(0, 18), pady=10)
        url_row.grid_columnconfigure(0, weight=1)
        self._url_entry = ctk.CTkEntry(
            url_row, textvariable=self.v_url,
            height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=C["bg"], border_color=C["bdr"],
            text_color=C["txt"], placeholder_text="https://www.youtube.com/watch?v=…",
        )
        self._url_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            url_row, text="Search Video", width=120, height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Semibold", size=12),
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=self._open_search,
        ).grid(row=0, column=1, padx=(8, 0))
        self._attach_entry_menu(self._url_entry)

        row_lbl("Format", 1)
        fmt_row = ctk.CTkFrame(card, fg_color="transparent")
        fmt_row.grid(row=1, column=1, sticky="w", pady=4)
        self._fmt_seg = ctk.CTkSegmentedButton(
            fmt_row,
            values=["M4A · audio", "MP4 · video"],
            command=self._on_fmt_seg,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=C["bg"],
            selected_color=C["acc"],
            selected_hover_color=C["acc_h"],
            unselected_color=C["b3"],
            unselected_hover_color=C["bdr"],
            text_color=C["txt"],
            height=34,
            corner_radius=10,
        )
        self._fmt_seg.set("M4A · audio")
        self._fmt_seg.pack(side="left")

        row_lbl("Quality", 2)
        self._qbox = ctk.CTkFrame(card, fg_color="transparent")
        self._qbox.grid(row=2, column=1, sticky="w", pady=4)

        self._qmp3 = ctk.CTkFrame(self._qbox, fg_color="transparent")
        for v in AUDIO_BITRATES:
            ctk.CTkRadioButton(
                self._qmp3, text=f"{v} kbps", variable=self.v_qmp3, value=str(v),
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=C["txt"],
                fg_color=C["acc"], hover_color=C["acc_h"],
                border_color=C["bdr"],
            ).pack(side="left", padx=(0, 10))

        self._qmp4 = ctk.CTkFrame(self._qbox, fg_color="transparent")
        # Two rows so 8 qualities fit cleanly
        self._qmp4_r1 = ctk.CTkFrame(self._qmp4, fg_color="transparent")
        self._qmp4_r2 = ctk.CTkFrame(self._qmp4, fg_color="transparent")
        self._qmp4_r1.pack(anchor="w")
        self._qmp4_r2.pack(anchor="w", pady=(6, 0))
        for i, v in enumerate(VIDEO_HEIGHTS):
            parent = self._qmp4_r1 if i < 4 else self._qmp4_r2
            ctk.CTkRadioButton(
                parent, text=_height_label(v), variable=self.v_qmp4, value=str(v),
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color=C["txt"],
                fg_color=C["acc"], hover_color=C["acc_h"],
                border_color=C["bdr"],
            ).pack(side="left", padx=(0, 12))

        row_lbl("Save to", 3)
        out_row = ctk.CTkFrame(card, fg_color="transparent")
        out_row.grid(row=3, column=1, sticky="ew", padx=(0, 18), pady=(4, 14))
        out_row.grid_columnconfigure(0, weight=1)
        self._out_entry = ctk.CTkEntry(
            out_row, textvariable=self.v_out,
            height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color=C["bg"], border_color=C["bdr"],
            text_color=C["txt"],
        )
        self._out_entry.grid(row=0, column=0, sticky="ew")
        ctk.CTkButton(
            out_row, text="Browse", width=80, height=38, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI Semibold", size=12),
            fg_color=C["grn"], hover_color=C["grn_h"], text_color="#0f0f0f",
            command=self._browse,
        ).grid(row=0, column=1, padx=(8, 0))
        self._attach_entry_menu(self._out_entry)

        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=2, column=0, sticky="ew", padx=16, pady=(8, 4))
        bar.grid_columnconfigure(1, weight=1)

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        self._btn_dl = ctk.CTkButton(
            left, text="⬇  Download", width=140, height=42, corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI Semibold", size=14),
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=self._start, state="disabled",
        )
        self._btn_dl.pack(side="left")

        self._btn_st = ctk.CTkButton(
            left, text="■  Stop", width=100, height=42, corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI Semibold", size=14),
            fg_color=C["acc2"], hover_color=C["acc2_h"], text_color="white",
            command=self._do_stop, state="disabled",
        )
        self._btn_st.pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            left, text="clear log", width=90, height=36, corner_radius=10,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=C["b3"], hover_color=C["bdr"], text_color=C["dim"],
            command=self._clear_log,
        ).pack(side="left", padx=(14, 0))

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.grid(row=0, column=1, sticky="ew", padx=(24, 0))
        right.grid_columnconfigure(0, weight=1)

        self._pbar = ctk.CTkProgressBar(
            right, variable=self.v_prog,
            height=10, corner_radius=6,
            progress_color=C["acc"], fg_color=C["b1"],
        )
        self._pbar.grid(row=0, column=0, sticky="ew", pady=(4, 2))
        self._pbar.set(0)

        self._plbl = ctk.CTkLabel(
            right, text="idle",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=C["dim"], anchor="e",
        )
        self._plbl.grid(row=1, column=0, sticky="e")

        log_fr = ctk.CTkFrame(
            self, fg_color=C["b1"], corner_radius=14,
            border_width=1, border_color=C["bdr"],
        )
        log_fr.grid(row=3, column=0, sticky="nsew", padx=16, pady=(6, 8))
        log_fr.grid_columnconfigure(0, weight=1)
        log_fr.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            log_fr, text="console",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=C["dim"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))

        self._log_w = ctk.CTkTextbox(
            log_fr,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=C["bg"], text_color=C["dim"],
            corner_radius=10, border_width=0,
            wrap="none", activate_scrollbars=True,
        )
        self._log_w.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self._log_w.configure(state="disabled")

        tb = self._log_w._textbox
        for tag, fg in (
            ("grn", C["grn"]), ("red", C["red"]),
            ("ylw", C["ylw"]), ("blu", C["blu"]),
            ("acc", C["acc"]), ("txt", C["txt"]),
        ):
            tb.tag_config(tag, foreground=fg)

        # Footer: About + contact Open buttons
        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 14))
        ctk.CTkLabel(
            foot, text="Contact",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=C["dim"],
        ).pack(side="left", padx=(2, 10))
        ctk.CTkButton(
            foot, text="About", width=80, height=30, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=C["b3"], hover_color=C["bdr"], text_color=C["txt"],
            command=self._open_about,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            foot, text="Open Telegram", width=120, height=30, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=lambda: webbrowser.open(CONTACT_TELEGRAM),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            foot, text="Open Discord User", width=140, height=30, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=lambda: webbrowser.open(CONTACT_DISCORD_USER),
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            foot, text="Open Discord Server", width=150, height=30, corner_radius=8,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=C["acc"], hover_color=C["acc_h"], text_color="white",
            command=lambda: webbrowser.open(CONTACT_DISCORD_SERVER),
        ).pack(side="left")

    def _open_about(self):
        AboutDialog(self)

    def _startup_check(self):
        parts = []
        if _YTDLP_OK:
            parts.append(f"yt-dlp {_YTDLP_VER} ✓")
            self._status_lbl.configure(text_color=C["grn"])
        else:
            parts.append("yt-dlp missing ✗")
            self._status_lbl.configure(text_color=C["red"])
            if not self._ready_logged:
                self._log("✗ yt-dlp not installed — run:  pip install yt-dlp")

        if _FFMPEG_OK:
            parts.append("ffmpeg ✓")
        else:
            parts.append("ffmpeg ✗")
            if not self._ready_logged:
                self._log(
                    "⚠ ffmpeg not found — install ffmpeg and add it to PATH "
                    "(required for audio convert / cover embed / MP4 mux)"
                )

        py = f"{sys.version_info.major}.{sys.version_info.minor}"
        parts.append(f"Python {py}")

        self._status_lbl.configure(text="  ·  ".join(parts))
        if _YTDLP_OK and _FFMPEG_OK and not self._ready_logged:
            self._log("✓ ready — paste a YouTube URL (right-click) or Search Video")
            self._ready_logged = True
        elif not self._ready_logged:
            self._ready_logged = True

    def _attach_entry_menu(self, entry: ctk.CTkEntry):
        """Right-click Paste / Copy / Select All on a CTkEntry."""
        menu = tk.Menu(
            self, tearoff=0,
            bg=C["b2"], fg=C["txt"],
            activebackground=C["acc"], activeforeground="white",
            bd=0, relief="flat",
        )
        menu.add_command(label="Paste", command=lambda: self._entry_paste(entry))
        menu.add_command(label="Copy", command=lambda: self._entry_copy(entry))
        menu.add_separator()
        menu.add_command(label="Select All", command=lambda: self._entry_select_all(entry))

        def popup(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()

        entry.bind("<Button-3>", popup)
        try:
            entry._entry.bind("<Button-3>", popup)
        except Exception:
            pass

    def _entry_paste(self, entry: ctk.CTkEntry):
        try:
            text = self.clipboard_get()
        except Exception:
            self._log("⚠ clipboard empty")
            return
        try:
            entry.delete("sel.first", "sel.last")
        except Exception:
            pass
        try:
            entry.insert("insert", text)
        except Exception:
            if entry is self._url_entry:
                self.v_url.set(text.strip())
            elif entry is getattr(self, "_out_entry", None):
                self.v_out.set(text.strip())

    def _entry_copy(self, entry: ctk.CTkEntry):
        try:
            text = entry.selection_get()
        except Exception:
            text = entry.get()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)

    def _entry_select_all(self, entry: ctk.CTkEntry):
        entry.select_range(0, "end")
        entry.icursor("end")
        return "break"

    def _open_search(self):
        if not _YTDLP_OK:
            self._log("✗ install yt-dlp first:  pip install yt-dlp")
            return
        SearchDialog(self)

    def _on_fmt_seg(self, value: str):
        self.v_fmt.set("mp3" if value.startswith("M4A") else "mp4")
        self._on_fmt()

    def _on_fmt(self):
        self._qmp3.pack_forget()
        self._qmp4.pack_forget()
        if self.v_fmt.get() == "mp3":
            self._qmp3.pack(side="left")
        else:
            self._qmp4.pack(side="left")

    def _browse(self):
        d = filedialog.askdirectory(initialdir=self.v_out.get())
        if d:
            self.v_out.set(d)

    def _log(self, msg: str):
        lo = msg.lower()
        tag = ""
        if msg.startswith("✓") or "done →" in lo or "saved" in lo:
            tag = "grn"
        elif msg.startswith("✗") or ("error" in lo and "no error" not in lo):
            tag = "red"
        elif msg.startswith("⚠") or "warning" in lo:
            tag = "ylw"
        elif msg.startswith("   ↓") or "yt-dlp" in lo:
            tag = "blu"
        elif msg.startswith("──"):
            tag = "acc"
        elif "→" in msg[:4]:
            tag = "txt"

        self._log_w.configure(state="normal")
        tb = self._log_w._textbox
        tb.insert("end", msg + "\n", tag if tag else ())
        tb.see("end")
        self._log_w.configure(state="disabled")

    def _clear_log(self):
        self._log_w.configure(state="normal")
        self._log_w.delete("1.0", "end")
        self._log_w.configure(state="disabled")

    def _set_prog(self, v: float):
        v = max(0.0, min(100.0, float(v)))
        self.v_prog.set(v / 100.0)
        self._plbl.configure(text="idle" if v <= 0 else f"{int(v)}%")

    def _run_mandatory_update_check(self):
        """Block use until update policy is satisfied."""
        self._status_lbl.configure(text="checking for updates…", text_color=C["blu"])
        self._btn_dl.configure(state="disabled")
        threading.Thread(target=self._update_check_thread, daemon=True).start()

    def _update_check_thread(self):
        info = check_github_update()
        status = info.get("status")
        if status == "ok":
            self.after(0, self._update_check_ok)
        elif status == "update":
            self.after(0, self._show_mandatory_update, info)
        else:
            self.after(0, self._update_check_error, info.get("error") or "Unknown error")

    def _update_check_ok(self):
        self._update_ready = True
        self._btn_dl.configure(state="normal")
        self._startup_check()

    def _show_mandatory_update(self, info: dict):
        self._update_ready = False
        self._btn_dl.configure(state="disabled")
        self._status_lbl.configure(text="update required", text_color=C["ylw"])
        UpdateRequiredDialog(self, info)

    def _update_check_error(self, err: str):
        dlg = UpdateCheckFailedDialog(self, err)
        choice = dlg.ask()
        if choice == "retry":
            self.after(50, self._run_mandatory_update_check)
        elif choice == "continue":
            self._update_ready = True
            self._btn_dl.configure(state="normal")
            self._log(f"⚠ update check failed — continuing offline: {err}")
            self._startup_check()
        else:
            self.destroy()
            sys.exit(0)

    def _confirm(self, title: str, message: str) -> bool:
        return ConfirmDialog(self, title, message).ask()

    def _start(self):
        if self._running:
            return
        if not self._update_ready:
            self._log("⚠ waiting for update check…")
            return

        url = self.v_url.get().strip()
        if not url:
            self._log("⚠ enter a YouTube URL")
            return
        if not re.search(r"youtube\.com|youtu\.be", url, re.I):
            self._log("⚠ doesn't look like a YouTube URL")
            return

        url = re.sub(r"[&?]list=[^&]+", "", url)
        url = re.sub(r"[&?]index=\d+", "", url)
        url = url.rstrip("?&")

        out = self.v_out.get().strip()
        if not out:
            self._log("⚠ choose an output folder")
            return
        os.makedirs(out, exist_ok=True)
        if not os.path.isdir(out):
            self._log(f"⚠ output dir not found: {out}")
            return

        if not _YTDLP_OK:
            self._log("✗ install yt-dlp first:  pip install yt-dlp")
            return

        fmt = self.v_fmt.get()
        quality = self.v_qmp3.get() if fmt == "mp3" else self.v_qmp4.get()

        self._stop.clear()
        self._running = True
        self._btn_dl.configure(state="disabled")
        self._btn_st.configure(state="normal")
        self._set_prog(0)

        self._log("─" * 62)
        self._log(f"── URL:     {url}")
        self._log("── probing formats / size…")

        threading.Thread(
            target=self._prepare_and_download,
            args=(url, fmt, quality, out),
            daemon=True,
        ).start()

    def _do_stop(self):
        if self._running:
            self._stop.set()
            self._log("⚠ stop requested...")

    def _prepare_and_download(self, url: str, fmt: str, quality: str, out: str):
        try:
            if self._stop.is_set():
                raise InterruptedError

            eff_q, downgrade_msg = self.api.resolve_quality(url, fmt, quality)
            if downgrade_msg:
                ev = threading.Event()
                box: dict = {"ok": False}

                def ask_max():
                    box["ok"] = self._confirm(
                        "Quality not available",
                        downgrade_msg + "\n\nDownload at the highest available quality?",
                    )
                    ev.set()

                self.after(0, ask_max)
                ev.wait()
                if not box["ok"]:
                    raise InterruptedError
                quality = eff_q
                self.after(0, self._log, f"── quality adjusted → {quality}")
            else:
                quality = eff_q

            size = self.api.estimate_download_size(url, fmt, quality)
            size_txt = _format_bytes(size)
            if fmt == "mp3":
                q_txt = f"{quality} kbps (M4A)"
            else:
                q_txt = _height_label(int(quality)) + " (MP4)"

            ev2 = threading.Event()
            box2: dict = {"ok": False}

            def ask_size():
                box2["ok"] = self._confirm(
                    "Confirm download",
                    f"Estimated download size: {size_txt}\n"
                    f"Quality: {q_txt}\n\n"
                    f"Do you want to download this file?",
                )
                ev2.set()

            self.after(0, ask_size)
            ev2.wait()
            if not box2["ok"]:
                raise InterruptedError

            fmt_label = "M4A" if fmt == "mp3" else fmt.upper()
            self.after(0, self._log, f"── format:  {fmt_label}  quality={quality}")
            self.after(0, self._log, f"── size:    {size_txt}")
            self.after(0, self._log, f"── out dir: {out}")

            title = self.api.get_title(
                url,
                log=lambda m: self.after(0, self._log, m),
            )
            name = title or Downloader.vid_id(url)

            dest = self.api.download(
                url, fmt, quality, out, name,
                prog=lambda v: self.after(0, self._set_prog, v),
                log=lambda m: self.after(0, self._log, m),
                stop=self._stop,
            )
            self.after(0, self._log, f"✓ Done → {dest}")

        except InterruptedError:
            self.after(0, self._log, "⚠ cancelled by user")
            self.after(0, self._set_prog, 0)

        except Exception as exc:
            self.after(0, self._log, f"✗ {exc}")
            self.after(0, self._set_prog, 0)

        finally:
            self._running = False
            self.after(0, lambda: self._btn_dl.configure(state="normal"))
            self.after(0, lambda: self._btn_st.configure(state="disabled"))


# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
