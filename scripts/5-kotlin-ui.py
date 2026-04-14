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
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import com.google.android.gms.ads.*
import com.google.android.gms.ads.appopen.AppOpenAd
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    private var appOpenAd: AppOpenAd? = null
    private val adUnitId = "ca-app-pub-7732503595590477/4459993522"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Initialize Mobile Ads SDK
        MobileAds.initialize(this) {}
        loadAd()

        setContent { WaterMarkerUI(onShowAd = { showAdIfAvailable() }) }
    }

    private fun loadAd() {
        val request = AdRequest.Builder().build()
        AppOpenAd.load(this, adUnitId, request, object : AppOpenAd.AppOpenAdLoadCallback() {
            override fun onAdLoaded(ad: AppOpenAd) {
                appOpenAd = ad
            }
            override fun onAdFailedToLoad(loadAdError: LoadAdError) {
                appOpenAd = null
            }
        })
    }

    private fun showAdIfAvailable() {
        appOpenAd?.let {
            it.fullScreenContentCallback = object : FullScreenContentCallback() {
                override fun onAdDismissedFullScreenContent() {
                    appOpenAd = null
                    loadAd() // Load the next one
                }
            }
            it.show(this)
        } ?: loadAd()
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WaterMarkerUI(onShowAd: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val snackbarHostState = remember { SnackbarHostState() }
    
    var baseBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var activeOverlay by remember { mutableStateOf<Bitmap?>(null) }
    
    // UI State
    var fileName by remember { mutableStateOf("MyWatermark") }
    var outputFormat by remember { mutableStateOf("JPG") }
    var overlayX by remember { mutableStateOf(0f) }
    var overlayY by remember { mutableStateOf(0f) }
    var overlayScale by remember { mutableStateOf(1f) }
    var overlayRotation by remember { mutableStateOf(0f) }
    var baseRotation by remember { mutableStateOf(0f) }
    var opacity by remember { mutableStateOf(1.0f) }
    var exportQuality by remember { mutableStateOf(0.9f) }
    var isSaving by remember { mutableStateOf(false) }

    val formats = listOf("PNG", "JPG", "WEBP")

    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { baseBitmap = decodeUri(context, it) }
    }
    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { activeOverlay = decodeUri(context, it) }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = Color(0xFF020617)
    ) { paddingValues ->
        Column(modifier = Modifier.fillMaxSize().padding(paddingValues)) {
            
            // Toolbar with Ad Button
            Row(modifier = Modifier.fillMaxWidth().padding(8.dp), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Button(onClick = { basePicker.launch("image/*") }) { Text("SUBJECT", fontSize = 10.sp) }
                // Dynamic Ad Button
                TextButton(onClick = onShowAd) { 
                    Text("SUPPORT US (AD)", color = Color(0xFFFACC15), fontSize = 10.sp, fontWeight = FontWeight.Bold) 
                }
                Button(onClick = { overlayPicker.launch("image/*") }) { Text("OVERLAY", fontSize = 10.sp) }
            }

            // Canvas Area
            BoxWithConstraints(modifier = Modifier.weight(1f).fillMaxWidth().background(Color.Black).clipToBounds()) {
                val constraints = this
                baseBitmap?.let { base ->
                    val isPortrait = (baseRotation / 90f) % 2 != 0f
                    val bw = if (isPortrait) base.height else base.width
                    val bh = if (isPortrait) base.width else base.height
                    val canvasRatio = constraints.maxWidth.value / constraints.maxHeight.value
                    val imageRatio = bw.toFloat() / bh.toFloat()
                    val fitScale = if (imageRatio > canvasRatio) constraints.maxWidth.value / bw.toFloat() else constraints.maxHeight.value / bh.toFloat()

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
                        drawContext.canvas.save()
                        drawContext.canvas.rotate(baseRotation)
                        drawImage(base.asImageBitmap(), dstOffset = IntOffset(-base.width / 2, -base.height / 2))
                        drawContext.canvas.restore()

                        activeOverlay?.let { over ->
                            drawContext.canvas.save()
                            drawContext.canvas.translate(overlayX, overlayY)
                            drawContext.canvas.rotate(overlayRotation)
                            drawContext.canvas.scale(overlayScale, overlayScale)
                            drawImage(over.asImageBitmap(), alpha = opacity, dstOffset = IntOffset(-over.width / 2, -over.height / 2))
                            drawContext.canvas.restore()
                        }
                        drawContext.canvas.restore()
                    }
                }
            }

            // Controls
            Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))) {
                Column(modifier = Modifier.padding(16.dp)) {
                    OutlinedTextField(value = fileName, onValueChange = { fileName = it }, label = { Text("Filename") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
                    Spacer(Modifier.height(8.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        formats.forEach { format ->
                            FilterChip(selected = outputFormat == format, onClick = { outputFormat = format }, label = { Text(format) })
                        }
                    }
                    Slider(value = exportQuality, onValueChange = { exportQuality = it })
                    Button(
                        onClick = {
                            if (baseBitmap != null && activeOverlay != null) {
                                scope.launch {
                                    isSaving = true
                                    saveCustomFormat(context, baseBitmap!!, activeOverlay!!, overlayX, overlayY, overlayScale, overlayRotation, opacity, baseRotation, fileName, outputFormat, exportQuality)
                                    isSaving = false
                                    snackbarHostState.showSnackbar("Exported successfully!")
                                }
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF38BDF8))
                    ) {
                        Text("EXPORT IMAGE", fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

fun decodeUri(context: Context, uri: Uri): Bitmap? {
    return try {
        context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, BitmapFactory.Options().apply { inMutable = true }) }
    } catch (e: Exception) { null }
}

suspend fun saveCustomFormat(context: Context, base: Bitmap, overlay: Bitmap, x: Float, y: Float, s: Float, r: Float, a: Float, baseRot: Float, name: String, format: String, quality: Float): Boolean {
    return withContext(Dispatchers.IO) {
        try {
            val matrixBase = Matrix().apply { postRotate(baseRot) }
            val finalBase = Bitmap.createBitmap(base, 0, 0, base.width, base.height, matrixBase, true)
            val result = finalBase.copy(Bitmap.Config.ARGB_8888, true)
            val canvas = Canvas(result)
            if (format == "JPG") canvas.drawColor(android.graphics.Color.WHITE)
            val paint = Paint().apply { alpha = (a * 255).toInt(); isFilterBitmap = true }
            val matrixOverlay = Matrix().apply {
                postTranslate(-overlay.width / 2f, -overlay.height / 2f)
                postScale(s, s)
                postRotate(r)
                postTranslate(result.width / 2f + x, result.height / 2f + y)
            }
            canvas.drawBitmap(overlay, matrixOverlay, paint)
            val ext = format.lowercase()
            val compressFormat = when (format) {
                "JPG" -> Bitmap.CompressFormat.JPEG
                "WEBP" -> if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) Bitmap.CompressFormat.WEBP_LOSSLESS else Bitmap.CompressFormat.WEBP
                else -> Bitmap.CompressFormat.PNG
            }
            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, "$name.$ext")
                put(MediaStore.MediaColumns.MIME_TYPE, "image/$ext")
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) put(MediaStore.MediaColumns.RELATIVE_PATH, "Pictures/WaterMarker")
            }
            val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
            uri?.let { context.contentResolver.openOutputStream(it)?.use { stream -> result.compress(compressFormat, (quality * 100).toInt(), stream) } }
            true
        } catch (e: Exception) { false }
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
    print("✅ AdMob Logic and UI updated.")

if __name__ == "__main__":
    generate_ui()
