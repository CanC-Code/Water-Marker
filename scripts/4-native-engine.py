import os

def generate_native_layer():
    # 1. CMakeLists.txt - Tells the NDK how to compile the C++ code
    cmake_content = """
cmake_minimum_required(VERSION 3.22.1)
project("watermarker")

find_library(log-lib log)
find_library(graphics-lib jnigraphics)

add_library(watermarker SHARED native-lib.cpp)

target_link_libraries(watermarker
    ${log-lib}
    ${graphics-lib}
)
"""

    # 2. native-lib.cpp - The actual C++ logic for pixel blending
    cpp_content = """
#include <jni.h>
#include <android/bitmap.h>
#include <android/log.h>
#include <cmath>
#include <algorithm>

#define LOG_TAG "WaterMarkerNative"
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, LOG_TAG, __VA_ARGS__)

extern "C"
JNIEXPORT void JNICALL
Java_com_watermarker_NativeEngine_blendImages(
    JNIEnv* env, jobject thiz,
    jobject baseBitmap, jobject overlayBitmap,
    jfloat x, jfloat y, jfloat scale, jfloat rotation, jfloat opacity) {

    AndroidBitmapInfo baseInfo;
    AndroidBitmapInfo overlayInfo;
    void* basePixels;
    void* overlayPixels;

    if (AndroidBitmap_getInfo(env, baseBitmap, &baseInfo) < 0 ||
        AndroidBitmap_getInfo(env, overlayBitmap, &overlayInfo) < 0) return;

    if (AndroidBitmap_lockPixels(env, baseBitmap, &basePixels) < 0 ||
        AndroidBitmap_lockPixels(env, overlayBitmap, &overlayPixels) < 0) return;

    int bw = baseInfo.width;
    int bh = baseInfo.height;
    int ow = overlayInfo.width;
    int oh = overlayInfo.height;

    // Calculate overlay dimensions based on scale relative to base width
    float targetOw = bw * scale;
    float aspect = (float)oh / (float)ow;
    float targetOh = targetOw * aspect;

    float rad = rotation * M_PI / 180.0f;
    float cosA = cos(rad);
    float sinA = sin(rad);

    uint32_t* baseData = (uint32_t*)basePixels;
    uint32_t* overlayData = (uint32_t*)overlayPixels;

    // Simple bounding box for the overlay to optimize loops
    // In a production app, we'd calculate the exact dirty rect.
    for (int py = 0; py < bh; py++) {
        for (int px = 0; px < bw; px++) {
            
            // Translate to overlay center and rotate back to find source pixel
            float dx = px - x;
            float dy = py - y;
            
            float srcX = (dx * cosA + dy * sinA) / (targetOw / ow) + (ow / 2.0f);
            float srcY = (-dx * sinA + dy * cosA) / (targetOh / oh) + (oh / 2.0f);

            if (srcX >= 0 && srcX < ow && srcY >= 0 && srcY < oh) {
                uint32_t overCol = overlayData[(int)srcY * ow + (int)srcX];
                uint32_t baseCol = baseData[py * bw + px];

                // Extract ARGB (assuming RGBA_8888)
                float a = ((overCol >> 24) & 0xFF) / 255.0f * opacity;
                if (a <= 0) continue;

                uint8_t r = (uint8_t)(((overCol >> 0) & 0xFF) * a + ((baseCol >> 0) & 0xFF) * (1 - a));
                uint8_t g = (uint8_t)(((overCol >> 8) & 0xFF) * a + ((baseCol >> 8) & 0xFF) * (1 - a));
                uint8_t b = (uint8_t)(((overCol >> 16) & 0xFF) * a + ((baseCol >> 16) & 0xFF) * (1 - a));

                baseData[py * bw + px] = (0xFF << 24) | (b << 16) | (g << 8) | r;
            }
        }
    }

    AndroidBitmap_unlockPixels(env, baseBitmap);
    AndroidBitmap_unlockPixels(env, overlayBitmap);
}
"""

    files = {
        "app/src/main/cpp/CMakeLists.txt": cmake_content,
        "app/src/main/cpp/native-lib.cpp": cpp_content
    }

    print("🛠️  Generating Native C++ Engine...")
    for path, content in files.items():
        try:
            with open(path, "w") as f:
                f.write(content.strip())
            print(f"✅ Generated: {path}")
        except Exception as e:
            print(f"❌ Failed to write {path}: {e}")

if __name__ == "__main__":
    generate_native_layer()
