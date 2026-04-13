import os

def generate_kotlin_ui():
    # 1. NativeEngine.kt - The JNI Bridge
    native_engine_content = """
package com.watermarker

import android.graphics.Bitmap

class NativeEngine {
    companion object {
        init {
            System.loadLibrary("watermarker")
        }
    }

    external fun blendImages(
        base: Bitmap, 
        overlay: Bitmap, 
        x: Float, 
        y: Float, 
        scale: Float, 
        rotation: Float, 
        opacity: Float
    )
}
"""

    # 2. MainActivity.kt - Full Logic with Save Functionality
    main_activity_content = """
package com.watermarker

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.io.InputStream
import java.io.OutputStream

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            WaterMarkerUI()
        }
    }
}

@Composable
fun WaterMarkerUI() {
    val context = LocalContext.current
    var baseBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var overlayBitmap by remember { mutableStateOf<Bitmap?>(null) }
    
    // State mirroring your HTML logic (Coordinates in pixels relative to base)
    var x by remember { mutableStateOf(0f) }
    var y by remember { mutableStateOf(0f) }
    var scale by remember { mutableStateOf(0.2f) }
    var rotation by remember { mutableStateOf(0f) }
    var opacity by remember { mutableStateOf(0.8f) }

    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { 
            val b = decodeUri(context, it)
            b?.let {
                baseBitmap = it
                x = it.width / 2f
                y = it.height / 2f
            }
        }
    }
    
    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { overlayBitmap = decodeUri(context, it) }
    }

    Column(modifier = Modifier.fillMaxSize().background(Color(0xFF020617))) {
        // Header
        Column(modifier = Modifier.padding(16.dp)) {
            Text("1. SELECT OVERLAY", color = Color(0xFF38BDF8), fontSize = 10.sp, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Button(
                onClick = { overlayPicker.launch("image/*") },
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0F172A))
            ) { Text("Load Overlay", color = Color.White) }
        }

        // Sub-header
        Row(
            modifier = Modifier.fillMaxWidth().background(Color(0xFF1E293B)).padding(16.dp), 
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("2. SUBJECT IMAGE", color = Color(0xFF38BDF8), fontSize = 10.sp, fontWeight = androidx.compose.ui.text.font.FontWeight.Bold)
            Button(onClick = { basePicker.launch("image/*") }) { Text("Load Subject") }
        }

        // Workspace (Canvas)
        Box(modifier = Modifier.weight(1f).fillMaxWidth().background(Color.Black).pointerInput(Unit) {
            detectTransformGestures { _, pan, zoom, rot ->
                x += pan.x
                y += pan.y
                scale *= zoom
                rotation += rot
            }
        }) {
            baseBitmap?.let {
                Canvas(modifier = Modifier.fillMaxSize()) {
                    // This draws a simple preview. 
                    // In a pixel-perfect app, we'd use DrawScope transformation to match C++ logic.
                    drawImage(it.asImageBitmap())
                }
            } ?: Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No Image Loaded", color = Color.DarkGray)
            }
        }

        // Footer
        Column(modifier = Modifier.background(Color(0xFF0F172A)).padding(16.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Overlay Opacity", color = Color(0xFF94A3B8), fontSize = 11.sp)
                Text("${(opacity * 100).toInt()}%", color = Color(0xFF38BDF8), fontSize = 11.sp)
            }
            Slider(value = opacity, onValueChange = { opacity = it }, colors = SliderDefaults.colors(thumbColor = Color(0xFF38BDF8)))
            
            Spacer(modifier = Modifier.height(8.dp))
            
            Button(
                onClick = {
                    if (baseBitmap != null && overlayBitmap != null) {
                        saveFullResolution(context, baseBitmap!!, overlayBitmap!!, x, y, scale, rotation, opacity)
                    } else {
                        Toast.makeText(context, "Select both images first", Toast.LENGTH_SHORT).show()
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF38BDF8))
            ) {
                Text("SAVE FULL RESOLUTION", color = Color(0xFF020617), fontWeight = androidx.compose.ui.text.font.FontWeight.ExtraBold)
            }
        }
    }
}

fun decodeUri(context: Context, uri: Uri): Bitmap? {
    val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
    val original = BitmapFactory.decodeStream(inputStream)
    // Create a mutable copy in ARGB_8888 so C++ can manipulate pixels
    return original?.copy(Bitmap.Config.ARGB_8888, true)
}

fun saveFullResolution(context: Context, base: Bitmap, overlay: Bitmap, x: Float, y: Float, scale: Float, rotation: Float, opacity: Float) {
    // 1. Run the Native C++ Engine
    NativeEngine().blendImages(base, overlay, x, y, scale, rotation, opacity)

    // 2. Save to Media Store
    val filename = "WaterMarker_${System.currentTimeMillis()}.png"
    val contentValues = ContentValues().apply {
        put(MediaStore.MediaColumns.DISPLAY_NAME, filename)
        put(MediaStore.MediaColumns.MIME_TYPE, "image/png")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            put(MediaStore.MediaColumns.RELATIVE_PATH, "Pictures/WaterMarker")
        }
    }

    val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, contentValues)
    uri?.let {
        val outputStream: OutputStream? = context.contentResolver.openOutputStream(it)
        outputStream?.use { stream ->
            base.compress(Bitmap.CompressFormat.PNG, 100, stream)
            Toast.makeText(context, "Saved to Gallery!", Toast.LENGTH_LONG).show()
        }
    }
}
"""

    files = {
        "app/src/main/java/com/watermarker/NativeEngine.kt": native_engine_content,
        "app/src/main/java/com/watermarker/MainActivity.kt": main_activity_content
    }

    print("📱 Generating Kotlin UI and JNI Bridge...")
    for path, content in files.items():
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content.strip())
            print(f"✅ Generated: {path}")
        except Exception as e:
            print(f"❌ Failed to write {path}: {e}")

    print("\n✨ UI logic complete. Proceed to script 6 for the build.")

if __name__ == "__main__":
    generate_kotlin_ui()
