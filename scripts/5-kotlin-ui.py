import os

def generate_kotlin_ui():
    native_engine_content = """
package com.watermarker
import android.graphics.Bitmap
class NativeEngine {
    companion object {
        init { System.loadLibrary("watermarker") }
    }
    external fun blendImages(base: Bitmap, overlay: Bitmap, x: Float, y: Float, scale: Float, rotation: Float, opacity: Float)
}
"""

    main_activity_content = """
package com.watermarker

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Color as GColor
import android.graphics.Paint as GPaint
import android.graphics.Typeface as GTypeface
import android.graphics.Rect as GRect
import android.graphics.Matrix as GMatrix
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.InputStream
import java.io.OutputStream
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.toRadians

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

    // Pre-populate with our custom generated text overlay
    val handdrawnOverlay = remember { generateCutoutOverlayBitmap() }
    
    var baseBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var overlayLibrary by remember(handdrawnOverlay) { mutableStateOf(if (handdrawnOverlay != null) listOf(handdrawnOverlay) else emptyList<Bitmap>()) }
    var activeOverlay by remember(handdrawnOverlay) { mutableStateOf<Bitmap?>(handdrawnOverlay) }
    
    // State in Full-Res Image-space Pixels
    var x by remember { mutableStateOf(0f) }
    var y by remember { mutableStateOf(0f) }
    var scale by remember { mutableStateOf(0.2f) }
    var rotation by remember { mutableStateOf(0f) }
    var opacity by remember { mutableStateOf(0.8f) }
    
    // Base image rotation state (degrees, 0, 90, 180, 270)
    var baseRotation by remember { mutableStateOf(0f) }
    
    // Saving state and progress meter
    var isSaving by remember { mutableStateOf(false) }
    var savingMessage by remember { mutableStateOf("Saving Full Resolution...") }

    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { decodeUri(context, it)?.let { b -> 
            baseBitmap = b 
            // Correct the initial coordinates and handle aspect changes from rotation
            x = b.width / 2f
            y = b.height / 2f
            baseRotation = 0f // Reset base rotation on new image load
        }}
    }
    
    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { decodeUri(context, it)?.let { b -> 
            overlayLibrary = overlayLibrary + b
            activeOverlay = b 
        }}
    }

    // Main Layout (Mirroring original dark-themed Pro Studio)
    Column(modifier = Modifier.fillMaxSize().background(Color(0xFF020617))) {
        
        // 1. SELECT OVERLAY (Library list, dark background)
        Column(modifier = Modifier.background(Color(0xFF0F172A)).padding(horizontal = 16.dp, vertical = 10.dp)) {
            Text("1. SELECT OVERLAY", color = Color(0xFF38BDF8), fontSize = 10.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(8.dp))
            LazyRow(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                item {
                    // + button for new overlays
                    Box(
                        modifier = Modifier
                            .size(60.dp)
                            .border(2.dp, Color(0xFF94A3B8).copy(alpha = 0.3f), RoundedCornerShape(8.dp))
                            .clickable { overlayPicker.launch("image/*") },
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(Icons.Default.Add, contentDescription = null, tint = Color(0xFF94A3B8))
                    }
                }
                items(overlayLibrary) { item ->
                    Image(
                        bitmap = item.asImageBitmap(),
                        contentDescription = null,
                        modifier = Modifier
                            .size(60.dp)
                            .clip(RoundedCornerShape(8.dp))
                            // Highlight active overlay
                            .border(2.dp, if(activeOverlay == item) Color(0xFF38BDF8) else Color.Transparent, RoundedCornerShape(8.dp))
                            .clickable { activeOverlay = item },
                        contentScale = ContentScale.Fit
                    )
                }
            }
        }

        // 2. SUBJECT IMAGE (Load button row, slightly lighter background)
        Row(modifier = Modifier.fillMaxWidth().background(Color(0xFF1E293B)).padding(horizontal = 16.dp, vertical = 10.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("2. SUBJECT IMAGE", color = Color(0xFF38BDF8), fontSize = 10.sp, fontWeight = FontWeight.Bold)
            Button(
                onClick = { basePicker.launch("image/*") },
                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp),
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF38BDF8))
            ) {
                Text("LOAD SUBJECT", fontSize = 11.sp, color = Color(0xFF020617), fontWeight = FontWeight.ExtraBold)
            }
        }

        // 3. Workspace (Aspect-Fit Zoom/Pan Preview and touch engine, with base rotation support)
        Box(modifier = Modifier.weight(1f).fillMaxWidth().background(Color.Black).clipToBounds()
            .pointerInput(Unit) {
                detectTransformGestures { _, pan, zoom, rot ->
                    baseBitmap?.let { base ->
                        // Calculate effective dimensions to find correct displayScale
                        val effWidth = if (baseRotation % 180f != 0f) base.height else base.width
                        val effHeight = if (baseRotation % 180f != 0f) base.width else base.height
                        
                        val viewWidth = size.width
                        val viewHeight = size.height
                        val displayScaleW = viewWidth / effWidth.toFloat()
                        val displayScaleH = viewHeight / effHeight.toFloat()
                        val displayScale = minOf(displayScaleW, displayScaleH)

                        // --- TOUCH ENGINE FIX: Rotate Screen Pan vector by Negative Base Rotation ---
                        // A right swipe on a landscape image rotated to portrait is actually image-space Y movement.
                        val rotatedPan = rotateVector(pan, -baseRotation)
                        
                        x += rotatedPan.x / displayScale
                        y += rotatedPan.y / displayScale
                        scale *= zoom
                        rotation += rot
                    }
                }
            }
        ) {
            baseBitmap?.let { base ->
                // Aspect-Fit scaling logic for full preview, respecting base image rotation
                Canvas(modifier = Modifier.fillMaxSize()) {
                    val canvasWidth = size.width
                    val canvasHeight = size.height
                    
                    val effWidth = if (baseRotation % 180f != 0f) base.height else base.width
                    val effHeight = if (baseRotation % 180f != 0f) base.width else base.height

                    val scaleW = canvasWidth / effWidth.toFloat()
                    val scaleH = canvasHeight / effHeight.toFloat()
                    val drawScale = minOf(scaleW, scaleH)

                    val offsetX = (canvasWidth - effWidth * drawScale) / 2
                    val offsetY = (canvasHeight - effHeight * drawScale) / 2

                    // --- DRAWING ENGINE: Base Rotation and Overlay Relative Drawing ---
                    drawContext.canvas.save()
                    
                    // 1. Set up Rotated Coordinate System
                    // Translate to effective center and rotate
                    drawContext.canvas.translate(offsetX + effWidth * drawScale / 2, offsetY + effHeight * drawScale / 2)
                    drawContext.canvas.rotate(baseRotation)
                    
                    // 2. Draw the Unrotated Base Bitmap Centered in this new frame
                    drawImage(
                        base.asImageBitmap(), 
                        dstOffset = androidx.compose.ui.unit.IntOffset(-(base.width * drawScale / 2).toInt(), -(base.height * drawScale / 2).toInt()), 
                        dstSize = androidx.compose.ui.unit.IntSize((base.width * drawScale).toInt(), (base.height * drawScale).toInt())
                    )

                    // 3. Prepare for drawing overlay relative to base image's corner (0,0)
                    drawContext.canvas.translate(-(base.width * drawScale / 2), -(base.height * drawScale / 2))

                    // 4. Draw aspect-fit preview of the watermark using transformed full-res x,y coordinates
                    activeOverlay?.let { over ->
                        val targetOw = base.width * scale
                        val aspect = over.height.toFloat() / over.width
                        val targetOh = targetOw * aspect

                        drawContext.canvas.save()
                        // Move to relative center and rotate
                        drawContext.canvas.translate(x * drawScale, y * drawScale)
                        drawContext.canvas.rotate(rotation)
                        
                        drawImage(
                            over.asImageBitmap(),
                            dstOffset = androidx.compose.ui.unit.IntOffset(-(targetOw * drawScale / 2).toInt(), -(targetOh * drawScale / 2).toInt()),
                            dstSize = androidx.compose.ui.unit.IntSize((targetOw * drawScale).toInt(), (targetOh * drawScale).toInt()),
                            alpha = opacity
                        )
                        drawContext.canvas.restore()
                    }

                    // Done with relative drawing
                    drawContext.canvas.restore()
                }
                
                // --- BASE IMAGE ROTATION BUTTON ---
                IconButton(
                    onClick = { baseRotation = (baseRotation + 90f) % 360f },
                    modifier = Modifier.align(Alignment.TopEnd).padding(16.dp).background(Color(0xFF1E293B).copy(alpha = 0.5f), RoundedCornerShape(8.dp))
                ) {
                    Icon(Icons.Default.Refresh, contentDescription = "Rotate Base Image", tint = Color.White)
                }
                
            } ?: Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                Text("No Image Loaded", color = Color(0xFF94A3B8), fontSize = 12.sp)
            }
        }

        // 4. Footer (Controls and Big blue save button)
        Column(modifier = Modifier.background(Color(0xFF0F172A)).padding(16.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Text("Overlay Opacity", color = Color(0xFF94A3B8), fontSize = 11.sp)
                Text("${(opacity * 100).toInt()}%", color = Color(0xFF38BDF8), fontSize = 12.sp, fontWeight = FontWeight.Bold)
            }
            Slider(value = opacity, onValueChange = { opacity = it }, colors = SliderDefaults.colors(thumbColor = Color(0xFF38BDF8), activeTrackColor = Color(0xFF38BDF8)))
            
            Spacer(Modifier.height(8.dp))
            
            Button(
                onClick = {
                    if (baseBitmap != null && activeOverlay != null) {
                        // Start an async save process via Coroutine to keep UI responsive
                        scope.launch {
                            isSaving = true // Show progress meter
                            try {
                                // Perform full resolution processing in the background
                                withContext(Dispatchers.IO) {
                                    saveFullResolution(context, baseBitmap!!, activeOverlay!!, x, y, scale, rotation, opacity, baseRotation)
                                }
                                Toast.makeText(context, "Saved to Pictures/WaterMarker!", Toast.LENGTH_SHORT).show()
                            } catch (e: Exception) {
                                Toast.makeText(context, "Failed to save: ${e.message}", Toast.LENGTH_LONG).show()
                            } finally {
                                isSaving = false // Hide progress meter
                            }
                        }
                    } else {
                         Toast.makeText(context, "Please select both images first", Toast.LENGTH_SHORT).show()
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF38BDF8)),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text("SAVE FULL RESOLUTION", color = Color(0xFF020617), fontWeight = FontWeight.ExtraBold)
            }
        }
    }
    
    // --- SAVING PROGRESS METER DIALOG ---
    if (isSaving) {
        SavingProgressMeterDialog(message = savingMessage)
    }
}

// Composable function for the visible saving progression meter
@Composable
fun SavingProgressMeterDialog(message: String) {
    Dialog(onDismissRequest = { /* Cannot dismiss until finished */ }) {
        Box(contentAlignment = Alignment.Center, modifier = Modifier.size(150.dp).background(Color(0xFF0F172A).copy(alpha = 0.95f), RoundedCornerShape(16.dp)).padding(24.dp)) {
            Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.Center) {
                CircularProgressIndicator(color = Color(0xFF38BDF8), modifier = Modifier.size(48.dp))
                Spacer(Modifier.height(16.dp))
                Text(message, color = Color.White, fontSize = 14.sp)
            }
        }
    }
}

// Utility to rotate a point vector by a set angle
fun rotateVector(vector: Offset, degrees: Float): Offset {
    val rad = toRadians(degrees.toDouble())
    val cosA = cos(rad)
    val sinA = sin(rad)
    return Offset(
        (vector.x * cosA - vector.y * sinA).toFloat(),
        (vector.x * sinA + vector.y * cosA).toFloat()
    )
}

fun decodeUri(context: Context, uri: Uri): Bitmap? {
    return try {
        val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
        // Ensure mutable in ARGB_8888 for JNI locking
        val options = BitmapFactory.Options().apply { inMutable = true }
        BitmapFactory.decodeStream(inputStream, null, options)
    } catch (e: Exception) { null }
}

// Full resolution blending and saving logic, executed in the background coroutine
fun saveFullResolution(context: Context, base: Bitmap, overlay: Bitmap, x: Float, y: Float, scale: Float, rotation: Float, opacity: Float, baseRotation: Float) {
    // 1. Create a clean mutable copy of the original base image to process on
    var baseToSave = base.copy(Bitmap.Config.ARGB_8888, true)

    // 2. APPLY BASE ROTATION *IN KOTLIN* BEFORE BLENDING
    // This allows the save process to reflect the rotated orientation you see in the UI, 
    // without requiring an expensive change to the C++ native blending engine.
    if (baseRotation % 360f != 0f) {
        val matrix = GMatrix()
        matrix.postRotate(baseRotation)
        // Create a new bitmap with the rotation applied
        baseToSave = Bitmap.createBitmap(baseToSave, 0, 0, baseToSave.width, baseToSave.height, matrix, true)
    }

    // 3. Run Native Blending Engine (blocking, native operation)
    NativeEngine().blendImages(baseToSave, overlay, x, y, scale, rotation, opacity)

    // 4. Write back full resolution result to Media Store
    val filename = "WM_${System.currentTimeMillis()}.png"
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
            baseToSave.compress(Bitmap.CompressFormat.PNG, 100, stream)
        }
    }
}

// Function to dynamically generate a "cutout" style text overlay in Kotlin
fun generateCutoutOverlayBitmap(): Bitmap? {
    val width = 600
    val height = 200
    val bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
    val canvas = android.graphics.Canvas(bitmap)

    // Fully transparent base layer
    canvas.drawColor(android.graphics.Color.TRANSPARENT)

    // Set up text paint with standardhanddrawn-styletypeface (justNormalisProgrammatic enough)
    val textPaint = GPaint().apply {
        color = GColor.WHITE
        textSize = 40f
        typeface = GTypeface.create(GTypeface.DEFAULT, GTypeface.NORMAL)
        textAlign = GPaint.Align.CENTER
        isAntiAlias = true
    }

    val text = "CARDS AND COLLECTIBLES"
    val textBounds = GRect()
    textPaint.getTextBounds(text, 0, text.length, textBounds)
    val textHeight = textBounds.height()

    // Create dark "cutout" rectangle proportional to text size plus padding
    val padding = 50f
    val cutoutLeft = (width / 2f) - (textPaint.measureText(text) / 2f) - padding
    val cutoutRight = (width / 2f) + (textPaint.measureText(text) / 2f) + padding
    val cutoutTop = (height / 2f) - (textHeight / 2f) - padding
    val cutoutBottom = (height / 2f) + (textHeight / 2f) + padding

    val cutoutPaint = GPaint().apply {
        color = GColor.argb(180, 0, 0, 0) // Semi-transparent black cutout box
        style = GPaint.Style.FILL
    }
    canvas.drawRect(cutoutLeft, cutoutTop, cutoutRight, cutoutBottom, cutoutPaint)
    
    // Draw centered text
    canvas.drawText(text, width / 2f, (height / 2f) + (textHeight / 3f), textPaint)

    return bitmap
}
"""

    files = {
        "app/src/main/java/com/watermarker/NativeEngine.kt": native_engine_content,
        "app/src/main/java/com/watermarker/MainActivity.kt": main_activity_content
    }

    print("✅ Kotlin UI Updated. Live Preview, Base Image Rotation, and Saving Progress Meter added.")
    for path, content in files.items():
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content.strip())
            print(f"Generated: {path}")
        except Exception as e:
            print(f"Failed to write {path}: {e}")

if __name__ == "__main__":
    generate_kotlin_ui()
