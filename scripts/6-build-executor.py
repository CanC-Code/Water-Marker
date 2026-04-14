import os
import subprocess
import sys

def run_build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)

    print("🏗️  Initializing Final Build...")
    
    try:
        if not os.path.exists("gradlew"):
            print("📦 Generating stable Gradle 8.10.2 wrapper...")
            subprocess.run(["gradle", "wrapper", "--gradle-version", "8.10.2"], check=True)
        
        if sys.platform != "win32":
            subprocess.run(["chmod", "+x", "gradlew"], check=True)
        
        print("🚀 Running Clean Build...")
        subprocess.run(["./gradlew", "clean", "assembleDebug", "--no-daemon"], check=True)
        
        apk_path = "app/build/outputs/apk/debug/app-debug.apk"
        if os.path.exists(apk_path):
            print("✅ Build Successful! APK located.")
        else:
            print("❌ Build finished but APK was not found.")
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"❌ Gradle build failed with exit code {e.returncode}")
        sys.exit(1) # Signal failure to GitHub Actions
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_build()
