# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onedir build — AV-safer than onefile (no TEMP dropper extract)."""

from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# CustomTkinter / yt-dlp ship data files that must be collected.
ctk_datas, ctk_binaries, ctk_hidden = collect_all("customtkinter")
ytdlp_datas, ytdlp_binaries, ytdlp_hidden = collect_all("yt_dlp")
pil_datas = collect_data_files("PIL")

a = Analysis(
    ["youtube_downloadr.py"],
    pathex=[],
    binaries=ctk_binaries + ytdlp_binaries,
    datas=ctk_datas
    + ytdlp_datas
    + pil_datas
    + [("YouTube Downloader.ico", ".")],
    hiddenimports=list(
        dict.fromkeys(
            ctk_hidden
            + ytdlp_hidden
            + [
                "PIL",
                "PIL.Image",
                "customtkinter",
                "yt_dlp",
            ]
        )
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="YouTube Downloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # never UPX — packer heuristic → Wacatac.!ml
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version="version_info.txt",
    icon="YouTube Downloader.ico",
    uac_admin=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="YouTube Downloader",
)
