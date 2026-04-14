import os
import subprocess
import sys

def run_build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)

    try:
        if not os.path.exists("gradlew"):
            subprocess.run(["gradle", "wrapper", "--gradle-version", "8.10.2"], check=True)
        
        if sys.platform != "win32":
            subprocess.run(["chmod", "+x", "gradlew"], check=True)
        
        subprocess.run(["./gradlew", "clean", "assembleDebug", "--no-daemon"], check=True)
        print("✅ APK Build Successful!")

    except subprocess.CalledProcessError:
        print("❌ Build failed.")
        sys.exit(1)

if __name__ == "__main__":
    run_build()
