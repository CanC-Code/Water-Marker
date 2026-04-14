import os
import subprocess

def run_build():
    if os.path.basename(os.getcwd()) == "scripts":
        os.chdir("..")
    try:
        if not os.path.exists("gradlew"):
            subprocess.run(["gradle", "wrapper", "--gradle-version", "8.10.2"], check=True)
        subprocess.run(["chmod", "+x", "gradlew"], check=True)
        subprocess.run(["./gradlew", "clean", "assembleDebug", "--no-daemon"], check=True)
        print("✅ Build Successful! APK in app/build/outputs/apk/debug/")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run_build()
