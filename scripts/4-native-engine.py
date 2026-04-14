import os

def generate_native():
    # CMake configuration for the NDK build system
    cmake_content = """
cmake_minimum_required(VERSION 3.22.1)
project("watermarker")

# Logic Fix: Added jnigraphics to the library link list 
# This is required to use AndroidBitmap functions
add_library(watermarker SHARED native-lib.cpp)
find_library(log-lib log)
find_library(jnigraphics-lib jnigraphics)

target_link_libraries(watermarker ${log-lib} ${jnigraphics-lib})
"""

    # C++ Implementation of the blending logic
    cpp_content = """
#include <jni.h>
#include <android/bitmap.h>
#include <android/log.h>

#define LOG_TAG "WaterMarkerNative"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

extern "C" JNIEXPORT void JNICALL
Java_com_watermarker_NativeEngine_blendImages(
    JNIEnv* env, jobject thiz, 
    jobject base, jobject overlay, 
    jfloat x, jfloat y, jfloat scale, jfloat rotation, jfloat opacity) {
    
    AndroidBitmapInfo baseInfo;
    AndroidBitmapInfo overInfo;
    void* basePixels;
    void* overPixels;

    // 1. Validate and Lock Bitmaps
    if (AndroidBitmap_getInfo(env, base, &baseInfo) < 0 ||
        AndroidBitmap_getInfo(env, overlay, &overInfo) < 0) {
        LOGE("Failed to get bitmap info");
        return;
    }

    if (AndroidBitmap_lockPixels(env, base, &basePixels) < 0 ||
        AndroidBitmap_lockPixels(env, overlay, &overPixels) < 0) {
        LOGE("Failed to lock pixels");
        return;
    }

    // 2. Simple Blending Logic (Simplified for demonstration)
    // In a production app, we would loop through the pixels 
    // and apply the scale/rotation/opacity math here.
    // For now, we ensure the native bridge is secure and functional.

    // 3. Unlock Pixels (Crucial to prevent memory leaks/crashes)
    AndroidBitmap_unlockPixels(env, base);
    AndroidBitmap_unlockPixels(env, overlay);
}
"""

    files = {
        "app/src/main/cpp/CMakeLists.txt": cmake_content.strip(),
        "app/src/main/cpp/native-lib.cpp": cpp_content.strip()
    }

    print("🛠️ Generating Native C++ Engine...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        print(f"  Generated: {path}")
    
    print("✅ Native Engine structure complete.")

if __name__ == "__main__":
    generate_native()
