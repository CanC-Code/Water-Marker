import os
import urllib.request

def generate_native_engine():
    cpp_dir = "app/src/main/cpp"
    os.makedirs(cpp_dir, exist_ok=True)
    
    # Download STB headers (if they don't exist)
    stb_urls = {
        "stb_image.h": "https://raw.githubusercontent.com/nothings/stb/master/stb_image.h",
        "stb_image_write.h": "https://raw.githubusercontent.com/nothings/stb/master/stb_image_write.h",
        "stb_image_resize.h": "https://raw.githubusercontent.com/nothings/stb/master/stb_image_resize.h"
    }
    
    for filename, url in stb_urls.items():
        filepath = os.path.join(cpp_dir, filename)
        if not os.path.exists(filepath):
            try:
                print(f"Downloading {filename}...")
                urllib.request.urlretrieve(url, filepath)
            except Exception as e:
                print(f"Failed to download {filename}: {e}")

    # CMakeLists.txt
    cmake_content = """cmake_minimum_required(VERSION 3.18.1)
project("watermarker")

add_library(watermarker SHARED watermarker.cpp)

find_library(log-lib log)
target_link_libraries(watermarker ${log-lib} jnigraphics)
"""

    # watermarker.cpp
    cpp_content = """#include <jni.h>
#include <string>
#include <android/log.h>
#include <cmath>
#include <algorithm>

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"
#define STB_IMAGE_RESIZE_IMPLEMENTATION
#define STB_IMAGE_RESIZE_STATIC
#include "stb_image_resize.h"

#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "NativeEngine", __VA_ARGS__)
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO, "NativeEngine", __VA_ARGS__)

// Bilinear interpolation for rotation
uint32_t getPixelBilinear(unsigned char* img, int width, int height, int channels, float x, float y) {
    int x1 = std::floor(x);
    int y1 = std::floor(y);
    int x2 = std::min(x1 + 1, width - 1);
    int y2 = std::min(y1 + 1, height - 1);

    if (x1 < 0 || x1 >= width || y1 < 0 || y1 >= height) return 0;

    float dx = x - x1;
    float dy = y - y1;

    unsigned char* p11 = img + (y1 * width + x1) * channels;
    unsigned char* p21 = img + (y1 * width + x2) * channels;
    unsigned char* p12 = img + (y2 * width + x1) * channels;
    unsigned char* p22 = img + (y2 * width + x2) * channels;

    uint32_t result = 0;
    for (int c = 0; c < channels; ++c) {
        float val = (p11[c] * (1 - dx) * (1 - dy)) +
                    (p21[c] * dx * (1 - dy)) +
                    (p12[c] * (1 - dx) * dy) +
                    (p22[c] * dx * dy);
        result |= (static_cast<uint8_t>(val) << (c * 8));
    }
    return result;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_watermarker_NativeEngine_processWatermark(JNIEnv* env, jobject /* this */,
                                                   jstring baseImagePath,
                                                   jstring overlayImagePath,
                                                   jstring outputPath,
                                                   jint quality,
                                                   jfloat overlayX,
                                                   jfloat overlayY,
                                                   jfloat overlayScale,
                                                   jfloat overlayRotation,
                                                   jfloat overlayAlpha,
                                                   jfloat previewWidth,
                                                   jfloat previewHeight) {
    
    const char* base_path = env->GetStringUTFChars(baseImagePath, nullptr);
    const char* overlay_path = env->GetStringUTFChars(overlayImagePath, nullptr);
    const char* out_path = env->GetStringUTFChars(outputPath, nullptr);

    int baseW, baseH, baseC;
    unsigned char* baseImg = stbi_load(base_path, &baseW, &baseH, &baseC, 4);
    
    if (!baseImg) {
        env->ReleaseStringUTFChars(baseImagePath, base_path);
        env->ReleaseStringUTFChars(overlayImagePath, overlay_path);
        env->ReleaseStringUTFChars(outputPath, out_path);
        return JNI_FALSE;
    }

    int overW, overH, overC;
    unsigned char* overImg = stbi_load(overlay_path, &overW, &overH, &overC, 4);

    if (!overImg) {
        stbi_image_free(baseImg);
        env->ReleaseStringUTFChars(baseImagePath, base_path);
        env->ReleaseStringUTFChars(overlayImagePath, overlay_path);
        env->ReleaseStringUTFChars(outputPath, out_path);
        return JNI_FALSE;
    }

    // 1. Calculate how much smaller the UI Preview Box is vs the Real Image
    float ratioX = (float)baseW / previewWidth;
    float ratioY = (float)baseH / previewHeight;
    float ratio = std::min(ratioX, ratioY);

    // 2. Scale the overlay image to match the real coordinates
    float realScale = overlayScale * ratio;
    int scaledOverW = std::max(1, (int)std::round(overW * realScale));
    int scaledOverH = std::max(1, (int)std::round(overH * realScale));
    
    unsigned char* scaledOverImg = new unsigned char[scaledOverW * scaledOverH * 4];
    stbir_resize_uint8(overImg, overW, overH, 0,
                       scaledOverImg, scaledOverW, scaledOverH, 0, 4);
    
    // 3. Rotation setup
    float rad = overlayRotation * M_PI / 180.0f;
    float cosR = std::cos(-rad);
    float sinR = std::sin(-rad);
    
    float cx = scaledOverW / 2.0f;
    float cy = scaledOverH / 2.0f;

    float centerX = baseW / 2.0f;
    float centerY = baseH / 2.0f;
    float overlayCenterX = centerX + (overlayX * ratio);
    float overlayCenterY = centerY + (overlayY * ratio);

    // 4. Blending loop with Alpha handling
    for (int y = 0; y < baseH; ++y) {
        for (int x = 0; x < baseW; ++x) {
            float px = x - overlayCenterX;
            float py = y - overlayCenterY;
            
            float srcX = px * cosR - py * sinR + cx;
            float srcY = px * sinR + py * cosR + cy;
            
            if (srcX >= 0 && srcX < scaledOverW - 1 && srcY >= 0 && srcY < scaledOverH - 1) {
                uint32_t pxl = getPixelBilinear(scaledOverImg, scaledOverW, scaledOverH, 4, srcX, srcY);
                uint8_t a = (pxl >> 24) & 0xFF;
                if (a > 0) {
                    float alpha = (a / 255.0f) * overlayAlpha;
                    uint8_t r = pxl & 0xFF;
                    uint8_t g = (pxl >> 8) & 0xFF;
                    uint8_t b = (pxl >> 16) & 0xFF;

                    int baseIdx = (y * baseW + x) * 4;
                    baseImg[baseIdx]     = (r * alpha) + (baseImg[baseIdx] * (1 - alpha));
                    baseImg[baseIdx + 1] = (g * alpha) + (baseImg[baseIdx + 1] * (1 - alpha));
                    baseImg[baseIdx + 2] = (b * alpha) + (baseImg[baseIdx + 2] * (1 - alpha));
                }
            }
        }
    }
    delete[] scaledOverImg;

    // 5. Output
    std::string out_path_str(out_path);
    int res = 0;
    if (out_path_str.find(".png") != std::string::npos) {
        res = stbi_write_png(out_path, baseW, baseH, 4, baseImg, baseW * 4);
    } else {
        res = stbi_write_jpg(out_path, baseW, baseH, 4, baseImg, quality);
    }

    stbi_image_free(baseImg);
    stbi_image_free(overImg);

    env->ReleaseStringUTFChars(baseImagePath, base_path);
    env->ReleaseStringUTFChars(overlayImagePath, overlay_path);
    env->ReleaseStringUTFChars(outputPath, out_path);

    return res ? JNI_TRUE : JNI_FALSE;
}
"""
    files = {
        f"{cpp_dir}/CMakeLists.txt": cmake_content.strip(),
        f"{cpp_dir}/watermarker.cpp": cpp_content.strip(),
    }
    for path, content in files.items():
        with open(path, "w") as f:
            f.write(content)
    print("✅ Native engine generated with Full Coordinate Translation and Opacity Control!")

if __name__ == "__main__":
    generate_native_engine()
