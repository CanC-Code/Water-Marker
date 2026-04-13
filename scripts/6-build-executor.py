import os
import subprocess

def run_build():
    print("🏗️ Initializing Final Build...")
    
    # Logic Fix: Navigate to root if script is run from /scripts
    if os.path.basename(os.getcwd()) == "scripts":
        os.chdir("..")

    try:
        # Force stable Gradle version to avoid API breaks
        if not os.path.exists("gradlew"):
            print("📦 Generating stable Gradle 8.10.2 wrapper...")
            subprocess.run(["gradle", "wrapper", "--gradle-version", "8.10.2"], check=True)
        
        # Ensure wrapper is executable
        subprocess.run(["chmod", "+x", "gradlew"], check=True)
        
        print("🚀 Running Clean Build...")
        # Use clean to ensure no leftover artifacts from previous failed attempts
        subprocess.run(["./gradlew", "clean", "assembleDebug", "--no-daemon"], check=True)
        print("✅ Build Successful! APK located in app/build/outputs/apk/debug/")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with exit code {e.returncode}")
        exit(1)

if __name__ == "__main__":
    run_build()
