import os

def generate():
    package_path = "app/src/main/java/com/watermarker"
    os.makedirs(package_path, exist_ok=True)
    
    app_class_content = """package com.watermarker
import android.app.Application
import com.google.android.gms.ads.MobileAds
class WaterMarkerApp : Application() {
    lateinit var appOpenAdManager: AppOpenAdManager
    override fun onCreate() {
        super.onCreate()
        MobileAds.initialize(this) {}
        appOpenAdManager = AppOpenAdManager(this)
        appOpenAdManager.loadAd()
    }
}"""

    ad_manager_content = """package com.watermarker
import android.content.Context
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.appopen.AppOpenAd
class AppOpenAdManager(private val context: Context) {
    private var appOpenAd: AppOpenAd? = null
    private var isLoadingAd = false
    fun loadAd() {
        if (isLoadingAd || appOpenAd != null) return
        isLoadingAd = true
        val request = AdRequest.Builder().build()
        AppOpenAd.load(context, "ca-app-pub-3940256099942544/3419835294", request,
            object : AppOpenAd.AppOpenAdLoadCallback() {
                override fun onAdLoaded(ad: AppOpenAd) { appOpenAd = ad; isLoadingAd = false }
                override fun onAdFailedToLoad(e: LoadAdError) { isLoadingAd = false }
            }
        )
    }
}"""

    engine_content = """package com.watermarker
import android.graphics.Bitmap
class NativeEngine {
    init { System.loadLibrary("watermarker") }
    external fun processWatermark(baseBitmap: Bitmap, overlayBitmap: Bitmap,
                                  realOffsetX: Float, realOffsetY: Float, 
                                  realOverScale: Float, overlayRotation: Float,
                                  overlayAlpha: Float): Boolean
}"""

    with open(f"{package_path}/WaterMarkerApp.kt", "w") as f: f.write(app_class_content)
    with open(f"{package_path}/AppOpenAdManager.kt", "w") as f: f.write(ad_manager_content)
    with open(f"{package_path}/NativeEngine.kt", "w") as f: f.write(engine_content)
    print("✅ 5-1 Generated Kotlin Core components")

if __name__ == "__main__":
    generate()
