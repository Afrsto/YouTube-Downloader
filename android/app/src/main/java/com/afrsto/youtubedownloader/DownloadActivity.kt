package com.afrsto.youtubedownloader

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.SeekBar
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.afrsto.youtubedownloader.databinding.ActivityDownloadBinding
import com.afrsto.youtubedownloader.download.DownloadService
import com.afrsto.youtubedownloader.extract.NewPipeInit
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.schabi.newpipe.extractor.stream.AudioStream
import org.schabi.newpipe.extractor.stream.StreamInfo
import org.schabi.newpipe.extractor.stream.SubtitlesStream
import org.schabi.newpipe.extractor.stream.VideoStream

class DownloadActivity : AppCompatActivity() {
    private lateinit var binding: ActivityDownloadBinding
    private lateinit var url: String

    private var streamInfo: StreamInfo? = null
    private var videoOptions = listOf<StreamOption>()
    private var audioOptions = listOf<StreamOption>()
    private var captionOptions = listOf<StreamOption>()
    private var currentOptions = listOf<StreamOption>()
    private var selectedIndex = 0
    private var pendingStartAfterPermission = false

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        if (pendingStartAfterPermission) {
            pendingStartAfterPermission = false
            launchDownloadService()
        }
    }

    data class StreamOption(
        val label: String,
        val codec: String,
        val sizeLabel: String,
        val url: String,
        val ext: String
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDownloadBinding.inflate(layoutInflater)
        setContentView(binding.root)

        url = intent.getStringExtra(EXTRA_URL).orEmpty()
        if (url.isBlank()) {
            Toast.makeText(this, R.string.invalid_url, Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        NewPipeInit.init(this)
        binding.btnBack.setOnClickListener { finish() }
        binding.btnOk.setOnClickListener { startDownload() }
        binding.qualityRow.setOnClickListener { showQualityPicker() }

        binding.typeGroup.setOnCheckedChangeListener { _, _ -> refreshQualityList() }

        binding.threadsSeek.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                binding.threadsValue.text = (progress + 1).toString()
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })

        loadInfo()
    }

    private fun loadInfo() {
        binding.loading.visibility = View.VISIBLE
        binding.content.visibility = View.INVISIBLE
        lifecycleScope.launch {
            try {
                val info = withContext(Dispatchers.IO) {
                    StreamInfo.getInfo(url)
                }
                streamInfo = info
                binding.filenameInput.setText(UrlUtils.sanitizeFilename(info.name ?: "video"))
                videoOptions = info.videoOnlyStreams.map { vs ->
                    toVideoOption(vs)
                } + info.videoStreams.map { vs ->
                    toVideoOption(vs)
                }
                audioOptions = info.audioStreams.map { asStream ->
                    toAudioOption(asStream)
                }
                captionOptions = info.subtitles.map { sub ->
                    toCaptionOption(sub)
                }
                refreshQualityList()
                binding.loading.visibility = View.GONE
                binding.content.visibility = View.VISIBLE
            } catch (e: Exception) {
                binding.loading.visibility = View.GONE
                val detail = e.message?.takeIf { it.isNotBlank() } ?: e.javaClass.simpleName
                Toast.makeText(
                    this@DownloadActivity,
                    getString(R.string.extract_failed, detail),
                    Toast.LENGTH_LONG
                ).show()
                finish()
            }
        }
    }

    private fun toVideoOption(vs: VideoStream): StreamOption {
        val codec = vs.format?.name ?: "video"
        val height = if (vs.height > 0) "${vs.height}p" else "video"
        val ext = vs.format?.suffix ?: "mp4"
        return StreamOption(height, codec, "—", vs.content, ext)
    }

    private fun toAudioOption(stream: AudioStream): StreamOption {
        val codec = stream.format?.name ?: "audio"
        val br = if (stream.averageBitrate > 0) "${stream.averageBitrate}kbps" else "audio"
        val ext = stream.format?.suffix ?: "m4a"
        return StreamOption(br, codec, "—", stream.content, ext)
    }

    private fun toCaptionOption(sub: SubtitlesStream): StreamOption {
        val lang = sub.languageTag ?: "und"
        val codec = sub.format?.name ?: "captions"
        val ext = sub.format?.suffix ?: "vtt"
        return StreamOption(lang, codec, "—", sub.content, ext)
    }

    private fun refreshQualityList() {
        currentOptions = when (binding.typeGroup.checkedRadioButtonId) {
            R.id.typeVideo -> videoOptions
            R.id.typeAudio -> audioOptions
            R.id.typeCaptions -> captionOptions
            else -> audioOptions
        }
        selectedIndex = 0
        updateQualityRow()
    }

    private fun updateQualityRow() {
        val opt = currentOptions.getOrNull(selectedIndex)
        if (opt == null) {
            binding.qualityCodec.text = "—"
            binding.qualityLabel.text = "No streams"
            binding.qualitySize.text = ""
            return
        }
        binding.qualityCodec.text = opt.codec
        binding.qualityLabel.text = opt.label
        binding.qualitySize.text = opt.sizeLabel
    }

    private fun showQualityPicker() {
        if (currentOptions.isEmpty()) return
        val labels = currentOptions.map { "${it.codec} · ${it.label} · ${it.sizeLabel}" }.toTypedArray()
        AlertDialog.Builder(this)
            .setTitle("Quality")
            .setSingleChoiceItems(labels, selectedIndex) { dialog, which ->
                selectedIndex = which
                updateQualityRow()
                dialog.dismiss()
            }
            .show()
    }

    private fun bestThumbnailUrl(info: StreamInfo): String? {
        val thumbs = info.thumbnails
        if (thumbs.isNullOrEmpty()) return null
        return thumbs.maxByOrNull { it.height * it.width }?.url
    }

    private fun bestSubtitleUrl(info: StreamInfo): String? {
        val subs = info.subtitles
        if (subs.isNullOrEmpty()) return null
        val preferred = listOf("en", "en-US", "en-GB", "ar")
        fun score(sub: SubtitlesStream): Int {
            val lang = (sub.languageTag ?: "").lowercase()
            val pref = preferred.indexOfFirst { lang == it.lowercase() || lang.startsWith(it.lowercase()) }
            val autoPenalty = if (sub.isAutoGenerated) 100 else 0
            return (if (pref >= 0) pref else 50) + autoPenalty
        }
        return subs.minByOrNull { score(it) }?.content
    }

    private fun missingPermissions(): Array<String> {
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
        return needed.toTypedArray()
    }

    private fun startDownload() {
        val opt = currentOptions.getOrNull(selectedIndex)
        if (opt == null) {
            Toast.makeText(this, "No stream selected", Toast.LENGTH_SHORT).show()
            return
        }
        val missing = missingPermissions()
        if (missing.isNotEmpty()) {
            pendingStartAfterPermission = true
            permissionLauncher.launch(missing)
            return
        }
        launchDownloadService()
    }

    private fun launchDownloadService() {
        val opt = currentOptions.getOrNull(selectedIndex) ?: return
        val name = UrlUtils.sanitizeFilename(
            binding.filenameInput.text?.toString().orEmpty().ifBlank { "video" }
        )
        val threads = binding.threadsSeek.progress + 1
        val isAudio = binding.typeGroup.checkedRadioButtonId == R.id.typeAudio
        val info = streamInfo
        val intent = Intent(this, DownloadService::class.java).apply {
            putExtra(DownloadService.EXTRA_URL, opt.url)
            putExtra(DownloadService.EXTRA_FILENAME, "$name.${opt.ext}")
            putExtra(DownloadService.EXTRA_THREADS, threads)
            if (isAudio && info != null) {
                putExtra(DownloadService.EXTRA_EMBED_META, true)
                putExtra(DownloadService.EXTRA_THUMB_URL, bestThumbnailUrl(info).orEmpty())
                putExtra(DownloadService.EXTRA_SUBTITLE_URL, bestSubtitleUrl(info).orEmpty())
            }
        }
        startForegroundService(intent)
        Toast.makeText(this, R.string.download_started, Toast.LENGTH_SHORT).show()
        finish()
    }

    companion object {
        private const val EXTRA_URL = "url"
        fun intent(context: Context, url: String): Intent =
            Intent(context, DownloadActivity::class.java).putExtra(EXTRA_URL, url)
    }
}
