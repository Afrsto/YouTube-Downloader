package com.afrsto.youtubedownloader.extract

import android.content.Context
import okhttp3.OkHttpClient
import okhttp3.RequestBody.Companion.toRequestBody
import org.schabi.newpipe.extractor.NewPipe
import org.schabi.newpipe.extractor.downloader.Downloader
import org.schabi.newpipe.extractor.downloader.Request
import org.schabi.newpipe.extractor.downloader.Response
import org.schabi.newpipe.extractor.localization.Localization
import java.util.concurrent.TimeUnit

object NewPipeInit {
    @Volatile
    private var ready = false

    fun init(context: Context) {
        if (ready) return
        synchronized(this) {
            if (ready) return
            NewPipe.init(OkHttpDownloader(), Localization.DEFAULT)
            ready = true
        }
    }
}

class OkHttpDownloader : Downloader() {
    private val client = OkHttpClient.Builder()
        .readTimeout(30, TimeUnit.SECONDS)
        .connectTimeout(30, TimeUnit.SECONDS)
        .build()

    override fun execute(request: Request): Response {
        val builder = okhttp3.Request.Builder().url(request.url())
        val method = request.httpMethod()
        val data = request.dataToSend()
        val body = if (data == null || method.equals("GET", ignoreCase = true) ||
            method.equals("HEAD", ignoreCase = true)
        ) {
            null
        } else {
            data.toRequestBody(null)
        }
        builder.method(method, body)
        request.headers().forEach { (key, values) ->
            values.forEach { value -> builder.addHeader(key, value) }
        }
        if (builder.build().header("User-Agent") == null) {
            builder.header(
                "User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        val response = client.newCall(builder.build()).execute()
        val body = response.body?.string().orEmpty()
        val headers = LinkedHashMap<String, List<String>>()
        response.headers.forEach { (name, value) ->
            headers[name] = listOf(value)
        }
        return Response(
            response.code,
            response.message,
            headers,
            body,
            response.request.url.toString()
        )
    }
}
