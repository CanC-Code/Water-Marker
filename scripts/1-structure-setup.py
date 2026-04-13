import os

def create_structure():
    # Logic Fix: Ensure we are working from the project root
    if os.path.basename(os.getcwd()) == "scripts":
        os.chdir("..")
        
    folders = [
        "app/src/main/cpp",
        "app/src/main/java/com/watermarker",
        "app/src/main/res/drawable",
        "app/src/main/res/layout",
        "app/src/main/res/values",
        "app/src/main/res/mipmap-hdpi",
        "gradle/wrapper"
    ]
    
    print("🚀 Starting Water-Marker scaffolding...")
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"  Created: {folder}")

if __name__ == "__main__":
    create_structure()
