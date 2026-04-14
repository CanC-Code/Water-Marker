# ... inside scripts/2-gradle-config.py ...
# Update the defaultConfig section:
    app_gradle_content = """
plugins {
    id 'com.android.application'
    id 'kotlin-android'
    id 'org.jetbrains.kotlin.plugin.compose' version '2.0.21'
}

android {
    namespace 'com.watermarker'
    compileSdk 35

    defaultConfig {
        applicationId "com.watermarker"
        minSdk 24
        targetSdk 35
        versionCode 2  // Incremented to force update recognition
        versionName "1.1"
        
        externalNativeBuild {
            cmake { cppFlags "" }
        }
    }
    # ... rest of the content ...
"""
