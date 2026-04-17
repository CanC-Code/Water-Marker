import os

def generate():
    package_path = "app/src/main/java/com/watermarker"
    os.makedirs(package_path, exist_ok=True)

    app_content = """package com.watermarker

import android.app.Activity
import android.app.Application
import android.os.Bundle
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.ProcessLifecycleOwner
import com.google.android.gms.ads.AdError
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.FullScreenContentCallback
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.MobileAds
import com.google.android.gms.ads.appopen.AppOpenAd
import java.util.Date

// Notice how WatermarkerApp no longer implements DefaultLifecycleObserver
class WatermarkerApp : Application(), Application.ActivityLifecycleCallbacks {

    private lateinit var appOpenAdManager: AppOpenAdManager
    private var currentActivity: Activity? = null

    override fun onCreate() {
        super.onCreate()
        registerActivityLifecycleCallbacks(this)
        
        MobileAds.initialize(this) {}
        
        appOpenAdManager = AppOpenAdManager()
        
        // Register the inner class as the observer instead of the App itself
        ProcessLifecycleOwner.get().lifecycle.addObserver(appOpenAdManager)
        
        appOpenAdManager.loadAd()
    }

    override fun onActivityStarted(activity: Activity) {
        currentActivity = activity
    }

    override fun onActivityResumed(activity: Activity) {
        currentActivity = activity
    }

    override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) {}
    override fun onActivityPaused(activity: Activity) {}
    override fun onActivityStopped(activity: Activity) {}
    override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) {}
    override fun onActivityDestroyed(activity: Activity) {
        if (currentActivity == activity) {
            currentActivity = null
        }
    }

    // The AdManager handles its own lifecycle observation now!
    inner class AppOpenAdManager : DefaultLifecycleObserver {
        private var appOpenAd: AppOpenAd? = null
        private var isLoadingAd = false
        var isShowingAd = false
        private var loadTime: Long = 0

        // Triggered when the app comes to the foreground
        override fun onStart(owner: LifecycleOwner) {
            super.onStart(owner)
            showAdIfAvailable(currentActivity)
        }

        fun loadAd() {
            if (isLoadingAd || isAdAvailable()) return
            isLoadingAd = true
            
            val request = AdRequest.Builder().build()
            
            AppOpenAd.load(
                this@WatermarkerApp,
                "ca-app-pub-7732503595590477/4459993522",
                request,
                AppOpenAd.APP_OPEN_AD_ORIENTATION_PORTRAIT,
                object : AppOpenAd.AppOpenAdLoadCallback() {
                    override fun onAdLoaded(ad: AppOpenAd) {
                        appOpenAd = ad
                        isLoadingAd = false
                        loadTime = Date().time
                    }
                    override fun onAdFailedToLoad(loadAdError: LoadAdError) {
                        isLoadingAd = false
                    }
                }
            )
        }

        private fun wasLoadTimeLessThanNHoursAgo(numHours: Long): Boolean {
            val dateDifference = Date().time - loadTime
            val numMilliSecondsPerHour: Long = 3600000
            return dateDifference < numMilliSecondsPerHour * numHours
        }

        private fun isAdAvailable(): Boolean {
            return appOpenAd != null && wasLoadTimeLessThanNHoursAgo(4)
        }

        fun showAdIfAvailable(activity: Activity?) {
            if (isShowingAd) return
            if (!isAdAvailable()) {
                loadAd()
                return
            }
            appOpenAd?.fullScreenContentCallback = object : FullScreenContentCallback() {
                override fun onAdDismissedFullScreenContent() {
                    appOpenAd = null
                    isShowingAd = false
                    loadAd()
                }
                override fun onAdFailedToShowFullScreenContent(adError: AdError) {
                    appOpenAd = null
                    isShowingAd = false
                    loadAd()
                }
                override fun onAdShowedFullScreenContent() {
                    isShowingAd = true
                }
            }
            activity?.let {
                appOpenAd?.show(it)
            }
        }
    }
}
"""
    with open(f"{package_path}/WatermarkerApp.kt", "w") as f:
        f.write(app_content)
    print("✅ 5-5 Generated WatermarkerApp.kt (Fixed Ambiguity Error)")

if __name__ == "__main__":
    generate()
