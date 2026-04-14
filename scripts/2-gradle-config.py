import os

def generate_gradle_files():
    # Root build script
    build_gradle = """
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.7.0'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:2.0.21"
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
"""

    # App-level build script
    app_gradle = """
plugins {
    id 'com.android.application'
    id 'kotlin-android'
    id 'org.jetbrains.kotlin.plugin.compose' version '2.0.21'
}

android {
    namespace 'com.watermarker'
    compileSdk 34  // Changed to 34 for broader stability

    defaultConfig {
        applicationId "com.watermarker"
        minSdk 24
        targetSdk 34 // Changed to 34
        versionCode 4 // Bumped to 4 to override previous failed installs
        versionName "1.3"
        
        externalNativeBuild {
            cmake {
                cppFlags ""
            }
        }
    }

    buildFeatures {
        compose true
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_11
        targetCompatibility JavaVersion.VERSION_11
    }
    
    kotlinOptions {
        jvmTarget = "11"
    }

    externalNativeBuild {
        cmake {
            path "src/main/cpp/CMakeLists.txt"
        }
    }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.15.0'
    implementation 'androidx.lifecycle:lifecycle-runtime-ktx:2.8.7'
    implementation 'androidx.activity:activity-compose:1.9.3'
    implementation platform('androidx.compose:compose-bom:2024.10.01')
    implementation 'androidx.compose.ui:ui'
    implementation 'androidx.compose.ui:ui-graphics'
    implementation 'androidx.compose.ui:ui-tooling-preview'
    implementation 'androidx.compose.material3:material3'
    implementation 'com.google.android.material:material:1.12.0'
}
"""

    settings_gradle = """
rootProject.name = "WaterMarker"
include ':app'
"""

    # Properties file to enable AndroidX
    gradle_properties = """
android.useAndroidX=true
android.enableJetifier=true
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
"""

    files = {
        "build.gradle": build_gradle.strip(),
        "app/build.gradle": app_gradle.strip(),
        "settings.gradle": settings_gradle.strip(),
        "gradle.properties": gradle_properties.strip()
    }

    for path, content in files.items():
        # Ensure subdirectory exists
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
            
    print("✅ Gradle configuration complete (SDK 34 / Version 4).")

if __name__ == "__main__":
    generate_gradle_files()
