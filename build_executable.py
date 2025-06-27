#!/usr/bin/env python3
"""
Build script for Vanguard Viz Desktop executable
Creates a standalone executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """Main build function"""
    
    print("🔧 Vanguard Viz Desktop - Build Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("vanguard_viz_desktop.py").exists():
        print("❌ Error: vanguard_viz_desktop.py not found!")
        print("Please run this script from the Vanguard Viz directory.")
        return 1
    
    # Check if PyInstaller is available
    try:
        import PyInstaller
        print(f"✅ PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✅ PyInstaller installed successfully")
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            return 1
    
    # Clean previous builds
    build_dirs = ["build", "dist", "__pycache__"]
    for dir_name in build_dirs:
        if Path(dir_name).exists():
            print(f"🧹 Cleaning {dir_name}/")
            shutil.rmtree(dir_name)
    
    # Remove spec file if it exists
    spec_file = "vanguard_viz_desktop.spec"
    if Path(spec_file).exists():
        print(f"🧹 Removing {spec_file}")
        os.remove(spec_file)
    
    # Create the executable
    print("\n🔨 Building executable...")
    
    # PyInstaller command
    pyinstaller_args = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Don't show console window (for GUI app)
        "--name", "VanguardViz",  # Name of the executable
        "--add-data", "desktop_manifest_helper.py;.",  # Include helper module
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "requests",
        "--hidden-import", "json",
        "--hidden-import", "threading",
        "--hidden-import", "webbrowser",
        "--hidden-import", "pathlib",
        "--clean",  # Clean PyInstaller cache
        "vanguard_viz_desktop.py"
    ]
    
    # Add icon if available
    if Path("icon.ico").exists():
        pyinstaller_args.insert(-1, "--icon")
        pyinstaller_args.insert(-1, "icon.ico")
        print("✅ Using icon.ico for executable")
    
    try:
        print("Running PyInstaller...")
        result = subprocess.run(pyinstaller_args, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build successful!")
            
            # Check if executable was created
            exe_path = Path("dist/VanguardViz.exe")
            if exe_path.exists():
                exe_size = exe_path.stat().st_size / (1024 * 1024)  # Size in MB
                print(f"📦 Executable created: {exe_path}")
                print(f"📊 Size: {exe_size:.1f} MB")
                
                # Create release directory
                release_dir = Path("release")
                if release_dir.exists():
                    shutil.rmtree(release_dir)
                release_dir.mkdir()
                
                # Copy executable to release directory
                shutil.copy2(exe_path, release_dir / "VanguardViz.exe")
                
                # Create README for release
                readme_content = """# Vanguard Viz Desktop v1.0

## Installation
1. Download VanguardViz.exe
2. Run the executable - no installation required!

## First Run
1. Get your Bungie API key from: https://www.bungie.net/en/Application
2. Enter your API key in the Configuration tab
3. Enter your Bungie name and code (e.g., "Guardian#1234")
4. Start collecting your Destiny 2 data!

## Features
- Weapon usage statistics
- Activity history tracking
- Manifest data browsing
- Data export capabilities
- Offline manifest caching

## Support
If you encounter any issues, please check:
1. Your internet connection
2. Your Bungie API key is valid
3. Your Bungie name and code are correct

## Privacy
All data is processed locally on your computer. Your API key and data are never sent anywhere except to Bungie's official API.
"""
                
                with open(release_dir / "README.txt", "w") as f:
                    f.write(readme_content)
                
                print(f"📁 Release package created in: {release_dir.absolute()}")
                
                # Optional: Create a zip file
                try:
                    shutil.make_archive("VanguardViz_v1.0_Windows", "zip", release_dir)
                    print("📦 Zip package created: VanguardViz_v1.0_Windows.zip")
                except Exception as e:
                    print(f"⚠️ Could not create zip package: {e}")
                
            else:
                print("❌ Executable not found after build")
                return 1
                
        else:
            print("❌ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return 1
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return 1
    
    print("\n🎉 Build completed successfully!")
    print("\n📋 Next steps:")
    print("1. Test the executable in the release/ directory")
    print("2. Share VanguardViz_v1.0_Windows.zip with users")
    print("3. Users just need to extract and run VanguardViz.exe")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
