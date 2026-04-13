import os

def generate_gradle_files():
    # 1. build.gradle (Root)
    build_gradle_content = """
buildscript {
    repositories { google(); mavenCentral() }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.7.0'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:2.0.21"
    }
}
allprojects {
    repositories { google(); mavenCentral() }
}
"""

    # 2. app/build.gradle
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
        versionCode 1
        versionName "1.0"
        externalNativeBuild { cmake { cppFlags "" } }
    }
    buildFeatures { compose true }
    compileOptions { sourceCompatibility JavaVersion.VERSION_11; targetCompatibility JavaVersion.VERSION_11 }
    kotlinOptions { jvmTarget = '11' }
    externalNativeBuild { cmake { path "src/main/cpp/CMakeLists.txt" } }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.15.0'
    implementation 'androidx.activity:activity-compose:1.9.3'
    implementation platform('androidx.compose:compose-bom:2024.10.01')
    implementation 'androidx.compose.ui:ui'
    implementation 'androidx.compose.material3:material3'
    // Logic Fault Fix: Added Material components for XML theme support
    implementation 'com.google.android.material:material:1.12.0'
}
"""

    # 3. settings.gradle & gradle.properties
    settings_content = "rootProject.name = 'WaterMarker'\\ninclude ':app'"
    properties_content = "android.useAndroidX=true\\nandroid.enableJetifier=true"

    files = {
        "build.gradle": build_gradle_content,
        "app/build.gradle": app_gradle_content,
        "settings.gradle": settings_content,
        "gradle.properties": properties_content
    }

    for path, content in files.items():
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, "w") as f:
            f.write(content.strip())
    print("✅ Gradle configs and AndroidX properties updated.")

if __name__ == "__main__":
    generate_gradle_files()
