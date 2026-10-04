# YouTube Downloader — Android

Kotlin app for **Android 9+** (`minSdk 28`) using [NewPipe Extractor](https://github.com/TeamNewPipe/NewPipeExtractor).

## Features

- **Setup-style home** when opened from the launcher (paste a YouTube URL)
- **Share target** — share a video from YouTube / other apps to open the NewPipe-like Download dialog
- Video / Audio / Captions stream picker, quality list, threads slider, foreground download service

## License note

NewPipe Extractor is **GPL-3.0**. This Android module inherits GPL obligations for distribution of the APK.

## Build

Requirements: **JDK 17+**, Android SDK 35, Android Studio or command-line tools.

```bash
cd android
./gradlew assembleRelease
```

Debug APK:

```bash
./gradlew assembleDebug
```

Outputs:

- `app/build/outputs/apk/release/app-release-unsigned.apk` (or signed if configured)
- `app/build/outputs/apk/debug/app-debug.apk`

On Windows (PowerShell):

```powershell
cd android
.\gradlew.bat assembleDebug
```

## Contacts

- Telegram: https://t.me/X2_616
- Discord user: https://discord.com/users/994817247061225633
- Discord server: https://discord.gg/btRCeujadA
