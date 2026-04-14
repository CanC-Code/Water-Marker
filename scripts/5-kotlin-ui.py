import os

def generate_ui():
    engine_content = """package com.watermarker
import android.graphics.Bitmap
class NativeEngine {
    companion object { init { System.loadLibrary("watermarker") } }
    external fun blendImages(base: Bitmap, overlay: Bitmap, x: Float, y: Float, scale: Float, rotation: Float, opacity: Float)
}
"""

    main_activity_content = """package com.watermarker

import android.content.ContentValues
import android.content.Context
import android.graphics.*
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { WaterMarkerUI() }
    }
}

@Composable
fun WaterMarkerUI() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    
    var baseBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var activeOverlay by remember { mutableStateOf<Bitmap?>(null) }
    
    // UI State
    var fileName by remember { mutableStateOf("MyWatermark") }
    var overlayX by remember { mutableStateOf(0f) }
    var overlayY by remember { mutableStateOf(0f) }
    var overlayScale by remember { mutableStateOf(1f) }
    var overlayRotation by remember { mutableStateOf(0f) }
    var opacity by remember { mutableStateOf(1.0f) }
    var isSaving by remember { mutableStateOf(false) }

    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { baseBitmap = decodeUri(context, it) }
    }
    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { activeOverlay = decodeUri(context, it) }
    }

    Column(modifier = Modifier.fillMaxSize().background(Color(0xFF020617))) {
        // Toolbar
        Row(modifier = Modifier.fillMaxWidth().padding(8.dp), horizontalArrangement = Arrangement.SpaceBetween) {
            Button(onClick = { basePicker.launch("image/*") }) { Text("LOAD IMAGE", fontSize = 10.sp) }
            Button(onClick = { overlayPicker.launch("image/*") }) { Text("OVERLAY", fontSize = 10.sp) }
        }

        // The Workspace Canvas
        BoxWithConstraints(modifier = Modifier.weight(1f).fillMaxWidth().background(Color.Black).clipToBounds()) {
            val constraints = this
            baseBitmap?.let { base ->
                // Calculate "Fit" Scale
                val canvasRatio = constraints.maxWidth / constraints.maxHeight
                val imageRatio = base.width.toFloat() / base.height.toFloat()
                
                val fitScale = if (imageRatio > canvasRatio) {
                    constraints.maxWidth.value / base.width.toFloat()
                } else {
                    constraints.maxHeight.value / base.height.toFloat()
                }

                Canvas(modifier = Modifier.fillMaxSize().pointerInput(Unit) {
                    detectTransformGestures { _, pan, zoom, rot ->
                        overlayX += pan.x / fitScale
                        overlayY += pan.y / fitScale
                        overlayScale *= zoom
                        overlayRotation += rot
                    }
                }) {
                    drawContext.canvas.save()
                    drawContext.canvas.translate(size.width / 2f, size.height / 2f)
                    drawContext.canvas.scale(fitScale, fitScale)

                    // Draw the Base (Original Image)
                    drawImage(base.asImageBitmap(), dstOffset = IntOffset(-base.width / 2, -base.height / 2))

                    // Draw Overlay relative to Base center
                    activeOverlay?.let { over ->
                        drawContext.canvas.save()
                        drawContext.canvas.translate(overlayX, overlayY)
                        drawContext.canvas.rotate(overlayRotation)
                        drawContext.canvas.scale(overlayScale, overlayScale)
                        drawImage(
                            over.asImageBitmap(), 
                            alpha = opacity,
                            dstOffset = IntOffset(-over.width / 2, -over.height / 2)
                        )
                        drawContext.canvas.restore()
                    }
                    drawContext.canvas.restore()
                }
            }
        }

        // QOL Footer
        Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))) {
            Column(modifier = Modifier.padding(16.dp)) {
                OutlinedTextField(
                    value = fileName,
                    onValueChange = { fileName = it },
                    label = { Text("Filename") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(unfocusedTextColor = Color.White, focusedTextColor = Color.White)
                )
                Spacer(Modifier.height(8.dp))
                Text("Opacity: ${(opacity * 100).toInt()}%", color = Color.White)
                Slider(value = opacity, onValueChange = { opacity = it })
                
                Button(
                    onClick = {
                        if (baseBitmap != null && activeOverlay != null) {
                            scope.launch {
                                isSaving = true
                                saveLossless(context, baseBitmap!!, activeOverlay!!, overlayX, overlayY, overlayScale, overlayRotation, opacity, fileName)
                                isSaving = false
                            }
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF38BDF8))
                ) {
                    Text(if (isSaving) "COMPRESSING..." else "EXPORT LOSSLESS IMAGE")
                }
            }
        }
    }
}

fun decodeUri(context: Context, uri: Uri): Bitmap? {
    return try {
        context.contentResolver.openInputStream(uri)?.use { 
            BitmapFactory.decodeStream(it, null, BitmapFactory.Options().apply { inMutable = true })
        }
    } catch (e: Exception) { null }
}

suspend fun saveLossless(context: Context, base: Bitmap, overlay: Bitmap, x: Float, y: Float, s: Float, r: Float, a: Float, name: String) {
    withContext(Dispatchers.IO) {
        // Pixel Matching logic: create a bitmap of exact dimensions as original
        val result = base.copy(Bitmap.Config.ARGB_8888, true)
        val canvas = Canvas(result)
        val paint = Paint().apply { alpha = (a * 255).toInt() }
        
        val matrix = Matrix()
        // Aligning coordinates to match the Canvas logic exactly
        matrix.postTranslate(-overlay.width / 2f, -overlay.height / 2f)
        matrix.postScale(s, s)
        matrix.postRotate(r)
        matrix.postTranslate(base.width / 2f + x, base.height / 2f + y)
        
        canvas.drawBitmap(overlay, matrix, paint)

        val cleanName = name.replace("[^a-zA-Z0-9]".toRegex(), "_")
        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, "$cleanName.webp")
            put(MediaStore.MediaColumns.MIME_TYPE, "image/webp")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.MediaColumns.RELATIVE_PATH, "Pictures/WaterMarker")
            }
        }

        val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
        uri?.let {
            context.contentResolver.openOutputStream(it)?.use { stream ->
                // 2026 Strategy: WEBP_LOSSLESS for max size reduction with 0 quality loss
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    result.compress(Bitmap.CompressFormat.WEBP_LOSSLESS, 100, stream)
                } else {
                    result.compress(Bitmap.CompressFormat.PNG, 100, stream)
                }
            }
        }
        withContext(Dispatchers.Main) { 
            Toast.makeText(context, "Metadata Stripped & Saved to Gallery", Toast.LENGTH_LONG).show() 
        }
    }
}
"""

    package_path = "app/src/main/java/com/watermarker"
    files = {
        f"{package_path}/NativeEngine.kt": engine_content.strip(),
        f"{package_path}/MainActivity.kt": main_activity_content.strip()
    }

    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Logic Updated: Fit-to-screen, Metadata stripping, and WebP Lossless enabled.")

if __name__ == "__main__":
    generate_ui()
