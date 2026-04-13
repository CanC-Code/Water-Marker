import os
import subprocess

def run_build():
    print("🏗️ Initializing Final Build...")
    
    # Ensure we are in the root directory
    if os.path.basename(os.getcwd()) == "scripts":
        os.chdir("..")

    try:
        # Logic Fault Fix: Ensure local wrapper is generated and prioritized
        if not os.path.exists("gradlew"):
            print("📦 Generating stable Gradle 8.10.2 wrapper...")
            subprocess.run(["gradle", "wrapper", "--gradle-version", "8.10.2"], check=True)
        
        subprocess.run(["chmod", "+x", "gradlew"], check=True)
        
        print("🚀 Executing Clean Build via Wrapper...")
        # CRITICAL: Always use ./gradlew to ensure the 8.10.2 version is used
        subprocess.run(["./gradlew", "clean", "assembleDebug", "--no-daemon"], check=True)
        print("✅ Build Successful!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with exit code {e.returncode}")
        exit(1)

if __name__ == "__main__":
    run_build()
