import os
import subprocess
import sys

def run_build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)

    print("🏗️  Starting API 35 Build Sequence...")
    
    try:
        # Check for Gradle Wrapper
        if not os.path.exists("gradlew"):
            print("📦 Generating Gradle wrapper...")
            subprocess.run(["gradle", "wrapper", "--gradle-version", "8.10.2"], check=True)
        
        if sys.platform != "win32":
            subprocess.run(["chmod", "+x", "gradlew"], check=True)
        
        # Logic Fix: Use clean to remove the previous API 34 artifacts
        print("🚀 Executing: ./gradlew clean assembleDebug --no-daemon")
        subprocess.run(["./gradlew", "clean", "assembleDebug", "--no-daemon"], check=True)
        
        # Verification
        apk_path = "app/build/outputs/apk/debug/app-debug.apk"
        if os.path.exists(apk_path):
            print(f"✅ SUCCESS! APK created at: {os.path.abspath(apk_path)}")
        else:
            print("❌ Build finished but APK was not found. Check logs for resource errors.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Gradle build failed (Exit {e.returncode}).")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    run_build()
