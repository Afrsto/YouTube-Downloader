package com.afrsto.youtubedownloader.media

object Captions {
    /** Strip WebVTT / SRT timing into plain lyrics lines. */
    fun toLyrics(text: String): String {
        val linesOut = LinkedHashSet<String>()
        for (raw in text.lineSequence()) {
            var line = raw.trim()
            if (line.isEmpty()) continue
            val upper = line.uppercase()
            if (upper.startsWith("WEBVTT")) continue
            if (line.startsWith("NOTE") || line.startsWith("STYLE") || line.startsWith("REGION")) continue
            if (line.matches(Regex("""^\d+$"""))) continue
            if (Regex("""\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->""").containsMatchIn(line)) continue
            if (Regex("""\d{2}:\d{2}[.,]\d{3}\s*-->""").containsMatchIn(line)) continue
            line = line.replace(Regex("""<[^>]+>"""), "").trim()
            if (line.isNotEmpty()) linesOut.add(line)
        }
        return linesOut.joinToString("\n").trim()
    }
}
