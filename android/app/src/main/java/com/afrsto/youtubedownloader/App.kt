package com.afrsto.youtubedownloader

import android.app.Application
import com.afrsto.youtubedownloader.extract.NewPipeInit

class App : Application() {
    override fun onCreate() {
        super.onCreate()
        NewPipeInit.init(this)
    }
}
