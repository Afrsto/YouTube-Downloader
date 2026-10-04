package com.afrsto.youtubedownloader

object UrlUtils {
    private val patterns = listOf(
        Regex("""(?i)https?://(?:www\.|m\.)?youtube\.com/watch\?[^\s]*v=([A-Za-z0-9_-]{11})"""),
        Regex("""(?i)https?://youtu\.be/([A-Za-z0-9_-]{11})"""),
        Regex("""(?i)https?://(?:www\.|m\.)?youtube\.com/shorts/([A-Za-z0-9_-]{11})"""),
        Regex("""(?i)https?://(?:www\.|m\.)?youtube\.com/embed/([A-Za-z0-9_-]{11})""")
    )

    fun extractYoutubeUrl(text: String?): String? {
        if (text.isNullOrBlank()) return null
        for (p in patterns) {
            val m = p.find(text)
            if (m != null) {
                val id = m.groupValues.getOrNull(1)
                if (!id.isNullOrBlank()) {
                    return "https://www.youtube.com/watch?v=$id"
                }
            }
        }
        return null
    }

    fun sanitizeFilename(name: String): String {
        val cleaned = name.replace(Regex("""[<>:"/\\|?*\x00-\x1f]"""), "_").trim('.', ' ')
        return (cleaned.ifBlank { "video" }).take(120)
    }
}
