package com.afrsto.youtubedownloader

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.afrsto.youtubedownloader.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.btnContinue.setOnClickListener {
            val url = UrlUtils.extractYoutubeUrl(binding.urlInput.text?.toString())
            if (url == null) {
                Toast.makeText(this, R.string.invalid_url, Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            startActivity(DownloadActivity.intent(this, url))
        }

        binding.btnAbout.setOnClickListener {
            AlertDialog.Builder(this)
                .setTitle(R.string.about)
                .setMessage(R.string.about_body)
                .setPositiveButton(android.R.string.ok, null)
                .show()
        }
        binding.btnTelegram.setOnClickListener { open("https://t.me/X2_616") }
        binding.btnDiscordUser.setOnClickListener {
            open("https://discord.com/users/994817247061225633")
        }
        binding.btnDiscordServer.setOnClickListener { open("https://discord.gg/btRCeujadA") }
    }

    private fun open(url: String) {
        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
    }
}
