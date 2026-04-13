import os

def generate_gradle_files():
    # Logic Fix: Added settings.gradle to define the project structure
    settings_content = """
rootProject.name = "WaterMarker"
include ':app'
"""

    root_gradle_content = """
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

    app_gradle_content = """
plugins {
    id 'com.android.application'
    id 'kotlin-android'
    id 'kotlin-compose'
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
    buildTypes { release { minifyEnabled false } }
    compileOptions { sourceCompatibility JavaVersion.VERSION_11; targetCompatibility JavaVersion.VERSION_11 }
    kotlinOptions { jvmTarget = '11' }
    buildFeatures { compose true }
    externalNativeBuild { cmake { path "src/main/cpp/CMakeLists.txt" } }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.15.0'
    implementation 'androidx.activity:activity-compose:1.9.3'
    implementation platform('androidx.compose:compose-bom:2024.10.01')
    implementation 'androidx.compose.ui:ui'
    implementation 'androidx.compose.material3:material3'
    implementation 'androidx.compose.ui:ui-tooling-preview'
}
"""

    files = {
        "settings.gradle": settings_content,
        "build.gradle": root_gradle_content,
        "app/build.gradle": app_gradle_content
    }

    for path, content in files.items():
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, "w") as f:
            f.write(content.strip())
    print("✅ Gradle configuration files updated.")

if __name__ == "__main__":
    generate_gradle_files()
