package com.afrsto.youtubedownloader

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.afrsto.youtubedownloader.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { /* granted or not — downloads fall back to app storage */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        requestRuntimePermissions()

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
        binding.btnTelegram.setOnClickListener { open(CONTACT_TELEGRAM) }
        binding.btnDiscordUser.setOnClickListener { open(CONTACT_DISCORD_USER) }
        binding.btnDiscordServer.setOnClickListener { open(CONTACT_DISCORD_SERVER) }
    }

    private fun requestRuntimePermissions() {
        val needed = mutableListOf<String>()
        if (Build.VERSION.SDK_INT <= 28) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED
            ) {
                needed += Manifest.permission.WRITE_EXTERNAL_STORAGE
            }
        }
        if (Build.VERSION.SDK_INT >= 33) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                needed += Manifest.permission.POST_NOTIFICATIONS
            }
        }
        if (needed.isNotEmpty()) {
            permissionLauncher.launch(needed.toTypedArray())
        }
    }

    private fun open(url: String) {
        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
    }

    companion object {
        private const val CONTACT_TELEGRAM = "https://t.me/X2_616"
        private const val CONTACT_DISCORD_USER = "https://discord.com/users/994817247061225633"
        private const val CONTACT_DISCORD_SERVER = "https://discord.gg/btRCeujadA"
    }
}
