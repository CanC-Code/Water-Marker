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

    # 2. MainActivity.kt - The UI and Touch Logic
    # This is a large file, it replicates your HTML state and touch engine
    main_activity_content = """
package com.watermarker

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.os.Bundle
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
    
    // State mirroring your HTML logic
    var x by remember { mutableStateOf(500f) }
    var y by remember { mutableStateOf(500f) }
    var scale by remember { mutableStateOf(0.2f) }
    var rotation by remember { mutableStateOf(0f) }
    var opacity by remember { mutableStateOf(0.8f) }

    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { baseBitmap = decodeUri(context, it) }
    }
    
    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { overlayBitmap = decodeUri(context, it) }
    }

    Column(modifier = Modifier.fillMaxSize().background(Color(0xFF020617))) {
        // Header
        Column(modifier = Modifier.padding(16.dp)) {
            Text("1. SELECT OVERLAY", color = Color(0xFF38BDF8), fontSize = 10.sp)
            Button(onClick = { overlayPicker.launch("image/*") }) { Text("Load Overlay") }
        }

        // Sub-header
        Row(modifier = Modifier.fillMaxWidth().padding(16.dp), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("2. SUBJECT IMAGE", color = Color(0xFF38BDF8), fontSize = 10.sp)
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
                    drawImage(it.asImageBitmap())
                    // Note: In a real app, we'd draw a preview here.
                    // For the "Save" step, we call the Native C++ Engine.
                }
            }
        }

        // Footer
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Overlay Opacity: ${(opacity * 100).toInt()}%", color = Color.White)
            Slider(value = opacity, onValueChange = { opacity = it })
            Button(
                onClick = { /* Call NativeEngine().blendImages(...) then save to file */ },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF38BDF8))
            ) {
                Text("SAVE FULL RESOLUTION", color = Color.Black)
            }
        }
    }
}

fun decodeUri(context: android.content.Context, uri: Uri): Bitmap? {
    val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
    return BitmapFactory.decodeStream(inputStream)
}
"""

    files = {
        "app/src/main/java/com/watermarker/NativeEngine.kt": native_engine_content,
        "app/src/main/java/com/watermarker/MainActivity.kt": main_activity_content
    }

    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content.strip())
            
    print("📱 Kotlin UI and JNI Bridge Generated.")

if __name__ == "__main__":
    generate_kotlin_ui()
