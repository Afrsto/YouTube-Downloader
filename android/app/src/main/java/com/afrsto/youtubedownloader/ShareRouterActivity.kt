package com.afrsto.youtubedownloader

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class ShareRouterActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val url = resolveUrl(intent)
        if (url == null) {
            Toast.makeText(this, R.string.invalid_url, Toast.LENGTH_LONG).show()
            finish()
            return
        }
        startActivity(DownloadActivity.intent(this, url))
        finish()
    }

    private fun resolveUrl(intent: Intent?): String? {
        if (intent == null) return null
        when (intent.action) {
            Intent.ACTION_SEND -> {
                val text = intent.getStringExtra(Intent.EXTRA_TEXT)
                return UrlUtils.extractYoutubeUrl(text)
            }
            Intent.ACTION_VIEW -> {
                return UrlUtils.extractYoutubeUrl(intent.dataString)
            }
        }
        return UrlUtils.extractYoutubeUrl(intent.dataString)
    }
}
