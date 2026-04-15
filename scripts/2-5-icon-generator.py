import os
import subprocess
import base64

# A valid 64x64 blue PNG fallback to prevent Windows thumbnail crashes
fallback_png = b'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAABRSURBVGhD7c8BDQAgAMBAl4M/jykYcEjS213ny1n05yT6cxL9OYn+nER/TqI/J9Gfk+jPSfTnJPpzEv05if6cRH9Ooj8n0Z+T6M9J9Ock+nMS/Tln/AFM4Q20c15yFAAAAABJRU5ErkJggg=='

def generate_icons():
    print("🎨 Generating dynamic APK icons with ImageMagick...")
    res_dir = "app/src/main/res"
    base_icon_path = "temp_base_icon.png"
    
    # 1. Safely locate ImageMagick (Avoids Windows 'convert.exe' fatal conflict)
    magick_cmd = "magick" 
    try:
        subprocess.run([magick_cmd, "-version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        magick_cmd = "convert" # Fallback for native Linux runners

    cmd = [
        magick_cmd, "-size", "512x512",
        "radial-gradient:#38BDF8-#0284C7",
        "-fill", "white", "-gravity", "center",
        "-font", "sans-serif", "-pointsize", "220",
        "-draw", "text 0,0 'WM'",
        base_icon_path
    ]
    
    success = False
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        success = True
    except Exception as e:
        print(f"⚠️ ImageMagick failed or is missing. Using safe fallback PNG to prevent crashes. ({e})")
        with open(base_icon_path, "wb") as f: f.write(base64.b64decode(fallback_png))

    sizes = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192,
        "mipmap-anydpi-v26": 0
    }

    # 2. Generate all Icon Sizes
    for folder, size in sizes.items():
        dir_path = os.path.join(res_dir, folder)
        os.makedirs(dir_path, exist_ok=True)
        
        if folder == "mipmap-anydpi-v26":
            xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>'''
            with open(os.path.join(dir_path, "ic_launcher.xml"), "w") as f: f.write(xml_content)
            with open(os.path.join(dir_path, "ic_launcher_round.xml"), "w") as f: f.write(xml_content)
        else:
            out_path = os.path.join(dir_path, "ic_launcher.png")
            round_path = os.path.join(dir_path, "ic_launcher_round.png")
            fg_path = os.path.join(dir_path, "ic_launcher_foreground.png")
            
            if success:
                subprocess.run([magick_cmd, base_icon_path, "-resize", f"{size}x{size}", out_path], check=True)
                subprocess.run([magick_cmd, base_icon_path, "-resize", f"{size}x{size}", round_path], check=True)
                subprocess.run([magick_cmd, base_icon_path, "-resize", f"{size}x{size}", fg_path], check=True)
            else:
                with open(out_path, "wb") as f: f.write(base64.b64decode(fallback_png))
                with open(round_path, "wb") as f: f.write(base64.b64decode(fallback_png))
                with open(fg_path, "wb") as f: f.write(base64.b64decode(fallback_png))
    
    # 3. Create Adaptive Background Resource
    val_dir = os.path.join(res_dir, "values")
    os.makedirs(val_dir, exist_ok=True)
    with open(os.path.join(val_dir, "ic_launcher_background.xml"), "w") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#0284C7</color>\n</resources>')
    
    if os.path.exists(base_icon_path): os.remove(base_icon_path)
    print("✅ Crash-proof Icon generation complete!")

if __name__ == "__main__":
    generate_icons()
