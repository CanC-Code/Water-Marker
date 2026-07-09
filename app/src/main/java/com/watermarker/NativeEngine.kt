package com.watermarker
import android.graphics.Bitmap
class NativeEngine {
    init { System.loadLibrary("watermarker") }
    external fun processWatermark(baseBitmap: Bitmap, overlayBitmap: Bitmap,
                                  realOffsetX: Float, realOffsetY: Float,
                                  realOverScale: Float, overlayRotation: Float,
                                  overlayAlpha: Float): Boolean
}