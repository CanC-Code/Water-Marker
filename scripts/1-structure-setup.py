import os

def create_structure():
    # Define the essential Android project folders
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
        try:
            os.makedirs(folder, exist_ok=True)
            # Create a .gitkeep so git tracks empty directories if needed
            with open(os.path.join(folder, ".gitkeep"), "w") as f:
                pass
            print(f"✅ Created: {folder}")
        except Exception as e:
            print(f"❌ Error creating {folder}: {e}")

    print("\n✨ Structure complete. Ready for Gradle configuration.")

if __name__ == "__main__":
    create_structure()
