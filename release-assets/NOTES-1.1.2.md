## YouTube Downloader v1.1.2

### Windows
- M4A downloads no longer request every caption language (`all`), which triggered HTTP 429 on obscure auto-translate codes like `ab-ar` and aborted the whole job
- Preferred caption langs (`en` / `ar`) + subtitle sleep + `ignoreerrors` so a failed caption fetch does not kill the audio download
- Version bump to 1.1.2

### Android
- Fixed Permission Denial when saving: MediaStore Downloads with Audio/Video and app-storage fallbacks
- Runtime permission requests for storage (Android 9) and notifications (Android 13+)
- Restored home contact buttons (Telegram, About, Discord Server, Discord User) to match the install-style design
- Fixed Download type radios (Captions / Audio / Video): LTR layout, no phantom extra radio, correct quality lists

### Downloads
- `YouTube-Downloader-Setup-1.1.2.exe` — Windows installer
- `YouTube-Downloader-1.1.2-android.apk` — Android 9+
