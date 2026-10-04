package com.afrsto.youtubedownloader.download

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.ContentValues
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.Environment
import android.os.IBinder
import android.provider.MediaStore
import androidx.core.app.NotificationCompat
import com.afrsto.youtubedownloader.R
import com.afrsto.youtubedownloader.media.Captions
import com.afrsto.youtubedownloader.media.M4aMetadata
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream
import java.util.concurrent.TimeUnit

class DownloadService : Service() {
    private val client = OkHttpClient.Builder()
        .followRedirects(true)
        .followSslRedirects(true)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val url = intent?.getStringExtra(EXTRA_URL).orEmpty()
        val filename = intent?.getStringExtra(EXTRA_FILENAME) ?: "download.bin"
        intent?.getIntExtra(EXTRA_THREADS, 3)
        val thumbUrl = intent?.getStringExtra(EXTRA_THUMB_URL).orEmpty()
        val subtitleUrl = intent?.getStringExtra(EXTRA_SUBTITLE_URL).orEmpty()
        val embedMeta = intent?.getBooleanExtra(EXTRA_EMBED_META, false) == true

        ensureChannel()
        val notification = buildNotification("Downloading $filename", 0, indeterminate = true)
        if (Build.VERSION.SDK_INT >= 29) {
            startForeground(NOTIF_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
        } else {
            startForeground(NOTIF_ID, notification)
        }

        Thread {
            try {
                download(url, filename, thumbUrl, subtitleUrl, embedMeta)
                notifyDone(filename, ok = true)
            } catch (e: Exception) {
                notifyDone("${e.message}", ok = false)
            } finally {
                stopForeground(STOP_FOREGROUND_DETACH)
                stopSelf(startId)
            }
        }.start()

        return START_NOT_STICKY
    }

    private fun download(
        url: String,
        filename: String,
        thumbUrl: String,
        subtitleUrl: String,
        embedMeta: Boolean
    ) {
        val request = Request.Builder().url(url).get().build()
        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) {
                throw IllegalStateException("HTTP ${response.code}")
            }
            val body = response.body ?: throw IllegalStateException("Empty body")
            val total = body.contentLength()
            val outFile = File(cacheDir, filename)
            body.byteStream().use { input ->
                FileOutputStream(outFile).use { output ->
                    val buf = ByteArray(64 * 1024)
                    var read: Int
                    var done = 0L
                    while (input.read(buf).also { read = it } != -1) {
                        output.write(buf, 0, read)
                        done += read
                        if (total > 0) {
                            val pct = ((done * 100) / total).toInt().coerceAtMost(90)
                            updateProgress(filename, pct)
                        }
                    }
                }
            }

            if (embedMeta && filename.endsWith(".m4a", ignoreCase = true)) {
                updateProgress(filename, 92)
                embedAudioExtras(outFile, thumbUrl, subtitleUrl)
            }

            updateProgress(filename, 98)
            persistToDownloads(outFile, filename)
            outFile.delete()
        }
    }

    private fun embedAudioExtras(m4a: File, thumbUrl: String, subtitleUrl: String) {
        val cover = if (thumbUrl.isNotBlank()) {
            runCatching { fetchBytes(thumbUrl) }.getOrNull()
        } else null
        val lyrics = if (subtitleUrl.isNotBlank()) {
            runCatching {
                val raw = fetchBytes(subtitleUrl)?.toString(Charsets.UTF_8).orEmpty()
                Captions.toLyrics(raw)
            }.getOrNull()?.takeIf { it.isNotBlank() }
        } else null
        if (cover != null || lyrics != null) {
            M4aMetadata.embed(m4a, cover, lyrics)
        }
    }

    private fun fetchBytes(url: String): ByteArray? {
        val request = Request.Builder().url(url).get().build()
        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) return null
            return response.body?.bytes()
        }
    }

    private fun persistToDownloads(file: File, filename: String) {
        val mime = when {
            filename.endsWith(".mp4", true) -> "video/mp4"
            filename.endsWith(".m4a", true) -> "audio/mp4"
            filename.endsWith(".webm", true) -> "video/webm"
            filename.endsWith(".opus", true) -> "audio/ogg"
            filename.endsWith(".vtt", true) -> "text/vtt"
            filename.endsWith(".srt", true) -> "application/x-subrip"
            else -> "application/octet-stream"
        }
        val collection = if (Build.VERSION.SDK_INT >= 29) {
            MediaStore.Downloads.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
        } else {
            MediaStore.Files.getContentUri("external")
        }
        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, filename)
            put(MediaStore.MediaColumns.MIME_TYPE, mime)
            if (Build.VERSION.SDK_INT >= 29) {
                put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/YouTubeDownloader")
                put(MediaStore.MediaColumns.IS_PENDING, 1)
            }
        }
        val resolver = contentResolver
        val uri = resolver.insert(collection, values)
            ?: throw IllegalStateException("Cannot create MediaStore entry")
        resolver.openOutputStream(uri)?.use { out ->
            file.inputStream().use { input -> input.copyTo(out) }
        } ?: throw IllegalStateException("Cannot open output stream")
        if (Build.VERSION.SDK_INT >= 29) {
            values.clear()
            values.put(MediaStore.MediaColumns.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
        }
    }

    private fun ensureChannel() {
        if (Build.VERSION.SDK_INT < 26) return
        val mgr = getSystemService(NotificationManager::class.java)
        val channel = NotificationChannel(
            CHANNEL_ID,
            getString(R.string.channel_downloads),
            NotificationManager.IMPORTANCE_LOW
        )
        mgr.createNotificationChannel(channel)
    }

    private fun buildNotification(text: String, progress: Int, indeterminate: Boolean): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(text)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setOnlyAlertOnce(true)
            .setOngoing(true)
            .setProgress(100, progress, indeterminate)
            .build()
    }

    private fun updateProgress(filename: String, pct: Int) {
        val mgr = getSystemService(NotificationManager::class.java)
        mgr.notify(NOTIF_ID, buildNotification("Downloading $filename ($pct%)", pct, false))
    }

    private fun notifyDone(text: String, ok: Boolean) {
        val mgr = getSystemService(NotificationManager::class.java)
        val n = NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle(getString(R.string.app_name))
            .setContentText(if (ok) "Saved: $text" else "Failed: $text")
            .setSmallIcon(
                if (ok) android.R.drawable.stat_sys_download_done
                else android.R.drawable.stat_notify_error
            )
            .setAutoCancel(true)
            .build()
        mgr.notify(NOTIF_ID + 1, n)
    }

    companion object {
        const val EXTRA_URL = "url"
        const val EXTRA_FILENAME = "filename"
        const val EXTRA_THREADS = "threads"
        const val EXTRA_THUMB_URL = "thumb_url"
        const val EXTRA_SUBTITLE_URL = "subtitle_url"
        const val EXTRA_EMBED_META = "embed_meta"
        private const val CHANNEL_ID = "downloads"
        private const val NOTIF_ID = 42
    }
}
