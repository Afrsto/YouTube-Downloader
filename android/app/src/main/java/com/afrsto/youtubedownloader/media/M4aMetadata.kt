package com.afrsto.youtubedownloader.media

import org.jaudiotagger.audio.AudioFileIO
import org.jaudiotagger.tag.FieldKey
import org.jaudiotagger.tag.images.ArtworkFactory
import java.io.File
import java.util.logging.Level
import java.util.logging.Logger

object M4aMetadata {
    init {
        // jaudiotagger is noisy on Android
        Logger.getLogger("org.jaudiotagger").level = Level.OFF
    }

    data class Result(val coverEmbedded: Boolean, val lyricsEmbedded: Boolean)

    fun embed(m4aFile: File, coverJpeg: ByteArray?, lyrics: String?): Result {
        var coverOk = false
        var lyricsOk = false
        val audio = AudioFileIO.read(m4aFile)
        val tag = audio.tagOrCreateAndSetDefault
        if (coverJpeg != null && coverJpeg.isNotEmpty()) {
            try {
                val artwork = ArtworkFactory.getNew()
                artwork.binaryData = coverJpeg
                artwork.mimeType = "image/jpeg"
                artwork.pictureType = 3
                tag.deleteArtworkField()
                tag.setField(artwork)
                coverOk = true
            } catch (_: Exception) {
                coverOk = false
            }
        }
        if (!lyrics.isNullOrBlank()) {
            try {
                tag.setField(FieldKey.LYRICS, lyrics)
                lyricsOk = true
            } catch (_: Exception) {
                lyricsOk = false
            }
        }
        audio.commit()
        return Result(coverOk, lyricsOk)
    }
}
