import os

def generate_resources():
    # Logic Fix: Added 'package' for compatibility and included icon references
    # Also added 'supportsRtl' and 'extractNativeLibs' for better installation stability
    manifest = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.watermarker">

    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />

    <application 
        android:label="WaterMarker" 
        android:theme="@style/Theme.WaterMarker"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:allowBackup="true"
        android:supportsRtl="true"
        android:extractNativeLibs="true">
        
        <activity 
            android:name=".MainActivity" 
            android:exported="true"
            android:configChanges="orientation|screenSize|screenLayout|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

    # Added primary variant colors to ensure the Material 3 theme links correctly
    colors = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="purple_200">#FFBB86FC</color>
    <color name="purple_500">#FF6200EE</color>
    <color name="purple_700">#FF3700B3</color>
    <color name="teal_200">#FF03DAC5</color>
    <color name="black">#FF000000</color>
    <color name="white">#FFFFFFFF</color>
</resources>
"""

    # Updated theme to use the new colors and handle the ActionBar fault
    themes = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.WaterMarker" parent="Theme.Material3.DayNight.NoActionBar">
        <item name="colorPrimary">@color/purple_500</item>
        <item name="colorPrimaryVariant">@color/purple_700</item>
        <item name="colorOnPrimary">@color/white</item>
        <item name="android:statusBarColor">@color/black</item>
    </style>
</resources>
"""

    files = {
        "app/src/main/AndroidManifest.xml": manifest.strip(),
        "app/src/main/res/values/colors.xml": colors.strip(),
        "app/src/main/res/values/themes.xml": themes.strip()
    }

    print("🎨 Generating Resources and Manifest...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        print(f"  Generated: {path}")
        
    print("✅ Resources and Manifest complete.")

if __name__ == "__main__":
    generate_resources()
