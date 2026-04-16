import os

def generate():
    manifest_dir = "app/src/main"
    res_values_dir = "app/src/main/res/values"
    os.makedirs(manifest_dir, exist_ok=True)
    os.makedirs(res_values_dir, exist_ok=True)

    # 1. colors.xml
    colors_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="primary">#6200EE</color>
    <color name="primary_variant">#3700B3</color>
    <color name="white">#FFFFFF</color>
</resources>
"""
    with open(f"{res_values_dir}/colors.xml", "w") as f:
        f.write(colors_content)

    # 2. themes.xml - Explicitly using library-defined Material3 tokens
    themes_content = """<?xml version="1.0" encoding="utf-8"?>
<resources xmlns:tools="http://schemas.android.com/tools">
    <style name="Theme.Watermarker" parent="Theme.Material3.DayNight.NoActionBar">
        <item name="colorPrimary">@color/primary</item>
        <item name="android:statusBarColor">@color/primary_variant</item>
    </style>
</resources>
"""
    with open(f"{res_values_dir}/themes.xml", "w") as f:
        f.write(themes_content)

    # 3. AndroidManifest.xml
    manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />

    <application
        android:name=".WatermarkerApp"
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="Water Marker"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.Watermarker">

        <meta-data
            android:name="com.google.android.gms.ads.APPLICATION_ID"
            android:value="ca-app-pub-7732503595590477~5528698466"/>

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""
    with open(f"{manifest_dir}/AndroidManifest.xml", "w") as f:
        f.write(manifest_content)
    
    print("✅ 3 Updated Manifest & Resources (XML Linking Fixed)")

if __name__ == "__main__":
    generate()
